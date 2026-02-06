# 晋江小说下载器 - 项目说明文档

## 项目概述

这是一个用于下载晋江文学城小说的工具，支持 TXT 和 EPUB 格式输出。**当前最新版本使用 Android API 方式抓取内容**，绕过了网页端的反爬虫机制。

---

## 最新版本 (exe整合版)

最新版本位于 `exe整合版/` 目录，是一个带有 PyQt5 GUI 界面的整合版本。

### 关键文件说明

#### 核心模块

| 文件 | 职责 |
|------|------|
| `models.py` | **数据模型**，定义 `DownloadConfig`(配置)、`NovelInfo`(小说信息)、`ChapterData`(章节数据) |
| `api.py` | **API调用**，负责与晋江 Android API 通信、章节内容获取和 DES-CBC 解密 |
| `chapter.py` | **章节处理**，章节列表解析、标题构建、内容格式化 |
| `output.py` | **文件输出**，TXT合并、EPUB生成、封面保存、信息页和卷标文件生成 |
| `downloader.py` | **下载编排器**，组合以上模块，编排完整的下载流程 |
| `utils.py` | **工具函数**，文本处理、繁简转换、HTML转义等通用功能 |

#### GUI 界面

| 文件 | 职责 |
|------|------|
| `app.py` | **NiceGUI 界面** (推荐)，基于 Web 的现代化 GUI，运行后访问 `http://localhost:8080` |
| `main.py` | **PyQt5 界面** (旧版)，桌面 GUI 界面 |
| `jjurl.py` | PyQt5 UI 定义，由 `jjurl.ui` 生成 |

#### 辅助模块

| 文件 | 职责 |
|------|------|
| `DESCBC.py` | **DES-CBC 解密模块**，用于解密 Android API 返回的加密内容 |
| `EPUB2.py` | **EPUB2 格式生成器**，创建符合 EPUB2 标准的电子书文件 |
| `EPUB3.py` | **EPUB3 格式生成器**，创建符合 EPUB3 标准的电子书文件 |
| `config.yml` | **配置文件**，存储用户设置（token、格式、线程数等） |

---

## 核心架构

### 1. 数据获取流程 (Android API 方式)

```
用户输入小说网址
       ↓
解析 novelId
       ↓
调用 Android API 获取小说基本信息
  → https://app.jjwxc.net/androidapi/novelbasicinfo?novelId=xxx
       ↓
调用 Android API 获取章节列表
  → https://app.jjwxc.net/androidapi/chapterList?novelId=xxx&more=0&whole=1
       ↓
多线程并发下载各章节内容
  → https://app.jjwxc.net/androidapi/chapterContent?novelId=xxx&chapterId=xxx&token=xxx
       ↓
DES-CBC 解密章节内容 (DESCBC.py)
       ↓
生成 TXT 或 EPUB 文件
```

### 2. 关键类和方法

#### `main.py` - MyWindow 类 (GUI层)

| 方法 | 功能 |
|------|------|
| `__init__()` | 初始化 GUI，加载配置文件 |
| `_init_ui()` | 初始化 UI 组件和事件绑定 |
| `_load_config()` | 从 `config.yml` 加载配置 |
| `saveconfig()` | 保存用户配置到 `config.yml` |
| `download()` | 下载入口，验证网址后调用 `_do_download()` |
| `_do_download()` | 执行下载流程，调用下载器模块 |

#### `downloader.py` - NovelDownloader 类 (核心层)

| 方法 | 功能 |
|------|------|
| `reset()` | 重置下载器状态 |
| `fetch_novel_info()` | 调用 API 获取小说基本信息和章节列表 |
| `download_chapter()` | 下载并解密单个章节内容 |
| `save_chapter()` | 保存章节到文件 |
| `download_cover()` | 下载封面图片 |
| `merge_txt_files()` | 合并 TXT 文件 |
| `create_epub()` | 创建 EPUB 文件 |

#### `utils.py` - 工具函数

| 函数 | 功能 |
|------|------|
| `convert_text()` | 繁简转换 |
| `clean_text()` | 清理无用内容 |
| `escape_html()` | HTML 转义 |
| `unescape_html()` | HTML 反转义 |
| `sanitize_filename()` | 清理文件名非法字符 |
| `remove_thanks_content()` | 删除一键感谢内容 |

#### `DESCBC.py` - 解密模块

| 函数 | 功能 |
|------|------|
| `decrypt_str(data)` | 使用固定密钥解密 Base64 编码的 DES-CBC 加密数据 |
| `decrypt_str1(data, Key, Iv)` | 使用自定义密钥解密 |
| `decrypt_content(res)` | 解析 HTTP 响应头，动态生成密钥并解密响应体 |

### 3. 认证方式

使用 Android App 的 **token** 进行身份验证：
- 用户需通过抓包软件（如"抓包精灵"）获取晋江 App 的 token
- token 附加在 API 请求 URL 中：`&token=xxx`
- User-Agent 设置为：`Dalvik/2.1.0` 或 `Mobile xxx`

---

## 输出格式

### TXT 格式
- 将所有章节合并为单个 `.txt` 文件
- 包含小说信息、目录、正文

### EPUB 格式
- **EPUB2**: 使用 `EPUB2.py` 生成，兼容性更好
- **EPUB3**: 使用 `EPUB3.py` 生成，支持更多特性

EPUB 文件结构：
```
├── mimetype
├── META-INF/
│   └── container.xml
└── OEBPS/
    ├── content.opf      # 包描述文件
    ├── toc.ncx          # 目录文件
    ├── nav.xhtml        # 导航文件 (EPUB3)
    ├── sgc-nav.css      # 样式表
    ├── C.xhtml          # 封面页
    ├── info.xhtml       # 小说信息页
    ├── zXXXX.xhtml      # 章节内容
    └── zp.jpg           # 封面图片
```

---

## 功能特性

- **多线程下载**: 支持自定义线程数 (1-999)
- **繁简转换**: 支持繁转简、简转繁
- **自定义标题格式**: 支持 `$1`(序号)、`$2`(章节名)、`$3`(内容提要) 占位符
- **自定义卷标格式**: 支持 `$1`(卷号)、`$2`(卷名) 占位符
- **章节信息**: 可选添加字数、更新时间
- **去除感谢**: 可选删除"一键感谢"相关内容
- **封面下载**: 自动下载并嵌入封面图片
- **自定义 CSS**: 支持自定义 EPUB 样式

---

## 旧版本说明 (已弃用)

以下目录包含旧版本代码，使用网页爬虫 + 字体反爬虫破解方式，**已不再维护**：

| 目录 | 说明 |
|------|------|
| `TXT下载/` | 旧版 TXT 下载器，使用 cookie + 字体反爬虫对照表 |
| `epub下载/` | 旧版 EPUB 下载器，使用 cookie + 字体反爬虫对照表 |
| `反爬虫对照表/` | 字体反爬虫对照表文件 |
| `反爬虫对照表_20210904/` | 更新的字体反爬虫对照表 |
| `client.py` | Selenium 登录脚本，用于获取 cookie |

---

## 依赖项

```
requests
lxml
opencc-python-reimplemented
PyQt5
Pillow
pyDes
pyyaml
```

---

## 使用方法

1. 运行 `exe整合版/main.py`
2. 输入小说网址（格式：`http://www.jjwxc.net/onebook.php?novelid=xxx`）
3. 输入从晋江 App 抓包获取的 token
4. 选择输出格式和其他选项
5. 点击"开始下载"

---

## 版本历史

- **2024-06-06**: 针对晋江 API 模式更改，更新反爬虫规则
- **2023-10-04**: 针对新反爬虫机制调整
- **2021-10-22**: 改用 Android API 下载方式，无需字体反爬虫
