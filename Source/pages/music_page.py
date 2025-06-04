import configparser
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime

from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QFileDialog, QHBoxLayout, QMessageBox
from qfluentwidgets import LargeTitleLabel, PushButton, BodyLabel, LineEdit, TableWidget, PrimaryPushButton, ProgressBar


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class ImageLoaderThread(QThread):
    image_loaded = Signal(int, QPixmap)

    def __init__(self, row, img_path):
        super().__init__()
        self.row = row
        self.img_path = img_path

    def run(self):
        if not self.img_path or not os.path.exists(self.img_path):
            return
        try:
            img = Image.open(self.img_path).convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            self.image_loaded.emit(self.row, QPixmap.fromImage(qimg))
        except Exception:
            pass


class FileOperationThread(QThread):
    operation_completed = Signal(bool, str)

    def __init__(self, operation_type, **kwargs):
        super().__init__()
        self.operation_type = operation_type
        self.kwargs = kwargs

    def run(self):
        try:
            if self.operation_type == "extract_image":
                self._extract_image()
            elif self.operation_type == "rebuild_index":
                self._rebuild_index()
            elif self.operation_type == "reload_index":
                self._reload_index()
        except Exception as e:
            self.operation_completed.emit(False, str(e))

    def _extract_image(self):
        img_path = self.kwargs['img_path']
        target_dir = self.kwargs['target_dir']
        if not os.path.exists(img_path):
            self.operation_completed.emit(False, self.tr(f"封面不存在: {img_path}"))
            return
        target = os.path.join(target_dir, os.path.basename(img_path))
        shutil.copy(img_path, target)
        self.operation_completed.emit(True, self.tr(f"已複製: {target}"))

    def _rebuild_index(self):
        index_path = self.kwargs['index_path']
        if os.path.exists(index_path):
            os.remove(index_path)
        self.operation_completed.emit(True, self.tr("已刪除索引, 準備重建"))

    def _reload_index(self):
        index_path = self.kwargs['index_path']
        if not os.path.exists(index_path):
            self.operation_completed.emit(False, self.tr("索引不存在, 請先建立"))
            return
        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        music_data = index_data.get("music_data", {})
        timestamp = datetime.fromtimestamp(os.path.getmtime(index_path)).strftime('%Y-%m-%d %H:%M:%S')
        self.operation_completed.emit(True, f"reload_success|{json.dumps(music_data)}|{timestamp}")


class MusicSearchThread(QThread):
    found = Signal(dict)
    progress = Signal(int)
    error = Signal(str, str)
    status_update = Signal(str)

    def run(self):
        try:
            self.status_update.emit(self.tr("檢查索引"))
            index_path = self.get_index_path()
            need_rescan = True
            music_data = {}
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                    last_opt_mtime = index_data.get("opt_last_modified", 0)
                    music_data = index_data.get("music_data", {})
                    current_opt_mtime = self.get_opt_last_modified_time()
                    if current_opt_mtime == last_opt_mtime:
                        need_rescan = False
                        self.status_update.emit(self.tr("使用現存索引"))
                except Exception as e:
                    self.error.emit(self.tr("索引讀取失敗"), str(e))
                    return
            if need_rescan:
                self.status_update.emit(self.tr("掃描XML檔案中"))
                xml_paths = self.find_xmls()
                music_data = {}
                total = len(xml_paths)
                if total == 0:
                    self.status_update.emit(self.tr("未找到XML檔案"))
                    self.found.emit({})
                    return
                for idx, xml_path in enumerate(xml_paths):
                    try:
                        data = self.parse_xml(xml_path)
                        music_data[data["music_id"]] = data
                        progress_val = int(((idx + 1) / total) * 100)
                        self.progress.emit(progress_val)
                        self.status_update.emit(self.tr(f"處理中: {data['music_name']} ({idx + 1}/{total})"))
                    except Exception as e:
                        print(self.tr(f"XML處理失敗: {xml_path}, error: {e}"))
                        continue
                self.status_update.emit(self.tr("儲存索引"))
                current_opt_mtime = self.get_opt_last_modified_time()
                try:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "opt_last_modified": current_opt_mtime,
                            "music_data": music_data
                        }, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.error.emit(self.tr("寫入索引失敗"), str(e))
                    return
            self.status_update.emit(self.tr("已完成"))
            self.found.emit(music_data)
        except Exception as e:
            self.error.emit(self.tr("搜尋失敗"), str(e))

    def get_cfg_path(self):
        base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
            os.path.dirname(sys.argv[0]))
        return os.path.join(base, "config.ini")

    def get_index_path(self):
        base_dir = os.path.dirname(self.get_cfg_path())
        return os.path.join(base_dir, "music_index.json")

    def get_opt_last_modified_time(self):
        cfg_path = self.get_cfg_path()
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        sega_path = cfg.get("GENERAL", "segatools_path", fallback=None)
        if not sega_path or not os.path.exists(sega_path):
            return 0
        sega_cfg = configparser.ConfigParser()
        sega_cfg.read(sega_path)
        opt_rel_path = sega_cfg.get("vfs", "option", fallback=None)
        if not opt_rel_path:
            return 0
        if os.path.isabs(opt_rel_path):
            opt_path = opt_rel_path
        else:
            opt_path = os.path.normpath(os.path.join(os.path.dirname(sega_path), opt_rel_path))
        max_mtime = 0
        if os.path.isdir(opt_path):
            for root, dirs, files in os.walk(opt_path):
                for name in files:
                    try:
                        full_path = os.path.join(root, name)
                        mtime = os.path.getmtime(full_path)
                        if mtime > max_mtime:
                            max_mtime = mtime
                    except Exception:
                        pass
        return max_mtime

    def find_xmls(self):
        result = []
        cfg_path = self.get_cfg_path()
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)
        sega_path = cfg.get("GENERAL", "segatools_path", fallback=None)
        if not sega_path or not os.path.exists(sega_path):
            return result
        sega_cfg = configparser.ConfigParser()
        sega_cfg.read(sega_path)
        opt_rel_path = sega_cfg.get("vfs", "option", fallback=None)
        if not opt_rel_path:
            return result
        opt_path = opt_rel_path if os.path.isabs(opt_rel_path) else os.path.normpath(
            os.path.join(os.path.dirname(sega_path), opt_rel_path))
        a000_path = os.path.normpath(os.path.join(os.path.dirname(sega_path), "..", "data", "A000", "music"))
        if os.path.isdir(a000_path):
            result.extend(self.scan_music_folder(a000_path))
        if os.path.isdir(opt_path):
            for name in os.listdir(opt_path):
                subfolder = os.path.join(opt_path, name)
                music_folder = os.path.join(subfolder, "music")
                if os.path.isdir(subfolder) and name.startswith("A") and os.path.isdir(music_folder):
                    result.extend(self.scan_music_folder(music_folder))
        return result

    def scan_music_folder(self, root_path):
        found = []
        if not os.path.exists(root_path):
            return found
        for folder in os.listdir(root_path):
            if re.match(r'^music\d+$', folder):
                music_path = os.path.join(root_path, folder)
                xml_path = os.path.join(music_path, "music.xml")
                if os.path.exists(xml_path):
                    found.append(xml_path)
        return found

    def xml_text(self, root, path, default="未知"):
        elem = root.find(path)
        return elem.text if elem is not None else default

    def parse_xml(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        music_id = self.xml_text(root, ".//name/id")
        music_name = self.xml_text(root, ".//name/str")
        artist = self.xml_text(root, ".//artistName/str")
        date_raw = self.xml_text(root, ".//releaseDate", "00000000")
        date = f"{date_raw[:4]}.{date_raw[4:6]}.{date_raw[6:8]}"
        genres = []
        for genre in root.findall(".//genreNames/list/StringID"):
            genre_str = genre.find("str")
            if genre_str is not None and genre_str.text:
                genres.append(genre_str.text)
        charts = []
        for chart in root.findall(".//fumens/MusicFumenData"):
            enable = chart.find("enable")
            if enable is not None and enable.text.lower() == "true":
                type_str = chart.findtext("./type/str", "未知")
                level = chart.findtext("./level", "未知")
                charts.append({
                    "type": type_str,
                    "level": level
                })
        jacket = self.xml_text(root, ".//jaketFile/path")
        jacket_path = os.path.join(os.path.dirname(xml_path), jacket)
        return {
            "jacket_path": jacket_path,
            "music_id": music_id,
            "music_name": music_name,
            "artist_name": artist,
            "genre_names": genres,
            "release_date": date,
            "fumens": charts
        }


class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("musicPage")
        self.has_searched = False
        self.music_data = {}
        self.image_loaders = {}
        self.current_file_operation = None
        self.init_ui()
        self.setup_search_thread()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.titleLabel = LargeTitleLabel(self.tr("樂曲管理"))
        self.layout.addWidget(self.titleLabel)
        self.searchMsg = BodyLabel(self.tr("正在搜尋資料..."))
        self.searchMsg.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.searchMsg)
        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)
        self.index_status = BodyLabel(self.tr("索引狀態：尚未建立"))
        self.index_status.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.index_status)
        search_layout = QHBoxLayout()
        self.searchBox = LineEdit(self)
        self.searchBox.setPlaceholderText(self.tr("搜尋音樂名稱..."))
        search_layout.addWidget(self.searchBox)
        self.searchBtn = PrimaryPushButton(self.tr("搜尋"))
        self.searchBtn.clicked.connect(self.filter_data)
        search_layout.addWidget(self.searchBtn)
        self.resetBtn = PushButton(self.tr("重置"))
        self.resetBtn.clicked.connect(self.reset_filter)
        search_layout.addWidget(self.resetBtn)
        self.layout.addLayout(search_layout)
        btn_layout = QHBoxLayout()
        self.rebuild_btn = PrimaryPushButton(self.tr("重建索引"))
        self.rebuild_btn.clicked.connect(self.rebuild_index)
        btn_layout.addWidget(self.rebuild_btn)
        self.reload_btn = PrimaryPushButton(self.tr("重新載入"))
        self.reload_btn.clicked.connect(self.reload_index)
        btn_layout.addWidget(self.reload_btn)
        self.layout.addLayout(btn_layout)
        self.table = TableWidget(self)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([self.tr("封面"), self.tr("ID"), self.tr("名稱"),
                                              self.tr("曲師"), self.tr("分類"), self.tr("日期"),
                                              self.tr("可用難度"), self.tr("提取封面"), self.tr("譜面資料夾"), self.tr("樂曲資料夾")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

    def setup_search_thread(self):
        self.search_thread = MusicSearchThread()
        self.search_thread.found.connect(self.on_search_done)
        self.search_thread.progress.connect(self.update_progress)
        self.search_thread.error.connect(self.on_search_error)
        self.search_thread.status_update.connect(self.update_status_message)

    def update_progress(self, value):
        self.progress.setValue(value)

    def update_status_message(self, message):
        self.searchMsg.setText(message)

    def on_search_error(self, title, message):
        QMessageBox.critical(self, title, message)
        self.searchMsg.hide()
        self.progress.hide()

    def showEvent(self, event):
        if not self.has_searched:
            self.searchMsg.show()
            self.progress.show()
            self.progress.setValue(0)
            QTimer.singleShot(100, self.start_search)
            self.has_searched = True

    def start_search(self):
        if not self.search_thread.isRunning():
            self.search_thread.start()

    def on_search_done(self, music_data):
        self.music_data = music_data
        self.update_table(list(music_data.values()))
        self.searchMsg.hide()
        self.progress.hide()
        index_path = self.search_thread.get_index_path()
        if os.path.exists(index_path):
            mtime = os.path.getmtime(index_path)
            from datetime import datetime
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            self.index_status.setText(self.tr(f"索引狀態：最後更新於 {timestamp}"))
        else:
            self.index_status.setText(self.tr("索引狀態：尚未建立"))

    def reset_filter(self):
        self.searchBox.clear()
        self.filter_data(reset=True)

    def filter_data(self, reset=False):
        if reset:
            filtered = list(self.music_data.values())
        else:
            query = self.searchBox.text().strip().lower()

            def safe_match(val):
                return str(val).lower() if val else ""

            filtered = [
                data for data in self.music_data.values()
                if any(query in safe_match(data[key]) for key in ["music_id", "music_name", "artist_name"])
            ]
        self.update_table(filtered)

    def update_table(self, data_list):
        for loader in self.image_loaders.values():
            if loader.isRunning():
                loader.terminate()
        self.image_loaders.clear()
        self.table.clearContents()
        self.table.setRowCount(len(data_list))
        for row, data in enumerate(data_list):
            self.table.setItem(row, 1, QTableWidgetItem(data["music_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["music_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["artist_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(data["genre_names"])))
            self.table.setItem(row, 5, QTableWidgetItem(data["release_date"]))
            diff_text = ", ".join([f"{d['type']}: {d['level']}" for d in data["fumens"]])
            self.table.setItem(row, 6, QTableWidgetItem(diff_text))
            img_label = BodyLabel(self.tr("載入中..."))
            img_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, img_label)
            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)
            self.load_image_async(row, data["jacket_path"])
            copy_btn = PushButton(self.tr("提取"))
            copy_btn.clicked.connect(lambda _, d=data: self.extract_image(d))
            self.table.setCellWidget(row, 7, copy_btn)
            humen_btn = PushButton(self.tr("開啟"))
            humen_btn.clicked.connect(lambda _, d=data: self.open_humen(d))
            self.table.setCellWidget(row, 8, humen_btn)
            open_btn = PushButton(self.tr("開啟"))
            open_btn.clicked.connect(lambda _, d=data: self.open_cuefile(d))
            self.table.setCellWidget(row, 9, open_btn)

    def load_image_async(self, row, img_path):
        loader = ImageLoaderThread(row, img_path)
        loader.image_loaded.connect(self.on_image_loaded)
        loader.finished.connect(lambda: self.cleanup_image_loader(row))
        self.image_loaders[row] = loader
        QTimer.singleShot(row * 50, loader.start)

    def on_image_loaded(self, row, pixmap):
        if row < self.table.rowCount():
            label = BodyLabel()
            label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, label)

    def cleanup_image_loader(self, row):
        if row in self.image_loaders:
            del self.image_loaders[row]

    def extract_image(self, data):
        target_dir = QFileDialog.getExistingDirectory(self, self.tr("選擇目標資料夾"), "")
        if not target_dir:
            return
        if self.current_file_operation and self.current_file_operation.isRunning():
            QMessageBox.information(self, self.tr("提示"), self.tr("請等待當前操作完成"))
            return
        self.current_file_operation = FileOperationThread(
            "extract_image",
            img_path=data["jacket_path"],
            target_dir=target_dir
        )
        self.current_file_operation.operation_completed.connect(self.on_file_operation_completed)
        self.current_file_operation.start()

    def rebuild_index(self):
        if self.search_thread.isRunning():
            QMessageBox.information(self, self.tr("提示"), self.tr("正在搜索中，請稍候"))
            return
        if self.current_file_operation and self.current_file_operation.isRunning():
            QMessageBox.information(self, self.tr("提示"), self.tr("請等待當前操作完成"))
            return
        index_path = self.search_thread.get_index_path()
        self.current_file_operation = FileOperationThread(
            "rebuild_index",
            index_path=index_path
        )
        self.current_file_operation.operation_completed.connect(self.on_rebuild_completed)
        self.current_file_operation.start()

    def on_rebuild_completed(self, success, message):
        if success:
            self.progress.setValue(0)
            self.progress.show()
            self.searchMsg.setText(self.tr("正在重新建立索引..."))
            self.searchMsg.show()
            self.index_status.setText(self.tr("索引狀態：重新建立中..."))
            self.has_searched = False
            QTimer.singleShot(100, self.start_search)
        else:
            QMessageBox.critical(self, self.tr("刪除索引失敗"), message)

    def reload_index(self):
        if self.search_thread.isRunning():
            QMessageBox.information(self, self.tr("提示"), self.tr("正在搜索中，請稍候"))
            return
        if self.current_file_operation and self.current_file_operation.isRunning():
            QMessageBox.information(self, self.tr("提示"), self.tr("請等待當前操作完成"))
            return
        index_path = self.search_thread.get_index_path()
        self.current_file_operation = FileOperationThread(
            "reload_index",
            index_path=index_path
        )
        self.current_file_operation.operation_completed.connect(self.on_reload_completed)
        self.current_file_operation.start()

    def on_reload_completed(self, success, message):
        if success:
            if message.startswith("reload_success"):
                parts = message.split("|")
                music_data_str = parts[1]
                timestamp = parts[2]
                music_data = json.loads(music_data_str)
                self.music_data = music_data
                self.update_table(list(music_data.values()))
                self.index_status.setText(self.tr(f"索引狀態：最後更新於 {timestamp}"))
                QMessageBox.information(self, self.tr("完成"), self.tr("已成功重新載入索引。"))
        else:
            QMessageBox.critical(self, self.tr("載入失敗"), message)

    def on_file_operation_completed(self, success, message):
        if success:
            QMessageBox.information(self, self.tr("成功"), message)
        else:
            QMessageBox.critical(self, self.tr("操作失敗"), message)

    def closeEvent(self, event):
        if self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()
        for loader in self.image_loaders.values():
            if loader.isRunning():
                loader.terminate()
        if self.current_file_operation and self.current_file_operation.isRunning():
            self.current_file_operation.terminate()
            self.current_file_operation.wait()
        event.accept()

    def open_humen(self, data):
        folder = os.path.dirname(data["jacket_path"])
        if not os.path.exists(folder):
            QMessageBox.warning(self, self.tr("錯誤"), self.tr("找不到資料夾"))
            return
        try:
            os.startfile(folder)
        except Exception as e:
            QMessageBox.critical(self, self.tr("錯誤"), str(e))

    def open_cuefile(self, data):
        music_id = data.get("music_id", "")
        if not music_id.isdigit():
            QMessageBox.warning(self, self.tr("錯誤"), self.tr("無效的樂曲 ID"))
            return

        jacket_path = data.get("jacket_path", "")
        if not os.path.exists(jacket_path):
            QMessageBox.warning(self, self.tr("錯誤"), self.tr("封面路徑不存在"))
            return

        valid_id = music_id.zfill(6)

        base_dir = os.path.abspath(os.path.join(jacket_path, "..", "..", "..", "cueFile"))
        cue_dir = os.path.join(base_dir, f"cueFile{valid_id}")

        if os.path.exists(cue_dir):
            os.startfile(cue_dir)
        else:
            QMessageBox.warning(self, self.tr("錯誤"), self.tr(f"找不到 cueFile 資料夾：{cue_dir}"))
