import asyncio
import unittest

from unittest import IsolatedAsyncioTestCase
from mockito import when, mock, verify, any, eq
from telethon import TelegramClient
from notification_senders.telegram_sender import TelegramSender


class TelegramSenderTest(IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        cls.telegram_sender = TelegramSender()

    def test_init(self):
        self.assertIsNotNone(self.telegram_sender.__getattribute__('_TelegramSender__api_id'))
        self.assertIsNotNone(self.telegram_sender.__getattribute__('_TelegramSender__api_hash'))
        self.assertIsNotNone(self.telegram_sender.__getattribute__('_TelegramSender__token'))
        self.assertIsNotNone(self.telegram_sender.__getattribute__('_TelegramSender__phone'))
        self.assertTrue(self.telegram_sender.channel_ids)

    async def test_send_message(self):
        async def coroutine_return(value):
            return value

        # Verify that the message is handled correctly
        telegram_client = mock(TelegramClient)
        when(telegram_client).is_connected().thenReturn(True)
        when(telegram_client).send_message(any(int), message=eq('message')).thenReturn(
            coroutine_return('message')).thenReturn(coroutine_return('message'))
        self.telegram_sender.client = telegram_client
        await self.telegram_sender.send_message('message')
        verify(telegram_client, times=1).send_message(self.telegram_sender.channel_ids[0],
                                                      message=eq('message'))
        verify(telegram_client, times=1).send_message(self.telegram_sender.channel_ids[1],
                                                      message=eq('message'))
        self.assertEqual(self.telegram_sender.last_sent_message.message, 'message')

        # Verify that it doesn't allow sending another message if equals to the previous one
        await self.telegram_sender.send_message('message')
        verify(telegram_client, times=1).send_message(self.telegram_sender.channel_ids[0],
                                                      message=eq('message'))
        verify(telegram_client, times=1).send_message(self.telegram_sender.channel_ids[1],
                                                      message=eq('message'))

        # Test with a passed in channel
        when(telegram_client).send_message(eq(-42), message=eq('message2')).thenReturn(
            coroutine_return('message2'))
        await self.telegram_sender.send_message('message2', -42)
        verify(telegram_client, times=1).send_message(eq(-42),
                                                      message=eq('message2'))


if __name__ == '__main__':
    unittest.main()
