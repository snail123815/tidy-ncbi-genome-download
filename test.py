import unittest
import os
import shutil
from collections import namedtuple

from tools import getInfoFrom, removeDup, removeEqu, getNumCtgs, \
    getExclusion, filterDownloads, filterTooManyCtgs, gatherAssemblies

class Test_strainNameComprehension(unittest.TestCase):
    def setUp(self) -> None:
        argParser = namedtuple('args', ['dir', 'tsv', 'excludeList', 'maxCtg'])
        self.args = argParser(
            dir='test_data/ncbi-ftp-download',
            tsv='test_data/ncbi-ftp-download.tsv',
            excludeList='test_data/exclusion.txt',
            maxCtg=400
        )
        self.strains = getInfoFrom(self.args)
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
        self.assertRaises(Exception, getNumCtgs, "abc.kk.gz")

    def test_getInfo(self):
        keys = list(self.strains.keys())
        keysSorted = [
            'Streptomyces albidoflavus 145',
            'Streptomyces albidoflavus J1074',
            'Streptomyces avermitilis MA-4680 NBRC 14893',
            'Streptomyces coelicolor A3(2) R4-mCherry-17',
            'Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963',
            'Streptomyces specialis GW41-1564'
        ]
        self.assertListEqual(sorted(keys), keysSorted)

    def test_getExclusion(self):
        targetList = [
            'Streptomyces coelicolor M1154',
            'Streptomyces coelicolor A3(2) R4-mCherry'
        ]
        self.assertListEqual(getExclusion('test_data/exclusion.txt'), targetList)
        self.assertListEqual(getExclusion('test_data/kkk.txt'), [])

    def test_filterTooManyCtgs(self):
        validAssemblies = {
            'Streptomyces specialis GW41-1564': ('GCF_001493375.1', self.strains['Streptomyces specialis GW41-1564']['GCF_001493375.1']),
            'Streptomyces albidoflavus 145': ('GCF_002289305.1', self.strains['Streptomyces albidoflavus 145']['GCF_002289305.1'])
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
        strainAccs = set((
                ("Streptomyces specialis GW41-1564", "GCF_001493375.1"),
                ("Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963", "GCF_001013905.1"),
                ("Streptomyces avermitilis MA-4680 NBRC 14893", "GCF_000009765.2"),
                ("Streptomyces albidoflavus J1074", "GCF_000359525.1"),
        ))

        validAssemblies, excludedAccs, skippedAccs, tooManyContigs = \
            filterDownloads(self.strains, exclusions, maxCtg=400)
        vas = []
        for s in validAssemblies:
            vas.append((s, validAssemblies[s][0]))
        self.assertSetEqual(strainAccs, set(vas))

    def test_gatherAssemblies(self):
        # for name in validAssemblies:
        #     print(f'"{name}": ("{validAssemblies[name][0]}", self.strains["{name}"]["{validAssemblies[name][0]}"]),')
        validAssemblies = {
            "Streptomyces specialis GW41-1564": ("GCF_001493375.1", self.strains["Streptomyces specialis GW41-1564"]["GCF_001493375.1"]),
            "Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963": ("GCF_001013905.1", self.strains["Streptomyces leeuwenhoekii C34 DSM 42122 NRRL B-24963"]["GCF_001013905.1"]),
            "Streptomyces avermitilis MA-4680 NBRC 14893": ("GCF_000009765.2", self.strains["Streptomyces avermitilis MA-4680 NBRC 14893"]["GCF_000009765.2"]),
            "Streptomyces albidoflavus J1074": ("GCF_000359525.1", self.strains["Streptomyces albidoflavus J1074"]["GCF_000359525.1"]),
        }
        targetFilesCorrect = [
            'GCF_001493375.1_Streptomyces_specialis_genomic.fna.gz',
            'GCF_001013905.1_sleC34_genomic.fna.gz',
            'GCF_000009765.2_ASM976v2_genomic.fna.gz',
            'GCF_000359525.1_ASM35952v1_genomic.fna.gz'
        ]
        targetDir = self.args.dir + '-ready'
        targetFiles = gatherAssemblies(validAssemblies,targetDir)
        self.assertSetEqual(set(targetFiles), set(os.listdir(targetDir)))
        self.assertSetEqual(set(targetFilesCorrect), set(os.listdir(targetDir)))
        shutil.rmtree(targetDir)



if __name__ == "__main__":
    unittest.main()