import sys
from dataclasses import dataclass
from enum import StrEnum, auto
from multiprocessing.managers import Token
from pprint import pprint
from typing import *

from lark import ast_utils, Transformer, v_args, Tree, Token

from parser.parser import do_parse
from syntax.extypes import UOP_MATCH, UOp, BOp, BOP_MATCH
from utils import string_unescape

"""
    Base parts
"""


class _Ast(ast_utils.Ast):
    pass


class _Expression(_Ast):
    pass


class _Statement(_Ast):
    pass


type Expression = _Expression
type Statement = _Statement
type Block = List[_Statement]

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
    body: Optional[Block] = None


@dataclass
class DeclStaticVar(_DeclGlobal):
    sig: VarSig
    init: Optional[_Literal] = None

    def __post_init__(self):
        if self.init is None and self.sig.type == DataType.STRING:
            raise Exception("Empty string declaration disallowed")


@dataclass
class Prog:
    globals: List[DeclStaticVar]
    functions: Dict[str, DeclFun]


"""
    Statements
"""


@dataclass
class StIf(_Statement):
    check_expr: Expression
    br_true: Optional[Block]
    br_false: Optional[Block] = None

    def __post_init__(self):
        if self.br_false is not None and len(self.br_false) == 0:
            self.br_false = None
        if len(self.br_true) == 0:
            self.br_true = None


@dataclass
class StWhile(_Statement):
    check_expr: Expression
    body: Block


@dataclass
class StVarDecl(_Statement):
    sig: VarSig
    init: Optional[Expression] = None

    def __post_init__(self):
        if self.init is None and self.sig.type == DataType.STRING:
            raise Exception("Empty string declaration disallowed")


@dataclass
class StBreak(_Statement):
    pass


@dataclass
class StContinue(_Statement):
    pass


@dataclass
class StReturn(_Statement):
    value: Optional[Expression] = None


@dataclass
class StAsn(_Statement):
    dst: str
    expr: _Expression


"""
    Expressions
"""


@dataclass
class ExRdVar(_Expression):
    name: str


@dataclass
class ExLit(_Expression):
    value: Literal


@dataclass
class ExCall(_Expression):
    name: str
    args: List[Expression]

    def __init__(self, name: str, *args: List[Expression]):
        self.name = name
        self.args = args

@dataclass
class ExUnary(_Expression):
    cmd: UOp
    value: Expression


@dataclass
class ExBinary(_Expression):
    exp1: Expression
    cmd: BOp
    exp2: Expression


"""
    Other manual transforms
"""


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

    def KW_BREAK(self, _):
        return StBreak()

    def KW_CONTINUE(self, _):
        return StContinue()

    @v_args(inline=True)
    def block_or_line(self, x):
        """ unpack blocks/oneline to list """
        match x:
            case Tree(data=Token(_, "block"), children=lines):
                return lines
            case list(lines):
                return lines
            case _:
                return [x]

    def block(self, lines):
        return lines

    @v_args(inline=True)
    def ex_uop(self, x):
        match x.children:
            case [Token(_, cmd), exp]:
                pass
            case [exp, Token(_, cmd)]:
                pass
            case _:
                return None
        return ExUnary(UOP_MATCH[cmd], exp)

    @v_args(inline=True)
    def BOP(self, x):
        return BOP_MATCH[str(x)]

    def start(self, x):
        funcs = {i.sig.name: i for i in x if isinstance(i, DeclFun)}
        funcs.update({i.name: DeclFun(i) for i in x if isinstance(i, DeclFunSig)})
        return Prog(
            globals=[i for i in x if isinstance(i, DeclStaticVar)],
            functions=funcs
        )


transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())


def do_ast(tree: Tree) -> Prog:
    return transformer.transform(tree)
