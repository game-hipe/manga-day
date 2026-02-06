from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ....core.service import PDFService
from ....core.manager import MangaManager
from .._text import GREETING, HELP


class CommandsHandler:
    def __init__(self, manager: MangaManager, pdf: PDFService):
        self.manager = manager
        self.router = Router()
        self.register_handlers()

    def register_handlers(self):
        self.router.message.register(self.start, Command("start"))
        self.router.message.register(self.help, Command("help"))
        self.router.message.register(self.download, Command("download"))

    async def start(self, message: Message):
        await message.answer(GREETING)

    async def help(self, message: Message):
        await message.answer(HELP)

    async def download(self, message: Message):
        await message.answer("Это не работает сорри XD")
