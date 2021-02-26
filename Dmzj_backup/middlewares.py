from Dmzj_backup.settings import MY_PROXY, MY_PROXY_ENABLED


class DmzjBackupProxyMiddleware:
    def process_request(self, request, spider):
        if MY_PROXY_ENABLED:
            request.meta['proxy'] = MY_PROXY
        return None
