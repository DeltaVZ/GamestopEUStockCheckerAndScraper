import unittest
from unittest import IsolatedAsyncioTestCase
from checkers import gamestop_checker


class GamestopCheckerTest(unittest.TestCase):

    def test_fill_titles(self):
        self.assertEqual(0, gamestop_checker.GS_HOME_TITLES.__len__())
        gamestop_checker.fill_home_titles()
        for title in gamestop_checker.GS_HOME_TITLES:
            self.assertIsNotNone(title)
        self.assertEqual(5, gamestop_checker.GS_HOME_TITLES.__len__())


if __name__ == '__main__':
    unittest.main()
