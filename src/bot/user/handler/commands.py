from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ....core.service import PDFService
from ....core.manager import MangaManager
from .._text import GREETING, HELP, SHOW_MANGA


class CommandsHandler:
    BASE_SAVE_PATH: str = "var/pdf"

    def __init__(
        self, manager: MangaManager, pdf: PDFService, save_path: str | None = None
    ):
        self.pdf = pdf
        self.manager = manager
        self.save_path = save_path or self.BASE_SAVE_PATH
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
        try:
            command, query = message.text.split()
            if query.startswith("http://") or query.startswith("https://"):
                manga = await self.manager.get_manga_by_url(query)
            else:
                manga = await self.manager.get_manga_by_sku(query)

            if manga is None:
                await message.answer(f"Не найдена манга по запросу {query} (ﾉД`)")
                return

            if manga.pdf_id:
                await message.answer_document(
                    manga.pdf_id,
                    caption=SHOW_MANGA.format(
                        title=manga.title,
                        genres=", ".join(x.name for x in manga.genres),
                        author=manga.author or "Неизвестно",
                    ),
                )
                return

            file = await self.pdf.download(manga, self.save_path)
            sent_message = await message.answer_document(file)

            if sent_message.document:
                file_id = sent_message.document.file_id

            await self.manager.add_pdf(file_id, manga.id)

        except ValueError:
            await message.answer(
                "Пожалуйста введите данные в виде download [АРТИКУЛ или URL]"
            )
