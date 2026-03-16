"""На будущее! Возможность не просто переходить по ссылкам на первоисточник а именно просматривать мангу внутри ТГ."""

from urllib.parse import urljoin

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ....core.manager import MangaManager
from ....core import config
from .._text import SHOW_MANGA


class GetMangaCommandHandler:
    PATH_TO_MANGA = "/manga/{sku}"

    def __init__(self, manager: MangaManager):
        self.router = Router()
        self.manager = manager
        self.register_handlers()

    def register_handlers(self):
        self.router.callback_query.register(
            self.get_manga_call, F.data.startswith("show")
        )
        self.router.message.register(self.get_manga, Command("get_manga"))

    async def get_manga_call(self, call: CallbackQuery):
        _, sku = call.data.split(":", maxsplit=1)
        await self._show_manga(message=call.message, sku=sku)

    async def get_manga(self, message: Message):
        try:
            _, sku = message.text.split(maxsplit=1)

        except ValueError:
            await message.answer(
                "Неверный формат команды. Правильный формат: /get_manga [sku]"
            )
            return

        await self._show_manga(message=message, sku=sku)

    async def _show_manga(self, message: Message, sku: str):
        manga = await self.manager.get_manga_by_sku(sku)
        if manga is None:
            await message.answer(f"Манга с артикулом {sku} не найдена")
            return

        await message.answer_photo(
            photo=str(manga.poster),
            caption=SHOW_MANGA.format(
                title=manga.title,
                genres=", ".join(x.name for x in manga.genres) or "Отсутствует",
                author=manga.author.name if manga.author else "Неизвестно",
                language=manga.language.name if manga.language else "Неизвестно",
                sku=manga.sku,
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Оригинал тут", url=str(manga.url))],
                    [
                        InlineKeyboardButton(
                            text="Скачать PDF", callback_data=f"pdf:{manga.sku}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Посмотреть на сайте!",
                            url=urljoin(
                                config.site.domen, self.PATH_TO_MANGA.format(sku=sku)
                            ),
                        )
                    ],
                ]
            ),
        )
