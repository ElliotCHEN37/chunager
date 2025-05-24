import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QFileDialog, QHBoxLayout, QMessageBox
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal
from qfluentwidgets import LargeTitleLabel, PushButton, BodyLabel, LineEdit, TableWidget, PrimaryPushButton, ProgressBar
import configparser
from PIL import Image


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class MusicScanner(QThread):
    scan_done = Signal(dict)
    progress = Signal(int)

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
                QMessageBox.critical(self, "讀取索引檔案錯誤", e)

        if need_rescan:
            xml_paths = self.find_xmls()
            music_data = {}

            total = len(xml_paths)
            for idx, path in enumerate(xml_paths):
                data = self.parse_xml(path)
                music_data[data["music_id"]] = data
                prog = int(((idx + 1) / total) * 100)
                self.progress.emit(prog)

            current_opt_mtime = self.get_opt_mod_time()
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "opt_last_modified": current_opt_mtime,
                        "music_data": music_data
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "寫入索引檔案錯誤", e)

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

class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("musicPage")
        self.scanned = False
        self.music_data_dict = {}

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
            data = [
                d for _, d in self.music_data_dict.items()
                if (query in d["music_id"].lower() or
                    query in d["music_name"].lower() or
                    query in d["artist_name"].lower())
            ]

        self.update_table(data)

    def update_table(self, data):
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

            img = self.load_dds(item["jacket_path"])
            if img:
                label = BodyLabel()
                label.setPixmap(img.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.table.setCellWidget(row, 0, label)
            else:
                label = BodyLabel("無法加載封面")
                self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(row, 128)

            copy_btn = PushButton("提取")
            copy_btn.clicked.connect(lambda _, d=item: self.save_cover(d))
            self.table.setCellWidget(row, 7, copy_btn)

    def load_dds(self, path):
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)
        except Exception as e:
            QMessageBox.critical(self, "讀取DDS封面失敗", f"路徑: {path}, 錯誤: {e}")
            return None

    def save_cover(self, data):
        target = QFileDialog.getExistingDirectory(self, "選擇目標資料夾", "")
        if not target:
            QMessageBox.critical(self, "錯誤", "未選擇任何資料夾")
            return

        if not os.path.exists(target):
            os.makedirs(target)

        src = data["jacket_path"]
        if os.path.exists(src):
            try:
                dst = os.path.join(target, os.path.basename(src))
                shutil.copy(src, dst)
                QMessageBox.information(self, "成功", f"已複製至: {dst}")
            except Exception as e:
                QMessageBox.critical(self, "複製封面失敗", e)
        else:
            QMessageBox.warning(self, "封面檔案不存在", src)

    def rebuild_index(self):
        index_path = self.scanner.get_index_path()
        if os.path.exists(index_path):
            try:
                os.remove(index_path)
            except Exception as e:
                QMessageBox.critical(self, "刪除索引失敗", f"無法刪除索引檔案:\n{str(e)}")
                return

        self.progress.setValue(0)
        self.progress.show()
        self.status.setText("正在重新建立索引...")
        self.status.show()
        self.index_status.setText("索引狀態：重新建立中...")
        self.scanned = False
        self.scanner.start()

    def reload_index(self):
        index_path = self.scanner.get_index_path()
        if not os.path.exists(index_path):
            QMessageBox.warning(self, "索引不存在", "尚未建立索引，請先使用「重建索引」。")
            return

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                music_data = index_data.get("music_data", {})
                self.music_data_dict = music_data
                self.update_table(list(music_data.values()))

                mtime = os.path.getmtime(index_path)
                from datetime import datetime
                timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                self.index_status.setText(f"索引狀態：最後更新於 {timestamp}")

                QMessageBox.information(self, "完成", "已成功重新載入索引。")

        except Exception as e:
            QMessageBox.critical(self, "讀取索引失敗", str(e))
