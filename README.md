# Dmzj_backup

dmzj备份——维护你的本地dmzj书架

## 简介

考虑到叔叔的大手以及无形大手的影响，有必要保全dmzj上的订阅内容，因此试着写了这个项目

本项目可以下载并同步更新用户在dmzj上的订阅内容

## 3.0更新

为了适配作者的另一个仓库[Comic2Epub](https://github.com/eesxy/Comic2Epub)，所有数据改用`.toml`格式存储，并在下载时生成一个Tachiyomi形式的元数据`.json`文件

**注意**：旧的元数据与此版本已不兼容

## 环境

需要scrapy, js2py库  

```bash
pip3 install scrapy, js2py
```

## 一分钟教程

对高级功能不感兴趣的用户只需阅读下面的一分钟教程即可轻松上手

1. 修改`settings.py`中的`MY_USERNAME`, `MY_PASSWORD`为自己的用户名和密码

2. 在命令行中转到项目目录，执行

    ```bash
    python run.py
    ```

    首次运行会爬取全部订阅内容，如果订阅内容较多，首次运行的时间会比较长，请耐心等待

3. 后续下载更新内容时，为缩短运行时间，避免重复请求和下载，可以将`MY_ROUGH_UPDATE`设置为`True`，同样地执行

    ```bash
    python run.py
    ```

## 基本用法

修改`settings.py`中的`MY_USERNAME`, `MY_PASSWORD`为自己的用户名和密码

在命令行中转到项目目录，执行

```bash
scrapy crawl Dmzj
```

也可运行项目文件夹中的`run.py`来快速启动(推荐)

```bash
python run.py
```

## 进阶用法

### 暂停和恢复程序

scrapy库支持暂停和恢复程序，通过`JOBDIR`参数传递，例如，在启动时执行

```bash
scrapy crawl Dmzj -s JOBDIR=jobs/test1
```

然后可以安全地停止程序(如`ctrl+C`或远程发送信号)，下一次启动时只需执行相同命令即可恢复请求队列

```bash
scrapy crawl Dmzj -s JOBDIR=jobs/test1
```

详细用法参见[scrapy:jobs](https://docs.scrapy.org/en/latest/topics/jobs.html)

### 设置代理

`middlewares.py`中实现了简单的proxy中间件，通过修改 `MY_PROXY_ENABLED`和`MY_PROXY`设置即可通过单一代理进行访问，后续可能会添加代理池的实现。建议设置代理使用，以免影响对dmzj的正常访问

### 快速更新书架

第一次下载完成后，通过将`MY_UPDATE_MODE`设置为`True`，爬虫将以更新模式运行，通过上一次保存的`info.toml`文件进行更新章节的匹配，并忽略上次已经抓取的章节，有效提高第二次及之后运行的速度

更进一步，开启`MY_ROUGH_UPDATE`粗略更新模式后，爬虫将只比较订阅页面中的最新章节信息与本地是否一致，大大提高运行速度

**注意**: 更新模式下将忽略已下载内容的完整性，若上一次下载未完成(例如通过`ctrl+C`中途退出)就开启更新模式将造成下载内容不完整。这是由于爬虫在成功抓取目录页后直接返回含有`info.toml`信息的`ComicItem`，并未检查后续请求成功与否

要避免这种情况，请完整运行第一次后开启此设置，并开启 `MY_RETRY`重试上一次运行中意外失败的请求(如403或429等)。重试后可能仍出现404错误，但部分404是服务器资源缺失造成的，如果多次运行后重试列表仍未清空，可以手动删除`error.toml`文件

### 更新封面

启用`MY_COVER_UPDATE`设置将重新请求各漫画的封面并覆盖本地封面，如果需要更新封面图，请开启此选项并关闭 `MY_ROUGH_UPDATE`选项

## 设置

在`settings.py`文件中修改设置，常用的设置如下

- `MY_USERNAME`, `MY_PASSWORD`: 用户名和密码
- `FILES_STORE`: 图片下载位置，默认为`'./download'`
- `CONCURRENT_REQUESTS`: 并行下载线程数，默认为4，请勿设置过大
- `DOWNLOAD_DELAY`: 两次请求间的延迟，为0时无延迟，请勿设置过小

一些进阶设置如下

- `LOG_LEVEL`: 日志等级，基于`logging`库
- `RETRY_ENABLED`: 请求失败后是否重试，默认为`True`
- `RETRY_TIMES`: 请求失败后的重试次数
- `DOWNLOAD_TIMEOUT`: 请求超时时间
- `TELNETCONSOLE_PORT`, `TELNETCONSOLE_USERNAME`, `TELNETCONSOLE_PASSWORD`: telnet控制台参数，详见[scrapy:telnet](https://docs.scrapy.org/en/latest/topics/telnetconsole.html)
- `MY_ROUGH_UPDATE`: 以粗略检查模式运行，将覆盖更新模式和更新封面的设置，建议日常更新使用时开启。开启后将忽略`MY_UPDATE_MODE`和`MY_COVER_UPDATE`
- `MY_UPDATE_MODE`: 以更新模式运行，默认为`False`，建议第一次运行结束后开启
- `MY_COVER_UPDATE`: 启用后会强制更新封面
- `MY_RETRY`: 启用后会在运行开始时重试上一次失败的请求，不启用时失败请求也会记录但不会重试，直到启用后的下一次运行开始时重试所有记录的请求

其余设置请谨慎修改，详见`settings.py`以及[scrapy:settings](https://docs.scrapy.org/en/latest/topics/settings.html)

## 免责声明

本项目作为作者个人练习项目仅供教学使用，下载作用仅为本项目的副作用。为避免对目标站点造成困扰，作者已将并发数和下载延迟设置为作者认为不会对目标站点造成影响的程度。作者不对项目使用者使用项目所造成的任何后果承担任何责任，同时作者不对任何下载内容承担任何责任。

## License

MIT
