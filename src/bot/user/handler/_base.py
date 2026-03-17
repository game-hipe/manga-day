import asyncio

from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urljoin
from functools import wraps
from typing import Callable

from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from aiogram.types import (
    FSInputFile,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from ....core import config
from ....core.entities.schemas import OutputMangaSchema
from ..._handler import BaseHandler
from .._bot import UserBot
from .._text import SHOW_MANGA


def send_on_error(on_error: str):
    """
    Декоратор: при ошибке в обработчике отправляет пользователю фото с сообщением об ошибке.

    Args:
        on_error (str): Текст ошибки, который будет показан пользователю.
    """

    def wrapper(func: Callable) -> Callable:
        logger.debug(f"Обработчик {func.__name__} будет обрабатывать ошибки")

        @wraps(func)
        async def inner(self: "BaseHandler", message: Message, *args, **kwargs):
            try:
                return await func(self, message, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в функции {func.__name__}: {e}", exc_info=True)
                try:
                    if message.from_user:
                        await message.answer_photo(
                            photo=FSInputFile(
                                "src/frontend/user/static/images/500.jpg"
                            ),
                            caption=self.build_error_message(on_error),
                        )
                except TelegramAPIError as te:
                    logger.warning(
                        f"Не удалось отправить сообщение об ошибке пользователю: {te}"
                    )
                except Exception as ue:
                    logger.warning(
                        f"Неожиданная ошибка при отправке ошибки пользователю: {ue}"
                    )

            finally:
                # Логируем вызов функции, только если message.text существует
                text = getattr(message, "text", None) or getattr(
                    message, "caption", None
                )
                safe_text = (text[:50] + "...") if text and len(text) > 50 else text
                logger.debug(f"Вызов функции {func.__name__}, текст: {safe_text}")

        return inner

    return wrapper


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
        self, message: Message, manga: OutputMangaSchema, delete_message: bool = True
    ) -> None:
        """Присылает подробности об манге

        Args:
            message (Message): Сообщение от пользователя
            manga (OutputMangaSchema): Манга из БД
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
            await message.answer_photo(
                photo=FSInputFile(path="src/frontend/user/static/images/500.jpg"),
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        finally:
            if delete_message:
                try:
                    await message.delete()
                except TelegramBadRequest:
                    pass

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
                pdf = await self.bot.pdf_service.download(
                    manga, Path(tmpdir) / f"{manga.sku}.pdf"
                )

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
            return await self.bot.manager.get_manga_by_url(query)

        return await self.bot.manager.get_manga_by_sku(query)

    async def manga_not_found(self, message: Message) -> Message:
        """Присылает сообщение по типу "Манга не найдено"

        Args:
            message (Message): Сообщение от пользователя

        Returns:
            Message: Сообщение от бота о том что манга не найдена
        """
        return await message.answer(self.build_error_message("Манга не найдено"))

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
