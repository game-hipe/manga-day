import asyncio

from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin

from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    FSInputFile,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from ....core import config
from ....core.entities.schemas import OutputMangaSchema
from ..._handler import BaseHandler, send_on_error
from .._bot import UserBot
from .._text import SHOW_MANGA
from ....core.exc import CantDownloadImage


class UserBaseHandler(BaseHandler[UserBot]):
    def _build_manga_text(self, manga: OutputMangaSchema) -> set:
        """Создаёт текст для манги из переменной `SHOW_MANGA`

        Args:
            manga (OutputMangaSchema): Манга из БД

        Returns:
            str: Итоговый текст для манги
        """
        genres = ", ".join(x.name for x in manga.genres) or "Неизвестно"
        author = manga.author.name if manga.author else "Неизвестно"
        language = manga.language.name if manga.language else "Неизвестно"

        return SHOW_MANGA.format(
            title=manga.title,
            genres=genres,
            author=author,
            language=language,
            sku=manga.sku,
        )

    def _build_manga_keyboard(self, manga: OutputMangaSchema) -> InlineKeyboardMarkup:
        """Создвёт клавиатуру

        Args:
            manga (OutputMangaSchema): Манга из БД

        Returns:
            InlineKeyboardMarkup: Клавиатура
        """

        button_pdf = InlineKeyboardButton(
            text=self.build_success_message("Хорошего дня!"), callback_data="NONE"
        )

        button_original = InlineKeyboardButton(text="Оригинал тут!", url=str(manga.url))
        button_on_site = InlineKeyboardButton(
            text="Посмотреть на сайте",
            url=urljoin(config.site.domen, f"/manga/{manga.sku}"),
        )

        if self.pdf_condition(manga):
            button_pdf = InlineKeyboardButton(
                text="Скачать в PDF", callback_data=f"pdf:{manga.sku}"
            )

        return InlineKeyboardMarkup(
            inline_keyboard=[[button_original], [button_on_site], [button_pdf]]
        )

    def pdf_condition(self, manga: OutputMangaSchema) -> bool:
        """Возвращает bool если условие выполнено

        Args:
            manga (OutputMangaSchema): Манга

        Returns:
            bool: Условие выполнено
        """
        if len(manga.gallery) > self.bot.pdf_service.BASE_MAX_IMAGES:
            return False

        return True

    @send_on_error("Неизвестная ошибка при попытке показать мангу")
    async def show_manga(
        self,
        message: Message,
        manga: OutputMangaSchema,
        state: FSMContext | None = None,
    ) -> None:
        """Присылает подробности об манге

        Args:
            message (Message): Сообщение от пользователя
            manga (OutputMangaSchema): Манга из БД
            state (FSMContext | None): Состояние FSM
        """
        text = self._build_manga_text(manga)
        keyboard = self._build_manga_keyboard(manga)

        try:
            await message.answer_photo(
                photo=str(manga.poster),
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
        except TelegramBadRequest:
            message_with_image = await message.answer_photo(
                photo=self.image_not_found,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            self.image_not_found = message_with_image
        finally:
            chat_id: int | None = None
            message_id: int | None = None
            try:
                if state:
                    chat_id = await state.get_value("delete_chat_id")
                    message_id = await state.get_value("delete_message_id")
                    if chat_id and message_id:
                        await self.bot.bot.delete_message(chat_id, message_id)
            except TelegramBadRequest:
                logger.info(
                    f"Не удалось удалить сообщение {message_id} в чате {chat_id}"
                )

            finally:
                if state:
                    await state.update_data(
                        {
                            "delete_chat_id": None,
                            "delete_message_id": None,
                        }
                    )

    @send_on_error("Неизвестная ошибка при попытке скачать мангу")
    async def send_pdf(
        self, message: Message, manga: OutputMangaSchema, delete_message: bool = True
    ) -> None:
        """Отправляет PDF, так-же записывает его в БД

        Args:
            message (Message): Сообщение от пользователя
            manga (OutputMangaSchema): Манга из БД
        """
        if not self.pdf_condition(manga):
            await message.answer(self.build_error_message("Манга слишком большая"))
            return

        text = self._build_manga_text(manga)
        sent_message: Message | None = None
        task: asyncio.Task | None = None

        if manga.pdf_id:
            await message.answer_document(
                document=manga.pdf_id, caption=text, parse_mode="HTML"
            )
            return

        try:
            task = asyncio.create_task(self.show_upload_status(message))
            message = await message.answer(
                self.build_success_message("Пожалуйста подождите...")
            )

            with TemporaryDirectory() as tmpdir:
                try:
                    pdf = await self.bot.pdf_service.download(
                        manga, Path(tmpdir) / f"{manga.sku}.pdf"
                    )
                except CantDownloadImage:
                    await self.manga_server_error(
                        message, "Не удалось скачать одно из ключевых изображенией"
                    )
                    return

                if pdf is None:
                    await message.answer(
                        self.build_error_message("Не удалось скачать PDF")
                    )
                    return

                sent_message = await message.answer_document(
                    document=FSInputFile(path=pdf), caption=text, parse_mode="HTML"
                )
                task.cancel()

        finally:
            if sent_message is not None and sent_message.document:
                await self.bot.manager.add_pdf(sent_message.document.file_id, manga.id)

            if delete_message:
                try:
                    await message.delete()
                except TelegramBadRequest:
                    pass

            if task:
                if not task.done():
                    task.cancel()

    async def get_manga(self, query: str) -> OutputMangaSchema | None:
        """Возращает мангу из БД

        Args:
            query (str): Артикул или HTTP ссылка

        Returns:
            OutputMangaSchema | None: Манга из БД если найдено иначе None
        """
        if query.startswith("http"):
            if not query.startswith(config.site.domen):
                return await self.bot.manager.get_manga_by_url(query)

            return await self.bot.manager.get_manga_by_sku(query.split("/")[-1])

        return await self.bot.manager.get_manga_by_sku(query)

    async def show_upload_status(self, message: Message):
        """Показывает статус загрузки PDF

        Args:
            message (Message): Сообщение от пользователя
        """
        try:
            while True:
                await self.bot.bot.send_chat_action(
                    chat_id=message.chat.id, action="upload_document"
                )
                await asyncio.sleep(5)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
