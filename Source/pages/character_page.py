import configparser
import json
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

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

    def __init__(self, row, dds_path):
        super().__init__()
        self.row = row
        self.dds_path = dds_path

    def run(self):
        pixmap = self.load_dds(self.dds_path)
        if pixmap:
            self.image_loaded.emit(self.row, pixmap)

    def load_dds(self, dds_path):
        if not dds_path or not os.path.exists(dds_path):
            return None

        try:
            img = Image.open(dds_path).convert("RGBA")
            data = img.tobytes("raw", "RGBA")
            qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
            return QPixmap.fromImage(qimg)
        except Exception:
            base, ext = os.path.splitext(dds_path)
            alt_path = base + (".DDS" if ext.lower() == ".dds" else ".dds")
            if os.path.exists(alt_path):
                try:
                    img = Image.open(alt_path).convert("RGBA")
                    data = img.tobytes("raw", "RGBA")
                    qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                    return QPixmap.fromImage(qimg)
                except Exception:
                    pass
        return None


class FileOperationThread(QThread):
    operation_completed = Signal(bool, str)

    def __init__(self, operation_type, **kwargs):
        super().__init__()
        self.operation_type = operation_type
        self.kwargs = kwargs

    def run(self):
        if self.operation_type == "extract_image":
            self.extract_image()
        elif self.operation_type == "rebuild_index":
            self.rebuild_index()
        elif self.operation_type == "reload_index":
            self.reload_index()

    def extract_image(self):
        try:
            img_path = self.kwargs['img_path']
            target_dir = self.kwargs['target_dir']

            if not os.path.exists(img_path):
                self.operation_completed.emit(False, self.tr(f"未找到角色圖像: {img_path}"))
                return

            target = os.path.join(target_dir, os.path.basename(img_path))
            shutil.copy(img_path, target)
            self.operation_completed.emit(True, self.tr(f"已複製: {target}"))
        except Exception as e:
            self.operation_completed.emit(False, self.tr(f"複製失敗: {str(e)}"))

    def rebuild_index(self):
        try:
            index_path = self.kwargs['index_path']
            if os.path.exists(index_path):
                os.remove(index_path)
            self.operation_completed.emit(True, self.tr("已刪除索引, 準備重建"))
        except Exception as e:
            self.operation_completed.emit(False, self.tr(f"無法刪除索引: {str(e)}"))

    def reload_index(self):
        try:
            index_path = self.kwargs['index_path']
            if not os.path.exists(index_path):
                self.operation_completed.emit(False, self.tr("索引不存在, 請先建立"))
                return

            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                chara_data = index_data.get("chara_data", {})

            mtime = os.path.getmtime(index_path)
            from datetime import datetime
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')

            self.operation_completed.emit(True, self.tr(f"成功重載|{json.dumps(chara_data)}|{timestamp}"))
        except Exception as e:
            self.operation_completed.emit(False, self.tr(f"索引讀取失敗: {str(e)}"))


class CharaSearchThread(QThread):
    found = Signal(dict)
    progress = Signal(int)
    error = Signal(str, str)
    status_update = Signal(str)

    def run(self):
        try:
            self.status_update.emit(self.tr("檢查索引"))
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
                        self.status_update.emit(self.tr("使用現存索引"))
                except Exception as e:
                    self.error.emit(self.tr("索引讀取失敗"), str(e))
                    return

            if need_rescan:
                self.status_update.emit(self.tr("掃描XML檔案"))
                xml_paths = self.find_xmls()
                chara_data = {}

                total = len(xml_paths)
                if total == 0:
                    self.status_update.emit(self.tr("找不到XML檔案"))
                    self.found.emit({})
                    return

                for idx, xml_path in enumerate(xml_paths):
                    try:
                        data = self.parse_xml(xml_path)
                        chara_data[data["chara_id"]] = data
                        progress_val = int(((idx + 1) / total) * 100)
                        self.progress.emit(progress_val)
                        self.status_update.emit(self.tr(f"處理中: {data['chara_name']} ({idx + 1}/{total})"))
                    except Exception as e:
                        print(self.tr(f"XML檔案解析失敗: {xml_path}, 錯誤: {e}"))
                        continue

                self.status_update.emit(self.tr("儲存索引"))
                current_opt_mtime = self.get_opt_last_modified_time()
                try:
                    with open(index_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "opt_last_modified": current_opt_mtime,
                            "chara_data": chara_data
                        }, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    self.error.emit(self.tr("寫入索引錯誤"), str(e))
                    return

            self.status_update.emit(self.tr("完成"))
            self.found.emit(chara_data)
        except Exception as e:
            self.error.emit(self.tr("搜尋失敗"), str(e))

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

    def xml_text(self, root, path, default="unknown"):
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
        self.image_loaders = {}
        self.current_file_operation = None

        self.init_ui()
        self.setup_search_thread()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)

        self.titleLabel = LargeTitleLabel(self.tr("角色管理"))
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
        self.searchBox.setPlaceholderText(self.tr("搜尋角色名稱..."))
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([self.tr("圖像"), self.tr("ID"), self.tr("名稱"), self.tr("出處"), self.tr("繪師"), self.tr("等級獎勵"), self.tr("提取圖像")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.layout.addWidget(self.table)

    def setup_search_thread(self):
        self.search_thread = CharaSearchThread()
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

    def on_search_done(self, chara_data):
        self.chara_data = chara_data
        self.update_table(list(chara_data.values()))
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
        for loader in self.image_loaders.values():
            if loader.isRunning():
                loader.terminate()
        self.image_loaders.clear()

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

            img_label = BodyLabel(self.tr("載入中..."))
            self.table.setCellWidget(row, 0, img_label)
            self.table.setRowHeight(row, 128)
            self.table.setColumnWidth(0, 128)

            self.load_image_async(row, data["image_path"])

            copy_btn = PushButton(self.tr("提取"))
            copy_btn.clicked.connect(lambda _, d=data: self.extract_image(d))
            self.table.setCellWidget(row, 6, copy_btn)

    def load_image_async(self, row, dds_path):
        loader = ImageLoaderThread(row, dds_path)
        loader.image_loaded.connect(self.on_image_loaded)
        loader.finished.connect(lambda: self.cleanup_image_loader(row))
        self.image_loaders[row] = loader

        QTimer.singleShot(row * 50, loader.start)

    def on_image_loaded(self, row, pixmap):
        if row < self.table.rowCount():
            label = BodyLabel()
            label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
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
            img_path=data["image_path"],
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
                chara_data_str = parts[1]
                timestamp = parts[2]

                chara_data = json.loads(chara_data_str)
                self.chara_data = chara_data
                self.update_table(list(chara_data.values()))
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
