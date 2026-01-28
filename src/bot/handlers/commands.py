from aiogram.types import Message

from ...core.manager.spider import SpiderManager


class CommandsHandler:
    def __init__(self, spider_manager: SpiderManager):
        self.spider_manager = spider_manager

    async def start(self, message: Message):
        await message.answer()
