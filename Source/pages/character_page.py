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


class CharaSearchThread(QThread):
    found = Signal(dict)
    progress = Signal(int)

    def run(self):
        index_path = self.get_index_path()
        need_rescan = True
        chara_data = {}

        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                last_opt_mtime = index_data.get("opt_last_modified", 0)
                chara_data = index_data.get("chara_data", {})

                current_opt_mtime = self.get_opt_last_modified_time()

                if current_opt_mtime == last_opt_mtime:
                    need_rescan = False
            except Exception as e:
                QMessageBox.critical(self, "讀取索引檔案錯誤", e)

        if need_rescan:
            xml_paths = self.find_xmls()
            chara_data = {}

            total = len(xml_paths)
            for idx, xml_path in enumerate(xml_paths):
                data = self.parse_xml(xml_path)
                chara_data[data["chara_id"]] = data
                self.progress.emit(int(((idx + 1) / total) * 100))

            current_opt_mtime = self.get_opt_last_modified_time()
            try:
                with open(index_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "opt_last_modified": current_opt_mtime,
                        "chara_data": chara_data
                    }, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QMessageBox.critical(self, "寫入索引檔案錯誤", e)

        self.found.emit(chara_data)

    def get_cfg_path(self):
        base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
            os.path.dirname(sys.argv[0]))
        return os.path.join(base, "config.ini")

    def get_index_path(self):
        base_dir = os.path.dirname(self.get_cfg_path())
        return os.path.join(base_dir, "character_index.json")

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

        a000_path = os.path.normpath(os.path.join(os.path.dirname(sega_path), "..", "data", "A000", "chara"))
        if os.path.isdir(a000_path):
            result.extend(self.scan_chara_folder(a000_path))

        if os.path.isdir(opt_path):
            for name in os.listdir(opt_path):
                subfolder = os.path.join(opt_path, name)
                chara_folder = os.path.join(subfolder, "chara")
                if os.path.isdir(subfolder) and name.startswith("A") and os.path.isdir(chara_folder):
                    result.extend(self.scan_chara_folder(chara_folder))

        return result

    def scan_chara_folder(self, root_path):
        found = []
        if not os.path.exists(root_path):
            return found

        for folder in os.listdir(root_path):
            if re.match(r'^chara\d+$', folder):
                chara_path = os.path.join(root_path, folder)
                xml_path = os.path.join(chara_path, "chara.xml")
                if os.path.exists(xml_path):
                    found.append(xml_path)

        return found

    def xml_text(self, root, path, default="未知"):
        elem = root.find(path)
        return elem.text if elem is not None else default

    def parse_xml(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        chara_id = self.xml_text(root, ".//name/id")
        chara_name = self.xml_text(root, ".//name/str")
        works = self.xml_text(root, ".//works/str")
        artist = self.xml_text(root, ".//illustratorName/str")
        sort_name = self.xml_text(root, ".//sortName")

        rewards = []
        for rank in root.findall(".//ranks/CharaRankData"):
            idx = rank.findtext("index", "0")
            reward = rank.find(".//rewardSkillSeed/rewardSkillSeed/str")
            if reward is not None and reward.text != "Invalid":
                rewards.append({
                    "rank": idx,
                    "reward_str": reward.text
                })

        img_default = self.xml_text(root, ".//defaultImages/str")
        padded_id = chara_id.zfill(6) if chara_id.isdigit() else chara_id

        img_suffix = img_default.replace("chara", "", 1) if img_default.startswith("chara") else img_default
        dds_folder = os.path.join(os.path.dirname(xml_path), "..", "..", "ddsImage", f"ddsImage{padded_id}")
        img_file = f"CHU_UI_Character_{img_suffix}_00.dds"
        img_path = os.path.join(dds_folder, img_file)

        return {
            "image_path": img_path,
            "chara_id": chara_id,
            "chara_name": chara_name,
            "works_name": works,
            "illustrator_name": artist,
            "sort_name": sort_name,
            "rank_rewards": rewards
        }


class CharacterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("characterPage")
        self.has_searched = False
        self.chara_data = {}

        self.init_ui()
        self.setup_search_thread()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.titleLabel = LargeTitleLabel("角色管理")
        self.layout.addWidget(self.titleLabel)

        self.searchMsg = BodyLabel("正在搜尋資料...")
        self.searchMsg.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.searchMsg)

        self.progress = ProgressBar(self)
        self.progress.setRange(0, 100)
        self.layout.addWidget(self.progress)

        search_layout = QHBoxLayout()
        self.searchBox = LineEdit(self)
        self.searchBox.setPlaceholderText("搜尋角色名稱...")
        search_layout.addWidget(self.searchBox)

        self.searchBtn = PrimaryPushButton("搜尋")
        self.searchBtn.clicked.connect(self.filter_data)
        search_layout.addWidget(self.searchBtn)

        self.resetBtn = PushButton("重置")
        self.resetBtn.clicked.connect(self.reset_filter)
        search_layout.addWidget(self.resetBtn)

        self.layout.addLayout(search_layout)

        self.table = TableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "圖像", "ID", "名稱", "出處", "繪師", "等級獎勵", "提取圖像"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

    def setup_search_thread(self):
        self.search_thread = CharaSearchThread()
        self.search_thread.found.connect(self.on_search_done)
        self.search_thread.progress.connect(self.update_progress)

    def update_progress(self, value):
        self.progress.setValue(value)

    def showEvent(self, event):
        if not self.has_searched:
            self.searchMsg.show()
            self.search_thread.start()
            self.has_searched = True

    def on_search_done(self, data):
        self.chara_data = data
        self.update_table(list(data.values()))
        self.searchMsg.hide()
        self.progress.hide()

    def reset_filter(self):
        self.searchBox.clear()
        self.filter_data(reset=True)

    def filter_data(self, reset=False):
        if reset:
            filtered = list(self.chara_data.values())
        else:
            query = self.searchBox.text().strip().lower()

            def safe_match(val):
                return str(val).lower() if val else ""

            filtered = [
                data for data in self.chara_data.values()
                if any(query in safe_match(data[key]) for key in
                       ["chara_id", "chara_name", "works_name", "illustrator_name"])
            ]

        self.update_table(filtered)

    def update_table(self, data_list):
        self.table.clearContents()
        self.table.setRowCount(len(data_list))

        for row, data in enumerate(data_list):
            self.table.setItem(row, 1, QTableWidgetItem(data["chara_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(data["chara_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(data["works_name"]))
            self.table.setItem(row, 4, QTableWidgetItem(data["illustrator_name"]))

            rewards = data["rank_rewards"]
            reward_text = ", ".join([f"Rank {r['rank']}: {r['reward_str']}" for r in rewards[:3]])
            if len(rewards) > 3:
                reward_text += f" (+{len(rewards) - 3})"
            self.table.setItem(row, 5, QTableWidgetItem(reward_text))

            pixmap = self.load_dds(data["image_path"])
            label = BodyLabel("無法加載圖像") if pixmap is None else BodyLabel()
            if pixmap:
                label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.table.setCellWidget(row, 0, label)

            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)

            copy_btn = PushButton("提取")
            copy_btn.clicked.connect(lambda _, d=data: self.extract_image(d))
            self.table.setCellWidget(row, 6, copy_btn)

    def load_dds(self, dds_path):
        if not dds_path or not os.path.exists(dds_path):
            QMessageBox.warning(self, "DDS圖像路徑不存在", dds_path)
            return None

        try:
            img = Image.open(dds_path).convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)
        except Exception as e:
            QMessageBox.critical(self, "讀取DDS圖像失敗", f"路徑: {dds_path}, 錯誤: {e}")

            base, ext = os.path.splitext(dds_path)
            alt_path = base + (".DDS" if ext.lower() == ".dds" else ".dds")
            if os.path.exists(alt_path):
                try:
                    img = Image.open(alt_path).convert("RGBA")
                    data = img.tobytes("raw", "RGBA")
                    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                    return QPixmap.fromImage(qimg)
                except Exception as e2:
                    QMessageBox.critical(self, "備用DDS圖像讀取失敗", f"路徑: {alt_path}, 錯誤: {e2}")

        return None

    def extract_image(self, data):
        target_dir = QFileDialog.getExistingDirectory(self, "選擇目標資料夾", "")
        if not target_dir:
            QMessageBox.warning(self, "錯誤", "未選擇任何資料夾")
            return

        img_path = data["image_path"]
        if not os.path.exists(img_path):
            QMessageBox.warning(self, "角色圖像檔案不存在", f"{img_path}")
            return

        try:
            target = os.path.join(target_dir, os.path.basename(img_path))
            shutil.copy(img_path, target)
            QMessageBox.information(self, "成功", f"成功將角色圖像複製到: {target}")
        except Exception as e:
            QMessageBox.critical(self, "複製角色圖像失敗", e)
