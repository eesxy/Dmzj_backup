import re
import os
import time
import json
import js2py
import scrapy
import logging
import requests
import urllib.parse
from pyquery import PyQuery as pq
from Dmzj_backup.items import ComicItem, ChapterItem, ImgItem, CoverItem
from Dmzj_backup.settings import MY_UPDATE_MODE, IMAGES_STORE, MY_USERNAME, MY_PASSWORD


class DmzjSpider(scrapy.Spider):
    name = 'Dmzj'
    image_base_url = 'https://images.dmzj.com/'
    chapter_base_url = 'http://manhua.dmzj.com'
    original_image_base_url = 'https://images.dmzj1.com/'

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
        response = self.login()
        if response == None:
            return
        page = pq(response.text)
        raw_url_list = page('.dy_r > h3 > a').items()

        comic_list = []
        for url in raw_url_list:
            comic_list.append(url.attr('href'))
        self.logger.info('Parsed subscribe, found %d comic(s)' %
                         (len(comic_list)))

        for url in comic_list:
            url = re.sub(r'\s+', '', url)
            host = re.sub(r'(http://|https://)', '', url).split('/')[0]
            if host == 'www.dmzj.com':
                yield scrapy.FormRequest(url, callback=self.parse_original_comic)
            elif host == 'manhua.dmzj.com':
                yield scrapy.FormRequest(url, callback=self.parse_comic)
            else:
                raise NotImplementedError

    def login(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
        }

        session = requests.session()
        response = session.get(url='https://i.dmzj.com/login', headers=headers)
        doc = pq(response.text)
        token = doc('.land_form.autoHeight form input').attr('value')
        data = {'nickname': MY_USERNAME,
                'password': MY_PASSWORD, 'token': token, 'type': 0}
        self.logger.info('Try to login')
        response = session.post(
            url='https://i.dmzj.com/doLogin', data=data, headers=headers)
        dic = json.loads(response.text)
        if dic['code'] != 1000:
            self.logger.error('Login failed: %d %s' %
                              (dic['code'], dic['msg']))
            session.close()
            return None
        data = {'page': 1, 'type_id': 1, 'letter_id': 0, 'read_id': 1}
        response = session.post(
            url='https://i.dmzj.com/ajax/my/subscribe', headers=headers, data=data)
        self.logger.info('Login successful')
        session.close()
        return response

    def parse_comic(self, response):
        cover_url = response.css(
            '.anim_intro_ptext > a > img::attr(src)').get()
        comic_name = response.css('h1::text').get()
        last_updated = response.css('.update2::text').get()
        comic_name = re.sub(r'(^\s*|\s*$|[/\?*:"<>|])', '', comic_name)

        chapter_list = []
        record_chapter_list = []
        raw_url_list = response.css(
            '.cartoon_online_border > ul > li > a')
        for url in raw_url_list:
            chapter_name = re.sub(
                r'(^\s*|\s*$|[/\?*:"<>|])', '', url.css('::text').get())
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
        raw_url_list = response.css(
            '.cartoon_online_border_other > ul > li > a')
        for url in raw_url_list:
            chapter_name = re.sub(
                r'(^\s*|\s*$|[/\?*:"<>|])', '', url.css('::text').get())
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
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
        yield ComicItem(comic_name=comic_name, last_updated=last_updated, chapter_list=record_chapter_list)

    def parse_original_comic(self, response):
        cover_url = response.css(
            '.comic_i_img > a > img::attr(src)').get()
        comic_name = response.css('.comic_deCon > h1 > a::text').get()
        last_updated = response.css('.zj_list_head_dat::text').get()
        comic_name = re.sub(r'(^\s*|\s*$|[/\?*:"<>|])', '', comic_name)

        chapter_list = []
        record_chapter_list = []
        raw_url_list = response.css(
            '.tab-content.zj_list_con.autoHeight > ul > li > a')
        for url in raw_url_list:
            chapter_name = re.sub(
                r'(^\s*|\s*$|[/\?*:"<>|])', '', url.css('::text').get())
            chapter_list.append(
                (url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
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
            yield scrapy.FormRequest(chapter[0], callback=self.parse_original_chapter,
                                     cb_kwargs=dict(comic_name=comic_name, chapter_name=chapter[1]))
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
                chapter_name = re.sub(
                    r'(^\s*|\s*$|[/\?*:"<>|])', '', chapter[1])
                if chapter_name not in downloaded_chapter_list:
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
            url = re.sub(r'^/+', '', url)
            img_list.append(self.image_base_url+url)

        self.logger.info('Parsed chapter: %s %s, found %d image(s)' %
                         (comic_name, chapter_name, len(img_list)))
        for url in img_list:
            yield ImgItem(comic_name=comic_name, chapter_name=chapter_name,
                          img_name=urllib.parse.unquote(url.split('/')[-1], 'utf-8'), img_url=url)

    def parse_original_chapter(self, response, comic_name, chapter_name):
        eval_script = response.css('head > script::text').re_first('eval(.*)')
        eval_script = eval_script.replace('&lt;', '<').replace('&gt;', '>')

        raw_url_dict = js2py.eval_js('eval'+eval_script)
        raw_url_dict = re.sub(r'\s+', ' ', raw_url_dict)
        raw_url_dict = json.loads(raw_url_dict)
        raw_url_list = raw_url_dict['page_url'].split(' ')
        img_list = []
        for url in raw_url_list:
            url = re.sub(r'^/+', '', url)
            img_list.append(self.original_image_base_url+url)

        self.logger.info('Parsed chapter: %s %s, found %d image(s)' %
                         (comic_name, chapter_name, len(img_list)))
        for url in img_list:
            yield ImgItem(comic_name=comic_name, chapter_name=chapter_name,
                          img_name=urllib.parse.unquote(url.split('/')[-1], 'utf-8'), img_url=url)

    def parse(self, response):
        raise NotImplementedError
