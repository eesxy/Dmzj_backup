import re
import os
import json
import js2py
import scrapy
import logging
import urllib.parse
from pyquery import PyQuery as pq
from Dmzj_backup.items import ComicItem, ChapterItem, ImgItem, CoverItem
from Dmzj_backup.settings import MY_UPDATE_MODE, IMAGES_STORE


class DmzjSpider(scrapy.Spider):
    name = 'Dmzj'
    image_base_url = 'https://images.dmzj.com/'
    chapter_base_url = 'http://manhua.dmzj.com'

    def __init__(self):
        logger = logging.getLogger()
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(levelname)s]%(asctime)s: %(message)s',
                                          datefmt=r'%Y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)
        logger = logging.getLogger('scrapy.core.scraper')
        logger.setLevel(logging.ERROR)

    def start_requests(self):
        page = pq(filename='./subscribe/我的订阅 - 动漫之家.html')
        raw_url_list = page('.dy_r > h3 > a').items()

        comic_list = []
        for url in raw_url_list:
            comic_list.append(url.attr('href'))
        self.logger.info('Parsed subscribe, found %d comic(s)' %
                         (len(comic_list)))

        for url in comic_list:
            yield scrapy.FormRequest(url, callback=self.parse_comic)

    def parse_comic(self, response):
        cover_url = response.css(
            '.anim_intro_ptext > a > img::attr(src)').get()
        comic_name = response.css('h1::text').get()
        last_updated = response.css('.update2::text').get()

        chapter_list = []
        raw_url_list = response.css(
            '.cartoon_online_border > ul > li > a')
        for url in raw_url_list:
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], url.css('::text').get()))
        raw_url_list = response.css(
            '.cartoon_online_border_other > ul > li > a')
        for url in raw_url_list:
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], url.css('::text').get()))
        self.logger.info('Parsed comic: %s, found %d chapter(s)' %
                         (comic_name, len(chapter_list)))

        if MY_UPDATE_MODE:
            chapter_list = self.check_update(
                comic_name, last_updated, chapter_list)
            if not os.path.exists(os.path.join(IMAGES_STORE, comic_name, 'cover.jpg')):
                yield CoverItem(comic_name=comic_name, cover_url=cover_url)
        else:
            yield CoverItem(comic_name=comic_name, cover_url=cover_url)
        for chapter in chapter_list:
            yield scrapy.FormRequest(chapter[0], callback=self.parse_chapter,
                                     cb_kwargs=dict(comic_name=comic_name, chapter_name=chapter[1]))
        record_chapter_list = [chapter[1] for chapter in chapter_list]
        yield ComicItem(comic_name=comic_name, last_updated=last_updated, chapter_list=record_chapter_list)

    def check_update(self, comic_name, last_updated, chapter_list):
        filename = os.path.join(IMAGES_STORE, comic_name, 'info.json')
        if not os.path.exists(filename):
            self.logger.info('New comic: %s' % (comic_name))
            return chapter_list
        else:
            with open(filename, 'r') as f:
                jstr = f.read()
            info_dict = json.loads(jstr)
            downloaded_chapter_list = info_dict['chapter_list']
            update_list = []
            for chapter in chapter_list:
                if chapter[1] not in downloaded_chapter_list:
                    update_list.append(chapter)
            self.logger.info('%d new chapter(s) in %s' %
                             (len(update_list), comic_name))
            return update_list

    def parse_chapter(self, response, comic_name, chapter_name):
        eval_script = response.css('head > script::text').re_first('eval(.*)')
        eval_script = eval_script.replace('&lt;', '<').replace('&gt;', '>')

        raw_url_list = js2py.eval_js('eval'+eval_script)
        raw_url_list = re.sub(r'[\[\"\]]', '', raw_url_list).split(',')
        img_list = []
        for url in raw_url_list:
            img_list.append(self.image_base_url+url)

        self.logger.info('Parsed chapter: %s %s, found %d image(s)' %
                         (comic_name, chapter_name, len(img_list)))
        for url in img_list:
            yield ImgItem(comic_name=comic_name, chapter_name=chapter_name,
                          img_name=urllib.parse.unquote(url.split('/')[-1], 'utf-8'), img_url=url)

    def parse(self, response):
        raise NotImplementedError
