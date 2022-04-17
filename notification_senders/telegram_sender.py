import logging
from datetime import datetime, timezone
from telethon import TelegramClient, sync, events
from utils import utils

logger = logging.getLogger('telegram_sender')
logger.setLevel(logging.INFO)


class TelegramSender:

    def __init__(self):
        logger.info('Initializing TelegramChannelSender')
        config_dict = utils.get_config_section_dic('TelegramConfig')

        self.__api_id = config_dict.get('api_id')
        self.__api_hash = config_dict.get('api_hash')

        # Currently unused. It can be automatically inserted instead of the phone number when requested, so that the
        # messages are sent via the bot
        self.__token = config_dict.get('bot_token')
        self.last_sent_message = None
        self.channel_ids = [int(i) for i in config_dict.get('channels').split(', ')]

        self.message_queue = []

        # The phone number (in case it's ever needed)
        self.__phone = config_dict.get('phone')

        # Create a telegram session and start it
        self.client = TelegramClient('telegram_sender', self.__api_id, self.__api_hash)

    async def start_client(self) -> None:
        """
        Starts the client. It may ask for an OTP code
        """
        await self.client.start()

        # If this is run for the first time, it will probably send an otp code to the phone number
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.__phone)

            # signing in the client
            await self.client.sign_in(self.__phone, input('Enter the code: '))

    async def force_reconnect(self) -> None:
        """
        Forces the reconnection
        :return: None
        """
        logger.info('Forcing reconnection...')
        if not self.client.is_connected():
            if await utils.async_check_internet_connection():
                await self.start_client()
                if self.client.is_connected():
                    logger.info('Reconnected!')
                else:
                    logger.warning('Cannot connect!')
            else:
                logger.warning('No internet connection!')
        else:
            logger.info('The client is already connected!')

    async def send_message(self, message: str, *channel_ids: int) -> None:
        """
        Sends a message to the given channels or, if not provided, to the channels in the self.channel_ids field

        :param message: the message to send
        :param channel_ids: the channel ids the message should be sent to
        :return: None
        """
        if not channel_ids:
            channel_ids = self.channel_ids
        try:
            if not self.client.is_connected():
                await self.force_reconnect()
            if message:
                if not self.__check_for_duplicated_message(message):
                    for channel_id in channel_ids:
                        await self.client.send_message(channel_id, message=message)
                    self.last_sent_message = MessageDateRelation(message=message, date=datetime.now(timezone.utc))
                else:
                    logger.warning('Last message equal check found the same message!')
            else:
                logger.warning('Cannot send an empty message!')
        except ConnectionError:
            logger.exception('Connection error!')

    def __check_for_duplicated_message(self, message: str) -> bool:
        """
        Checks whether the given messages is equals to the previous message that was sent in the past 60 seconds
        :param message:
        :return: None
        """
        if self.last_sent_message and self.last_sent_message.message == message:
            if (datetime.now(timezone.utc) - self.last_sent_message.date).total_seconds() < 60:
                return True
        return False


class MessageDateRelation:

    def __init__(self, message: str = None, date: datetime = None):
        self.message = message
        self.date = date
