import unittest
import uuid

import mockito

from checkers import gamestop_checker
from unittest import IsolatedAsyncioTestCase


async def mock_get(html_page: str):
    return html_page


# This test will not actually make any http requests but will use pre-saved html pages
class MyTestCase(IsolatedAsyncioTestCase):

    # This test will simply check that multiple items are correctly detected as available or unavailable
    async def test_check_stock(self):
        available_url = 'https://www.gamestop.it/PS4/Games/136782'
        unavailable_url = 'https://www.gamestop.it/PS4/Games/134750'
        mockito.spy(gamestop_checker)
        with open('./html_pages/available_product_it_1.html', encoding='utf-8') as f:
            html_page = f.read()
            mockito.when(gamestop_checker).__getattr__('__get')(mockito.eq(available_url)).thenReturn(
                mock_get(html_page))
            result = await gamestop_checker.check_stock(available_url)
            self.assertTrue(result)
        with open('./html_pages/unavailable_product_it_1.html', encoding='utf-8') as f:
            html_page = f.read()
            mockito.when(gamestop_checker).__getattr__('__get')(mockito.eq(unavailable_url)).thenReturn(
                mock_get(html_page))
            result = await gamestop_checker.check_stock(unavailable_url)
            self.assertFalse(result)

    # This is a simple test that will just check that the core functionalities of the function work as expected. It
    # does not check all edges cases (e.g. the check_availability flag is always False in this test)
    async def test_check_search(self):
        base_url = 'https://www.gamestop.it/SearchResult/QuickSearch?q=elden+ring'
        with open('./html_pages/search_url.html', encoding='utf-8') as f:
            html_page = f.read()
            mockito.when(gamestop_checker).__getattr__('__get')(mockito.eq(base_url)).thenReturn(
                mock_get(html_page)).thenReturn(
                mock_get(html_page)).thenReturn(mock_get(html_page)).thenReturn(mock_get(html_page)).thenReturn(
                mock_get(html_page))

            string_not_in_html_page = 'string_not_in_html_page_for_test'

            # Checks that if there is at least one of the keywords, then it returns True
            result = await gamestop_checker.check_search(base_url, 12, False, ['elden', string_not_in_html_page], False)
            self.assertTrue(result)

            # Checks that if there are not all the keywords, then it returns False
            result = await gamestop_checker.check_search(base_url, 12, False, ['elden', string_not_in_html_page], True)
            self.assertFalse(result)

            # Checks that if there are all the keywords, it returns True
            result = await gamestop_checker.check_search(base_url, 12, False, ['elden', 'collector'], True)
            self.assertTrue(result)

            # Checks that if there is none of the keywords, it returns False
            result = await gamestop_checker.check_search(base_url, 12, False, [string_not_in_html_page], False)
            self.assertFalse(result)

            # Checks that if there is none of the keywords, but the sum count is different from expected,
            # then it returns True
            result = await gamestop_checker.check_search(base_url, 11, False, [string_not_in_html_page], False)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
