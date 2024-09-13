import os
import re
import toml
import json
import scrapy
import logging
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from Dmzj_backup.items import ComicItem, ImgItem, CoverItem
from Dmzj_backup.spiders.Dmzj import error_logger


class DmzjBackupPipeline:
    def process_item(self, item, spider):
        if spider.mysettings.MY_OVERWRITE_EXISTING_FILES:
            return item
        elif isinstance(item, CoverItem):
            if (not spider.mysettings.MY_COVER_UPDATE) and os.path.exists(
                    os.path.join(spider.mysettings.FILES_STORE, item['comic_name'], 'cover.jpg')):
                logging.info('Cover exists: %s' % (item['comic_name']))
                raise DropItem
        elif isinstance(item, ImgItem):
            if os.path.exists(
                    os.path.join(spider.mysettings.FILES_STORE, item['comic_name'],
                                 item['chapter_name'], item['img_name'])):
                logging.info('Image exists: %s in %s %s' %
                             (item['img_name'], item['comic_name'], item['chapter_name']))
                raise DropItem
        return item


class ComicPipeline:
    def process_item(self, item, spider):
        if isinstance(item, ComicItem):
            info_file = os.path.join(spider.mysettings.FILES_STORE, item['comic_name'], 'info.toml')
            meta_file = os.path.join(spider.mysettings.FILES_STORE, item['comic_name'],
                                     'details.json')
            if not os.path.exists(os.path.dirname(info_file)):
                os.makedirs(os.path.dirname(info_file))
            info_dict = dict(comic_name=item['comic_name'], comic_url=item['comic_url'],
                             status=item['tachiyomi_meta'].status,
                             last_updated=item['last_updated'], chapter_list=item['chapter_list'])
            jstr = json.dumps(item['tachiyomi_meta'].dump())
            with open(info_file, 'w') as f:
                toml.dump(info_dict, f)
            with open(meta_file, 'w') as f:
                f.write(jstr)
        return item


class ImgPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return '%s/%s/%s' % (item['comic_name'], item['chapter_name'], item['img_name'])

    def get_media_requests(self, item, info):
        if isinstance(item, ImgItem):
            host = re.sub(r'(http://|https://)', '', item['img_url']).split('/')[0]
            yield scrapy.FormRequest(
                item['img_url'], headers={
                    'Host': host,
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})

    def item_completed(self, results, item, info):
        if isinstance(item, ImgItem):
            if results[0][0]:
                logging.info('Downloaded %s in %s %s' %
                             (item['img_name'], item['comic_name'], item['chapter_name']))
            else:
                info_dict = {
                    'comic_name': item['comic_name'],
                    'chapter_name': item['chapter_name'],
                    'img_name': item['img_name'],
                    'url': item['img_url'],
                    'type': 'img'}
                error_logger.err_ls(info_dict)
        return item


class CoverPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):
        return '%s/cover.jpg' % (item['comic_name'])

    def get_media_requests(self, item, info):
        if isinstance(item, CoverItem):
            host = re.sub(r'(http://|https://)', '', item['cover_url']).split('/')[0]
            yield scrapy.FormRequest(
                item['cover_url'], headers={
                    'Host': host,
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})

    def item_completed(self, results, item, info):
        if isinstance(item, CoverItem):
            if results[0][0]:
                logging.info('Downloaded cover of %s' % (item['comic_name']))
            else:
                info_dict = {
                    'comic_name': item['comic_name'],
                    'url': item['cover_url'],
                    'type': 'cover'}
                error_logger.err_ls(info_dict)
        return item
