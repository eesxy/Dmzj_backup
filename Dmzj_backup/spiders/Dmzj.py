import re
import os
import time
import json
import js2py
import scrapy
import logging
import requests
import importlib
import configparser
import urllib.parse
from Dmzj_backup.items import ComicItem, ChapterItem, ImgItem, CoverItem


def safe_pathname(p):
    return re.sub(r'(^\s*|\s*$|[/\?*:"<>|])', '', p)


def err_ls(dic):
    if os.path.exists('error.json'):
        with open("error.json", 'r+') as f:
            info_list = []
            s = f.read()
            if len(s) != 0:
                info_list = json.loads(s)
            info_list.append(dic)
            f.seek(0, 0)
            f.truncate()
            f.write(json.dumps(info_list))
    else:
        with open("error.json", 'w') as f:
            info_list = [dic]
            f.write(json.dumps(info_list))


class DmzjSpider(scrapy.Spider):
    name = 'Dmzj'
    image_base_url = 'https://images.dmzj.com/'
    chapter_base_url = 'http://manhua.dmzj.com'
    original_image_base_url = 'https://images.dmzj.com/'

    def __init__(self):
        logger = logging.getLogger()
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(logging.Formatter('[%(levelname)s]%(asctime)s: %(message)s',
                                          datefmt=r'%Y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)
        logger = logging.getLogger('scrapy.core.scraper')
        logger.setLevel(logging.ERROR)
        cfg = configparser.ConfigParser()
        cfg.read('scrapy.cfg')
        setting = cfg.get('settings', 'default')
        self.mysettings = importlib.import_module(setting)

    def start_requests(self):
        yield scrapy.Request('https://i.dmzj.com/login', callback=self.start_login, meta={'cookiejar': 0})

    def start_login(self, response):
        token = response.css(
            '.land_form.autoHeight > form > input::attr(value)').get()
        data = {'nickname': self.mysettings.MY_USERNAME,
                'password': self.mysettings.MY_PASSWORD, 'token': token, 'type': '0',
                'to': 'https://i.dmzj.com'}
        self.logger.info('Try to login')
        self.logger.debug('token: %s' % (token))
        yield scrapy.FormRequest('https://i.dmzj.com/doLogin', callback=self.get_subscribe,
                                 formdata=data, meta={'cookiejar': response.meta['cookiejar']})

    def get_subscribe(self, response):
        dic = json.loads(response.text)
        if dic['code'] != 1000:
            self.logger.error('Login failed: %d %s' %
                              (dic['code'], dic['msg']))
            raise UserWarning
        data = {'page': '1', 'type_id': '1', 'letter_id': '0', 'read_id': '1'}
        yield scrapy.FormRequest('https://i.dmzj.com/ajax/my/subscribe', callback=self.start_parse,
                                 formdata=data, meta={'cookiejar': response.meta['cookiejar']})

    def start_parse(self, response):
        self.logger.info('Login successful')
        if self.mysettings.MY_RETRY:
            for i in self.retry():
                yield i

        info_dict = dict()
        filename = os.path.join(self.mysettings.FILES_STORE, 'info.json')
        if os.path.exists(filename) and self.mysettings.MY_ROUGH_UPDATE:
            with open(filename, 'r') as f:
                info_dict = json.load(f)

        comic_list = []
        raw_url_list = response.css('.dy_r')
        for url in raw_url_list:
            comic_name = url.css('h3 > a::text').get()
            comic_name = safe_pathname(comic_name)
            last_update = url.css('p > em > a::text').get()
            last_update = safe_pathname(last_update)
            comic_url = url.css('h3 > a::attr(href)').get()
            if comic_name in info_dict and info_dict[comic_name] == last_update:
                continue
            else:
                info_dict[comic_name] = last_update
                comic_list.append(comic_url)
        self.logger.info('Parsed subscribe, found %d comic(s)' %
                         (len(info_dict)))
        self.logger.info('%d comic(s) updated' %
                         (len(comic_list)))

        with open(filename, 'w') as f:
            f.write(json.dumps(info_dict))

        for url in comic_list:
            url = re.sub(r'\s+', '', url)
            host = re.sub(r'(http://|https://)', '', url).split('/')[0]
            if host == 'www.dmzj.com':
                yield scrapy.Request(url, callback=self.parse_original_comic, errback=self.err_original_comic)
            elif host == 'manhua.dmzj.com':
                yield scrapy.Request(url, callback=self.parse_comic, errback=self.err_comic)
            else:
                raise NotImplementedError

    def retry(self):
        info_list = []
        if os.path.exists('error.json'):
            with open("error.json", 'r+') as f:
                s = f.read()
                if len(s) != 0:
                    info_list = json.loads(s)
                    f.seek(0, 0)
                    f.truncate()
        self.logger.info('Retry %d request(s)' % (len(info_list)))
        for req in info_list:
            if req['type'] == 'comic':
                yield scrapy.Request(req['url'], callback=self.parse_comic, errback=self.err_comic)
            elif req['type'] == 'original_comic':
                yield scrapy.Request(req['url'], callback=self.parse_original_comic, errback=self.err_comic)
            elif req['type'] == 'chapter':
                yield scrapy.Request(req['url'], callback=self.parse_chapter, errback=self.err_chapter,
                                     cb_kwargs=req['cb_kwargs'])
            elif req['type'] == 'original_chapter':
                yield scrapy.Request(req['url'], callback=self.parse_original_chapter, errback=self.err_chapter,
                                     cb_kwargs=req['cb_kwargs'])
            elif req['type'] == 'img':
                yield ImgItem(comic_name=req['comic_name'], chapter_name=req['chapter_name'],
                              img_name=req['img_name'], img_url=req['url'])
            elif req['type'] == 'cover':
                yield CoverItem(comic_name=req['comic_name'], cover_url=req['url'])
            else:
                raise NotImplementedError

    def err_comic(self, failure):
        request = failure.request
        info_dict = {'type': 'comic', 'url': request.url}
        err_ls(info_dict)

    def err_original_comic(self, failure):
        request = failure.request
        info_dict = {'type': 'original_comic', 'url': request.url}
        err_ls(info_dict)

    def parse_comic(self, response):
        cover_url = response.css(
            '.anim_intro_ptext > a > img::attr(src)').get()
        comic_name = response.css('h1::text').get()
        last_updated = response.css('.update2::text').get()
        comic_name = safe_pathname(comic_name)

        chapter_list = []
        record_chapter_list = []
        raw_url_list = response.css(
            '.cartoon_online_border > ul > li > a')
        for url in raw_url_list:
            chapter_name = safe_pathname(url.css('::text').get())
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
        raw_url_list = response.css(
            '.cartoon_online_border_other > ul > li > a')
        for url in raw_url_list:
            chapter_name = safe_pathname(url.css('::text').get())
            chapter_list.append(
                (self.chapter_base_url+url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
        self.logger.info('Parsed comic: %s, found %d chapter(s)' %
                         (comic_name, len(chapter_list)))

        if self.mysettings.MY_UPDATE_MODE:
            chapter_list = self.check_update(
                comic_name, last_updated, chapter_list)
            if self.mysettings.MY_COVER_UPDATE or not os.path.exists(os.path.join(self.mysettings.FILES_STORE, comic_name, 'cover.jpg')):
                yield CoverItem(comic_name=comic_name, cover_url=cover_url)
        else:
            yield CoverItem(comic_name=comic_name, cover_url=cover_url)

        for chapter in chapter_list:
            yield scrapy.Request(chapter[0], callback=self.parse_chapter, errback=self.err_chapter,
                                 cb_kwargs=dict(comic_name=comic_name, chapter_name=chapter[1]))
        yield ComicItem(comic_name=comic_name, last_updated=last_updated, chapter_list=record_chapter_list)

    def parse_original_comic(self, response):
        cover_url = response.css(
            '.comic_i_img > a > img::attr(src)').get()
        comic_name = response.css('.comic_deCon > h1 > a::text').get()
        last_updated = response.css('.zj_list_head_dat::text').get()
        comic_name = safe_pathname(comic_name)

        chapter_list = []
        record_chapter_list = []
        raw_url_list = response.css(
            '.tab-content.zj_list_con.autoHeight > ul > li > a')
        for url in raw_url_list:
            chapter_name = safe_pathname(url.css('::text').get())
            chapter_list.append(
                (url.attrib['href'], chapter_name))
            record_chapter_list.append(chapter_name)
        self.logger.info('Parsed comic: %s, found %d chapter(s)' %
                         (comic_name, len(chapter_list)))

        if self.mysettings.MY_UPDATE_MODE:
            chapter_list = self.check_update(
                comic_name, last_updated, chapter_list)
            if not os.path.exists(os.path.join(self.mysettings.FILES_STORE, comic_name, 'cover.jpg')):
                yield CoverItem(comic_name=comic_name, cover_url=cover_url)
        else:
            yield CoverItem(comic_name=comic_name, cover_url=cover_url)

        for chapter in chapter_list:
            yield scrapy.Request(chapter[0], callback=self.parse_original_chapter, errback=self.err_original_chapter,
                                 cb_kwargs=dict(comic_name=comic_name, chapter_name=chapter[1]))
        yield ComicItem(comic_name=comic_name, last_updated=last_updated, chapter_list=record_chapter_list)

    def err_chapter(self, failure):
        request = failure.request
        info_dict = {'type': 'chapter', 'url': request.url,
                     'cb_kwargs': request.cb_kwargs}
        err_ls(info_dict)

    def err_original_chapter(self, failure):
        request = failure.request
        info_dict = {'type': 'original_chapter', 'url': request.url,
                     'cb_kwargs': request.cb_kwargs}
        err_ls(info_dict)

    def check_update(self, comic_name, last_updated, chapter_list):
        filename = os.path.join(
            self.mysettings.FILES_STORE, comic_name, 'info.json')
        if not os.path.exists(filename):
            self.logger.info('New comic: %s' % (comic_name))
            return chapter_list
        else:
            with open(filename, 'r') as f:
                info_dict = json.load(f)
            downloaded_chapter_list = info_dict['chapter_list']
            update_list = []
            for chapter in chapter_list:
                chapter_name = safe_pathname(chapter[1])
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
