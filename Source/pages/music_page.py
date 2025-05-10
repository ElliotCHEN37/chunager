import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QFileDialog, QHBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal
from qfluentwidgets import LargeTitleLabel, PushButton, BodyLabel, LineEdit, TableWidget, PrimaryPushButton, ProgressBar
import configparser
from PIL import Image

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class MusicSearchThread(QThread):
    search_completed = Signal(dict)
    progress_update = Signal(int)

    def run(self):
        music_xml_paths = self.find_all_music_xmls()
        music_data = {}

        total_files = len(music_xml_paths)
        for index, xml_path in enumerate(music_xml_paths):
            data = self.parse_music_xml(xml_path)
            music_data[data["music_id"]] = data
            progress = int(((index + 1) / total_files) * 100)
            self.progress_update.emit(progress)

        self.search_completed.emit(music_data)

    def get_config_path(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(base_path, "config.ini")

    def find_all_music_xmls(self):
        result = []
        config_path = self.get_config_path()
        config = configparser.ConfigParser()
        config.read(config_path)

        segatools_path = config.get("GENERAL", "segatools_path", fallback=None)
        if not segatools_path or not os.path.exists(segatools_path):
            return result

        segatools_config = configparser.ConfigParser()
        segatools_config.read(segatools_path)

        option_relative_path = segatools_config.get("vfs", "option", fallback=None)
        if not option_relative_path:
            return result

        if os.path.isabs(option_relative_path):
            option_path = option_relative_path
        else:
            option_path = os.path.normpath(os.path.join(os.path.dirname(segatools_path), option_relative_path))

        data_a000_music_path = os.path.normpath(
            os.path.join(os.path.dirname(segatools_path), "..", "data", "A000", "music"))
        if os.path.isdir(data_a000_music_path):
            result.extend(self.find_music_xml_in_music_folder(data_a000_music_path))

        if os.path.isdir(option_path):
            for name in os.listdir(option_path):
                subfolder_path = os.path.join(option_path, name)
                music_folder_path = os.path.join(subfolder_path, "music")
                if os.path.isdir(subfolder_path) and name.startswith("A") and os.path.isdir(music_folder_path):
                    result.extend(self.find_music_xml_in_music_folder(music_folder_path))

        return result

    def find_music_xml_in_music_folder(self, music_folder_root):
        found = []
        if not os.path.exists(music_folder_root):
            return found

        for folder in os.listdir(music_folder_root):
            if re.match(r'^music\d+$', folder):
                music_folder_path = os.path.join(music_folder_root, folder)
                music_xml_path = os.path.join(music_folder_path, "music.xml")
                if os.path.exists(music_xml_path):
                    found.append(music_xml_path)

        return found

    def parse_music_xml(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        def safe_find_text(path, default="未知"):
            element = root.find(path)
            return element.text if element is not None else default

        music_id = safe_find_text(".//name/id")
        music_name = safe_find_text(".//name/str")
        artist_name = safe_find_text(".//artistName/str")
        release_date_raw = safe_find_text(".//releaseDate", "00000000")
        release_date = f"{release_date_raw[:4]}.{release_date_raw[4:6]}.{release_date_raw[6:8]}"

        genre_names = []
        for genre in root.findall(".//genreNames/list/StringID"):
            genre_str = genre.find("str")
            if genre_str is not None and genre_str.text:
                genre_names.append(genre_str.text)

        fumens = []
        for fumen in root.findall(".//fumens/MusicFumenData"):
            enable = fumen.find("enable")
            if enable is not None and enable.text.lower() == "true":
                fumen_type = fumen.findtext("./type/str", "未知")
                level = fumen.findtext("./level", "未知")
                fumens.append({
                    "type": fumen_type,
                    "level": level
                })

        jacket_filename = f"CHU_UI_Jacket_{int(music_id):04d}.dds"
        jacket_abs_path = os.path.join(os.path.dirname(xml_path), jacket_filename)

        return {
            "jacket_path": jacket_abs_path,
            "music_id": music_id,
            "music_name": music_name,
            "artist_name": artist_name,
            "genre_names": genre_names,
            "release_date": release_date,
            "fumens": fumens
        }

class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("musicPage")
        self.has_searched = False

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.titleLabel = LargeTitleLabel("樂曲管理")
        self.layout.addWidget(self.titleLabel)

        self.searchingLabel = BodyLabel("正在搜尋資料...")
        self.searchingLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.searchingLabel)

        self.progressBar = ProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.layout.addWidget(self.progressBar)

        search_layout = QHBoxLayout()
        self.searchBox = LineEdit(self)
        self.searchBox.setPlaceholderText("搜尋音樂名稱...")
        search_layout.addWidget(self.searchBox)

        self.searchButton = PrimaryPushButton("搜尋")
        self.searchButton.clicked.connect(self.filter_music_data)
        search_layout.addWidget(self.searchButton)

        self.resetButton = PushButton("重置")
        self.resetButton.clicked.connect(self.reset_search_filter)
        search_layout.addWidget(self.resetButton)

        self.layout.addLayout(search_layout)

        self.table = TableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "封面", "音樂ID", "音樂名稱", "藝術家", "類型", "發行日期", "難度", "提取封面"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        self.music_search_thread = MusicSearchThread()
        self.music_search_thread.search_completed.connect(self.on_search_completed)
        self.music_search_thread.progress_update.connect(self.update_progress)

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def showEvent(self, event):
        if not self.has_searched:
            self.searchingLabel.show()
            self.music_search_thread.start()
            self.has_searched = True

    def on_search_completed(self, music_data):
        self.music_data_dict = music_data
        self.table.setRowCount(len(music_data))

        for row, data in enumerate(music_data.values()):
            self.table.setItem(row, 1, QTableWidgetItem(data["music_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["music_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["artist_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(data["genre_names"])))
            self.table.setItem(row, 5, QTableWidgetItem(data["release_date"]))

            difficulty_text = ", ".join([f"{d['type']}: {d['level']}" for d in data["fumens"]])
            self.table.setItem(row, 6, QTableWidgetItem(difficulty_text))

            pixmap = self.load_dds_image(data["jacket_path"])
            if pixmap is not None:
                label = BodyLabel()
                label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.table.setCellWidget(row, 0, label)
            else:
                label = BodyLabel("無法加載封面")
                self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(row, 128)

            copy_button = PushButton("提取")
            copy_button.clicked.connect(lambda _, d=data: self.copy_cover_image(d))
            self.table.setCellWidget(row, 7, copy_button)

        self.searchingLabel.hide()
        self.progressBar.hide()

    def reset_search_filter(self):
        self.searchBox.clear()
        self.filter_music_data(reset=True)

    def filter_music_data(self, reset=False):
        if reset:
            filtered_data = list(self.music_data_dict.values())
        else:
            search_text = self.searchBox.text().strip().lower()
            filtered_data = [
                data for music_id, data in self.music_data_dict.items()
                if (search_text in data["music_id"].lower() or
                    search_text in data["music_name"].lower() or
                    search_text in data["artist_name"].lower())
            ]

        self.table.clearContents()
        self.table.setRowCount(len(filtered_data))

        for row, data in enumerate(filtered_data):
            self.table.setItem(row, 1, QTableWidgetItem(data["music_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["music_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["artist_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(", ".join(data["genre_names"])))
            self.table.setItem(row, 5, QTableWidgetItem(data["release_date"]))

            difficulty_text = ", ".join([f"{d['type']}: {d['level']}" for d in data["fumens"]])
            self.table.setItem(row, 6, QTableWidgetItem(difficulty_text))

            pixmap = self.load_dds_image(data["jacket_path"])
            if pixmap is not None:
                label = BodyLabel()
                label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.table.setCellWidget(row, 0, label)
            else:
                label = BodyLabel("無法加載封面")
                self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(row, 128)

            copy_button = PushButton("提取")
            copy_button.clicked.connect(lambda _, d=data: self.copy_cover_image(d))
            self.table.setCellWidget(row, 7, copy_button)

    def load_dds_image(self, dds_path):
        if not os.path.exists(dds_path):
            return None
        try:
            img = Image.open(dds_path)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimage)
        except Exception as e:
            print(f"讀取DDS封面失敗: {dds_path}，錯誤: {e}")
            return None

    def copy_cover_image(self, data):
        target_folder = QFileDialog.getExistingDirectory(self, "選擇目標資料夾", "")
        if target_folder:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            if os.path.exists(data["jacket_path"]):
                try:
                    target_path = os.path.join(target_folder, os.path.basename(data["jacket_path"]))
                    shutil.copy(data["jacket_path"], target_path)
                    print(f"成功將封面複製到: {target_path}")
                except Exception as e:
                    print(f"複製封面失敗: {e}")
            else:
                print(f"封面檔案不存在: {data['jacket_path']}")
        else:
            print("未選擇任何資料夾")
