import asyncio
import webbrowser
import logging
from checkers import gamestop_checker
from notification_senders.telegram_sender import TelegramSender
from utils.utils import get_bool, get_config_section_dic, is_valid_url
from playsound import playsound

SOUND_LOCATION = get_config_section_dic('CommonConfig').get('sound_path')


async def handle_sound(play_sound: bool) -> None:
    """
    Plays a custom sound if the given argument is True
    :param play_sound: True if a sound should be played
    :return: None
    """
    if play_sound:
        playsound(sound=SOUND_LOCATION, block=False)


def handle_open_browser(open_browser: bool, url: str) -> None:
    """
    Opens the given url in the browser if the first argument is True
    :param open_browser: if True the browser should be opened
    :param url: the url to open in the browser
    :return: None
    """
    if open_browser:
        webbrowser.open(url)


async def handle_send_message(telegram_sender: TelegramSender, message: str) -> None:
    """
    Sends the given message via Telegram
    :param telegram_sender: the TelegramSender object to use to send the message
    :param message: the message to send
    :return: None
    """
    if telegram_sender:
        await telegram_sender.send_message(message)


async def check_for_stock_gamestop(telegram_gamestop_sender: TelegramSender = None,
                                   url: str = None, open_browser: bool = False, play_sound: bool = False,
                                   sleep: int = 60,
                                   sleep_after_found: int = 3600) -> None:
    """
    Checks if a Gamestop product with the given url is in stock and notifies in several ways
    :param telegram_gamestop_sender: The TelegramSender. Can be None
    :param url: The url
    :param open_browser: true if a browser should be opened if the product is in stock
    :param play_sound: true if a sound should be played if the product is in stock
    :param sleep: how much it should sleep between checks
    :param sleep_after_found: how much it should sleep after realizing that the product is in stock
    :return: None
    """
    while True:
        try:
            if url:
                available = await gamestop_checker.check_stock(url)
                if available:
                    await handle_send_message(telegram_gamestop_sender, 'Disponibile! ' + url)
                    handle_open_browser(open_browser, url)
                    await handle_sound(play_sound)
                    await asyncio.sleep(sleep_after_found)
            if sleep != 0:
                await asyncio.sleep(sleep)
        except Exception as exception:
            logging.exception('An error occurred', exception)
            if sleep != 0:
                await asyncio.sleep(sleep)


async def scrape_gamestop_products(telegram_gamestop_sender: TelegramSender,
                                   starting_product_id: int,
                                   ending_product_id: int,
                                   base_url: str,
                                   check_stock: bool = True,
                                   play_sound: bool = True,
                                   open_browser: bool = True,
                                   keywords: list = None,
                                   check_all_keywords: bool = False,
                                   sleep: int = 60,
                                   continue_after_found: bool = False,
                                   sleep_after_found: int = 3600):
    """
    Scrapes for gamestop products whose pages contain any of the given keywords, from the given product_id to the given product_id that  and notifies and stops when required
    :param telegram_gamestop_sender: the TelegramSender for sending messages. Can be None
    :param starting_product_id: the product_id it should start from
    :param ending_product_id: the product_id it should end at
    :param base_url: the base_url
    :param check_stock: if True, it will also check if the products that were found are in stock
    :param play_sound: if True, it will play a sound if a product that has the corresponding keywords is found
    :param open_browser: if True, it will open the browser if a product that has the corresponding keywords is found
    :param keywords: the keywords to check for
    :param check_all_keywords: if True, the result will be considered as successful only if all keywords are found in the product page
    :param sleep: the amount of sleep between two searches
    :param continue_after_found: if True, it will continue scraping even a successful result has been provided
    :param sleep_after_found: the amount of sleep after a successful result
    :return: None
    """
    if keywords is None:
        keywords = []

    current_product_id = starting_product_id
    while current_product_id <= ending_product_id:
        url = base_url + str(current_product_id)
        try:
            return_value = await gamestop_checker.check_if_page_contains_keywords(base_url + str(current_product_id),
                                                                                  check_all_keywords=check_all_keywords,
                                                                                  keywords=keywords)
            if return_value:
                stock_found = False
                if check_stock:
                    stock_found = gamestop_checker.check_stock_from_soup(return_value, url)
                if telegram_gamestop_sender:
                    if stock_found:
                        await telegram_gamestop_sender.send_message('Found keyword and stock:' + url)
                    else:
                        await telegram_gamestop_sender.send_message('Found keyword: ' + url)
                handle_open_browser(open_browser, url)
                await handle_sound(play_sound)
                if continue_after_found:
                    await asyncio.sleep(sleep_after_found)
                else:
                    break
            if sleep != 0:
                await asyncio.sleep(sleep)
        except Exception:
            logging.error('An error occurred, going on...')
            if sleep != 0:
                await asyncio.sleep(sleep)
        finally:
            current_product_id = current_product_id + 1


async def check_for_search_gamestop(telegram_gamestop_sender: TelegramSender,
                                    play_sound: bool = False,
                                    open_browser: bool = False,
                                    search_url: str = None,
                                    results: int = None,
                                    keywords: list = None,
                                    check_all_keywords: bool = False,
                                    check_availability: bool = False,
                                    sleep: int = 30):
    if keywords is None:
        keywords = []

    should_break = False
    while should_break is False:
        try:
            return_value = await gamestop_checker.check_search(url=search_url, results=results,
                                                               keywords=keywords,
                                                               check_all_keywords=check_all_keywords,
                                                               check_availability=check_availability)
            if return_value:
                message = 'Search was successful: ' + search_url
                if telegram_gamestop_sender:
                    await telegram_gamestop_sender.send_message(message)
                handle_open_browser(open_browser, search_url)
                await handle_sound(play_sound)
                should_break = True
            if should_break is False:
                await asyncio.sleep(sleep)
        except Exception:
            logging.debug('An error occurred, going on...')
            if sleep != 0:
                await asyncio.sleep(sleep)


async def set_up_telegram_sender():
    telegram_sender = TelegramSender()
    await telegram_sender.start_client()
    return telegram_sender


def set_up_gamestop():
    gamestop_checker.fill_home_titles()


def set_up_logging():
    logging.basicConfig(level=logging.INFO)


async def main():
    stock_config = get_config_section_dic('StockConfig')
    scrape_config = get_config_section_dic('ScrapeConfig')
    search_config = get_config_section_dic('SearchConfig')
    set_up_logging()
    set_up_gamestop()
    telegram_sender_check_stock = None
    telegram_sender_scrape = None
    telegram_sender_search = None
    if get_bool(stock_config.get('telegram')) or get_bool(scrape_config.get('telegram')) or get_bool(
            search_config.get('telegram')):
        telegram_sender = await set_up_telegram_sender()
        if get_bool(stock_config.get('telegram')):
            telegram_sender_check_stock = telegram_sender
        if get_bool(scrape_config.get('telegram')):
            telegram_sender_scrape = telegram_sender
        if get_bool(search_config.get('telegram')):
            telegram_sender_search = telegram_sender

    urls = stock_config.get('urls').split(', ')
    base_scrape_url = scrape_config.get('base_url')
    search_url = search_config.get('search_url')
    tasks = []
    for url in urls:
        if is_valid_url(url):
            tasks.append(
                check_for_stock_gamestop(telegram_sender_check_stock, url,
                                         open_browser=get_bool(stock_config.get('open_browser_when_found')),
                                         play_sound=get_bool(stock_config.get('sound_when_found')),
                                         sleep=int(stock_config.get('sleep')),
                                         sleep_after_found=int(stock_config.get('sleep_after_found'))))

    if base_scrape_url and is_valid_url(base_scrape_url):
        tasks.append(
            scrape_gamestop_products(telegram_sender_scrape, int(scrape_config.get('start_id')),
                                     int(scrape_config.get('end_id')),
                                     base_scrape_url, get_bool(scrape_config.get('check_stock')),
                                     get_bool(scrape_config.get('sound_when_found')),
                                     get_bool(scrape_config.get('open_browser_when_found')),
                                     scrape_config.get('keywords').split(', '),
                                     get_bool(scrape_config.get('check_all_keywords')), int(scrape_config.get('sleep')),
                                     get_bool(scrape_config.get('continue_after_found')),
                                     int(scrape_config.get('sleep_after_found'))))

    if search_url and is_valid_url(search_url):
        tasks.append(
            check_for_search_gamestop(telegram_gamestop_sender=telegram_sender_search,
                                      play_sound=bool(search_config.get('sound_when_found')),
                                      open_browser=get_bool(search_config.get('open_browser_when_found')),
                                      search_url=search_url,
                                      results=search_config.get('expected_results'),
                                      keywords=search_config.get('keywords').split(', '),
                                      check_all_keywords=get_bool(search_config.get('check_all_keywords')),
                                      sleep=int(search_config.get('sleep')),
                                      check_availability=get_bool(search_config.get('check_availability'))))
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
