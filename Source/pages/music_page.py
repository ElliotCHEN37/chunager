import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QFileDialog, QHBoxLayout, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from qfluentwidgets import LargeTitleLabel, PushButton, BodyLabel, LineEdit, TableWidget, PrimaryPushButton, ProgressBar
import configparser
from PIL import Image


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class MusicScanner(QThread):
    scan_done = Signal(dict)
    progress = Signal(int)
    error = Signal(str, str)

    def run(self):
        index_path = self.get_index_path()
        need_rescan = True
        music_data = {}

        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                last_opt_mtime = index_data.get("opt_last_modified", 0)
                music_data = index_data.get("music_data", {})
                current_opt_mtime = self.get_opt_mod_time()

                if current_opt_mtime == last_opt_mtime:
                    need_rescan = False
            except Exception as e:
                self.error.emit("讀取索引檔案錯誤", str(e))

        if need_rescan:
            xml_paths = self.find_xmls()
            music_data = {}

            total = len(xml_paths)
            if total == 0:
                self.progress.emit(100)
                self.scan_done.emit({})
                return

            for idx, path in enumerate(xml_paths):
                data = self.parse_xml(path)
                music_data[data["music_id"]] = data

                progress_percent = int(((idx + 1) / total) * 100)
                self.progress.emit(progress_percent)

            current_opt_mtime = self.get_opt_mod_time()
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "opt_last_modified": current_opt_mtime,
                        "music_data": music_data
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.error.emit("寫入索引檔案錯誤", str(e))

        self.progress.emit(100)
        self.scan_done.emit(music_data)

    def get_cfg_path(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(base, "config.ini")

    def get_index_path(self):
        base_dir = os.path.dirname(self.get_cfg_path())
        return os.path.join(base_dir, "music_index.json")

    def get_opt_mod_time(self):
        cfg_path = self.get_cfg_path()
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        segatools = cfg.get("GENERAL", "segatools_path", fallback=None)
        if not segatools or not os.path.exists(segatools):
            return 0

        st_cfg = configparser.ConfigParser()
        st_cfg.read(segatools)

        opt_rel_path = st_cfg.get("vfs", "option", fallback=None)
        if not opt_rel_path:
            return 0

        if os.path.isabs(opt_rel_path):
            opt_path = opt_rel_path
        else:
            opt_path = os.path.normpath(os.path.join(os.path.dirname(segatools), opt_rel_path))

        max_mtime = 0
        if os.path.isdir(opt_path):
            for root, dirs, files in os.walk(opt_path):
                for name in files:
                    full_path = os.path.join(root, name)
                    try:
                        mtime = os.path.getmtime(full_path)
                        if mtime > max_mtime:
                            max_mtime = mtime
                    except Exception:
                        pass
        return max_mtime

    def find_xmls(self):
        results = []
        cfg_path = self.get_cfg_path()
        cfg = configparser.ConfigParser()
        cfg.read(cfg_path)

        segatools = cfg.get("GENERAL", "segatools_path", fallback=None)
        if not segatools or not os.path.exists(segatools):
            return results

        st_cfg = configparser.ConfigParser()
        st_cfg.read(segatools)

        opt_rel_path = st_cfg.get("vfs", "option", fallback=None)
        if not opt_rel_path:
            return results

        if os.path.isabs(opt_rel_path):
            opt_path = opt_rel_path
        else:
            opt_path = os.path.normpath(os.path.join(os.path.dirname(segatools), opt_rel_path))

        a000_path = os.path.normpath(
            os.path.join(os.path.dirname(segatools), "..", "data", "A000", "music"))
        if os.path.isdir(a000_path):
            results.extend(self.scan_folder(a000_path))

        if os.path.isdir(opt_path):
            for name in os.listdir(opt_path):
                subdir = os.path.join(opt_path, name)
                music_dir = os.path.join(subdir, "music")
                if os.path.isdir(subdir) and name.startswith("A") and os.path.isdir(music_dir):
                    results.extend(self.scan_folder(music_dir))

        return results

    def scan_folder(self, root):
        found = []
        if not os.path.exists(root):
            return found

        for folder in os.listdir(root):
            if re.match(r'^music\d+$', folder):
                music_dir = os.path.join(root, folder)
                xml_path = os.path.join(music_dir, "music.xml")
                if os.path.exists(xml_path):
                    found.append(xml_path)

        return found

    def parse_xml(self, path):
        tree = ET.parse(path)
        root = tree.getroot()

        def get_text(path, default="未知"):
            elem = root.find(path)
            return elem.text if elem is not None else default

        music_id = get_text(".//name/id")
        music_name = get_text(".//name/str")
        artist = get_text(".//artistName/str")
        date_raw = get_text(".//releaseDate", "00000000")
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

        jacket = get_text(".//jaketFile/path")
        jacket_path = os.path.join(os.path.dirname(path), jacket)

        return {
            "jacket_path": jacket_path,
            "music_id": music_id,
            "music_name": music_name,
            "artist_name": artist,
            "genre_names": genres,
            "release_date": date,
            "fumens": charts
        }


class ImageLoader(QThread):
    image_loaded = Signal(int, QPixmap)
    error_loading = Signal(int, str)

    def __init__(self, row, path):
        super().__init__()
        self.row = row
        self.path = path

    def run(self):
        try:
            if not os.path.exists(self.path):
                self.error_loading.emit(self.row, "檔案不存在")
                return

            img = Image.open(self.path)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(qimg)
            self.image_loaded.emit(self.row, pixmap)
        except Exception as e:
            self.error_loading.emit(self.row, str(e))


class FileCopyWorker(QThread):
    copy_completed = Signal(str)
    copy_failed = Signal(str)

    def __init__(self, src_path, dst_path):
        super().__init__()
        self.src_path = src_path
        self.dst_path = dst_path

    def run(self):
        try:
            if not os.path.exists(self.src_path):
                self.copy_failed.emit("來源檔案不存在")
                return

            dst_dir = os.path.dirname(self.dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            shutil.copy(self.src_path, self.dst_path)
            self.copy_completed.emit(f"已複製至: {self.dst_path}")
        except Exception as e:
            self.copy_failed.emit(f"複製失敗: {str(e)}")


class IndexLoader(QThread):
    index_loaded = Signal(dict, str)
    index_error = Signal(str)

    def __init__(self, index_path):
        super().__init__()
        self.index_path = index_path

    def run(self):
        try:
            if not os.path.exists(self.index_path):
                self.index_error.emit("索引檔案不存在")
                return

            with open(self.index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                music_data = index_data.get("music_data", {})

            mtime = os.path.getmtime(self.index_path)
            from datetime import datetime
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            self.index_loaded.emit(music_data, timestamp)
        except Exception as e:
            self.index_error.emit(f"讀取索引失敗: {str(e)}")


class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("musicPage")
        self.scanned = False
        self.music_data_dict = {}
        self.image_loaders = {}
        self.pending_images = []
        self.max_concurrent_images = 5

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.title = LargeTitleLabel("樂曲管理")
        self.layout.addWidget(self.title)

        self.status = BodyLabel("正在搜尋資料...")
        self.status.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status)

        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)

        self.index_status = BodyLabel("索引狀態：尚未建立")
        self.index_status.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.index_status)

        search_layout = QHBoxLayout()
        self.search_box = LineEdit(self)
        self.search_box.setPlaceholderText("搜尋音樂名稱...")
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_music)
        self.search_box.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_box)

        self.search_btn = PrimaryPushButton("搜尋")
        self.search_btn.clicked.connect(self.filter_music)
        search_layout.addWidget(self.search_btn)

        self.reset_btn = PushButton("重置")
        self.reset_btn.clicked.connect(self.reset_filter)
        search_layout.addWidget(self.reset_btn)

        self.layout.addLayout(search_layout)

        btn_layout = QHBoxLayout()

        self.rebuild_btn = PrimaryPushButton("重建索引")
        self.rebuild_btn.clicked.connect(self.rebuild_index)
        btn_layout.addWidget(self.rebuild_btn)

        self.reload_btn = PrimaryPushButton("重新載入")
        self.reload_btn.clicked.connect(self.reload_index)
        btn_layout.addWidget(self.reload_btn)

        self.layout.addLayout(btn_layout)

        self.table = TableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "封面", "音樂ID", "音樂名稱", "藝術家", "類型", "日期", "難度", "提取封面"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        self.scanner = MusicScanner()
        self.scanner.scan_done.connect(self.on_scan_done)
        self.scanner.progress.connect(self.update_progress)
        self.scanner.error.connect(self.on_scanner_error)

    def on_search_text_changed(self):
        self.search_timer.stop()
        self.search_timer.start(300)

    def update_progress(self, value):
        self.progress.setValue(value)

    def showEvent(self, event):
        if not self.scanned:
            self.status.show()
            self.scanner.start()
            self.scanned = True

    def on_scan_done(self, music_data):
        self.music_data_dict = music_data
        self.update_table(list(music_data.values()))
        self.status.hide()
        self.progress.hide()
        self.update_index_status()

    def on_scanner_error(self, title, message):
        QMessageBox.critical(self, title, message)
        self.status.setText("掃描失敗")

    def update_index_status(self):
        index_path = self.scanner.get_index_path()
        if os.path.exists(index_path):
            mtime = os.path.getmtime(index_path)
            from datetime import datetime
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            self.index_status.setText(f"索引狀態：最後更新於 {timestamp}")
        else:
            self.index_status.setText("索引狀態：尚未建立")

    def reset_filter(self):
        self.search_box.clear()
        self.filter_music(True)

    def filter_music(self, reset=False):
        if reset:
            data = list(self.music_data_dict.values())
        else:
            query = self.search_box.text().strip().lower()
            if not query:
                data = list(self.music_data_dict.values())
            else:
                data = [
                    d for _, d in self.music_data_dict.items()
                    if (query in d["music_id"].lower() or
                        query in d["music_name"].lower() or
                        query in d["artist_name"].lower())
                ]

        self.update_table(data)

    def update_table(self, data):
        self.stop_all_image_loading()

        self.table.clearContents()
        self.table.setRowCount(len(data))

        for row, item in enumerate(data):
            self.table.setItem(row, 1, QTableWidgetItem(item["music_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(item["music_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(item["artist_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(item["genre_names"])))
            self.table.setItem(row, 5, QTableWidgetItem(item["release_date"]))

            diff_text = ", ".join([f"{d['type']}: {d['level']}" for d in item["fumens"]])
            self.table.setItem(row, 6, QTableWidgetItem(diff_text))

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)

            loading_label = BodyLabel("載入中...")
            loading_label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, loading_label)

            self.pending_images.append((row, item["jacket_path"]))

            copy_btn = PushButton("提取")
            copy_btn.clicked.connect(lambda _, d=item: self.save_cover(d))
            self.table.setCellWidget(row, 7, copy_btn)

        self.start_image_loading()

    def stop_all_image_loading(self):
        for loader in self.image_loaders.values():
            if loader.isRunning():
                loader.terminate()
                loader.wait()
        self.image_loaders.clear()
        self.pending_images.clear()

    def start_image_loading(self):
        while len(self.image_loaders) < self.max_concurrent_images and self.pending_images:
            row, path = self.pending_images.pop(0)
            self.load_image_async(row, path)

    def load_image_async(self, row, path):
        loader = ImageLoader(row, path)
        loader.image_loaded.connect(self.on_image_loaded)
        loader.error_loading.connect(self.on_image_error)
        loader.finished.connect(lambda: self.on_image_loader_finished(row))

        self.image_loaders[row] = loader
        loader.start()

    def on_image_loaded(self, row, pixmap):
        if row < self.table.rowCount():
            label = BodyLabel()
            label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, label)

    def on_image_error(self, row, error_msg):
        if row < self.table.rowCount():
            label = BodyLabel("無法載入")
            label.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 0, label)

    def on_image_loader_finished(self, row):
        if row in self.image_loaders:
            del self.image_loaders[row]

        if self.pending_images:
            next_row, next_path = self.pending_images.pop(0)
            self.load_image_async(next_row, next_path)

    def save_cover(self, data):
        target = QFileDialog.getExistingDirectory(self, "選擇目標資料夾", "")
        if not target:
            return

        src = data["jacket_path"]
        dst = os.path.join(target, os.path.basename(src))

        self.copy_worker = FileCopyWorker(src, dst)
        self.copy_worker.copy_completed.connect(self.on_copy_completed)
        self.copy_worker.copy_failed.connect(self.on_copy_failed)
        self.copy_worker.start()

    def on_copy_completed(self, message):
        QMessageBox.information(self, "成功", message)

    def on_copy_failed(self, error_msg):
        QMessageBox.critical(self, "複製失敗", error_msg)

    def rebuild_index(self):
        self.rebuild_btn.setEnabled(False)
        self.reload_btn.setEnabled(False)

        index_path = self.scanner.get_index_path()
        if os.path.exists(index_path):
            try:
                os.remove(index_path)
            except Exception as e:
                QMessageBox.critical(self, "刪除索引失敗", f"無法刪除索引檔案:\n{str(e)}")
                self.rebuild_btn.setEnabled(True)
                self.reload_btn.setEnabled(True)
                return

        self.progress.setValue(0)
        self.progress.show()
        self.status.setText("正在重新建立索引...")
        self.status.show()
        self.index_status.setText("索引狀態：重新建立中...")

        self.stop_all_image_loading()

        if not self.scanner.scan_done.connect(self.on_rebuild_done):
            self.scanner.scan_done.disconnect()
            self.scanner.scan_done.connect(self.on_rebuild_done)

        self.scanner.start()

    def on_rebuild_done(self, music_data):
        self.music_data_dict = music_data
        self.update_table(list(music_data.values()))
        self.status.hide()
        self.progress.hide()
        self.update_index_status()

        self.rebuild_btn.setEnabled(True)
        self.reload_btn.setEnabled(True)

        self.scanner.scan_done.disconnect()
        self.scanner.scan_done.connect(self.on_scan_done)

    def reload_index(self):
        self.reload_btn.setEnabled(False)

        index_path = self.scanner.get_index_path()
        if not os.path.exists(index_path):
            QMessageBox.warning(self, "索引不存在", "尚未建立索引，請先使用「重建索引」。")
            self.reload_btn.setEnabled(True)
            return

        self.index_loader = IndexLoader(index_path)
        self.index_loader.index_loaded.connect(self.on_index_loaded)
        self.index_loader.index_error.connect(self.on_index_load_error)
        self.index_loader.start()

    def on_index_loaded(self, music_data, timestamp):
        self.music_data_dict = music_data
        self.update_table(list(music_data.values()))
        self.index_status.setText(f"索引狀態：最後更新於 {timestamp}")
        self.reload_btn.setEnabled(True)
        QMessageBox.information(self, "完成", "已成功重新載入索引。")

    def on_index_load_error(self, error_msg):
        QMessageBox.critical(self, "載入失敗", error_msg)
        self.reload_btn.setEnabled(True)

    def closeEvent(self, event):
        self.stop_all_image_loading()
        if hasattr(self, 'copy_worker') and self.copy_worker.isRunning():
            self.copy_worker.terminate()
            self.copy_worker.wait()
        if hasattr(self, 'index_loader') and self.index_loader.isRunning():
            self.index_loader.terminate()
            self.index_loader.wait()
        if self.scanner.isRunning():
            self.scanner.terminate()
            self.scanner.wait()
        event.accept()