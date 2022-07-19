import unittest
from unittest.mock import patch
from io import StringIO
from typing import Callable
from collections import namedtuple

from combine import checkIllegal, splitExt, checkDup, checkCombine

argParser = namedtuple(
    'argParser',
    [
        'paths'
    ]
)

@patch('sys.stdout', new_callable=StringIO)
def get_print(func: Callable, input, mock_stdout) -> str:
    func(input)
    return mock_stdout.getvalue().strip()

class Test_check_safe_combine_databases(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_checkIllegal(self):
        # major function implemented in safeName(), also tested there.
        sources = [
            'test1_.*)]{.faa.gz',
            '2test_sp. a.fna.xz',
            '2tes_(t)_sp. a.fna.xz',
            'correct_name.fna.xz'
        ]
        corr = [
            ('test1_.*)]{.faa.gz', 'test1_._.faa.gz'),
            ('2test_sp. a.fna.xz', '2test_sp._a.fna.xz'),
            ('2tes_(t)_sp. a.fna.xz', '2tes_t_sp._a.fna.xz'),
            ('correct_name.fna.xz', None),
        ]
        for tupT, tupC in zip(checkIllegal(sources), corr):
            self.assertTupleEqual(tupT, tupC)

    def test_splitExt(self):
        self.assertTupleEqual(splitExt('file.name.faa.gz'), ('file.name', '.faa.gz'))
        self.assertTupleEqual(splitExt('file.name.fna.xz'), ('file.name', '.fna.xz'))
        self.assertTupleEqual(splitExt('file.name.fna'), ('file.name', '.fna'))
        self.assertTupleEqual(splitExt(None), (None, None))
    

    def test_checkDup_checkCombine(self):
        inputA = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
                ('file4.aa.xz', None),
                ('filE2.faa.xz', None),
                ('file2.fna.xz', None)
            ]
        }
        outputA_expects = [
            "Found duplicated name file2:",
                "\ttests/test_data/tdbs/tdb1/filE2.faa.xz",
                "\ttests/test_data/tdbs/tdb1/file2.fna.xz",
            "Found 1 none unique name(s), 4 unique one(s).",
            "Total checked files: 5",
        ]
        inputB = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
                ('filE2.faa.xz', None),
                ('file2.fna.xz', None)
            ],
            'tests/test_data/tdbs/tdb2': [
                ('file5.fna.gz', None),
            ],
            'tests/test_data/tdbs/tdb3': [
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
                ('illeGal patt(a)[b*].txt.gz', 'illeGal_patt_a_b_.txt.gz')
            ]
        }
        outputB_expects = [
            "Found duplicated name file2:",
                "\ttests/test_data/tdbs/tdb1/filE2.faa.xz",
                "\ttests/test_data/tdbs/tdb1/file2.fna.xz",
            "Found duplicated name illegal_patt_a_b_:",
                "\ttests/test_data/tdbs/tdb1/illegal patt(a)[b*].txt",
                    "\t\ttests/test_data/tdbs/tdb1/illegal_patt_a_b_.txt",
                "\ttests/test_data/tdbs/tdb3/illegal patt(a)[b*].txt",
                    "\t\ttests/test_data/tdbs/tdb3/illegal_patt_a_b_.txt",
                "\ttests/test_data/tdbs/tdb3/illeGal patt(a)[b*].txt.gz",
                    "\t\ttests/test_data/tdbs/tdb3/illeGal_patt_a_b_.txt.gz",
            "Found 2 none unique name(s), 4 unique one(s).",
            "Total checked files: 7",
        ]
        outputA = get_print(checkDup, inputA)
        outputB = get_print(checkDup, inputB)

        linesA = outputA.split('\n')
        for exp in outputA_expects:
            self.assertIn(exp, linesA)
        
        linesB = outputB.split('\n')
        for exp in outputB_expects:
            self.assertIn(exp, linesB)
        self.assertNotIn("tests/test_data/tdbs/tdb2", linesB)

        outputC = get_print(checkCombine, ['tests/test_data/tdbs/tdb1', 'tests/test_data/tdbs/tdb2', 'tests/test_data/tdbs/tdb3'])
        linesC = outputC.split('\n')
        outputC_expects = [
            'Checking dirs as combined:'
        ]
        for exp in outputC_expects:
            self.assertIn(exp, linesC)
        excepts_toCheck_consecutively = [
            [
                "Checking dir tests/test_data/tdbs/tdb2 individually.",
                "No illegal characters found.",
                "No possible duplication found in dir(s):",
                "\ttests/test_data/tdbs/tdb2",
            ]
        ]
        for exps in excepts_toCheck_consecutively:
            foundFirst = False
            for i, l in enumerate(linesC):
                if exps[0] == l:
                    foundFirst = True
                    self.assertListEqual(exps, linesC[i:i+len(exps)])
                    break
            self.assertTrue(foundFirst)
        


if __name__ == "__main__":
    unittest.main()
