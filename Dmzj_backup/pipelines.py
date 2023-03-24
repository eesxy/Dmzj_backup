import os
import json
import scrapy
import logging
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from Dmzj_backup.items import ComicItem, ChapterItem, ImgItem, CoverItem


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


class DmzjBackupPipeline:
    def process_item(self, item, spider):
        if spider.mysettings.MY_OVERWRITE_EXISTING_FILES:
            return item
        elif isinstance(item, CoverItem):
            if os.path.exists(os.path.join(spider.mysettings.FILES_STORE, item['comic_name'], 'cover.jpg')):
                logging.info('Cover exists: %s' % (item['comic_name']))
                raise DropItem
        elif isinstance(item, ImgItem):
            if os.path.exists(os.path.join(spider.mysettings.FILES_STORE, item['comic_name'], item['chapter_name'], item['img_name'])):
                logging.info('Image exists: %s in %s %s' % (
                    item['img_name'], item['comic_name'], item['chapter_name']))
                raise DropItem
        return item


class ComicPipeline:
    def process_item(self, item, spider):
        if isinstance(item, ComicItem):
            filename = os.path.join(
                spider.mysettings.FILES_STORE, item['comic_name'], 'info.json')
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            info_dict = dict(comic_name=item['comic_name'],
                             last_updated=item['last_updated'], chapter_list=item['chapter_list'])
            jstr = json.dumps(info_dict)
            with open(filename, 'w') as f:
                f.write(jstr)
        return item


class ImgPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return '%s/%s/%s' % (item['comic_name'], item['chapter_name'], item['img_name'])

    def get_media_requests(self, item, info):
        if isinstance(item, ImgItem):
            yield scrapy.FormRequest(item['img_url'], headers={'Host': 'images.dmzj.com', 'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})

    def item_completed(self, results, item, info):
        if isinstance(item, ImgItem):
            if results[0][0]:
                logging.info('Downloaded %s in %s %s' % (
                    item['img_name'], item['comic_name'], item['chapter_name']))
            else:
                info_dict = {'comic_name': item['comic_name'], 'chapter_name': item['chapter_name'],
                             'img_name': item['img_name'], 'url': item['img_url'], 'type': 'img'}
                err_ls(info_dict)
        return item


class CoverPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return '%s/cover.jpg' % (item['comic_name'])

    def get_media_requests(self, item, info):
        if isinstance(item, CoverItem):
            yield scrapy.FormRequest(item['cover_url'], headers={'Host': 'images.dmzj.com', 'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})

    def item_completed(self, results, item, info):
        if isinstance(item, CoverItem):
            if results[0][0]:
                logging.info('Downloaded cover of %s' % (item['comic_name']))
            else:
                info_dict = {
                    'comic_name': item['comic_name'], 'url': item['cover_url'], 'type': 'cover'}
                err_ls(info_dict)
        return item
