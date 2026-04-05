from aiogram.fsm.state import State, StatesGroup


class FindMangaStates(StatesGroup):
    browsing = State()
    """Указывает на то что человек находится в поиске"""
