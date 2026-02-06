# -*- coding: UTF-8 -*-
"""
文件输出模块
负责TXT合并、EPUB生成、封面保存、信息页生成、卷标文件生成
"""
import re
import os
import html
import shutil
import zipfile
from lxml import etree
from PIL import Image
from io import BytesIO

import EPUB2
import EPUB3
import utils
from models import DownloadConfig, NovelInfo, ChapterData


def save_chapter_file(chapter_url, title, content, config):
    """
    保存单个章节到文件
    :param chapter_url: 章节URL（用于提取章节号）
    :param title: 章节标题
    :param content: 格式化后的内容
    :param config: DownloadConfig
    """
    titleOrigin = chapter_url.split('=')
    chap_num = titleOrigin[2].zfill(4)

    if config.format_type == 'txt':
        filename = "z" + chap_num + ".txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        filename = "z" + chap_num + ".xhtml"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>''' + re.sub('<.*?>', '', title) + '''</title>
<meta charset="utf-8"/>
<link href="sgc-nav.css" rel="stylesheet" type="text/css"/>
</head><body>''')
            f.write(content)


def save_volume_files(chapter_data, config, output_dir):
    """
    保存卷标文件
    :param chapter_data: ChapterData
    :param config: DownloadConfig
    :param output_dir: 输出目录
    """
    for vol in range(len(chapter_data.roll_sign_place)):
        chapter_data.roll_sign_place[vol] = chapter_data.roll_sign_place[vol].strip()
        volt = chapter_data.roll_sign_place[vol]
        ros = chapter_data.roll_sign[vol]
        ros = utils.convert_text(ros, config.state)

        if config.format_type == "txt":
            nm = 'z' + str(int(volt) - 1).zfill(4) + '_vol.txt'
            with open(os.path.join(output_dir, nm), 'w', encoding='utf-8') as f:
                f.write('\n\n' + ros + '\n')
        else:
            nm = 'z' + str(int(volt) - 1).zfill(4) + '_vol.xhtml'
            with open(os.path.join(output_dir, nm), 'w', encoding='utf-8') as f:
                f.write(f'''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{ros}</title><meta charset="utf-8"/>
<link href="sgc-nav.css" rel="stylesheet" type="text/css"/></head>
<body><h1>{ros}</h1></body></html>''')


def save_cover(cover_data, output_dir):
    """
    保存封面图片和封面页
    :param cover_data: 封面图片二进制数据
    :param output_dir: 输出目录
    :return: 是否成功
    """
    if not cover_data:
        return False

    try:
        im = Image.open(BytesIO(cover_data))
        im.save(os.path.join(output_dir, 'zp.jpg'), 'JPEG')

        with open(os.path.join(output_dir, "C.xhtml"), 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Cover</title></head>
<body><div style="text-align: center; padding: 0pt; margin: 0pt;">
<svg xmlns="http://www.w3.org/2000/svg" height="100%" preserveAspectRatio="xMidYMid meet" version="1.1" width="100%" xmlns:xlink="http://www.w3.org/1999/xlink">
<image width="100%" xlink:href="zp.jpg"/></svg></div></body></html>''')
        return True
    except Exception:
        return False


def save_info_page(novel_info, loc, config, output_dir, req_url):
    """
    保存信息页
    :param novel_info: NovelInfo
    :param loc: 锁定章节列表
    :param config: DownloadConfig
    :param output_dir: 输出目录
    :param req_url: 原始请求URL
    """
    apicont = novel_info.apicont
    ress = novel_info.ress
    xtitle = novel_info.title
    xaut = novel_info.author
    xauthref = f"http://www.jjwxc.net/oneauthor.php?authorid={apicont.get('authorId', '')}"

    # 获取文案
    if config.special_intro and ress is not None:
        intro = ress.xpath("//html/body/table/tr/td[1]/div[2]/div[@id='novelintro']")
    else:
        intro = apicont.get("novelIntro", "")
        intro = re.sub("&lt;br/&gt;", "\n", intro).splitlines()

    # 获取标签信息
    info = [
        "<b>标签：</b>" + apicont.get("novelTags", ""),
        apicont.get("protagonist", ""),
        apicont.get("costar", ""),
        apicont.get("other", ""),
        "<b>简介：</b>" + apicont.get("novelIntroShort", "")
    ]

    infox = [
        "文章类型：" + apicont.get("novelClass", ""),
        "作品视角：" + apicont.get("mainview", ""),
        "作品风格：" + apicont.get("novelStyle", ""),
        "所属系列：" + apicont.get("series", ""),
        "全文字数：" + apicont.get("novelSize", "") + "字"
    ]

    # 锁定章节信息
    lockinfo = ''
    if loc:
        if config.format_type != "txt":
            lockinfo = "<p><em>被锁章节：" + " ".join(loc) + "</em></p>"
        else:
            lockinfo = "被锁章节：" + " ".join(loc) + "\n"
        lockinfo = utils.convert_text(lockinfo, config.state)

    # 写入信息页
    if config.format_type == "txt":
        TOC = f"{xtitle}\n作者：{xaut}\n源网址：{req_url}\n"
        for ix in infox:
            ix = re.sub('\n', '', ix.strip())
            ix = re.sub(' +', '', ix)
            ix = utils.unescape_html(ix)
            TOC += ix + "\n"
        TOC += "文案：\n"
        if config.special_intro and intro:
            v = etree.tostring(intro[0], encoding="utf-8").decode()
            TOC += v
        else:
            for nx in intro:
                v = re.sub(' +', ' ', str(nx))
                v = utils.unescape_html(v)
                TOC += v + "\n"
        for v in info:
            v = utils.unescape_html(v)
            TOC += re.sub("<.*?>", "", v) + '\n'
        TOC = utils.convert_text(TOC, config.state)
        with open(os.path.join(output_dir, "info.txt"), 'w', encoding='utf-8') as fo:
            fo.write(TOC.strip() + '\n')
            fo.write(lockinfo.strip() + '\n')
    else:
        TOC = f"<h1 class='title' title='{xtitle}-{xaut}'><a href='{req_url}'>{xtitle}</a></h1>"
        TOC += f"<h2 class='sigil_not_in_toc title'>作者：<a href='{xauthref}'>{xaut}</a></h2>"
        TOC += "<blockquote>"
        for ix in infox:
            ix = re.sub('\n', '', ix.strip())
            ix = re.sub(' +', '', ix)
            TOC += "<p>" + ix + "</p>"
        TOC += "</blockquote>"
        TOC += "<hr/><p><b>文案：</b></p>"
        if config.special_intro and intro:
            v = etree.tostring(intro[0], encoding="utf-8").decode()
            TOC += v
        else:
            for nx in intro:
                v = re.sub(' +', ' ', str(nx))
                v = html.escape(v)
                TOC += "<p>" + v + "</p>"
        for v in info:
            v = re.sub("主角：", "<b>主角：</b>", v)
            v = re.sub("配角：", "<b>配角：</b>", v)
            v = re.sub("其它：", "<b>其它：</b>", v)
            TOC += "<p>" + v + "</p>"
        TOC = utils.convert_text(TOC, config.state)
        with open(os.path.join(output_dir, "info.xhtml"), 'w', encoding='utf-8') as fo:
            fo.write('''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title></title><meta charset="utf-8"/>
<link href="sgc-nav.css" rel="stylesheet" type="text/css"/></head>
<body>''' + TOC + lockinfo + '''</body></html>''')


def rename_chapter_files(source_dir, chapter_data, config):
    """
    按章保存模式：将临时文件重命名为可读的章节文件名
    :param source_dir: 源目录
    :param chapter_data: ChapterData
    :param config: DownloadConfig
    """
    import utils
    filenames = sorted(os.listdir(source_dir))
    for filename in filenames:
        if not filename.endswith('.txt'):
            continue
        # 跳过 info.txt 和卷标文件
        if filename == 'info.txt' or '_vol' in filename:
            continue
        filepath = os.path.join(source_dir, filename)
        # 从文件名提取章节号，如 z0001.txt -> 1
        base = filename.replace('.txt', '').lstrip('z').lstrip('0') or '0'
        try:
            chap_num = int(base)
        except ValueError:
            continue
        # 在href_list中查找对应章节的标题
        new_name = filename  # fallback
        for idx, url in enumerate(chapter_data.href_list):
            url_chap_id = url.split('=')[2]
            if str(url_chap_id) == str(chap_num):
                title = chapter_data.titleindex[idx].strip()
                title = utils.convert_text(title, config.state)
                title = utils.sanitize_filename(title)
                new_name = f"{title}.txt"
                break
        new_path = os.path.join(source_dir, new_name)
        if filepath != new_path and not os.path.exists(new_path):
            os.rename(filepath, new_path)


def merge_txt_files(source_dir, output_file):
    """
    合并TXT文件
    :param source_dir: 源目录
    :param output_file: 输出文件路径
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        filenames = sorted(os.listdir(source_dir))
        for filename in filenames:
            filepath = os.path.join(source_dir, filename)
            for line in open(filepath, encoding='utf-8', errors='ignore'):
                f.writelines(line)
    shutil.rmtree(source_dir)


def create_epub(output_file, author, title, dir_name, index, roll_sign, base_path, config):
    """
    创建EPUB文件
    :param output_file: 输出文件路径
    :param author: 作者
    :param title: 书名
    :param dir_name: 目录名
    :param index: 目录列表
    :param roll_sign: 卷标列表
    :param base_path: 基础路径
    :param config: DownloadConfig
    """
    epub = zipfile.ZipFile(output_file, 'w')

    if config.format_type == 'epub2':
        epubfile = EPUB2.epubfile()
        if config.html_vol:
            epubfile.htmlvol = 1
    else:
        epubfile = EPUB3.epubfile()

    epubfile.csstext = config.css_text
    epubfile.createEpub(epub, author, title, dir_name, index, roll_sign, base_path)
