import logging
import os
from time import time

from bs4 import BeautifulSoup


def save_soup_to_file(soup: BeautifulSoup) -> None:
    """
    Saves a BeautifulSoup object to a file
    :param soup: the BeautifulSoup object to save
    :return: None
    """
    try:
        if not os.path.exists("ExceptionSoups"):
            os.makedirs("ExceptionSoups")
        with open("ExceptionSoups/soup" + str(time()) + ".txt", "x+", encoding="utf-8") as f:
            f.write(str(soup))
    except Exception as e:
        logging.error("Could not log soup! Error while writing soup to file: " + str(e))