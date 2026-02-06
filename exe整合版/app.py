# -*- coding: UTF-8 -*-
"""
晋江小说下载器 - NiceGUI 界面
基于Web的现代化GUI
"""
import os
import re
import yaml
import asyncio
from functools import partial

from nicegui import ui, app

from models import DownloadConfig
from downloader import NovelDownloader


# ============================================================
# 配置管理
# ============================================================

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


def load_config() -> dict:
    """从config.yml加载配置"""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, encoding='utf-8') as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader) or {}


def save_config(data: dict):
    """保存配置到config.yml"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)


# ============================================================
# 主页面
# ============================================================

def create_page():
    """创建主页面"""
    conf = load_config()

    # 状态
    state = {'downloading': False, 'downloader': None}

    # ---- 页面样式 ----
    ui.add_head_html('''<style>
        .log-area { font-family: monospace; font-size: 13px; white-space: pre-wrap;
                     background: #1e1e1e; color: #d4d4d4; padding: 12px;
                     border-radius: 8px; max-height: 400px; overflow-y: auto; }
    </style>''')

    # ---- 标题 ----
    with ui.column().classes('w-full max-w-3xl mx-auto p-4 gap-4'):
        ui.label('晋江小说下载器').classes('text-3xl font-bold text-center w-full')
        ui.label('基于 Android API').classes('text-sm text-gray-500 text-center w-full')

        # ---- 基本设置卡片 ----
        with ui.card().classes('w-full'):
            ui.label('基本设置').classes('text-lg font-semibold')
            url_input = ui.input('小说网址', placeholder='http://www.jjwxc.net/onebook.php?novelid=xxx').classes('w-full')
            token_input = ui.input('Token', placeholder='从晋江App抓包获取').classes('w-full')
            token_input.value = conf.get('token', '')

            with ui.row().classes('w-full gap-4 items-center'):
                format_select = ui.select(
                    ['txt', 'epub2', 'epub3'],
                    label='输出格式',
                    value=conf.get('format', 'txt')
                ).classes('w-32')

                state_select = ui.select(
                    {'': '不转换', 's': '繁→简', 't': '简→繁'},
                    label='繁简转换',
                    value=conf.get('state', '')
                ).classes('w-32')

                thread_input = ui.number(
                    '线程数', value=conf.get('ThreadPoolMaxNum', 100),
                    min=1, max=999, step=1
                ).classes('w-28')

        # ---- 章节范围卡片 ----
        with ui.card().classes('w-full'):
            ui.label('章节范围').classes('text-lg font-semibold')
            with ui.row().classes('w-full gap-4 items-center'):
                ui.label('从第')
                ch_start_input = ui.number(value=0, min=0, step=1).classes('w-24').props('dense')
                ui.label('章  到第')
                ch_end_input = ui.number(value=0, min=0, step=1).classes('w-24').props('dense')
                ui.label('章').classes('mr-4')
                ui.label('(0表示不限制)').classes('text-xs text-gray-400')
            with ui.row().classes('w-full items-center gap-6'):
                chk_save_per_ch = ui.checkbox('按章保存文件（仅txt）', value=False)
                chk_rm_blank = ui.checkbox('去除段间空行（仅txt）', value=False)

            def _on_format_change():
                is_txt = format_select.value == 'txt'
                if not is_txt:
                    chk_save_per_ch.set_value(False)
                    chk_rm_blank.set_value(False)
                chk_save_per_ch.set_enabled(is_txt)
                chk_rm_blank.set_enabled(is_txt)
            format_select.on_value_change(lambda _: _on_format_change())
            _on_format_change()

        # ---- 标题选项卡片 ----
        with ui.card().classes('w-full'):
            ui.label('标题与内容选项').classes('text-lg font-semibold')

            title_info = conf.get('titleInfo', '1 1 1').split(' ')
            while len(title_info) < 3:
                title_info.append('1')

            with ui.row().classes('gap-4 flex-wrap'):
                chk_number = ui.checkbox('显示序号', value=title_info[0] != '0')
                chk_title = ui.checkbox('显示标题', value=title_info[1] != '0')
                chk_summary = ui.checkbox('显示提要', value=title_info[2] != '0')
                chk_chinfo = ui.checkbox('章节信息', value=bool(conf.get('chinfo', 0)))
                chk_cover = ui.checkbox('下载封面', value=bool(conf.get('cover', '')))
                chk_delthk = ui.checkbox('去除感谢', value=bool(conf.get('delthk', 0)))
                chk_special = ui.checkbox('网页文案', value=bool(conf.get('special', 0)))
                chk_htmlvol = ui.checkbox('HTML卷标', value=bool(conf.get('htmlvol', 0)))

            with ui.row().classes('w-full gap-4'):
                chk_selftitle = ui.checkbox('自定义标题', value=bool(conf.get('selftitle', 0)))
                title_fmt = ui.input('标题格式', placeholder='$1 $2 $3').classes('flex-grow')
                if conf.get('selftitle') and isinstance(conf['selftitle'], str):
                    title_fmt.value = conf['selftitle']

            with ui.row().classes('w-full gap-4'):
                chk_selfvol = ui.checkbox('自定义卷标', value=bool(conf.get('volumn', 0)))
                vol_fmt = ui.input('卷标格式', placeholder='第$1卷 $2').classes('flex-grow')
                if conf.get('volumn') and isinstance(conf['volumn'], str):
                    vol_fmt.value = conf['volumn']

        # ---- CSS编辑卡片 ----
        with ui.card().classes('w-full'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('自定义CSS').classes('text-lg font-semibold')
                ui.button('恢复默认', on_click=lambda: css_editor.set_value(DEFAULT_CSS)).props('flat dense')
            css_editor = ui.textarea(value=conf.get('css', DEFAULT_CSS)).classes('w-full font-mono text-sm').props('rows=6')

        # ---- 进度区域 ----
        with ui.card().classes('w-full'):
            ui.label('下载进度').classes('text-lg font-semibold')
            progress = ui.linear_progress(value=0, show_value=False).classes('w-full')
            progress_label = ui.label('等待开始...').classes('text-sm text-gray-500')
            log_area = ui.log(max_lines=200).classes('w-full h-80')

        # ---- 操作按钮 ----
        with ui.row().classes('w-full gap-4 justify-center'):
            save_btn = ui.button('保存配置', icon='save').props('outline')
            download_btn = ui.button('开始下载', icon='download').props('color=primary')

    # ============================================================
    # 日志和进度
    # ============================================================
    def append_log(msg):
        """追加日志"""
        log_area.push(msg)

    def update_progress(pct, current, total):
        """更新进度"""
        progress.set_value(pct / 100)
        progress_label.set_text(f'{current}/{total} ({pct}%)')

    # ============================================================
    # 保存配置
    # ============================================================
    def on_save_config():
        doc = load_config()
        doc['token'] = token_input.value or ''
        doc['state'] = state_select.value or ''
        doc['format'] = format_select.value or 'txt'
        doc['ThreadPoolMaxNum'] = int(thread_input.value or 100)

        ti = ''
        ti += '1' if chk_number.value else '0'
        ti += ' 1' if chk_title.value else ' 0'
        ti += ' 1' if chk_summary.value else ' 0'
        doc['titleInfo'] = ti

        doc['chinfo'] = 1 if chk_chinfo.value else 0
        doc['cover'] = 'e' if chk_cover.value else ''
        doc['delthk'] = 1 if chk_delthk.value else 0
        doc['special'] = 1 if chk_special.value else 0
        doc['htmlvol'] = 1 if chk_htmlvol.value else 0
        doc['selftitle'] = title_fmt.value if chk_selftitle.value else 0
        doc['volumn'] = vol_fmt.value if chk_selfvol.value else 0
        doc['css'] = css_editor.value or ''

        save_config(doc)
        ui.notify('配置已保存', type='positive')

    save_btn.on_click(on_save_config)

    # ============================================================
    # 下载
    # ============================================================
    async def on_download():
        if state['downloading']:
            ui.notify('正在下载中，请等待...', type='warning')
            return

        url = url_input.value.strip()
        if not re.findall(r'(http|https)://www.jjwxc.net/onebook.php\?novelid=[0-9]+', url):
            ui.notify('网址格式错误！请使用网页版网址', type='negative')
            return

        state['downloading'] = True
        download_btn.props('loading')
        log_area.clear()
        progress.set_value(0)
        progress_label.set_text('准备中...')

        # 构建配置
        config = DownloadConfig()
        config.token = token_input.value or ''
        config.format_type = format_select.value or 'txt'
        config.state = state_select.value or ''
        config.thread_num = int(thread_input.value or 100)
        config.show_number = chk_number.value
        config.show_title = chk_title.value
        config.show_summary = chk_summary.value
        config.show_chinfo = chk_chinfo.value
        config.del_thanks = chk_delthk.value
        config.add_cover = chk_cover.value
        config.html_vol = chk_htmlvol.value
        config.special_intro = chk_special.value
        config.css_text = css_editor.value or ''
        if chk_selftitle.value:
            config.custom_title = title_fmt.value
        if chk_selfvol.value:
            config.custom_vol = vol_fmt.value
        config.chapter_start = int(ch_start_input.value or 0)
        config.chapter_end = int(ch_end_input.value or 0)
        config.save_per_chapter = chk_save_per_ch.value
        config.remove_blank_lines = chk_rm_blank.value

        downloader = NovelDownloader(
            config=config,
            progress_callback=update_progress,
            log_callback=append_log
        )
        state['downloader'] = downloader

        # 在线程池中执行下载
        loop = asyncio.get_event_loop()
        try:
            success, output_file, error = await loop.run_in_executor(
                None, partial(downloader.download_novel, url)
            )
            if success:
                ui.notify(f'下载完成：{output_file}', type='positive')
                progress.set_value(1.0)
                progress_label.set_text('下载完成！')
            else:
                ui.notify(f'下载失败：{error}', type='negative')
                progress_label.set_text(f'失败：{error}')

            if downloader.percent < len(downloader.chapter_data.href_list if downloader.chapter_data else []):
                ui.notify('部分章节下载失败，请检查token', type='warning')
        except Exception as e:
            ui.notify(f'下载出错：{str(e)}', type='negative')
            append_log(f'错误：{str(e)}')
        finally:
            state['downloading'] = False
            download_btn.props(remove='loading')

    download_btn.on_click(on_download)


# ============================================================
# 启动
# ============================================================
@ui.page('/')
def index():
    ui.dark_mode(False)
    create_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title='晋江小说下载器', port=8080, reload=False)
