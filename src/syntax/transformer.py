import codecs
import sys

from lark import ast_utils, Transformer

class _Ast(ast_utils.Ast):
    pass

class _Statement(_Ast):
    pass

class Expression(_Ast):
    pass

class ToAst(Transformer):

    def SIG_INTEGER(self, s):
        return int(s)

    def STRING_CHAR(self, s):
        return codecs.escape_decode(s)[0].decode()

    def lit_char(self, s):
        return s[0]

    def lit_string(self, s):
        return ''.join(s)

    def lit_int(self, s):
        return s[0]


transformer = ast_utils.create_transformer(sys.modules[__name__], ToAst())


def do_ast(tree):
    return transformer.transform(tree)

