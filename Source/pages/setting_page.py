import configparser
import os
import sys
import webbrowser
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import ComboBox, StrongBodyLabel, TitleLabel, LineEdit, PrimaryPushButton


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class SettingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("configPage")
        self.cfg_path = self.get_cfg_path()
        self.cfg = self.load_cfg()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = TitleLabel("設定")
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel("檢查更新："))
        update_btn = PrimaryPushButton(QIcon(get_path("img/web.svg")), "訪問GitHub發佈頁")
        update_btn.clicked.connect(self.open_repo)
        layout.addWidget(update_btn)
        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel("選擇主題："))
        self.theme_box = ComboBox(self)
        self.theme_box.addItems(["AUTO", "DARK", "LIGHT"])
        self.theme_box.setCurrentText(self.cfg.get("DISPLAY", "theme", fallback="AUTO"))
        self.theme_box.currentTextChanged.connect(self.update_theme)
        layout.addWidget(self.theme_box)
        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel("選擇 segatools.ini 路徑："))
        st_layout = QHBoxLayout()
        self.st_path = LineEdit(self)
        self.st_path.setText(self.cfg.get("GENERAL", "segatools_path", fallback=""))
        self.st_path.textChanged.connect(self.update_segatools_path)

        st_btn = PrimaryPushButton(QIcon(get_path("img/folder.svg")), "選擇檔案")
        st_btn.clicked.connect(self.pick_st_path)

        st_layout.addWidget(self.st_path)
        st_layout.addWidget(st_btn)
        layout.addLayout(st_layout)

    def get_cfg_path(self):
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(app_dir, "config.ini")

    def load_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read(self.cfg_path, encoding="utf-8")
        if not cfg.has_section("DISPLAY"):
            cfg.add_section("DISPLAY")
        if not cfg.has_section("GENERAL"):
            cfg.add_section("GENERAL")
        return cfg

    def save_cfg(self):
        with open(self.cfg_path, "w", encoding="utf-8") as file:
            self.cfg.write(file)

    def update_theme(self, text):
        self.cfg.set("DISPLAY", "theme", text)
        self.save_cfg()

    def update_segatools_path(self, text):
        self.cfg.set("GENERAL", "segatools_path", text)
        self.save_cfg()

    def pick_st_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "選擇 segatools.ini", "", "SEGATOOLS配置檔 (segatools.ini)")
        if path:
            self.st_path.setText(path)

    def open_repo(self):
        webbrowser.open("https://github.com/ElliotCHEN37/chunager/releases")
