import unittest
from utils import calculate_profit

class TestUtils(unittest.TestCase):
    def test_calculate_profit(self):
        self.assertEqual(calculate_profit("100₽", "50₽"), 50)
        self.assertEqual(calculate_profit("N/A", "100₽"), 0)
        self.assertEqual(calculate_profit("50₽", "100₽"), 0)
        self.assertEqual(calculate_profit("100₽", "N/A"), 0)

if __name__ == '__main__':
    unittest.main()