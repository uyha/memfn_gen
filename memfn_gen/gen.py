import click

from enum import IntFlag, auto
from itertools import product
from dataclasses import dataclass


class Qualifier(IntFlag):
    none = auto()
    const = auto()
    volatile = auto()
    cv = auto()


class Ref(IntFlag):
    none = auto()
    lvalue = auto()
    rvalue = auto()


class Noexcept(IntFlag):
    no = auto()
    yes = auto()


@dataclass
class Formatter:
    free_fn_format: str
    member_fn_format: str
    member_var_format: str


@dataclass
class FreeFnConfig:
    noexcept: Noexcept

    def gen(self, formatter: Formatter):
        print(
            eval(
                f"f'''{formatter.free_fn_format}'''",
                {},
                dict(
                    type="free_fn_ptr",
                    noexcept=self.noexcept == Noexcept.yes,
                ),
            )
        )


@dataclass
class MemberVarConfig:
    def gen(self, formatter: Formatter):
        print(
            eval(
                f"f'''{formatter.member_var_format}'''",
                {},
                dict(type="member_var_ptr"),
            )
        )


@dataclass
class MemberFnConfig:
    noexcept: Noexcept
    qualifier: Qualifier
    ref: Ref

    def gen(self, formatter: Formatter):
        noexcept = self.noexcept == Noexcept.yes
        match self.qualifier:
            case Qualifier.none:
                const = False
                volatile = False
            case Qualifier.const:
                const = True
                volatile = False
            case Qualifier.volatile:
                const = False
                volatile = True
            case Qualifier.cv:
                const = True
                volatile = True

        match self.ref:
            case Ref.none:
                ref = ""
            case Ref.lvalue:
                ref = "&"
            case Ref.rvalue:
                ref = "&&"

        print(
            eval(
                f"f'''{formatter.member_fn_format}'''",
                {},
                dict(
                    type="member_fn_ptr",
                    noexcept=noexcept,
                    const=const,
                    volatile=volatile,
                    ref=ref,
                ),
            )
        )


@click.command
@click.option(
    "-c",
    "--config",
    default=0x7F3_1_3,
    help="""
    The config flag for generating function traits,
    the bits are laid out as\n
    MF(URRR QQQQ UUEE) MV(UUUB) FF(UUEE)

    U is unused bits

    UTTT are the types to be included: member_var_ptr, member_fn_ptr, and free_fn_ptr

    QQQQ are the cv qualifiers to be included: const volatile, volatile, const, and none

    URRR are the references to be included: rvalue, lvalue, and none

    UUEE are the noexcept to be included: yes, and no
    """,
)
@click.option(
    "-f",
    "--free-fn",
    default="{type} auto (*)(Args...){' noexcept ' if noexcept else ' '}-> R",
)
@click.option(
    "-f",
    "--member-fn",
    default="""{type} auto (T::*)(Args...){' const' if const else ''}{' volatile' if volatile else ''}{f' {ref}' if ref else ''}{' noexcept ' if noexcept else ' '}-> R""",
)
@click.option("-f", "--member-var", default="{type} R (T::*)")
def main(config, free_fn, member_var, member_fn):
    """
    ff is free function
    mv is member variable
    mf is member function
    """

    formatter = Formatter(
        free_fn_format=free_fn,
        member_var_format=member_var,
        member_fn_format=member_fn,
    )
    ff_noexcept = Noexcept((config & 0x000_0_3))
    for conf in map(FreeFnConfig, ff_noexcept):
        conf.gen(formatter)

    mv = (config & 0x000_1_0) != 0
    if mv:
        MemberVarConfig().gen(formatter)

    mf_noexcept = Noexcept((config & 0x00F_0_0) >> 8)
    mf_qualifier = Qualifier((config & 0x0F0_0_0) >> 12)
    mf_ref = Ref((config & 0xF00_0_0) >> 16)

    for conf in map(
        lambda args: MemberFnConfig(*args), product(mf_noexcept, mf_qualifier, mf_ref)
    ):
        conf.gen(formatter)


if __name__ == "__main__":
    main()
