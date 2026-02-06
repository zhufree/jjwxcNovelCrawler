# 晋江小说下载器

[![GitHub release](https://img.shields.io/github/release/7325156/jjwxcNovelCrawler.svg)](https://github.com/7325156/jjwxcNovelCrawler/releases/latest/)

一款用于下载晋江文学城小说的工具，支持 TXT 和 EPUB 格式输出，fork自 [jjwxcNovelCrawler](https://github.com/7325156/jjwxcNovelCrawler)，添加了自己需要的章节下载功能及重写了GUI。

> ⚠️ **声明**：此项目仅供学习交流使用，严禁用于商业用途，请在24小时之内删除。

---

## ✨ 功能特性

- **多格式输出**：支持 TXT、EPUB2、EPUB3 格式
- **章节范围下载**：可指定下载第 N 章到第 M 章
- **按章保存**：TXT 格式支持每章单独保存为文件
- **去除空行**：可选去除段落间的空行
- **繁简转换**：支持繁体转简体、简体转繁体
- **自定义标题**：支持自定义章节标题和卷标格式
- **自定义 CSS**：EPUB 格式支持自定义样式
- **多线程下载**：支持设置线程数，加快下载速度
- **双版本界面**：
  - **桌面版** (`main_ttkui.py`)：基于 ttkbootstrap，轻量快速
  - **网页版** (`app.py`)：基于 NiceGUI，现代美观

---

## 📥 下载安装

### 方式一：直接下载 EXE（推荐）

前往 Releases 下载最新版本的 exe 文件，双击即可运行。

### 方式二：从源码运行

1. **安装 Python 3.8+**

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   - 桌面版：`python main_ttkui.py`
   - 网页版：`python app.py`（浏览器访问 http://localhost:8080）

---

## 🚀 使用方法

### 1. 获取 Token

1. 在手机上安装晋江 App 并登录
2. 使用抓包工具（如 HttpCanary）抓取请求
3. 在请求头中找到 `token` 参数，复制到程序中

### 2. 下载小说

1. 打开程序，粘贴小说网址（格式：`https://www.jjwxc.net/onebook.php?novelid=xxx`）
2. 填入 Token
3. 选择输出格式和其他选项
4. 点击"开始下载"

### 3. 选项说明

| 选项 | 说明 |
|------|------|
| **章节范围** | 填 0 或留空表示不限制 |
| **按章保存文件** | 仅 TXT 格式可用，每章保存为单独文件 |
| **去除段间空行** | 仅 TXT 格式可用，去除段落之间的空行 |
| **显示序号/标题/提要** | 控制章节标题显示内容 |
| **章节信息** | 显示字数和发布日期 |
| **下载封面** | 下载并嵌入封面图片 |
| **去除感谢** | 去除作话中的一键感谢内容 |
| **繁简转换** | 繁体↔简体转换 |

---

## 📁 项目结构

```
jjwxcNovelCrawler/
├── main_ttkui.py    # 桌面版 GUI（ttkbootstrap）
├── app.py           # 网页版 GUI（NiceGUI）
├── downloader.py    # 下载器核心逻辑
├── models.py        # 数据模型
├── chapter.py       # 章节内容处理
├── output.py        # 文件输出处理
├── api.py           # API 调用
├── utils.py         # 工具函数
├── DESCBC.py        # 解密模块
├── EPUB2.py         # EPUB2 生成
├── EPUB3.py         # EPUB3 生成
├── config.yml       # 配置文件（自动生成）
└── requirements.txt # 依赖列表
```

---

## ❓ 常见问题

**Q: 下载失败怎么办？**
- 检查 Token 是否正确、是否过期
- 检查网址格式是否正确
- 确认已购买 VIP 章节

**Q: 如何打包成 EXE？**
- 桌面版：`pyinstaller --onefile --windowed main_ttkui.py`
- 网页版：`nicegui-pack --onefile --name "jjdownload" app.py`
