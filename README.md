# Dmzj_backup

dmzj备份——基于scrapy框架的爬虫练习项目

## 简介

考虑到叔叔的大手以及无形大手的影响，有必要保全dmzj上的订阅内容，因此试着写了这个项目

## 环境

需要scrapy, PyQuery, js2py库  

```bash
pip3 install scrapy, PyQuery, js2py
```

自带库中需要re, os, json, logging, urllib, datetime

```bash
pip3 install re, os, json, logging, urllib, datetime
```

## 基本用法

修改settings.py中的MY_USERNAME, MY_PASSWORD为自己的用户名和密码

在命令行中转到项目目录，执行

```bash
scrapy crawl Dmzj
```

也可运行项目文件夹中的run.py来快速启动

## 进阶用法

### 暂停和恢复程序

scrapy库支持暂停和恢复程序，通过JOBDIR参数传递，例如，在启动时执行

```bash
scrapy crawl Dmzj -s JOBDIR=jobs/test1
```

然后可以安全地停止程序(如ctrl+C或远程发送信号)，下一次启动时只需执行相同命令即可恢复请求队列

```bash
scrapy crawl Dmzj -s JOBDIR=jobs/test1
```

详细用法参见[scrapy jobs](https://docs.scrapy.org/en/latest/topics/jobs.html)

### 设置代理

middlewares.py中实现了简单的proxy中间件，通过修改 **MY_PROXY_ENABLED** 和 **MY_PROXY** 设置即可通过单一代理进行访问，后续可能会添加代理池的实现。建议设置代理使用，以免影响对dmzj的正常访问

### 快速更新书架

第一次下载完成后，通过开启 **MY_UPDATE_MODE** 设置，爬虫将以更新模式运行，通过上一次保存的 *info.json* 文件进行更新章节的匹配，并忽略上次已经抓取的章节，有效提高第二次及之后运行的速度

注意: 更新模式下将忽略已下载内容的完整性，若上一次下载未完成(例如通过ctrl+C中途退出)就开启更新模式将造成下载内容不完整。这是由于爬虫在成功抓取目录页后直接返回含有 *info.json* 信息的ComicItem，并未检查后续请求成功与否

## 设置

在settings.py文件中修改设置，常用的设置如下

- **MY_USERNAME, MY_PASSWORD :** 用户名和密码
- **IMAGE_STORE :** 图片下载位置，默认为'./download'
- **CONCURRENT_REQUESTS :** 并行下载线程数，默认为4，请勿设置过大
- **DOWNLOAD_DELAY :**  两次请求间的延迟，为0时无延迟，请勿设置过小

一些进阶设置如下

- **LOG_LEVEL :** 日志等级，基于logging库
- **RETRY_ENABLED :** 请求失败后是否重试，默认为True
- **RETRY_TIMES :** 请求失败后的重试次数
- **DOWNLOAD_TIMEOUT :** 请求超时时间
- **TELNETCONSOLE_PORT, TELNETCONSOLE_USERNAME, TELNETCONSOLE_PASSWORD :** telnet控制台参数，详见[scrapy_telnet](https://docs.scrapy.org/en/latest/topics/telnetconsole.html)
- **MY_UPDATE_MODE :** 以更新模式运行，默认为False，建议第一次运行结束后开启

其余设置请谨慎修改，详见settings.py以及[scrapy_settings](https://docs.scrapy.org/en/latest/topics/settings.html)

## 免责声明

本项目作为作者个人练习项目仅供教学使用，下载作用仅为本项目的副作用。为避免对目标站点造成困扰，作者已将并发数和下载延迟设置为作者认为不会对目标站点造成影响的程度。作者对项目使用者使用项目所造成的后果不承担任何责任，同时作者不对任何下载内容承担任何责任。

## License

MIT
