import sys
from dataclasses import dataclass
from enum import StrEnum, auto
from pprint import pprint
from typing import *

from lark import ast_utils, Transformer

from parser.parser import do_parse
from utils import string_unescape


class _Ast(ast_utils.Ast):
    pass


class _Statement(_Ast):
    pass


"""
    Data
"""


class DataType(StrEnum):
    INT = auto()
    CHAR = auto()
    STRING = auto()
    VOID = auto()

    def __repr__(self):
        return f"DT<{self.value}>"

    def __str__(self):
        return self.__repr__()


type Literal = _Literal


class _Literal(_Ast):
    pass


@dataclass
class LitInt(_Literal):
    value: int


@dataclass
class LitChar(_Literal):
    value: str


@dataclass
class LitString(_Literal):
    value: str


"""
   Top level 
"""


class _DeclGlobal(_Ast):
    pass


@dataclass
class VarSig(_Ast):
    type: DataType
    name: str

    def __repr__(self):
        return f"Var<{self.name}:{self.type}>"


@dataclass
class DeclFunSigParams(_Ast, ast_utils.AsList):
    params: List[VarSig]


@dataclass
class DeclFunSig(_DeclGlobal):
    ret_type: DataType
    name: str
    args: List[VarSig] | DeclFunSigParams

    def __post_init__(self):
        self.args = self.args.params


@dataclass
class DeclFun(_DeclGlobal):
    sig: DeclFunSig
    body: Optional[List[Any]] = None


@dataclass
class DeclVar(_DeclGlobal):
    sig: VarSig
    init: Optional[_Literal] = None

    def __post_init__(self):
        if self.init is None and self.sig.type == DataType.STRING:
            raise Exception("Empty string declaration disallowed")


@dataclass
class Prog:
    globals: List[DeclVar]
    functions: Dict[str, DeclFun]


"""
"""


# class Expression(_Ast):
#     pass


# @dataclass
# class Start(_Ast, ast_utils.AsList):
#     decls: List[_Statement]


class ToAst(Transformer):

    def TYP(self, s):
        return DataType[str(s).upper()]

    def CNAME(self, s):
        return str(s)

    def SIG_INTEGER(self, s):
        return int(s)

    def STRING_CHAR(self, s):
        s = string_unescape(str(s))
        assert len(s) == 1
        return s

    def STRING(self, s):
        return string_unescape(s)

    #
    # def lit_char(self, s):
    #     return s[0]
    #
    # def lit_string(self, s):
    #     return ''.join(s)
    #
    # def lit_int(self, s):
    #     return s[0]

    def start(self, x):
        funcs = {i.sig.name: i for i in x if isinstance(i, DeclFun)}
        funcs.update({i.name: DeclFun(i) for i in x if isinstance(i, DeclFunSig)})
        return Prog(
            globals=[i for i in x if isinstance(i, DeclVar)],
            functions=funcs
        )


transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())


def do_ast(tree):
    return transformer.transform(tree)


def demo():
    x = open("/home/petr/projects/compiler-py-impl/tests/golden/test.c").read()
    x = do_parse(x)
    with open("/home/petr/projects/compiler-py-impl/tests/golden/test.p", "w") as f:
        f.write(x.pretty())
    x = do_ast(x)
    with open("/home/petr/projects/compiler-py-impl/tests/golden/test.a", "w") as f:
        pprint(x, f, width=40)


demo()
