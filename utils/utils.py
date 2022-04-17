import asyncio
import configparser
import re
import socket

import aiohttp

url_regex = ("((http|https)://)(www.)?" +
             "[a-zA-Z0-9@:%._\\+~#?&//=]" +
             "{2,256}\\.[a-z]" +
             "{2,6}\\b([-a-zA-Z0-9@:%" +
             "._\\+~#?&//=]*)")
compiled_regex = re.compile(url_regex)


def get_config_section_dic(section: str, config_path: str = './config.cfg') -> dict:
    """
    Gets the configuration from the config.cfg file for the given section and return a dict
    :param section: the section of the configuration to read
    :param config_path: the path to the config file
    :return: the dict for all key/value pairs for the given section
    """
    config_parser = configparser.RawConfigParser()
    config_parser.read(config_path)
    return dict(config_parser.items(section))


def check_internet_connection() -> bool:
    """
    Blocking check for internet connection
    :return: true if there is an internet connection
    """

    IP_ADDRESS_LIST = [
        "1.1.1.1",  # Cloudflare
        "1.0.0.1",
        "8.8.8.8",  # Google DNS
        "8.8.4.4",
        "208.67.222.222",  # Open DNS
        "208.67.220.220"
    ]

    port = 53
    timeout = 3

    for host in IP_ADDRESS_LIST:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            pass
    return False


async def async_check_internet_connection() -> bool:
    """
    Non-blocking check for internet connection
    :return: true if there is an internet connection
    """

    IP_ADDRESS_LIST = [
        "1.1.1.1",  # Cloudflare
        "1.0.0.1",
        "8.8.8.8",  # Google DNS
        "8.8.4.4",
        "208.67.222.222",  # Open DNS
        "208.67.220.220"
    ]

    timeout = 3

    for host in IP_ADDRESS_LIST:

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head('http://' + host, timeout=timeout):
                    return True
        except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError):  # Refine this
            continue
    return False


def is_valid_url(url: str):
    """
    Checks whether the given string represents a valid url
    :param url: the string to check
    :return: True if it is a syntactically valid url, false otherwise
    """
    return re.search(url_regex, url)


def get_bool(bool_str: str) -> bool:
    """
    Returns True if the given string is equals to 'true' ignoring cases, false otherwise
    :param bool_str:  the string to check
    :return: True or False
    """
    if bool_str and bool_str.lower() == 'true':
        return True
    else:
        return False
