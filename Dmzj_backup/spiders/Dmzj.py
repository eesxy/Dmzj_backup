import re
import os
import json
import toml
import js2py
import scrapy
import logging
import threading
import importlib
import configparser
import urllib.parse
from Dmzj_backup.items import ComicItem, ImgItem, CoverItem, TachiyomiMeta


def safe_pathname(p):
    return re.sub(r'(^\s*|\s*$|[/\?*:"<>|])', '', p)


class ErrorLog:
    def __init__(self) -> None:
        self.lock = threading.Lock()

    def err_ls(self, dic):
        self.lock.acquire()
        with open('error.toml', 'r+t') as f:
            data = toml.load('error.toml')
            f.seek(0, 0)
            f.truncate()
            dic_name = f'err_{len(data)}'
            data[dic_name] = dic
            _ = toml.dump(data, f)
        self.lock.release()


error_logger = ErrorLog()


class DmzjSpider(scrapy.Spider):
    name = 'Dmzj'
    login_domain = 'https://i.dmzj.com/'
    image_domain = 'https://images.dmzj.com/'
    comic_domain = 'https://manhua.dmzj.com/'

    def __init__(self):
        logger = logging.getLogger()
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(
            logging.Formatter('[%(levelname)s]%(asctime)s: %(message)s',
                              datefmt=r'%Y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)
        logger = logging.getLogger('scrapy.core.scraper')
        logger.setLevel(logging.ERROR)
        cfg = configparser.ConfigParser()
        cfg.read('scrapy.cfg')
        setting = cfg.get('settings', 'default')
        self.mysettings = importlib.import_module(setting)
        if not os.path.exists('error.toml'):
            with open('error.toml', 'x'):
                pass
        self.info_lock = threading.Lock()

    def start_requests(self):
        yield scrapy.Request(self.login_domain + 'login', callback=self.start_login)

    def start_login(self, response):
        token = response.css('.land_form.autoHeight > form > input::attr(value)').get()
        data = {
            'nickname': self.mysettings.MY_USERNAME,
            'password': self.mysettings.MY_PASSWORD,
            'token': token,
            'type': '0',
            'to': self.login_domain}
        self.logger.info('Try to login')
        self.logger.debug('token: %s' % (token))
        yield scrapy.FormRequest(self.login_domain + 'doLogin', callback=self.get_subscribe,
                                 formdata=data)

    def get_subscribe(self, response):
        dic = json.loads(response.text)
        if dic['code'] != 1000:
            self.logger.error('Login failed: %d %s' % (dic['code'], dic['msg']))
            raise UserWarning
        cookies = response.headers.getlist('Set-Cookie')
        for cookie in cookies:
            cookie = cookie.decode('utf-8')
            if 'my=' in cookie:
                user_id = re.search(r'my=(.*?)%7C', cookie).group(1)
                break
        data = {'page': '1', 'type_id': '1', 'letter_id': '0', 'read_id': '1'}
        yield scrapy.FormRequest(self.login_domain + 'ajax/my/subscribe',
                                 callback=self.parse_subscribe, formdata=data,
                                 cb_kwargs=dict(page=1), meta={'user_id': user_id})

    def parse_subscribe(self, response, page):
        user_id = response.request.meta['user_id']
        if page == 1:
            self.logger.info('Login successful')
            if self.mysettings.MY_RETRY:
                for i in self.retry(response):
                    yield i

        self.info_lock.acquire()
        info_dict = {}
        filename = os.path.join(self.mysettings.FILES_STORE, 'info.toml')
        if os.path.exists(filename):
            info_dict = toml.load(filename)

        comic_list = []
        raw_url_list = response.css('.dy_r')
        for url in raw_url_list:
            comic_name = url.css('h3 > a::text').get()
            comic_name = safe_pathname(comic_name)
            last_update = url.css('p > em > a::text').get()
            last_update = safe_pathname(last_update)
            comic_url = url.css('h3 > a::attr(href)').get()
            if self.mysettings.MY_ROUGH_UPDATE and comic_name in info_dict and info_dict[
                    comic_name] == last_update:
                continue
            else:
                info_dict[comic_name] = last_update
                comic_list.append(comic_url)
        self.logger.info('Parsed subscribe page %d, found %d comic(s)' % (page, len(raw_url_list)))
        self.logger.info('%d comic(s) updated' % (len(comic_list)))

        with open(filename, 'w') as f:
            _ = toml.dump(info_dict, f)
        self.info_lock.release()

        for url in comic_list:
            url = re.sub(r'\s+', '', url)
            domain = re.sub(r'(http://|https://)', '', url).split('/')[0]
            if domain == re.sub(r'(http://|https://)', '', self.comic_domain).split('/')[0]:
                comic_py = url.split('/')[-1]
                fetch_url = self.comic_domain + 'api/v1/comic2/comic/detail?channel=pc&app_name=comic&version=1.0.0'
                fetch_url += '&comic_py=' + comic_py + '&uid=' + user_id
                yield scrapy.Request(fetch_url, callback=self.parse_comic, errback=self.err_comic,
                                     meta={'user_id': user_id})
            else:
                self.logger.warning(f'Unsupported domain in URL {url}')

        if len(raw_url_list) != 0:
            page += 1
            data = {'page': str(page), 'type_id': '1', 'letter_id': '0', 'read_id': '1'}
            yield scrapy.FormRequest(self.login_domain + 'ajax/my/subscribe',
                                     callback=self.parse_subscribe, formdata=data,
                                     cb_kwargs=dict(page=page), meta={'user_id': user_id})

    def retry(self, response):
        user_id = response.request.meta['user_id']
        info_list = []
        with open('error.toml', 'r+t') as f:
            data = toml.load('error.toml')
            f.seek(0, 0)
            f.truncate()
            for dic in data.values():
                info_list.append(dic)
        self.logger.info('Retry %d request(s)' % (len(info_list)))
        for req in info_list:
            if req['type'] == 'comic':
                yield scrapy.Request(req['url'], callback=self.parse_comic, errback=self.err_comic,
                                     meta={'user_id': user_id})
            elif req['type'] == 'chapter':
                yield scrapy.Request(req['url'], callback=self.parse_chapter,
                                     errback=self.err_chapter, cb_kwargs=req['cb_kwargs'],
                                     meta={'user_id': user_id})
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
        error_logger.err_ls(info_dict)

    def parse_comic(self, response):
        user_id = response.request.meta['user_id']
        data = json.loads(response.text)
        comic_info = data['data']['comicInfo']
        cover_url = comic_info['cover']
        comic_name = comic_info['title']
        comic_url = self.comic_domain + comic_info['comicPy']
        last_updated = comic_info['lastUpdateChapterName']
        comic_name = safe_pathname(comic_name)

        # tachiyomi meta
        authors, genre, status = [], [], 0
        for author_dic in comic_info['authorsTagList']:
            authors.append(author_dic['tagName'])
        authors = ', '.join(authors)
        for theme_dic in comic_info['themeTagList']:
            genre.append(theme_dic['tagName'])
        if comic_info['statusTagList'][0]['tagName'] == '连载中': status = 1
        elif comic_info['statusTagList'][0]['tagName'] == '已完结': status = 2
        description = comic_info['description']
        tachiyomi_meta = TachiyomiMeta(comic_name, authors, description, genre, status)

        if comic_info['chapterList'] is None:
            self.logger.warning('No chapter found in %s' % (comic_name))
        else:
            chapter_list = []
            record_chapter_list = []
            for dic in comic_info['chapterList']:
                record_chapter_sublist = []
                for chapter in dic['data']:
                    chapter_name = safe_pathname(chapter['chapter_title'])
                    fetch_url = self.comic_domain
                    fetch_url += 'api/v1/comic2/chapter/detail?channel=pc&app_name=comic&version=1.0.0'
                    fetch_url += '&comic_py=' + comic_info['comicPy'] + '&chapter_id=' + str(
                        chapter['chapter_id'])
                    fetch_url += '&uid=' + user_id
                    chapter_list.append((fetch_url, chapter_name))
                    record_chapter_sublist.append(chapter_name)
                record_chapter_sublist.reverse()
                record_chapter_list += record_chapter_sublist
            self.logger.info('Parsed comic: %s, found %d chapter(s)' %
                             (comic_name, len(chapter_list)))

            if self.mysettings.MY_UPDATE_MODE:
                chapter_list = self.check_update(comic_name, last_updated, chapter_list)
                if self.mysettings.MY_COVER_UPDATE or not os.path.exists(
                        os.path.join(self.mysettings.FILES_STORE, comic_name, 'cover.jpg')):
                    yield CoverItem(comic_name=comic_name, cover_url=cover_url)
            else:
                yield CoverItem(comic_name=comic_name, cover_url=cover_url)

            for chapter in chapter_list:
                yield scrapy.Request(chapter[0], callback=self.parse_chapter,
                                     errback=self.err_chapter,
                                     cb_kwargs=dict(comic_name=comic_name, chapter_name=chapter[1]),
                                     meta={'user_id': user_id})
            yield ComicItem(comic_name=comic_name, comic_url=comic_url,
                            tachiyomi_meta=tachiyomi_meta, last_updated=last_updated,
                            chapter_list=record_chapter_list)

    def err_chapter(self, failure):
        request = failure.request
        info_dict = {'type': 'chapter', 'url': request.url, 'cb_kwargs': request.cb_kwargs}
        error_logger.err_ls(info_dict)

    def check_update(self, comic_name, last_updated, chapter_list):
        dir = os.path.join(self.mysettings.FILES_STORE, comic_name)
        if not os.path.exists(dir):
            self.logger.info('New comic: %s' % (comic_name))
            return chapter_list
        else:
            downloaded_chapter_list = [d for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
            update_list = []
            for chapter in chapter_list:
                chapter_name = safe_pathname(chapter[1])
                if chapter_name not in downloaded_chapter_list:
                    update_list.append(chapter)
            self.logger.info('%d new chapter(s) in %s' % (len(update_list), comic_name))
            return update_list

    def parse_chapter(self, response, comic_name, chapter_name):
        data = json.loads(response.text)
        page_list = data['data']['chapterInfo']['page_url']

        if page_list is None:
            self.logger.warning('No page found in %s %s' % (comic_name, chapter_name))
        else:
            self.logger.info('Parsed chapter: %s %s, found %d page(s)' %
                             (comic_name, chapter_name, len(page_list)))
            for page in page_list:
                yield ImgItem(comic_name=comic_name, chapter_name=chapter_name,
                              img_name=urllib.parse.unquote(page,
                                                            'utf-8').split('/')[-1], img_url=page)

    def parse(self, response):
        raise NotImplementedError
