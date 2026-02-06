# -*- coding: UTF-8 -*-
"""
数据模型模块
包含配置类和小说信息类
"""


class DownloadConfig:
    """下载配置类"""
    def __init__(self):
        self.token = ''
        self.format_type = 'txt'  # txt, epub2, epub3
        self.state = ''  # 繁简转换状态: '', 's'(繁转简), 't'(简转繁)
        self.show_number = True
        self.show_title = True
        self.show_summary = True
        self.show_chinfo = False
        self.del_thanks = False
        self.add_cover = True
        self.html_vol = False
        self.special_intro = False
        self.custom_title = ''
        self.custom_vol = ''
        self.css_text = ''
        self.thread_num = 100
        self.chapter_start = 0  # 起始章节号(0表示从头开始)
        self.chapter_end = 0  # 结束章节号(0表示到最后)
        self.save_per_chapter = False  # 按章保存(仅txt)
        self.remove_blank_lines = False  # 去除段间空行(仅txt)


class NovelInfo:
    """小说信息类"""
    def __init__(self):
        self.novel_id = ''
        self.title = ''
        self.author = ''
        self.author_id = ''
        self.cover_url = ''
        self.chapter_count = 0
        self.locked_chapters = []
        self.apicont = {}  # 原始API返回数据
        self.ress = None  # 网页解析结果


class ChapterData:
    """章节数据类"""
    def __init__(self):
        self.href_list = []  # 章节链接
        self.titleindex = []  # 章节标题
        self.summary_list = []  # 内容提要
        self.roll_sign = []  # 卷标
        self.roll_sign_place = []  # 卷标位置
        self.index = []  # 目录
        self.fill_num = 0  # 章节填充位数
