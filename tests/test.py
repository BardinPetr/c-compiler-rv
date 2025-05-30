import pytest
from pytest_golden.plugin import GoldenTestFixture

from parser.parser import do_parse
from syntax.transformer import do_ast

@pytest.mark.golden_test("golden/*.yml")
def test_golden(golden: GoldenTestFixture):
    test_level = golden['test_level']
    if 'parse' in test_level:
        text = golden['text']
        tree = do_parse(text)
        assert tree.pretty() == golden.out['parse_tree'], "Parse tree mismatch"

    if 'ast' in test_level:
        ast = do_ast(tree)
        assert str(ast) == golden.out['ast_tree'], "AST mismatch"

    # if 'asm' in test_level:
    #     asm = do_asm(ast)
    #     assert str(asm) == golden.out['asm'], "ASM mismatch"
