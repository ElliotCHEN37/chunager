import configparser
import os
import shutil
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt
from qfluentwidgets import TableWidget, LargeTitleLabel, PrimaryPushButton

class OptPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("optPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = LargeTitleLabel("OPT管理")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["資料夾", "類型", "版本", "操作"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(titleLabel)
        layout.addWidget(self.table)

        self.load_opt_data()

    def load_opt_data(self):
        self.table.clearContents()
        self.table.setRowCount(0)

        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        config.read(config_path)

        segatools_path = config.get("GENERAL", "segatools_path", fallback=None)
        if not segatools_path or not os.path.exists(segatools_path):
            print("找不到 segatools.ini")
            return

        segatools_config = configparser.ConfigParser()
        segatools_config.read(segatools_path)

        option_path = segatools_config.get("vfs", "option", fallback=None)
        if not option_path:
            print("找不到 [vfs] option")
            return

        if os.path.isabs(option_path):
            opt_dir = option_path
        else:
            opt_dir = os.path.join(os.path.dirname(segatools_path), option_path)

        if not os.path.exists(opt_dir):
            print("找不到 option 目錄")
            return

        folder_list = []

        a000 = os.path.normpath(os.path.join(os.path.dirname(segatools_path), "..", "data", "A000"))
        if os.path.exists(a000):
            folder_list.append(a000)

        for f in os.listdir(opt_dir):
            full_path = os.path.join(opt_dir, f)
            if f.startswith('A') and os.path.isdir(full_path):
                folder_list.append(full_path)

        self.table.setRowCount(len(folder_list))

        for row, folder_path in enumerate(folder_list):
            folder_name = os.path.basename(folder_path)
            data_conf_path = os.path.join(folder_path, "data.conf")

            self.table.setItem(row, 0, QTableWidgetItem(folder_name))

            if os.path.exists(data_conf_path):
                self.table.setItem(row, 1, QTableWidgetItem("官方更新"))
                version = self.read_version_from_data_conf(data_conf_path)
                self.table.setItem(row, 2, QTableWidgetItem(version))
            else:
                self.table.setItem(row, 1, QTableWidgetItem("自製更新"))
                self.table.setItem(row, 2, QTableWidgetItem("\\"))

            delete_button = PrimaryPushButton("刪除", self)
            delete_button.clicked.connect(lambda checked, path=folder_path, name=folder_name: self.confirm_delete_folder(path, name))
            self.table.setCellWidget(row, 3, delete_button)

    def confirm_delete_folder(self, path, folder_name):
        reply = QMessageBox.warning(
            self,
            "確認刪除",
            f"你確定要刪除資料夾「{folder_name}」嗎？此操作無法復原！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.delete_folder(path)

    def delete_folder(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            try:
                shutil.rmtree(path)
                print(f"已刪除資料夾: {path}")
                self.load_opt_data()  # 刷新表格
            except Exception as e:
                print(f"刪除失敗: {e}")

    def read_version_from_data_conf(self, conf_path):
        version_config = configparser.ConfigParser()
        with open(conf_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content = "[dummy]\n" + "".join(lines)
        version_config.read_string(content)

        try:
            major = version_config.getint("Version", "VerMajor", fallback=0)
            minor = version_config.getint("Version", "VerMinor", fallback=0)
            release = version_config.getint("Version", "VerRelease", fallback=0)
            return f"{major}.{minor}.{release}"
        except Exception as e:
            print(f"讀取版本失敗: {e}")
            return "未知"
