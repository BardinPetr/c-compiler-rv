import codecs
import sys
from dataclasses import dataclass
from typing import List

from lark import ast_utils, Transformer

from utils import string_unescape


class _Ast(ast_utils.Ast):
    pass


class _Statement(_Ast):
    pass


class Expression(_Ast):
    pass


# class _DeclGlobals(_Ast):
#     pass


# @dataclass
# class DeclFun(_DeclGlobals):
#     pass
#
#
# @dataclass
# class DeclVar(_DeclGlobals):
#     pass


# @dataclass
# class DeclFunSig(_DeclGlobals):
#     pass


# @dataclass
# class Start(_Ast, ast_utils.AsList):
#     decls: List[_Statement]



class ToAst(Transformer):

    def SIG_INTEGER(self, s):
        return int(s)

    def STRING_CHAR(self, s):
        return string_unescape(s)

    def lit_char(self, s):
        return s[0]

    def lit_string(self, s):
        return ''.join(s)

    def lit_int(self, s):
        return s[0]


transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())


def do_ast(tree):
    return transformer.transform(tree)
