# -*- coding: UTF-8 -*-
"""
工具函数模块
包含文本处理、繁简转换等通用功能
"""
import re
import html
from opencc import OpenCC


def convert_text(text, state):
    """
    繁简转换
    :param text: 原始文本
    :param state: 's' 繁转简, 't' 简转繁, '' 不变
    :return: 转换后的文本
    """
    if state == 's':
        return OpenCC('t2s').convert(text)
    elif state == 't':
        return OpenCC('s2t').convert(text)
    return text


def clean_text(text):
    """
    清理文本中的无用内容
    :param text: 原始文本
    :return: 清理后的文本
    """
    text = re.sub('@无限好文，尽在晋江文学城', '', text)
    text = re.sub('　+', ' ', text)
    text = re.sub(' +', ' ', text)
    return text


def escape_html(text):
    """
    HTML转义并修复常见问题
    :param text: 原始文本
    :return: 转义后的文本
    """
    text = html.escape(text)
    text = re.sub("&amp;amp;", "&amp;", text)
    text = re.sub("&amp;gt;", "&gt;", text)
    text = re.sub("&amp;lt;", "&lt;", text)
    text = re.sub('&amp;#', '&#', text)
    return text


def unescape_html(text):
    """
    HTML反转义
    :param text: 转义后的文本
    :return: 原始文本
    """
    return html.unescape(text)


def sanitize_filename(filename):
    """
    清理文件名中的非法字符
    :param filename: 原始文件名
    :return: 合法的文件名
    """
    filename = re.sub(r'[\/:*?"<>|]', '_', filename)
    filename = re.sub('&', '&amp;', filename)
    filename = re.sub('\r', '', filename)
    return filename


def remove_thanks_content(text):
    """
    删除一键感谢相关内容
    :param text: 原始文本
    :return: 清理后的文本
    """
    pattern = (
        r'(感谢灌溉)[\w\W]+(.).*感谢(灌|投|支持).*|'
        r'感谢(在|为).*小天使.*|'
        r'.*(扔|投|砸|灌)了.*时间.*|'
        r'.*\\d瓶.*|'
        r'.*(扔|投|砸|灌|谢).*(手榴弹|营养液|地雷|浅水炸弹|深水炸弹|深水鱼雷|火箭炮|投雷|霸王票).*|'
        r'非常感谢.*努力的.*'
    )
    return re.sub(pattern, '', text)
