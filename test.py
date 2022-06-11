import unittest
import os
import shutil
from collections import namedtuple

from tools import getInfoFrom, removeDup, removeEqu, getNumCtgs, \
    getExclusion, filterDownloads, filterTooManyCtgs, gatherAssemblies, \
    generateTargetDir

argParser = namedtuple(
    'args',
    [
        'dir', 'tsv', 'excludeList', 'maxCtg', 'targetDir'
    ]
)

class Test_strainNameComprehension(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_removeEqu(self):
        sources = [
            ["MA-4680", "NBRC 14893 NBRC 14893"],
            ["NBRC 14893", "MA-4680 NBRC 14893"],
            ["MA-4680", "NBRC 14893 MA-4680"],
            ["C34", "DSM 42122", "NRRL B-24963"],
        ]
        results = [
            ["MA-4680", "NBRC 14893"],
            ["NBRC 14893", "MA-4680"],
            ["MA-4680", "NBRC 14893"],
            ["C34", "DSM 42122", "NRRL B-24963"],
        ]
        for s, r in zip(sources, results):
            self.assertListEqual(removeEqu(s), r)

    def test_removeDup(self):
        sources = [
            "MA-4680 = NBRC 14893 NBRC 14893",
            "NBRC 14893 = NBRC 14893 NBRC 14893",
            "MA-4680 = NBRC 14893 MA-4680",
            "MA-4680",
            "NBRC 14893 NBRC 14893",
            "AKKAK",
            "M1154/pAMX4/pGP1416",
            "M1154 M1154",
            "C34 = DSM 42122 = NRRL B-24963",
            ""
        ]
        results = [
            "MA-4680 NBRC 14893",
            "NBRC 14893",
            "MA-4680 NBRC 14893",
            "MA-4680",
            "NBRC 14893",
            "AKKAK",
            "M1154/pAMX4/pGP1416",
            "M1154",
            "C34 DSM 42122 NRRL B-24963",
            ""
        ]
        for s, r in zip(sources, results):
            self.assertEqual(removeDup(s), r)

class test_biosequenceCounting(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def test_countCtgs(self):
        testDataDir = 'test_data/numCtgs'
        files = [
            "test.fna.gz",
            "test.gpff.gz"
        ]
        ns = [
            3,
            27
        ]
        for f, n in zip(files, ns):
            f = os.path.join(testDataDir, f)
            self.assertEqual(getNumCtgs(f), n)
        self.assertRaises(Exception, getNumCtgs, "abc.unknown.gz")

class test_basicFunctions(unittest.TestCase):
    # not biosequencereading, not strain name comprehension
    # not based on other functions
    def setUp(self) -> None:
        return super().setUp()

    def test_getExclusion(self):
        targetList = [
            'Streptomyces coelicolor M1154',
            'Streptomyces coelicolor A3(2) R4-mCherry'
        ]
        self.assertListEqual(getExclusion('test_data/exclusion.txt'), targetList)
        self.assertListEqual(getExclusion('test_data/notExist.txt'), [])

    def test_generateTargetDir(self):
        withTargetDirArgs = argParser(dir='', tsv='',
            excludeList='', maxCtg='', targetDir='targetDir')
        noneTargetDirArgs = argParser(dir='', tsv='',
            excludeList='', maxCtg='', targetDir=None)
        self.assertEqual(generateTargetDir(noneTargetDirArgs),
            os.path.realpath('.') + "-ready")
        self.assertEqual(generateTargetDir(withTargetDirArgs),
            os.path.realpath('targetDir'))

class test_crossDependentFunctions(unittest.TestCase):
    def setUp(self) -> None:
        self.args = argParser(
            dir='test_data/ncbi-ftp-download',
            tsv='test_data/ncbi-ftp-download.tsv',
            excludeList='test_data/exclusion.txt',
            maxCtg=400,
            targetDir=None,
        )
        return super().setUp()

    def test_getInfo(self):
        strains = getInfoFrom(self.args)
        keys = list(strains.keys())
        keysSorted = [
            'Streptomyces albidoflavus 145',
            'Streptomyces albidoflavus J1074',
            'Streptomyces avermitilis MA-4680 NBRC 14893',
            'Streptomyces coelicolor A3(2) R4-mCherry-17',
            'Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963',
            'Streptomyces specialis GW41-1564'
        ]
        self.assertListEqual(sorted(keys), keysSorted)

    def test_filterTooManyCtgs(self):
        strains = getInfoFrom(self.args)
        validAssemblies = {
            'Streptomyces specialis GW41-1564': ('GCF_001493375.1', strains['Streptomyces specialis GW41-1564']['GCF_001493375.1']),
            'Streptomyces albidoflavus 145': ('GCF_002289305.1', strains['Streptomyces albidoflavus 145']['GCF_002289305.1'])
        }
        validAssemblies, tooManyContigs = filterTooManyCtgs(validAssemblies, self.args.maxCtg, [])
        self.assertListEqual(tooManyContigs,[('Streptomyces albidoflavus 145', 'GCF_002289305.1')])
        self.assertEqual(len(validAssemblies), 1)
        vaKeys = list(validAssemblies.keys())
        self.assertListEqual(vaKeys, ['Streptomyces specialis GW41-1564'])

    def test_filterDownloads(self):
        exclusions = [
            'Streptomyces coelicolor M1154',
            'Streptomyces coelicolor A3(2) R4-mCherry'
        ]
        strainAccs = (
                ("Streptomyces specialis GW41-1564", "GCF_001493375.1"),
                ("Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963", "GCF_001013905.1"),
                ("Streptomyces avermitilis MA-4680 NBRC 14893", "GCF_000009765.2"),
                ("Streptomyces albidoflavus J1074", "GCF_000359525.1"),
        )
        validAssemblies, _, _, _= \
            filterDownloads(getInfoFrom(self.args), exclusions, maxCtg=400)
        # Only accession is checked, not data
        # strains = getInfoFrom(self.args)
        # for name in validAssemblies:
        #     print(f'"{name}": ("{validAssemblies[name][0]}", strains["{name}"]["{validAssemblies[name][0]}"]),')
        vas = [(s, validAssemblies[s][0]) for s in validAssemblies]
        self.assertSetEqual(set(strainAccs), set(vas))

    def test_gatherAssemblies(self):
        strainAccs = {
            "Streptomyces specialis GW41-1564": "GCF_001493375.1",
            "Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963": "GCF_001013905.1",
            "Streptomyces avermitilis MA-4680 NBRC 14893": "GCF_000009765.2",
            "Streptomyces albidoflavus J1074": "GCF_000359525.1",
        }
        targetFilesCorrect = [
            "Streptomyces_albidoflavus_J1074.fna.gz",
            "Streptomyces_avermitilis_MA-4680_NBRC_14893.fna.gz",
            "Streptomyces_leeuwenhoekii_C34_DSM_42122_NRRL_B-24963.fna.gz",
            "Streptomyces_specialis_GW41-1564.fna.gz",
        ]
        excludedList = { 
            "Streptomyces coelicolor A3(2) R4-mCherry-17": "GCF_008124975.1",
            "Streptomyces avermitilis MA-4680 NBRC 14893": "GCF_000764715.1",
            "Streptomyces albidoflavus J1074": "GCF_000156475.1",
            "Streptomyces albidoflavus 145": "GCF_002289305.1",
        }
        targetFiles, includeListFile, excludeListFile = gatherAssemblies(self.args)
        targetDir = generateTargetDir(self.args)
        self.assertSetEqual(set(targetFiles), set(os.listdir(targetDir)))
        self.assertSetEqual(set(targetFilesCorrect), set(os.listdir(targetDir)))
        shutil.rmtree(targetDir)

        n = 0
        with open(includeListFile, 'r') as elf:
            for l in elf:
                l = l.strip()
                if not '\t' in l: continue
                n += 1
                s, a = l.split('\t')
                self.assertEqual(a, strainAccs.pop(s))
        self.assertEqual(n, 4)
        self.assertEqual(len(strainAccs), 0)
        os.remove(includeListFile)

        n = 0
        with open(excludeListFile, 'r') as elf:
            for l in elf:
                l = l.strip()
                if not '\t' in l: continue
                n += 1
                s, a = l.split('\t')
                self.assertEqual(a, excludedList.pop(s))
        self.assertEqual(n, 4)
        os.remove(excludeListFile)

if __name__ == "__main__":
    unittest.main()