import configparser
import os
import sys
import shutil
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, QObject
from qfluentwidgets import TableWidget, LargeTitleLabel, PushButton


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class OptLoader(QObject):
    done = Signal(list)
    fail = Signal(str)

    def run(self):
        try:
            cfg = configparser.ConfigParser()
            base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
                os.path.dirname(sys.argv[0]))
            cfg_path = os.path.join(base, "config.ini")
            cfg.read(cfg_path)

            st_path = cfg.get("GENERAL", "segatools_path", fallback=None)
            if not st_path or not os.path.exists(st_path):
                self.fail.emit("找不到 segatools.ini")
                return

            st_cfg = configparser.ConfigParser()
            st_cfg.read(st_path)

            opt_path = st_cfg.get("vfs", "option", fallback=None)
            if not opt_path:
                self.fail.emit("找不到 [vfs] option")
                return

            opt_dir = opt_path if os.path.isabs(opt_path) else os.path.join(os.path.dirname(st_path), opt_path)
            if not os.path.exists(opt_dir):
                self.fail.emit("找不到 option 目錄")
                return

            folders = []
            a000 = os.path.normpath(os.path.join(os.path.dirname(st_path), "..", "data", "A000"))
            if os.path.exists(a000):
                folders.append(a000)

            for f in os.listdir(opt_dir):
                path = os.path.join(opt_dir, f)
                if f.startswith('A') and os.path.isdir(path):
                    folders.append(path)

            self.done.emit(folders)
        except Exception as e:
            self.fail.emit(str(e))


class OptPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("optPage")
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = LargeTitleLabel("OPT管理")
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)

        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["資料夾", "類型", "版本", "操作"])
        self.table.horizontalHeader().setStretchLastSection(True)

        layout.addWidget(title)
        layout.addWidget(self.table)

    def load_data(self):
        self.thread = QThread()
        self.loader = OptLoader()
        self.loader.moveToThread(self.thread)

        self.thread.started.connect(self.loader.run)
        self.loader.done.connect(self.show_data)
        self.loader.fail.connect(self.show_error)
        self.loader.done.connect(self.thread.quit)
        self.loader.done.connect(self.loader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def show_data(self, folders):
        self.table.setRowCount(len(folders))
        for row, path in enumerate(folders):
            name = os.path.basename(path)
            conf_path = os.path.join(path, "data.conf")

            self.table.setItem(row, 0, QTableWidgetItem(name))
            if os.path.exists(conf_path):
                self.table.setItem(row, 1, QTableWidgetItem("官方更新"))
                ver = self.get_version(conf_path)
                self.table.setItem(row, 2, QTableWidgetItem(ver))
            else:
                self.table.setItem(row, 1, QTableWidgetItem("自製更新"))
                self.table.setItem(row, 2, QTableWidgetItem("\\"))

            del_btn = PushButton("刪除", self)
            del_btn.clicked.connect(lambda checked, p=path, n=name: self.ask_delete(p, n))
            self.table.setCellWidget(row, 3, del_btn)

    def show_error(self, msg):
        QMessageBox.critical(self, "載入錯誤", msg)

    def ask_delete(self, path, name):
        reply = QMessageBox.warning(
            self,
            "確認刪除",
            f"你確定要刪除資料夾「{name}」嗎？此操作無法復原！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.rm_folder(path)

    def rm_folder(self, path):
        if os.path.exists(path) and os.path.isdir(path):
            try:
                shutil.rmtree(path)
                print(f"已刪除資料夾: {path}")
                self.load_data()
            except Exception as e:
                print(f"刪除失敗: {e}")

    def get_version(self, conf_path):
        ver_cfg = configparser.ConfigParser()
        try:
            with open(conf_path, "r", encoding="utf-8") as f:
                content = "[dummy]\n" + f.read()
            ver_cfg.read_string(content)
            major = ver_cfg.getint("Version", "VerMajor", fallback=0)
            minor = ver_cfg.getint("Version", "VerMinor", fallback=0)
            release = ver_cfg.getint("Version", "VerRelease", fallback=0)
            return f"{major}.{minor}.{release}"
        except Exception as e:
            print(f"讀取版本失敗: {e}")
            return "未知"
