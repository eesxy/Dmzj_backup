import scrapy
from typing import List
from dataclasses import dataclass


class DmzjBackupItem(scrapy.Item):
    comic_name = scrapy.Field()


class ComicItem(DmzjBackupItem):
    comic_url = scrapy.Field()
    tachiyomi_meta = scrapy.Field()
    last_updated = scrapy.Field()
    chapter_list = scrapy.Field()


class ImgItem(DmzjBackupItem):
    chapter_name = scrapy.Field()
    img_name = scrapy.Field()
    img_url = scrapy.Field()


class CoverItem(DmzjBackupItem):
    cover_url = scrapy.Field()


@dataclass(eq=False)
class TachiyomiMeta:
    title: str
    author: str
    description: str
    genre: List[str]
    status: int

    def dump(self):
        return {
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'genre': self.genre,
            'status': str(self.status), }
