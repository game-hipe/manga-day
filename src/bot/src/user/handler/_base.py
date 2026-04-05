import asyncio

from urllib.parse import urljoin
from itertools import batched

from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from loguru import logger

from ...core.schemas import Manga
from ..._handler import BaseHandler, send_on_error
from .._bot import UserBot
from .._text import SHOW_MANGA


class UserBaseHandler(BaseHandler[UserBot]):
    def _build_manga_text(self, manga: Manga) -> set:
        """Создаёт текст для манги из переменной `SHOW_MANGA`

        Args:
            manga (Manga): Манга из БД

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

    def _build_manga_keyboard(self, manga: Manga) -> InlineKeyboardMarkup:
        """Создвёт клавиатуру

        Args:
            manga (Manga): Манга из БД

        Returns:
            InlineKeyboardMarkup: Клавиатура
        """

        button_pdf = InlineKeyboardButton(
            text=self.build_success_message("Хорошего дня!"), callback_data="NONE"
        )

        button_original = InlineKeyboardButton(
            text="Оригинал тут!", url=str(manga.url), style="primary"
        )
        if self.site:
            button_on_site = InlineKeyboardButton(
                text="Посмотреть на сайте",
                url=urljoin(self.site, f"/manga/{manga.sku}"),
                style="primary",
            )

        else:
            button_on_site = None

        if self.pdf_condition(manga):
            button_pdf = InlineKeyboardButton(
                text="Скачать в PDF", callback_data=f"pdf:{manga.sku}", style="success"
            )

        author = (
            [
                InlineKeyboardButton(
                    text=manga.author.name,
                    callback_data=f"page:author:{manga.author.id}:1",
                    style="primary",
                )
            ]
            if manga.author
            else None
        )

        language = (
            [
                InlineKeyboardButton(
                    text=manga.language.name,
                    callback_data=f"page:language:{manga.language.id}:1",
                    style="primary",
                )
            ]
            if manga.language
            else None
        )

        genre_markup = []
        for genre_batch in batched(manga.genres, 3):
            genre_part = []
            for genre in genre_batch:
                genre_part.append(
                    InlineKeyboardButton(
                        text=genre.name,
                        callback_data=f"page:genre:{genre.id}:1",
                        style="success",
                    )
                )
            genre_markup.append(genre_part)

        final_markup = [
            [button_original],
            [button_pdf],
        ]

        if button_on_site:
            final_markup.insert(1, [button_on_site])

        if author:
            final_markup.append(
                [
                    InlineKeyboardButton(
                        text="Автор".center(20, "-"), callback_data="DONT_USEBLE"
                    )
                ]
            )
            final_markup.append(author)

        if language:
            final_markup.append(
                [
                    InlineKeyboardButton(
                        text="Язык".center(20, "-"), callback_data="DONT_USEBLE"
                    )
                ]
            )
            final_markup.append(language)

        if genre_markup:
            final_markup.append(
                [
                    InlineKeyboardButton(
                        text="Жанры".center(20, "-"), callback_data="DONT_USEBLE"
                    )
                ]
            )
            final_markup.extend(genre_markup)

        return InlineKeyboardMarkup(inline_keyboard=final_markup)

    def pdf_condition(self, manga: Manga) -> bool:
        """Возвращает bool если условие выполнено

        Args:
            manga (Manga): Манга

        Returns:
            bool: Условие выполнено
        """
        if len(manga.gallery) > self.bot.pdf.BASE_MAX_IMAGES:
            return False

        return True

    @send_on_error("Неизвестная ошибка при попытке показать мангу")
    async def show_manga(
        self,
        message: Message,
        manga: Manga,
        state: FSMContext | None = None,
    ) -> None:
        """Присылает подробности об манге

        Args:
            message (Message): Сообщение от пользователя
            manga (Manga): Манга из БД
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
        self, message: Message, manga: Manga, delete_message: bool = True
    ) -> None:
        """Отправляет PDF, так-же записывает его в БД

        Args:
            message (Message): Сообщение от пользователя
            manga (Manga): Манга из БД
        """
        if not self.pdf_condition(manga):
            await message.answer(self.build_error_message("Манга слишком большая"))
            return

        text = self._build_manga_text(manga)
        sent_message: Message | None = None
        task: asyncio.Task | None = None

        send_pdf = self.bot.pdf.get_pdf(manga)

        if isinstance(send_pdf, str):
            await message.answer_document(
                document=send_pdf, caption=text, parse_mode="HTML"
            )
            return

        try:
            task = asyncio.create_task(self.show_upload_status(message))
            message = await message.answer(
                self.build_success_message("Пожалуйста подождите...")
            )

            sent_message = await message.answer_document(
                document=send_pdf, caption=text, parse_mode="HTML"
            )
            task.cancel()

        finally:
            if sent_message is not None and sent_message.document:
                self.bot.pdf.set_pdf(manga, sent_message.document.file_id)

            if delete_message:
                try:
                    await message.delete()
                except TelegramBadRequest:
                    pass

            if task:
                if not task.done():
                    task.cancel()

    async def get_manga(self, query: str) -> Manga | None:
        """Возращает мангу из БД

        Args:
            query (str): Артикул или HTTP ссылка

        Returns:
            Manga | None: Манга из БД если найдено иначе None
        """
        if not query.startswith("http"):
            response = await self.bot.api.get_by_sku(query)

        elif self.site and query.startswith(self.site):
            response = await self.bot.api.get_by_sku(query.split("/")[-1])

        else:
            response = await self.bot.api.get_by_url(query)

        if response.ok and response.data:
            return response.data

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

    @property
    def site(self) -> str | None:
        return self.bot.config.get("site")
