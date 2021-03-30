class DmzjBackupProxyMiddleware:
    def process_request(self, request, spider):
        if spider.mysettings.MY_PROXY_ENABLED:
            request.meta['proxy'] = spider.mysettings.MY_PROXY
        return None
