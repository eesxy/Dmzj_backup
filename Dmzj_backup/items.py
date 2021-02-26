import scrapy


class DmzjBackupItem(scrapy.Item):
    comic_name = scrapy.Field()

class ComicItem(DmzjBackupItem):
    last_updated = scrapy.Field()
    chapter_list = scrapy.Field()

class ChapterItem(DmzjBackupItem):
    chapter_name = scrapy.Field()
    
class ImgItem(DmzjBackupItem):
    chapter_name = scrapy.Field()
    img_name = scrapy.Field()
    img_url = scrapy.Field()

class CoverItem(DmzjBackupItem):
    cover_url = scrapy.Field()
