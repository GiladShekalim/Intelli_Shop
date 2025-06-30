import unittest
import sys
from test_utils import ResultFileWriter
from Scraper.pages.tests.jemix.HomePage_load import TestHomePageLoad
from Scraper.pages.tests.jemix.LoginPage_test import TestLogin
from Scraper.pages.tests.jemix.test_logout import TestLogout
from Scraper.pages.tests.jemix.test_main_navigation import TestMainNavigation
from Scraper.pages.tests.jemix.test_category_navigation import TestCategoryNavigation
from Scraper.pages.tests.jemix.test_coupon_data_collection import TestCouponDataCollection

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_cases = [
        TestHomePageLoad,
        TestLogin,
        TestLogout,
        TestMainNavigation,
        TestCategoryNavigation,
        TestCouponDataCollection  # New comprehensive coupon collection test
    ]
    
    for test_case in test_cases:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    #DO NOT EDIT THE FOLLOWING FUNCTION. IT IS USED TO RUN THE TESTS. DO NOT CHANGE!!!
    # Run tests with output
    # Verbosity levels:
    # 0 = quiet (dots for success)
    # 1 = default (dots for success with basic details)
    # 2 = verbose (detailed test names and results)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Write results to file
    writer = ResultFileWriter()
    writer.write_results(result)
    
    # Exit with appropriate code
    sys.exit(not result.wasSuccessful())
