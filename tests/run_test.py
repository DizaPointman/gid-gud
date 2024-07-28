import unittest

from tests.factory_tests import FactoryCase
from tests.model_tests import CategoryModelCase, GidGudModelCase, UserModelCase, BullshitGeneratorModelCase


if __name__ == '__main__':
    unittest.main(verbosity=2)

    # Create test suite
    suite = unittest.TestSuite()

    # Add the test cases to the suite
    suite.addTest(unittest.makeSuite(FactoryCase))
    suite.addTest(unittest.makeSuite(BullshitGeneratorModelCase))
    suite.addTest(unittest.makeSuite(UserModelCase))
    suite.addTest(unittest.makeSuite(CategoryModelCase))
    suite.addTest(unittest.makeSuite(GidGudModelCase))

    # Execute the test suite
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)