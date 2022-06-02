import unittest

from main import removeDup, removeEqu

class Test_strainNameComprehension(unittest.TestCase):
    def setUp(self) -> None:
        from main import removeDup, removeEqu
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
        ]
        for s, r in zip(sources, results):
            self.assertEqual(removeDup(s), r)

if __name__ == "__main__":
    unittest.main()