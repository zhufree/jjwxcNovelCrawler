# -*- coding: UTF-8 -*-
"""
章节内容处理模块
负责章节列表解析、标题构建、内容格式化
"""
import re
import html

import utils
from models import DownloadConfig, ChapterData


def parse_chapters(cdic, novel_id, config):
    """
    解析章节列表，构建ChapterData
    :param cdic: API返回的章节列表
    :param novel_id: 小说ID
    :param config: DownloadConfig
    :return: (chapter_data, locked_chapters)
    """
    data = ChapterData()
    loc = []
    vcount = 0

    for i in cdic:
        if i["chaptertype"] == "1":
            # 卷标
            vcount += 1
            v = html.escape(i["chaptername"])
            if config.format_type == "txt":
                v = re.sub('</?\w+[^>]*>', '', v).strip()
            v = "§ " + v + " §"
            if config.custom_vol:
                v = re.sub(r'\$1', str(vcount), config.custom_vol)
                v = re.sub(r'\$2', i["chaptername"], v)
            data.roll_sign.append(v)
            data.roll_sign_place.append(i["chapterid"])
        else:
            # 普通章节
            u = f"https://app.jjwxc.net/androidapi/chapterContent?novelId={novel_id}&chapterId={i['chapterid']}"
            data.href_list.append(u)
            v = html.escape(i["chaptername"])
            v = re.sub('&&amp;#', '&#', v)
            v = re.sub('</?\w+[^>]*>', '', v)
            data.titleindex.append(v.strip())
            v = html.escape(i["chapterintro"])
            v = re.sub('&&amp;#', '&#', v)
            if config.format_type == "txt":
                v = re.sub('</?\w+[^>]*>', '', v)
            data.summary_list.append(v.strip())
            if i["islock"] != "0":
                loc.append(i["chapterid"])

    data.fill_num = len(str(len(data.href_list)))
    return data, loc


def build_index(chapter_data, loc, config):
    """
    构建目录列表
    :param chapter_data: ChapterData
    :param loc: 锁定章节列表
    :param config: DownloadConfig
    :return: 目录列表
    """
    index = []
    for idx, url in enumerate(chapter_data.href_list):
        titleOrigin = url.split('=')
        title = ''
        if titleOrigin[2] in loc:
            title += "[锁]"
        title += str(titleOrigin[2]) + " "
        title += chapter_data.titleindex[idx].strip() + " "
        title += chapter_data.summary_list[idx].strip()
        title = utils.convert_text(title, config.state)
        index.append(title)
    chapter_data.index = index
    return index


def build_title(chapter_url, chapter_data, config):
    """
    构建章节标题
    :param chapter_url: 章节URL
    :param chapter_data: ChapterData
    :param config: DownloadConfig
    :return: 标题字符串
    """
    titleOrigin = chapter_url.split('=')
    idx = chapter_data.href_list.index(chapter_url)
    title = ''

    if config.custom_title:
        title = re.sub(r'\$1', str(titleOrigin[2]), config.custom_title)
        title = re.sub(r'\$2', chapter_data.titleindex[idx].strip(), title)
        title = re.sub(r'\$3', chapter_data.summary_list[idx].strip(), title)
    else:
        if config.show_number:
            title = str(titleOrigin[2])
            if config.format_type == 'txt':
                title += " #"
        if config.show_title:
            title = title + " " + chapter_data.titleindex[idx].strip()
        if config.show_summary:
            title = title + " " + chapter_data.summary_list[idx].strip()

    title = title.strip()
    title = utils.convert_text(title, config.state)
    return title


def format_content(title, raw_data, config, fill_num):
    """
    格式化章节内容
    :param title: 章节标题
    :param raw_data: api.fetch_chapter_content返回的dict
    :param config: DownloadConfig
    :param fill_num: 章节填充位数
    :return: (formatted_content, is_failed) is_failed为失败章节号或None
    """
    tex = raw_data['content']
    tex1 = raw_data['sayBody']
    sign = raw_data['upDown']
    texm = raw_data['message']
    is_txt = config.format_type == 'txt'
    failed_id = None

    content = ''

    # 写入标题
    if is_txt:
        title_display = utils.unescape_html(title)
        content += "\n\n" + title_display + "\n"
    else:
        title_display = utils.escape_html(title)
        title_display = re.sub('&amp;amp;', '&amp;', title_display)
        content += '<h2>' + title_display + "</h2>"

    if len(tex) == 0:
        # 下载失败
        if is_txt:
            content += texm + "\n"
        else:
            content += '<p>' + texm + '</p>'
        return content, True
    else:
        # 添加章节信息
        if config.show_chinfo:
            if is_txt:
                content += "字数：" + raw_data['chapterSize'] + '\n日期：' + raw_data['chapterDate'] + '\r\n'
            else:
                content += "<p class='note'>字数：" + raw_data['chapterSize'] + '<br/>日期：' + raw_data['chapterDate'] + '</p>'

        # 处理作话
        if config.del_thanks:
            tex1 = utils.remove_thanks_content(tex1)

        tex1 = utils.clean_text(tex1)
        tex1 = utils.escape_html(tex1)
        tex = utils.clean_text(tex)
        tex = utils.escape_html(tex)

        contenta = ''
        contentb = '' if is_txt else '<p>'

        # 作话内容
        if len(tex1.strip()):
            if not is_txt:
                contenta += "<p><b>作者有话要说</b>：</p><blockquote>"
            else:
                contenta += "作者有话要说：\n"
            for v in tex1.splitlines():
                if is_txt:
                    v = utils.unescape_html(v).strip()
                    contenta += v + "\n"
                else:
                    contenta += "<p>" + v + "</p>"
            if not is_txt:
                contenta += "</blockquote>"

        # 正文内容
        for v in tex.splitlines():
            if is_txt:
                v = utils.unescape_html(v).strip()
                v = re.sub(r'^</?p>$', '', v)  # 去掉独立的<p>标签行
                v = re.sub(r'</?p>', '', v)  # 去掉行内的<p>标签
                contentb += v + "\n"
            else:
                contentb += v + "<br/>"
        if not is_txt:
            contentb += "</p>"
            contentb = re.sub(r' ?<br/> ?<br/> ?', '</p><p>', contentb)

        # txt模式：去除段间空行
        if is_txt and config.remove_blank_lines:
            lines = contentb.split('\n')
            contentb = '\n'.join(line for line in lines if line.strip()) + '\n'

        # 根据作话位置组合内容
        separator = "\n*\n" if is_txt else "<hr/>"
        if sign:  # 作话在文后
            content += contentb + separator + contenta
        else:  # 作话在文前
            content += contenta + separator + contentb

    if not is_txt:
        content += "</body></html>"

    content = re.sub("<p> *</p>", "<p><br/></p>", content)
    content = re.sub("(<p><br/></p>)+", "<p><br/></p>", content)
    content = utils.convert_text(content, config.state)

    return content, False
