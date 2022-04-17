# Gamestop EU Stock Checker and Scraper

The main purpose of this code is to enable checking whether a product is in stock in any EU Gamestop stores with simple
and effective asynchronous HTTP requests and notify the presence of in stock products via sound notifications and
telegram messages.

There are 3 main functions:

- Checking if a product is in stock
- Checking if a search page has any given keyword or if the obtained results are different from the expected ones
- Checking for all product IDs in certain range with given keywords

An example main is provided to show examples on how this software should be used.

How to use
- 

- Use pipenv
- Modify the config.cfg with the appropriate configuration. You can find out about any of those by reading docstrings.
  In order to be able to send telegram messages, you need to have API access to it and modify the config.cfg fields
  under TelegramConfig, as they are currently randomized
- Run main.py or run.bat

Small Overview of the code
-

- "gamestop_checker.py" is where all the gamestop-related code is.
- "telegram_sender.py" includes the TelegramSender class which makes use of TelegramClient from the telethon library.
- "utils.py" and "soup_utils.py" contain some useful function that can be used all over the code, sometimes just for
  debug purposes

