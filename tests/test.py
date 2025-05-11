import pytest
from pytest_golden.plugin import GoldenTestFixture

from parser.parser import parse


@pytest.mark.golden_test("golden/*.yml")
def test_golden(golden: GoldenTestFixture):
    match golden['test_level']:
        case 'parse':
            text = golden['text']
            tree = parse(text)
            textual_result = tree.pretty()
            assert textual_result == golden.out['parse_tree'], "Parse tree mismatch"
