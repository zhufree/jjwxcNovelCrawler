# -*- coding: UTF-8 -*-
"""
晋江小说下载器 - 桌面GUI (ttkbootstrap)
"""
import os
import re
import threading
import yaml
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from tkinter import messagebox

from models import DownloadConfig
from downloader import NovelDownloader

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_BASE_DIR, 'config.yml')

DEFAULT_CSS = '''nav#landmarks {display:none;}
nav#page-list {display:none;}
ol {list-style-type: none;}/*epub3目录格式*/
h1{font-size:1.4em;text-align:center;}/*一级标题*/
h2{font-size:1.24em;text-align:center;}/*二级标题*/
.title{text-align:center;}/*文章名*/
.note{font-size:0.8em;text-align:right;}/*章节信息*/
body{text-indent:2em;}/*全局格式*/'''

STATE_MAP = {'不转换': '', '繁→简': 's', '简→繁': 't'}
STATE_MAP_REV = {v: k for k, v in STATE_MAP.items()}


class App(ttk.Window):
    """主窗口"""

    def __init__(self):
        super().__init__(title='晋江小说下载器', themename='cosmo',
                         size=(720, 780), resizable=(True, True))
        self._downloading = False
        self._build_ui()
        self._load_config()

    # ================================================================
    # UI 构建
    # ================================================================
    def _build_ui(self):
        notebook = ttk.Notebook(self, bootstyle=PRIMARY)
        notebook.pack(fill=BOTH, expand=True, padx=8, pady=8)

        # --- Tab 1: 基本设置 ---
        tab_basic = ttk.Frame(notebook, padding=10)
        notebook.add(tab_basic, text=' 基本设置 ')

        # 网址
        frm = ttk.Labelframe(tab_basic, text='下载地址', padding=8)
        frm.pack(fill=X, pady=(0, 6))
        self.var_url = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_url, width=70).pack(fill=X)

        # Token + 线程数
        frm2 = ttk.Frame(tab_basic)
        frm2.pack(fill=X, pady=(0, 6))
        lf_token = ttk.Labelframe(frm2, text='Token', padding=8)
        lf_token.pack(side=LEFT, fill=X, expand=True, padx=(0, 4))
        self.var_token = tk.StringVar()
        ttk.Entry(lf_token, textvariable=self.var_token, width=50).pack(fill=X)

        lf_thread = ttk.Labelframe(frm2, text='线程数', padding=8)
        lf_thread.pack(side=LEFT, padx=(4, 0))
        self.var_thread = tk.StringVar(value='100')
        ttk.Entry(lf_thread, textvariable=self.var_thread, width=6).pack()

        # 格式 + 繁简
        frm3 = ttk.Frame(tab_basic)
        frm3.pack(fill=X, pady=(0, 6))

        lf_fmt = ttk.Labelframe(frm3, text='输出格式', padding=8)
        lf_fmt.pack(side=LEFT, padx=(0, 4))
        self.var_format = tk.StringVar(value='txt')
        self.fmt_combo = ttk.Combobox(lf_fmt, textvariable=self.var_format, width=8,
                      values=['txt', 'epub2', 'epub3'], state='readonly')
        self.fmt_combo.pack()
        self.fmt_combo.bind('<<ComboboxSelected>>', self._on_format_changed)

        lf_state = ttk.Labelframe(frm3, text='繁简转换', padding=8)
        lf_state.pack(side=LEFT, padx=(4, 0))
        self.var_state = tk.StringVar(value='不转换')
        ttk.Combobox(lf_state, textvariable=self.var_state, width=8,
                      values=['不转换', '繁→简', '简→繁'], state='readonly').pack()

        # 章节范围
        lf_range = ttk.Labelframe(tab_basic, text='章节范围（留空或填0表示不限制）', padding=8)
        lf_range.pack(fill=X, pady=(0, 6))
        range_row = ttk.Frame(lf_range)
        range_row.pack(fill=X)
        ttk.Label(range_row, text='从第').pack(side=LEFT)
        self.var_ch_start = tk.StringVar(value='')
        ttk.Entry(range_row, textvariable=self.var_ch_start, width=6).pack(side=LEFT, padx=4)
        ttk.Label(range_row, text='章  到第').pack(side=LEFT)
        self.var_ch_end = tk.StringVar(value='')
        ttk.Entry(range_row, textvariable=self.var_ch_end, width=6).pack(side=LEFT, padx=4)
        ttk.Label(range_row, text='章').pack(side=LEFT)

        # 按章保存（仅txt）
        self.var_save_per_ch = tk.BooleanVar(value=False)
        self.chk_save_per_ch = ttk.Checkbutton(range_row, text='按章保存文件', variable=self.var_save_per_ch)
        self.chk_save_per_ch.pack(side=LEFT, padx=(20, 0))

        # 去除空行（仅txt）
        self.var_rm_blank = tk.BooleanVar(value=False)
        self.chk_rm_blank = ttk.Checkbutton(range_row, text='去除段间空行', variable=self.var_rm_blank)
        self.chk_rm_blank.pack(side=LEFT, padx=(12, 0))
        self._on_format_changed()  # 初始状态

        # 选项
        lf_opts = ttk.Labelframe(tab_basic, text='标题与内容选项', padding=8)
        lf_opts.pack(fill=X, pady=(0, 6))

        row1 = ttk.Frame(lf_opts)
        row1.pack(fill=X, pady=2)
        self.var_number = tk.BooleanVar(value=True)
        self.var_title = tk.BooleanVar(value=True)
        self.var_summary = tk.BooleanVar(value=True)
        self.var_chinfo = tk.BooleanVar(value=False)
        ttk.Checkbutton(row1, text='显示序号', variable=self.var_number).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row1, text='显示标题', variable=self.var_title).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row1, text='显示提要', variable=self.var_summary).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row1, text='章节信息', variable=self.var_chinfo).pack(side=LEFT)

        row2 = ttk.Frame(lf_opts)
        row2.pack(fill=X, pady=2)
        self.var_cover = tk.BooleanVar(value=True)
        self.var_delthk = tk.BooleanVar(value=False)
        self.var_special = tk.BooleanVar(value=False)
        self.var_htmlvol = tk.BooleanVar(value=False)
        ttk.Checkbutton(row2, text='下载封面', variable=self.var_cover).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row2, text='去除感谢', variable=self.var_delthk).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row2, text='网页文案', variable=self.var_special).pack(side=LEFT, padx=(0, 12))
        ttk.Checkbutton(row2, text='HTML卷标', variable=self.var_htmlvol).pack(side=LEFT)

        # 自定义标题
        row3 = ttk.Frame(lf_opts)
        row3.pack(fill=X, pady=2)
        self.var_selftitle = tk.BooleanVar(value=False)
        ttk.Checkbutton(row3, text='自定义标题', variable=self.var_selftitle).pack(side=LEFT)
        self.var_titlefmt = tk.StringVar()
        ttk.Entry(row3, textvariable=self.var_titlefmt, width=30).pack(side=LEFT, padx=(8, 0), fill=X, expand=True)
        ttk.Label(row3, text='($1序号 $2标题 $3提要)', font=('', 8)).pack(side=LEFT, padx=(4, 0))

        # 自定义卷标
        row4 = ttk.Frame(lf_opts)
        row4.pack(fill=X, pady=2)
        self.var_selfvol = tk.BooleanVar(value=False)
        ttk.Checkbutton(row4, text='自定义卷标', variable=self.var_selfvol).pack(side=LEFT)
        self.var_volfmt = tk.StringVar()
        ttk.Entry(row4, textvariable=self.var_volfmt, width=30).pack(side=LEFT, padx=(8, 0), fill=X, expand=True)
        ttk.Label(row4, text='($1卷号 $2卷名)', font=('', 8)).pack(side=LEFT, padx=(4, 0))

        # --- Tab 2: CSS ---
        tab_css = ttk.Frame(notebook, padding=10)
        notebook.add(tab_css, text=' 自定义CSS ')

        btn_frm = ttk.Frame(tab_css)
        btn_frm.pack(fill=X, pady=(0, 4))
        ttk.Button(btn_frm, text='恢复默认CSS', bootstyle=SECONDARY,
                   command=self._reset_css).pack(side=RIGHT)

        self.css_text = ScrolledText(tab_css, height=12, autohide=True)
        self.css_text.pack(fill=BOTH, expand=True)
        self.css_text.insert(tk.END, DEFAULT_CSS)

        # --- 底部：进度 + 日志 + 按钮 ---
        bottom = ttk.Frame(self, padding=(8, 0, 8, 8))
        bottom.pack(fill=BOTH, expand=True)

        # 进度条
        prog_frm = ttk.Frame(bottom)
        prog_frm.pack(fill=X, pady=(0, 4))
        self.progress = ttk.Progressbar(prog_frm, bootstyle=SUCCESS, maximum=100)
        self.progress.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        self.lbl_progress = ttk.Label(prog_frm, text='等待开始', width=16, anchor=CENTER)
        self.lbl_progress.pack(side=LEFT)

        # 日志
        self.log_text = ScrolledText(bottom, height=10, autohide=True, state=tk.DISABLED)
        self.log_text.pack(fill=BOTH, expand=True, pady=(0, 6))

        # 按钮
        btn_bar = ttk.Frame(bottom)
        btn_bar.pack(fill=X)
        ttk.Button(btn_bar, text='保存配置', bootstyle=OUTLINE,
                   command=self._save_config).pack(side=LEFT, padx=(0, 8))
        self.btn_download = ttk.Button(btn_bar, text='开始下载', bootstyle=SUCCESS,
                                        command=self._start_download)
        self.btn_download.pack(side=LEFT)

    # ================================================================
    # 配置管理
    # ================================================================
    def _load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return
        with open(CONFIG_FILE, encoding='utf-8') as f:
            conf = yaml.load(f.read(), Loader=yaml.FullLoader)
        if not conf:
            return

        self.var_token.set(conf.get('token', ''))
        self.var_thread.set(str(conf.get('ThreadPoolMaxNum', 100)))
        self.var_format.set(conf.get('format', 'txt'))
        self.var_state.set(STATE_MAP_REV.get(conf.get('state', ''), '不转换'))

        ti = conf.get('titleInfo', '1 1 1').split(' ')
        while len(ti) < 3:
            ti.append('1')
        self.var_number.set(ti[0] != '0')
        self.var_title.set(ti[1] != '0')
        self.var_summary.set(ti[2] != '0')

        self.var_chinfo.set(bool(conf.get('chinfo', 0)))
        self.var_cover.set(bool(conf.get('cover', '')))
        self.var_delthk.set(bool(conf.get('delthk', 0)))
        self.var_special.set(bool(conf.get('special', 0)))
        self.var_htmlvol.set(bool(conf.get('htmlvol', 0)))

        if conf.get('selftitle') and isinstance(conf['selftitle'], str):
            self.var_selftitle.set(True)
            self.var_titlefmt.set(conf['selftitle'])
        if conf.get('volumn') and isinstance(conf['volumn'], str):
            self.var_selfvol.set(True)
            self.var_volfmt.set(conf['volumn'])

        css = conf.get('css', '')
        if css:
            self.css_text.delete('1.0', tk.END)
            self.css_text.insert(tk.END, css)

    def _save_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, encoding='utf-8') as f:
                doc = yaml.load(f.read(), Loader=yaml.FullLoader) or {}
        else:
            doc = {}

        doc['token'] = self.var_token.get()
        doc['state'] = STATE_MAP.get(self.var_state.get(), '')
        doc['format'] = self.var_format.get()

        ti = ('1' if self.var_number.get() else '0') + ' ' + \
             ('1' if self.var_title.get() else '0') + ' ' + \
             ('1' if self.var_summary.get() else '0')
        doc['titleInfo'] = ti

        doc['chinfo'] = 1 if self.var_chinfo.get() else 0
        doc['cover'] = 'e' if self.var_cover.get() else ''
        doc['delthk'] = 1 if self.var_delthk.get() else 0
        doc['special'] = 1 if self.var_special.get() else 0
        doc['htmlvol'] = 1 if self.var_htmlvol.get() else 0
        doc['selftitle'] = self.var_titlefmt.get() if self.var_selftitle.get() else 0
        doc['volumn'] = self.var_volfmt.get() if self.var_selfvol.get() else 0

        if self.var_format.get() in ('epub2', 'epub3'):
            doc['css'] = self.css_text.get('1.0', tk.END).strip()

        try:
            thread_num = int(self.var_thread.get())
            if 0 < thread_num < 1000:
                doc['ThreadPoolMaxNum'] = thread_num
            else:
                messagebox.showwarning('警告', '最大线程数超出范围(1-999)！')
        except ValueError:
            messagebox.showwarning('警告', '线程数格式错误！')

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(doc, f)
        self.title('晋江小说下载器 - 配置已保存')

    def _on_format_changed(self, event=None):
        """格式切换时控制txt专属选项的可用性"""
        if self.var_format.get() == 'txt':
            self.chk_save_per_ch.configure(state=tk.NORMAL)
            self.chk_rm_blank.configure(state=tk.NORMAL)
        else:
            self.var_save_per_ch.set(False)
            self.chk_save_per_ch.configure(state=tk.DISABLED)
            self.var_rm_blank.set(False)
            self.chk_rm_blank.configure(state=tk.DISABLED)

    def _reset_css(self):
        self.css_text.delete('1.0', tk.END)
        self.css_text.insert(tk.END, DEFAULT_CSS)

    # ================================================================
    # 下载
    # ================================================================
    def _build_config(self):
        config = DownloadConfig()
        config.token = self.var_token.get()
        config.format_type = self.var_format.get()
        config.state = STATE_MAP.get(self.var_state.get(), '')
        config.thread_num = int(self.var_thread.get() or 100)
        config.show_number = self.var_number.get()
        config.show_title = self.var_title.get()
        config.show_summary = self.var_summary.get()
        config.show_chinfo = self.var_chinfo.get()
        config.del_thanks = self.var_delthk.get()
        config.add_cover = self.var_cover.get()
        config.html_vol = self.var_htmlvol.get()
        config.special_intro = self.var_special.get()
        config.css_text = self.css_text.get('1.0', tk.END).strip()
        if self.var_selftitle.get():
            config.custom_title = self.var_titlefmt.get()
        if self.var_selfvol.get():
            config.custom_vol = self.var_volfmt.get()
        # 章节范围
        try:
            config.chapter_start = int(self.var_ch_start.get()) if self.var_ch_start.get().strip() else 0
        except ValueError:
            config.chapter_start = 0
        try:
            config.chapter_end = int(self.var_ch_end.get()) if self.var_ch_end.get().strip() else 0
        except ValueError:
            config.chapter_end = 0
        config.save_per_chapter = self.var_save_per_ch.get()
        config.remove_blank_lines = self.var_rm_blank.get()
        return config

    def _on_log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _on_progress(self, percent, current, total):
        self.progress['value'] = percent
        self.lbl_progress.configure(text=f'{current}/{total} ({percent}%)')

    def _start_download(self):
        if self._downloading:
            messagebox.showwarning('提示', '正在下载中，请等待...')
            return

        url = self.var_url.get().strip()
        if not re.findall(r'(http|https)://www.jjwxc.net/onebook.php\?novelid=[0-9]+', url):
            messagebox.showwarning('警告', '网址格式错误！请使用网页版网址')
            return

        self._downloading = True
        self.btn_download.configure(state=tk.DISABLED, text='下载中...')
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.progress['value'] = 0
        self.lbl_progress.configure(text='准备中...')

        config = self._build_config()
        downloader = NovelDownloader(
            config=config,
            progress_callback=lambda p, c, t: self.after(0, self._on_progress, p, c, t),
            log_callback=lambda m: self.after(0, self._on_log, m),
        )

        def _run():
            try:
                success, output_file, error = downloader.download_novel(url)
                self.after(0, self._on_download_done, success, output_file, error, downloader)
            except Exception as e:
                self.after(0, self._on_download_done, False, None, str(e), downloader)

        threading.Thread(target=_run, daemon=True).start()

    def _on_download_done(self, success, output_file, error, downloader):
        self._downloading = False
        self.btn_download.configure(state=tk.NORMAL, text='开始下载')

        if success:
            info = downloader.novel_info
            name = f"{info.title}-{info.author}" if info else output_file
            self.title(f'下载完成：{name}')
            self.lbl_progress.configure(text='下载完成！')
            self.progress['value'] = 100

            if downloader.fail_info:
                messagebox.showwarning('提示',
                    f'部分章节下载失败({len(downloader.fail_info)}章)\n请检查token是否正确')
        else:
            messagebox.showerror('下载失败', error or '未知错误')
            self.lbl_progress.configure(text='下载失败')


if __name__ == '__main__':
    app = App()
    app.mainloop()
