import unittest
from unittest.mock import patch
from io import StringIO
import os
import shutil
from typing import Callable, Any
from collections import namedtuple

from combine import checkIllegal, splitExt, checkDup, checkCombine, combineDatabases

argParser = namedtuple(
    'argParser',
    [
        'paths'
    ]
)
combinedDatabaseTarget = 'tests/test_data/combined'
combinedDatabaseTarget_ka = 'tests/test_data/combined_ka'

@patch('sys.stdout', new_callable=StringIO)
def get_print(func: Callable, input, mock_stdout) -> tuple[str, Any]:
    ret = func(input)
    return mock_stdout.getvalue().strip(), ret

class Test_check_safe_combine_databases(unittest.TestCase):
    
    @classmethod
    def tearDownClass(cls):
        for dir in [combinedDatabaseTarget, combinedDatabaseTarget_ka]:
            try:
                shutil.rmtree(dir)
            except FileNotFoundError:
                pass

    def test_checkIllegal(self):
        # major function implemented in safeName(), also tested there.
        sources = [
            'test1_.*)]{.faa.gz',
            '2test_sp. a.fna.xz',
            '2tes_(t)_sp. a.fna.xz',
            'correct_name.fna.xz'
        ]
        corr = [
            ('2tes_(t)_sp. a.fna.xz', '2tes_t_sp._a.fna.xz'),
            ('2test_sp. a.fna.xz', '2test_sp._a.fna.xz'),
            ('correct_name.fna.xz', None),
            ('test1_.*)]{.faa.gz', 'test1_._.faa.gz'),
        ]
        for tupT, tupC in zip(checkIllegal(sources), corr):
            self.assertTupleEqual(tupT, tupC)

    def test_splitExt(self):
        self.assertTupleEqual(splitExt('file.name.faa.gz'), ('file.name', '.faa.gz'))
        self.assertTupleEqual(splitExt('file.name.fna.xz'), ('file.name', '.fna.xz'))
        self.assertTupleEqual(splitExt('file.name.fna'), ('file.name', '.fna'))
        self.assertTupleEqual(splitExt(None), (None, None))
    

    def test_checkDup(self):
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
                ('filE2.faa.xz', None),
                ('file5.fna.gz', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
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
                "\ttests/test_data/tdbs/tdb2/filE2.faa.xz",
            "Found duplicated name illegal_patt_a_b_:",
                "\ttests/test_data/tdbs/tdb1/illegal patt(a)[b*].txt",
                    "\t\ttests/test_data/tdbs/tdb1/illegal_patt_a_b_.txt",
                "\ttests/test_data/tdbs/tdb2/illegal patt(a)[b*].txt",
                    "\t\ttests/test_data/tdbs/tdb2/illegal_patt_a_b_.txt",
                "\ttests/test_data/tdbs/tdb3/illegal patt(a)[b*].txt",
                    "\t\ttests/test_data/tdbs/tdb3/illegal_patt_a_b_.txt",
                "\ttests/test_data/tdbs/tdb3/illeGal patt(a)[b*].txt.gz",
                    "\t\ttests/test_data/tdbs/tdb3/illeGal_patt_a_b_.txt.gz",
            "Found 2 none unique name(s), 4 unique one(s).",
            "Total checked files: 9",
        ]
        retB_keepFirst_expects = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('filE2.faa.xz', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
            ],
            'tests/test_data/tdbs/tdb2': [
                ('file5.fna.gz', None),
            ],
            'tests/test_data/tdbs/tdb3': [
            ]
        }
        retB_keepAll_expects = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('filE2.faa.xz', None),
                ('file2.fna.xz', 'file2_name_rep1.fna.xz'),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
            ],
            'tests/test_data/tdbs/tdb2': [
                ('filE2.faa.xz', 'filE2_name_rep2.faa.xz'),
                ('file5.fna.gz', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b__name_rep1.txt'),
                # do not change the double underscore __, you need origional name anyway.
            ],
            'tests/test_data/tdbs/tdb3': [
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b__name_rep2.txt'),
                ('illeGal patt(a)[b*].txt.gz', 'illeGal_patt_a_b__name_rep3.txt.gz'),
            ]
        }

        outputA, retA = get_print(checkDup, inputA)
        linesA = outputA.split('\n')
        for exp in outputA_expects:
            self.assertIn(exp, linesA)
            linesA.remove(exp)
        self.assertEqual(len(linesA), 0, linesA)
        self.assertEqual(retA.keys(), inputA.keys())

        outputB, retB = get_print(checkDup, inputB)
        linesB = outputB.split('\n')
        for exp in outputB_expects:
            self.assertIn(exp, linesB)
            linesB.remove(exp)
        self.assertEqual(len(linesB), 0, linesB)
        self.assertNotIn("tests/test_data/tdbs/tdb2", linesB)
        self.assertEqual(retB.keys(), inputB.keys())
        for p in retB:
            self.assertListEqual(retB[p], retB_keepFirst_expects[p], retB)
        
        retB_ka = checkDup(inputB, keep="all")
        for p in retB_ka:
            self.assertListEqual(retB_ka[p], retB_keepAll_expects[p], retB_ka)

    def test_checkCombine(self):
        outputC, retC = get_print(checkCombine, ['tests/test_data/tdbs/tdb1', 'tests/test_data/tdbs/tdb2', 'tests/test_data/tdbs/tdb3'])
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
        
        retC_keepFirst_expects = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('filE2.faa.xz', None),
                ('file3.faa.xz', None),
                ('file4.aa.xz', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
            ],
            'tests/test_data/tdbs/tdb2': [
                ('file5.fna.gz', None)
            ],
            'tests/test_data/tdbs/tdb3': [
            ]
        }
        retC_keepAll_expects = {
            'tests/test_data/tdbs/tdb1': [
                ('file1.txt', None),
                ('filE2.faa.xz', None),
                ('file2.fna.xz', 'file2_name_rep1.fna.xz'),
                ('file3.faa.xz', None),
                ('file4.aa.xz', None),
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b_.txt'),
            ],
            'tests/test_data/tdbs/tdb2': [
                ('file3.fna.gz', 'file3_name_rep1.fna.gz'),
                ('FIle4.aa.gz', 'FIle4_name_rep1.aa.gz'),
                ('file5.fna.gz', None),
            ],
            'tests/test_data/tdbs/tdb3': [
                ('illegal patt(a)[b*].txt', 'illegal_patt_a_b__name_rep1.txt'),
                ('illeGal patt(a)[b*].txt.gz', 'illeGal_patt_a_b__name_rep2.txt.gz'),
            ]
        }
        for p in retC:
            self.assertListEqual(retC[p], retC_keepFirst_expects[p], retC)
        retC_ka = checkCombine(
            ['tests/test_data/tdbs/tdb1', 'tests/test_data/tdbs/tdb2', 'tests/test_data/tdbs/tdb3'],
            keep='all'
        )
        for p in retC_ka:
            self.assertListEqual(retC_ka[p], retC_keepAll_expects[p], retC_ka)

        
    def test_combineDatabases(self):
        combineDatabases(
            ['tests/test_data/tdbs/tdb1', 'tests/test_data/tdbs/tdb2', 'tests/test_data/tdbs/tdb3'],
            combinedDatabaseTarget
        )
        expectFiles = [
            'filE2.faa.xz',
            'file1.txt',
            'file3.faa.xz',
            'file4.aa.xz',
            'file5.fna.gz',
            'illegal_patt_a_b_.txt'
        ]
        combinedDirFiles = sorted(os.listdir(combinedDatabaseTarget))
        self.assertListEqual(combinedDirFiles, expectFiles, combinedDirFiles)

        combineDatabases(
            ['tests/test_data/tdbs/tdb1', 'tests/test_data/tdbs/tdb2', 'tests/test_data/tdbs/tdb3'],
            combinedDatabaseTarget_ka,
            keep='all'
        )
        expectFiles_ka = [
            'FIle4_name_rep1.aa.gz',
            'filE2.faa.xz',
            'file1.txt',
            'file2_name_rep1.fna.xz',
            'file3.faa.xz',
            'file3_name_rep1.fna.gz',
            'file4.aa.xz',
            'file5.fna.gz',
            'illeGal_patt_a_b__name_rep2.txt.gz',
            'illegal_patt_a_b_.txt',
            'illegal_patt_a_b__name_rep1.txt'
        ]
        combinedDirFiles_ka = sorted(os.listdir(combinedDatabaseTarget_ka))
        self.assertListEqual(combinedDirFiles_ka, expectFiles_ka, combinedDirFiles_ka)


if __name__ == "__main__":
    unittest.main()
