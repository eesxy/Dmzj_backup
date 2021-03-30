#
# scrapy settings
# 基本scrapy设定, 请谨慎修改

import datetime
import logging

dt = datetime.datetime.now()
LOG_FILE = '%04d_%02d_%02d__%02d%02d%02d.log' % (dt.year,
                                                 dt.month, dt.day, dt.hour, dt.minute, dt.second)

BOT_NAME = 'Dmzj_backup'

SPIDER_MODULES = ['Dmzj_backup.spiders']
NEWSPIDER_MODULE = 'Dmzj_backup.spiders'

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'http://manhua.dmzj.com/'
}

# Enable or disable spider middlewares
# SPIDER_MIDDLEWARES = {
#    'Dmzj_backup.middlewares.DmzjBackupSpiderMiddleware': 500,
# }

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    # 'Dmzj_backup.middlewares.DmzjBackupDownloaderMiddleware': 500,
    # 'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 300,
    'Dmzj_backup.middlewares.DmzjBackupProxyMiddleware': 100,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
}

# Enable or disable extensions
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
ITEM_PIPELINES = {
    'Dmzj_backup.pipelines.DmzjBackupPipeline': 100,
    'Dmzj_backup.pipelines.ImgPipeline': 300,
    'Dmzj_backup.pipelines.CoverPipeline': 200,
    'Dmzj_backup.pipelines.ComicPipeline': 400,
}

# Enable and configure the AutoThrottle extension (disabled by default)
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


#
# Additional scrapy settings
# 额外的scrapy settings, 可供修改

# 下载位置
IMAGES_STORE = './download'
# 并行下载线程数(请勿设置过大)
CONCURRENT_REQUESTS = 4
# 两次请求间的延迟, 为0时无延迟(请勿设置过小)
DOWNLOAD_DELAY = 0.5
# 日志等级
LOG_LEVEL = logging.INFO
# request失败后是否重试
RETRY_ENABLED = True
# request失败后重试的最大次数, 仅在设置了RETRY_ENABLED后有效
RETRY_TIMES = 5
# 需要重试的HTTP错误代码
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408, 429]
# 超时时间: 秒
DOWNLOAD_TIMEOUT = 10
# 图像避免重复下载的天数, 后于MY_OVERWRITE_EXISTING_FILES生效,
# 请选择其中之一使用
IMAGES_EXPIRES = 0
# telnet控制台端口范围, 默认使用6023
TELNETCONSOLE_PORT = [6023, 6073]
# telnet控制台登录用户名
TELNETCONSOLE_USERNAME = 'Dmzj'
# telnet控制台登录密码
TELNETCONSOLE_PASSWORD = 'dmzj'

#
# Additional user settings
# 用户设定

# 用户名
MY_USERNAME = 'username'
# 密码
MY_PASSWORD = 'password'
# 以下设置优先级: 粗略检查模式 > 更新模式 == 更新封面
# 启用后，会开启粗略检查模式
MY_ROUGH_UPDATE = False
# 启用后, 已经爬取过的章节在下一次运行时将被忽略(无论是否下载完毕)
# 建议在第一次下载完成后启用, 以提高后续更新的效率
MY_UPDATE_MODE = False
# 启用后会强制更新封面
MY_COVER_UPDATE = False
# 启用后会重试上一次失败的请求
MY_RETRY = True
# 启用后, 已存在的文件也将重复下载, 先于IMAGES_EXPIRES生效
# 请选择其中之一使用(推荐设置为False以避免重复下载)
MY_OVERWRITE_EXISTING_FILES = False
# 是否启用代理
MY_PROXY_ENABLED = False
# 代理地址
MY_PROXY = "http://127.0.0.1:1080"
