from ..hitomi.parser import HitomiMangaParser


class MoeImgParser(HitomiMangaParser):
    GENRES_TAG = "Tags"
    AUTHOR_TAG = "Author"
    LANGUAGE_TAG = "Language"
