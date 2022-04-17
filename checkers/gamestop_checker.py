import logging
import re
import aiohttp
import requests
from bs4 import BeautifulSoup
from lxml.html import fromstring
from utils.soup_utils import save_soup_to_file

ALLOWED_SITES_URLS = ['https://www.gamestop.de', 'https://www.gamestop.it', 'https://www.gamestop.ie',
                      'https://www.gamestop.ch', 'https://www.gamestop.at']

COULD_NOT_GET_GAMESTOP = 'Could not get Gamestop!'
GS_HOME_TITLES = []
logger = logging.getLogger('gamestop_checker')


def fill_home_titles():
    for url in ALLOWED_SITES_URLS:
        GS_HOME_TITLES.append(__get_home_page_title(url))


async def check_if_page_contains_keywords(url: str, keywords: list = None, check_all_keywords: bool = False) -> bool:
    """
    Checks if the page obtained after requesting the given url contains the given keywords
    :param url: the url
    :param keywords: the list of keywords
    :param check_all_keywords: if True, the return will be True only if all the keywords are present in the html page, otherwise one keyword will be enough
    :return: True if one or more keywords are found, depending on the check_all_keywords flag
    """
    if keywords is None:
        keywords = []

    allowed_domains = ['at', 'ch', 'de', 'it', 'ie']
    __check_if_domain_is_allowed(allowed_domains, url)

    try:
        text = await __get(url)
    except Exception:
        logger.error(COULD_NOT_GET_GAMESTOP)
        return False

    __check_keywords_from_text(html_text=text, url=url, keywords=keywords, check_all_keywords=check_all_keywords)


async def check_stock(url: str) -> bool:
    """
    Given a gamestop product URL, it checks whether the product is available or not

    :param url: the url
    :return: True if available, false if not or unknown
    :rtype: boolean
    """
    allowed_domains = ['at', 'ch', 'de', 'it', 'ie']
    __check_if_domain_is_allowed(allowed_domains, url)
    try:
        text = await __get(url)
    except Exception:
        logger.error(COULD_NOT_GET_GAMESTOP)
        return False

    return check_stock_from_soup(BeautifulSoup(text, 'html.parser'), url)


async def check_search(url: str, results: int = 0, check_availability: bool = False, keywords: list = None,
                       check_all_keywords: bool = False) -> bool:
    """
    Given a gamestop search URL, it checks whether it finds a product with the input keyword or if the number of
    results changed

    :param check_availability: if True, it will also check if any of the found results are available
    :param url: the url
    :param results: how many results are normal. Any variation of the results will be notified
    :param keywords: the keywords to look for in the search
    :param check_all_keywords: if True, the check will be successful only if all the keywords are present
    :return: True if the search was successful
    """
    if keywords is None:
        keywords = []
    allowed_domains = ['at', 'ch', 'de', 'it', 'ie']
    __check_if_domain_is_allowed(allowed_domains, url)
    try:
        text = await __get(url)
    except Exception:
        logger.error('Could not get gamestop!')
        return False
    return_value = None
    try:
        soup = BeautifulSoup(text, 'html.parser')
        return_value = __check_keywords_from_text(html_text=text, url=url, keywords=keywords,
                                                  check_all_keywords=check_all_keywords)
        search_sum_count = None
        if not return_value:
            search_sum_count = soup.find('strong', {'class': 'searchSumCount'})
            return_value = __handle_sum_count(search_sum_count, results, url)
        if return_value and check_availability and search_sum_count is not None:
            return_value = __handle_check_multiple_stock(soup, int(search_sum_count.text), url)
        if return_value is False:
            logger.info("No good results from search {}".format(url))
    except Exception as exception:
        logger.exception("Exception while checking for search!", exception)
    return return_value


def check_stock_from_soup(soup: BeautifulSoup, url: str) -> bool:
    """
    Checks whether the product of the given BeautifulSoup is in stock
    :param soup: the BeautifulSoup of the product page
    :param url: the url, used simply for logging
    :return: True if in stock, false if not or unknown
    """
    try:
        check_box_two_id = soup.find("input", {"id": "checkboxTwo"})
        if check_box_two_id:
            available = __is_available(check_box_two_id)
        else:
            radio_add = soup.find("input", {"class": "radioAdd"})
            available = radio_add is not None

        if available:
            logger.info('Product {} available!'.format(url))
            return True
        else:
            logger.info('Product {} not available'.format(url))
            return False
    except Exception:
        msg = 'Unknown error occurred'
        save_soup_to_file(soup)
        logger.error(msg)


async def __get(url: str) -> str:
    """
    Asynchronously gets the html page given a URL
    :param url: the URL to get
    :return: the html page
    """
    async with aiohttp.ClientSession(headers=__get_headers()) as session:
        async with session.get(url) as r:
            return await r.text()


def __get_headers() -> dict:
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    }


def __check_if_domain_is_allowed(allowed_domains: list, url: str) -> None:
    """
    Checks whether the given url is part of the given allowed domains list, raising an exception in case it is not
    :param allowed_domains: the allowed domains list
    :param url: the url to check
    :return: None
    :raises Exception when the url is not in the allowed domains list
    """
    if __get_domain(url) not in allowed_domains:
        raise DomainNotAllowedException('url provided is not in the allowed gamestop domains list! The only'
                                        ' gamestop local sites allowed are the following: ' + str(
            allowed_domains) + ' but the url provided is ' + url)


def __get_domain(url: str) -> str:
    """
    Gets the domain of a gamestop url
    :param url: the url to get the domain from
    :return: the domain as a string
    """
    return url.split('gamestop.')[1][:2]


def __check_keywords_from_text(html_text: str, url: str, keywords: list, check_all_keywords: bool = False):
    """
    Checks whether a set of keywords is present in the given text of a html page
    :param html_text: the html text page
    :param url: the url
    :param keywords: the keywords to check for
    :param check_all_keywords: if True, the search will be successful only if all keywords are found. Otherwise, it will be successful even if only one of the keywords is found
    :return: True if found, false if not or unknown
    """
    soup = None
    found = False
    if __is_not_home_page(html_text, url):
        soup = BeautifulSoup(html_text, 'html.parser')
        for keyword in keywords:
            found_keyword = soup.body.findAll(text=re.compile(keyword, re.IGNORECASE))
            if found_keyword:
                logger.info('Keyword {} found in url {}'.format(keyword, url))
                found = True
                if check_all_keywords is False:
                    break
            else:
                logger.info('Keyword {} not found in url {}'.format(keyword, url))
                found = False
    else:
        logger.info('It redirected to the home page when checking url {}'.format(url))

    if found:
        return soup
    else:
        return None


def __is_not_home_page(html_text: str, url: str) -> bool:
    """
    Checks whether the given html page from the given url is not a home page of Gamestop.it. It does not directly
    compare the given html page with a home page url, but it understands whether it's a home page or not from
    the title and the content of the html page
    :param html_text: the html page
    :param url: the url
    :return: True if not the home page, False if the check failed
    """
    is_not_home_page = False
    if 'SearchResult' in url:
        quick_search_str = url.split('SearchResult/')[1].replace('+', '%20')
        if quick_search_str in html_text:
            is_not_home_page = True
    else:
        tree = fromstring(html_text)
        title = tree.findtext('.//title')
        is_not_home_page = title not in GS_HOME_TITLES

    return is_not_home_page


def __is_available(check_box_two_id) -> bool:
    """
    Checks whether the given Tag contains reveals whether a product is available or not
    :param check_box_two_id: the tag
    :return: True if the product is available, False if not available or unknown
    """
    try:
        available = check_box_two_id['data-available']
        if available.lower() == 'true':
            return True
        else:
            return False
    except Exception:
        return False


def __get_home_page_title(url: str):
    try:
        text = requests.get(url).text
    except Exception:
        logger.exception('Could not get gamestop!')
        return None
    tree = fromstring(text)
    title = tree.findtext('.//title')
    return title


async def __handle_check_multiple_stock(soup: BeautifulSoup, results: int, url: str) -> bool:
    """
    Utility function to check if at least one of the products from the given soup of a search page is in stock
    :param soup: the BeautifulSoup of the given page
    :param results: the number of results
    :param url: the url
    :return: true if at least one is in stock, false otherwise
    """
    return_value = False
    for i in range(1, results + 1):
        search_product_div = soup.find("div", {"id": "product_" + str(i)})
        links = search_product_div.findAll("a")
        href = links[0]['href']
        link = 'https://www.gamestop.' + __get_domain(url) + str(href)
        return_value = await check_stock(link)
        if i == results and return_value is False:
            logger.info("Stocks from search are all unavailable!")
        if return_value:
            break
    return return_value


def __handle_sum_count(search_sum_count, expected_results: int, url: str) -> bool:
    """
    Checks whether the given PageElement that contains the number of results is different from the number of expected results and handles
    :param search_sum_count: the PageElement that contains the number of results
    :param expected_results: the expected number of results
    :param url: the url
    :return: True if the actual and expected results are different, False otherwise
    """
    return_value = False
    if search_sum_count and expected_results is not None:
        try:
            if search_sum_count.text != str(expected_results):
                logger.info('Expected results are ' + str(
                    expected_results) + ', but ' + search_sum_count.text + ' results were found in url {}!'.format(
                    url))
                return_value = True
            else:
                logger.info('Results are still ' + str(expected_results) + " for search url {}".format(url))
        except Exception:
            logger.exception('Error occurred while checking for results')

    return return_value


class DomainNotAllowedException(Exception):
    pass
