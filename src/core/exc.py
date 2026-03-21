class CantDownloadImage(Exception):
    """Ошибка что-бы указать на ошибку во время скачивание"""


class ParserError(Exception):
    """Базовая ошибка для указание ошибки во время парсинга"""


class AttributeNotSetted(ParserError):
    """Не найден один из ключевых параметров"""


class ParseSituationNotAllowed(ParserError):
    """Указывает что вызываемый метод parse не поддерживается"""
