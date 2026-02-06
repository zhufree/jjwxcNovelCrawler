# -*- coding: UTF-8 -*-
"""
下载编排器模块
组合api、chapter、output模块，编排完整的下载流程
"""
import os
import concurrent.futures

import api
import chapter
import output
import utils
from models import DownloadConfig, NovelInfo


class NovelDownloader:
    """小说下载编排器"""

    def __init__(self, config=None, progress_callback=None, log_callback=None):
        """
        :param config: DownloadConfig 配置对象
        :param progress_callback: 进度回调 (percent, current, total)
        :param log_callback: 日志回调 (message)
        """
        self.config = config or DownloadConfig()
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.reset()

    def reset(self):
        """重置状态"""
        self.percent = 0
        self.fail_info = []
        self.current_title = ''
        self.novel_info = None
        self.chapter_data = None

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def _update_progress(self, current, total):
        if self.progress_callback:
            pct = int(100 * current / total) if total > 0 else 0
            self.progress_callback(pct, current, total)

    def _download_and_save_chapter(self, chapter_url):
        """下载并保存单个章节"""
        title = chapter.build_title(chapter_url, self.chapter_data, self.config)
        raw = api.fetch_chapter_content(chapter_url, self.config.token)
        content, failed = chapter.format_content(
            title, raw, self.config, self.chapter_data.fill_num
        )
        self.current_title = title

        if failed:
            chap_id = chapter_url.split('=')[2]
            self.fail_info.append(chap_id.zfill(self.chapter_data.fill_num))

        output.save_chapter_file(chapter_url, title, content, self.config)
        self.percent += 1

    def download_novel(self, url, threadnum=None):
        """
        下载小说主流程
        :param url: 小说网址
        :param threadnum: 线程数（None则使用config中的值）
        :return: (success, output_file, error_message)
        """
        self.reset()
        threadnum = threadnum or self.config.thread_num

        # 解析小说ID
        nid = url.split('=')[1]

        # 获取小说信息
        self._log("正在获取小说信息...")
        apicont, cdic, ress = api.fetch_novel_info(nid)

        if "message" in apicont and "novelIntro" not in apicont:
            return False, None, apicont.get("message", "获取小说信息失败")

        # 构建小说信息
        info = NovelInfo()
        info.novel_id = nid
        info.title = apicont["novelName"]
        info.author = apicont["authorName"]
        info.author_id = apicont.get("authorId", "")
        info.cover_url = apicont.get("novelCover", "")
        info.apicont = apicont
        info.ress = ress
        self.novel_info = info

        ti = info.title + '-' + info.author
        ti = utils.convert_text(ti, self.config.state)
        self._log(f"网址：{url}\n小说信息：{ti}")

        # 解析章节列表
        self.chapter_data, loc = chapter.parse_chapters(cdic, nid, self.config)
        info.locked_chapters = loc
        total_chapters = len(self.chapter_data.href_list)
        info.chapter_count = total_chapters

        self._log(f"总章节数：{total_chapters}")
        if loc:
            self._log(f"被锁章节：{' '.join(loc)}")

        # 按章节范围筛选
        ch_start = self.config.chapter_start
        ch_end = self.config.chapter_end
        if ch_start > 0 or ch_end > 0:
            start_idx = max(0, ch_start - 1) if ch_start > 0 else 0
            end_idx = min(ch_end, total_chapters) if ch_end > 0 else total_chapters
            self.chapter_data.href_list = self.chapter_data.href_list[start_idx:end_idx]
            self.chapter_data.titleindex = self.chapter_data.titleindex[start_idx:end_idx]
            self.chapter_data.summary_list = self.chapter_data.summary_list[start_idx:end_idx]
            self._log(f"选定范围：第{start_idx+1}章 ~ 第{end_idx}章")

        section_ct = len(self.chapter_data.href_list)
        self._log(f"待下载章节数：{section_ct}")

        # 准备输出目录
        ti = utils.sanitize_filename(ti) + '.' + nid
        base_path = os.getcwd()

        output_dir = os.path.join(base_path, ti)
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        os.chdir(output_dir)

        # 保存卷标
        output.save_volume_files(self.chapter_data, self.config, output_dir)

        # 构建目录
        chapter.build_index(self.chapter_data, loc, self.config)

        # 保存封面
        if self.config.add_cover and self.config.format_type != "txt":
            cover_data = api.download_cover(info.cover_url)
            if not output.save_cover(cover_data, output_dir):
                self._log("【封面下载失败或为默认封面】")

        # 保存信息页
        output.save_info_page(info, loc, self.config, output_dir, url)

        # 多线程下载章节
        self._log("开始下载章节...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=threadnum) as executor:
            futures = {
                executor.submit(self._download_and_save_chapter, u): u
                for u in self.chapter_data.href_list
            }
            for future in concurrent.futures.as_completed(futures):
                self._update_progress(self.percent, section_ct)

        self._log(f'\n下载完成，总进度：{self.percent}/{section_ct}')

        # 显示失败章节
        if self.fail_info:
            self.fail_info.sort()
            self._log(f"\n未购买或加载失败章节：\n{'|'.join(self.fail_info)}")

        # 生成最终文件
        os.chdir(base_path)
        if self.config.format_type == "txt":
            if self.config.save_per_chapter:
                # 按章保存：重命名临时文件到可读文件名
                output.rename_chapter_files(output_dir, self.chapter_data, self.config)
                output_file = output_dir
                self._log(f"\ntxt按章保存完成，目录：{output_dir}")
            else:
                output_file = ti + ".txt"
                output.merge_txt_files(output_dir, output_file)
                self._log("\ntxt文件整合完成")
        else:
            output_file = ti + ".epub"
            output.create_epub(
                output_file, info.author, info.title, ti,
                self.chapter_data.index, self.chapter_data.roll_sign,
                base_path, self.config
            )
            self._log("\nepub打包完成")

        return True, output_file, None
