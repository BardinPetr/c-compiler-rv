import pprint

import pytest
from pytest_golden.plugin import GoldenTestFixture

from parser.parser import do_parse
from syntax.astdef import do_ast
from syntax.ast2ir import do_ir


@pytest.mark.golden_test("golden/*.yml")
def test_golden(golden: GoldenTestFixture):
    test_level = golden['test_level']
    text = golden['text']
    if 'parse' in test_level:
        tree = do_parse(text)
        assert tree.pretty() == golden.out['parse_tree'], "Parse tree mismatch"
    else:
        return

    if 'ast' in test_level:
        ast = do_ast(tree)
        assert pprint.pformat(ast, width=20) == golden.out['ast_tree'], "AST mismatch"
    else:
        return

    if 'ir' in test_level:
        ir = do_ir(ast)
        assert pprint.pformat(ir, width=20) == golden.out['ir_text'], "IR mismatch"
    else:
        return

    # if 'asm' in test_level:
    #     asm = do_asm(ir)
    #     assert str(asm) == golden.out['asm'], "ASM mismatch"
