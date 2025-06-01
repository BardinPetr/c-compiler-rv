import pprint

import pytest
from pytest_golden.plugin import GoldenTestFixture

from frontend.parser import do_parse
from backend.ir2asm import do_asm
from frontend.astdef import do_ast
from middlend.ast2ir import do_ir
from tests.qemu import run_qemu


@pytest.mark.golden_test("golden/*.yml")
def test_golden(golden: GoldenTestFixture):
    test_level = golden['test_level']
    text = golden['text']
    if 'parse' in test_level:
        tree = do_parse(text)
        if 'asm' not in test_level:
            assert tree.pretty() == golden.out['parse_tree'], "Parse tree mismatch"
    else:
        return

    if 'ast' in test_level:
        ast = do_ast(tree)
        if 'asm' not in test_level:
            assert pprint.pformat(ast, width=30) == golden.out['ast_tree'], "AST mismatch"
    else:
        return

    if 'ir' in test_level:
        ir = do_ir(ast)
        assert pprint.pformat(ir, width=100) == golden.out['ir_text'], "IR mismatch"
    else:
        return

    if 'asm' in test_level:
        asm = do_asm(ir)
        assert str(asm) == golden.out['asm'], "ASM mismatch"

        stdout = run_qemu(asm)
        assert stdout.strip() == golden.out['qemu_output'], "QEMU run mismatch"
