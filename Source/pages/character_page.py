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


class CharacterSearchThread(QThread):
    search_completed = Signal(dict)
    progress_update = Signal(int)

    def run(self):
        chara_xml_paths = self.find_all_chara_xmls()
        chara_data = {}

        total_files = len(chara_xml_paths)
        for index, xml_path in enumerate(chara_xml_paths):
            data = self.parse_chara_xml(xml_path)
            chara_data[data["chara_id"]] = data
            progress = int(((index + 1) / total_files) * 100)
            self.progress_update.emit(progress)

        self.search_completed.emit(chara_data)

    def get_config_path(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(base_path, "config.ini")

    def find_all_chara_xmls(self):
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

        data_a000_chara_path = os.path.normpath(
            os.path.join(os.path.dirname(segatools_path), "..", "data", "A000", "chara"))
        if os.path.isdir(data_a000_chara_path):
            result.extend(self.find_chara_xml_in_chara_folder(data_a000_chara_path))

        if os.path.isdir(option_path):
            for name in os.listdir(option_path):
                subfolder_path = os.path.join(option_path, name)
                chara_folder_path = os.path.join(subfolder_path, "chara")
                if os.path.isdir(subfolder_path) and name.startswith("A") and os.path.isdir(chara_folder_path):
                    result.extend(self.find_chara_xml_in_chara_folder(chara_folder_path))

        return result

    def find_chara_xml_in_chara_folder(self, chara_folder_root):
        found = []
        if not os.path.exists(chara_folder_root):
            return found

        for folder in os.listdir(chara_folder_root):
            if re.match(r'^chara\d+$', folder):
                chara_folder_path = os.path.join(chara_folder_root, folder)
                chara_xml_path = os.path.join(chara_folder_path, "chara.xml")
                if os.path.exists(chara_xml_path):
                    found.append(chara_xml_path)

        return found

    def parse_chara_xml(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        def safe_find_text(path, default="未知"):
            element = root.find(path)
            return element.text if element is not None else default

        chara_id = safe_find_text(".//name/id")
        chara_name = safe_find_text(".//name/str")
        works_name = safe_find_text(".//works/str")
        illustrator_name = safe_find_text(".//illustratorName/str")
        sort_name = safe_find_text(".//sortName")

        rank_rewards = []
        for rank_data in root.findall(".//ranks/CharaRankData"):
            index = rank_data.findtext("index", "0")
            reward_str = rank_data.find(".//rewardSkillSeed/rewardSkillSeed/str")

            if reward_str is not None:
                rank_rewards.append({
                    "rank": index,
                    "reward_str": reward_str.text
                })

        default_images = safe_find_text(".//defaultImages/str")

        padded_id = chara_id.zfill(6)

        image_suffix = default_images.replace("chara", "", 1) if default_images.startswith("chara") else default_images

        dds_folder = os.path.join(os.path.dirname(xml_path), "..", "..", "ddsImage", f"ddsImage{padded_id}")
        image_filename = f"CHU_UI_Character_{image_suffix}_00.dds"
        image_abs_path = os.path.join(dds_folder, image_filename)

        return {
            "image_path": image_abs_path,
            "chara_id": chara_id,
            "chara_name": chara_name,
            "works_name": works_name,
            "illustrator_name": illustrator_name,
            "sort_name": sort_name,
            "rank_rewards": rank_rewards
        }


class CharacterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("characterPage")
        self.has_searched = False

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.titleLabel = LargeTitleLabel("角色管理")
        self.layout.addWidget(self.titleLabel)

        self.searchingLabel = BodyLabel("正在搜尋資料...")
        self.searchingLabel.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.searchingLabel)

        self.progressBar = ProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.layout.addWidget(self.progressBar)

        search_layout = QHBoxLayout()
        self.searchBox = LineEdit(self)
        self.searchBox.setPlaceholderText("搜尋角色名稱...")
        search_layout.addWidget(self.searchBox)

        self.searchButton = PrimaryPushButton("搜尋")
        self.searchButton.clicked.connect(self.filter_chara_data)
        search_layout.addWidget(self.searchButton)

        self.resetButton = PushButton("重置")
        self.resetButton.clicked.connect(self.reset_search_filter)
        search_layout.addWidget(self.resetButton)

        self.layout.addLayout(search_layout)

        self.table = TableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "圖像", "角色ID", "角色名稱", "作品", "繪師", "等級獎勵", "提取圖像"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

        self.chara_search_thread = CharacterSearchThread()
        self.chara_search_thread.search_completed.connect(self.on_search_completed)
        self.chara_search_thread.progress_update.connect(self.update_progress)

    def update_progress(self, value):
        self.progressBar.setValue(value)

    def showEvent(self, event):
        if not self.has_searched:
            self.searchingLabel.show()
            self.chara_search_thread.start()
            self.has_searched = True

    def on_search_completed(self, chara_data):
        self.chara_data_dict = chara_data
        self.table.setRowCount(len(chara_data))

        for row, data in enumerate(chara_data.values()):
            self.table.setItem(row, 1, QTableWidgetItem(data["chara_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["chara_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["works_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(data["illustrator_name"]))

            rank_rewards_text = ", ".join([f"Rank {r['rank']}: {r['reward_str']}" for r in data["rank_rewards"][:3]])
            if len(data["rank_rewards"]) > 3:
                rank_rewards_text += f" (+{len(data['rank_rewards']) - 3})"
            self.table.setItem(row, 5, QTableWidgetItem(rank_rewards_text))

            pixmap = self.load_dds_image(data["image_path"])
            if pixmap is not None:
                label = BodyLabel()
                label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.table.setCellWidget(row, 0, label)
            else:
                label = BodyLabel("無法加載圖像")
                self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)

            copy_button = PushButton("提取")
            copy_button.clicked.connect(lambda _, d=data: self.copy_character_image(d))
            self.table.setCellWidget(row, 6, copy_button)

        self.searchingLabel.hide()
        self.progressBar.hide()

    def reset_search_filter(self):
        self.searchBox.clear()
        self.filter_chara_data(reset=True)

    def filter_chara_data(self, reset=False):
        if reset:
            filtered_data = list(self.chara_data_dict.values())
        else:
            search_text = self.searchBox.text().strip().lower()

            def safe_search(value):
                if value is None:
                    return ""
                return str(value).lower()

            filtered_data = [
                data for chara_id, data in self.chara_data_dict.items()
                if (search_text in safe_search(data["chara_id"]) or
                    search_text in safe_search(data["chara_name"]) or
                    search_text in safe_search(data["works_name"]) or
                    search_text in safe_search(data["illustrator_name"]))
            ]

        self.table.clearContents()
        self.table.setRowCount(len(filtered_data))

        for row, data in enumerate(filtered_data):
            self.table.setItem(row, 1, QTableWidgetItem(data["chara_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["chara_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["works_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(data["illustrator_name"]))

            rank_rewards_text = ", ".join([f"Rank {r['rank']}: {r['reward_str']}" for r in data["rank_rewards"][:3]])
            if len(data["rank_rewards"]) > 3:
                rank_rewards_text += f" (+{len(data['rank_rewards']) - 3})"
            self.table.setItem(row, 5, QTableWidgetItem(rank_rewards_text))

            pixmap = self.load_dds_image(data["image_path"])
            if pixmap is not None:
                label = BodyLabel()
                label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.table.setCellWidget(row, 0, label)
            else:
                label = BodyLabel("無法加載圖像")
                self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)

            copy_button = PushButton("提取")
            copy_button.clicked.connect(lambda _, d=data: self.copy_character_image(d))
            self.table.setCellWidget(row, 6, copy_button)

    def load_dds_image(self, dds_path):
        if not dds_path or not os.path.exists(dds_path):
            print(f"DDS圖像路徑不存在: {dds_path}")
            return None

        try:
            img = Image.open(dds_path)
            img = img.convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimage)
        except Exception as e:
            print(f"讀取DDS圖像失敗: {dds_path}，錯誤: {e}")

            alt_path = dds_path.replace(".dds", ".DDS") if dds_path.endswith(".dds") else dds_path.replace(".DDS",
                                                                                                           ".dds")
            if os.path.exists(alt_path):
                try:
                    print(f"尝试加载备用路径: {alt_path}")
                    img = Image.open(alt_path)
                    img = img.convert("RGBA")
                    data = img.tobytes("raw", "RGBA")
                    qimage = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                    return QPixmap.fromImage(qimage)
                except Exception as e2:
                    print(f"讀取備用DDS圖像也失敗: {alt_path}，錯誤: {e2}")

            return None

    def copy_character_image(self, data):
        target_folder = QFileDialog.getExistingDirectory(self, "選擇目標資料夾", "")
        if target_folder:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            image_path = data["image_path"]
            if os.path.exists(image_path):
                try:
                    target_path = os.path.join(target_folder)

                    shutil.copy(image_path, target_path)
                    print(f"成功將角色圖像複製到: {target_path}")
                except Exception as e:
                    print(f"複製角色圖像失敗: {e}")
            else:
                print(f"角色圖像檔案不存在: {image_path}")
        else:
            print("未選擇任何資料夾")
