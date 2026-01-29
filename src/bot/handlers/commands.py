from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from ...core.manager.spider import SpiderManager
from .._text import GREETING, HELP
from ...core import config

class CommandsHandler:
    def __init__(self, spider_manager: SpiderManager):
        self.router = Router()
        self.spider_manager = spider_manager
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.startparsing, Command("startparsing"))
        self.router.message.register(self.stopparsing, Command("stopparsing"))
        self.router.message.register(self.status, Command("status"))

    async def start(self, message: Message):
        await message.answer(GREETING)

    async def help(self, message: Message):
        await message.answer(HELP)

    async def startparsing(self, message: Message):
        await message.answer("Попытка начать парсинг")
        await self.spider_manager.start_parsing()

    async def stopparsing(self, message: Message):
        await message.answer("Попытка остановить парсинг")
        await self.spider_manager.stop_parsing()

    async def status(self, message: Message):
        await message.answer(self.spider_manager.status)
