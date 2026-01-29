import hashlib

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, JSON, Index


class Base(DeclarativeBase): ...


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas_connection: Mapped[list[GenreManga]] = relationship(  # noqa
        "GenreManga", back_populates="genre"
    )


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas: Mapped[list[Manga]] = relationship(  # noqa
        "Manga", back_populates="author"
    )


class Language(Base):
    __tablename__ = "language"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    mangas: Mapped[list[Manga]] = relationship(  # noqa
        "Manga", back_populates="language"
    )


class GenreManga(Base):
    __tablename__ = "genre_manga"

    id: Mapped[int] = mapped_column(primary_key=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id"))
    manga_id: Mapped[int] = mapped_column(ForeignKey("mangas.id"))

    genre: Mapped[Genre] = relationship("Genre", back_populates="mangas_connection")  # noqa
    manga: Mapped[Manga] = relationship("Manga", back_populates="genres_connection")  # noqa


class Gallery(Base):
    __tablename__ = "gallery"
    id: Mapped[int] = mapped_column(primary_key=True)
    urls: Mapped[list[str]] = mapped_column(JSON())
    manga_id: Mapped[int] = mapped_column(ForeignKey("mangas.id"))

    manga: Mapped[Manga] = relationship("Manga", back_populates="gallery")  # noqa


class Manga(Base):
    __tablename__ = "mangas"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    poster: Mapped[str] = mapped_column(String(2048))

    language_id: Mapped[int] = mapped_column(ForeignKey("language.id"), nullable=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"), nullable=True)
    sku: Mapped[str] = mapped_column(String(32), unique=True, index=True)

    genres_connection: Mapped[list[GenreManga]] = relationship(
        "GenreManga", back_populates="manga"
    )

    author: Mapped[Author] = relationship("Author", back_populates="mangas")

    language: Mapped[Language] = relationship("Language", back_populates="mangas")

    gallery: Mapped[Gallery] = relationship("Gallery", back_populates="manga")

    @property
    def genres(self) -> list[Genre]:
        return [genre.genre for genre in self.genres_connection]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "poster": self.poster,
            "genres": self.genres,
            "author": self.author.name,
            "langauge": self.language.name,
            "gallery": self.gallery.urls,
        }

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.title and self.url and not self.sku:
            self.generate_sku()

    def generate_sku(self):
        """Генерирует и устанавливает sku"""
        if self.title and self.url:
            data = self.title.encode("utf-8")
            self.sku = hashlib.sha256(data).hexdigest()[:32]
    
    __table_args__ = (
        Index('idx_sku', 'sku'),
        Index('idx_title', 'title'),
        Index('idx_url', 'url'),
    )