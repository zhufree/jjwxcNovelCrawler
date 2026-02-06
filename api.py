# -*- coding: UTF-8 -*-
"""
API调用模块
负责与晋江Android API通信、章节内容获取和解密
"""
import requests
import json
import re
import time

import DESCBC


def get_headers():
    """获取请求头"""
    return {"User-Agent": "Mobile " + time.asctime()}


def fetch_novel_info(novel_id):
    """
    获取小说基本信息和章节列表
    :param novel_id: 小说ID
    :return: (apicont, cdic, ress) 小说信息dict、章节列表list、网页解析结果
    """
    from lxml import etree

    req_url = f'http://www.jjwxc.net/onebook.php?novelid={novel_id}'
    apireq = f'https://app.jjwxc.net/androidapi/novelbasicinfo?novelId={novel_id}'
    apivol = f'https://app.jjwxc.net/androidapi/chapterList?novelId={novel_id}&more=0&whole=1'

    # 获取网页信息（用于特殊文案获取）
    res = requests.get(req_url, headers=get_headers())
    ress = etree.HTML(res.content.decode("GB18030", "ignore").encode("utf-8", "ignore").decode('utf-8'))
    res.close()

    # 获取API信息
    apires = requests.get(apireq, headers=get_headers())
    apicont = json.loads(apires.text)

    if "message" in apicont and "novelIntro" not in apicont:
        return apicont, None, ress

    # 获取章节列表
    rc = requests.get(apivol, headers=get_headers())
    cdic = json.loads(rc.text)
    cdic = cdic["chapterlist"]

    return apicont, cdic, ress


def fetch_chapter_content(chapter_url, token):
    """
    获取并解密单个章节的原始内容
    :param chapter_url: 章节API URL
    :param token: 用户token
    :return: dict with keys: content, sayBody, upDown, message, chapterSize, chapterDate
             content已解密，如果获取失败则content为空字符串
    """
    full_url = chapter_url + '&versionCode=349&token=' + token

    result = {
        'content': '',
        'sayBody': '',
        'upDown': '',
        'message': '',
        'chapterSize': '',
        'chapterDate': '',
    }

    badgateway = True
    retry = 100

    while badgateway and retry > 0:
        chcot = requests.get(full_url, headers=get_headers())
        try:
            chcont = json.loads(chcot.text)
        except:
            chcont = json.loads(DESCBC.decrypt_content(chcot))

        if 'message' not in chcont.keys():
            tex = chcont['content']
            tex = DESCBC.decrypt_str(tex).decode('utf-8')
            tex = re.sub('&lt;br&gt;', '\n', tex)

            result['content'] = tex
            result['sayBody'] = chcont.get('sayBody', '')
            result['upDown'] = chcont.get('upDown', '')
            result['chapterSize'] = chcont.get('chapterSize', '')
            result['chapterDate'] = chcont.get('chapterDate', '')
            badgateway = False
        else:
            result['message'] = chcont["message"]
            if re.findall('用晋江币购买章节后即可阅读', chcont["message"]):
                badgateway = False
            else:
                retry -= 1

    return result


def download_cover(cover_url):
    """
    下载封面图片
    :param cover_url: 封面URL
    :return: 图片二进制数据或None
    """
    if not cover_url:
        return None

    if re.findall(r'i9-static.jjwxc.net', cover_url):
        return None

    try:
        pres = requests.get(cover_url)
        return pres.content
    except Exception:
        return None
