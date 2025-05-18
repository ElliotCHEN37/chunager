import configparser
import os
import sys
import webbrowser
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import ComboBox, StrongBodyLabel, TitleLabel, PrimaryPushButton, Flyout, InfoBarIcon, \
    FlyoutAnimationType, LineEdit, PushButton


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
        title.setAlignment(Qt.AlignLeft)
        layout.addWidget(title)
        layout.addSpacing(10)

        update_lbl = StrongBodyLabel("檢查更新：")
        self.update_btn = PushButton(QIcon(get_path("img/web.svg")), "訪問GitHub發佈頁")
        self.update_btn.clicked.connect(self.open_repo)
        layout.addWidget(update_lbl)
        layout.addWidget(self.update_btn)
        layout.addSpacing(10)

        theme_lbl = StrongBodyLabel("選擇主題：")
        self.theme_box = ComboBox(self)
        self.theme_box.addItems(["AUTO", "DARK", "LIGHT"])
        theme = self.cfg.get("DISPLAY", "theme", fallback="AUTO")
        self.theme_box.setCurrentText(theme)
        self.theme_box.currentTextChanged.connect(self.set_theme)
        layout.addWidget(theme_lbl)
        layout.addWidget(self.theme_box)
        layout.addSpacing(10)

        st_lbl = StrongBodyLabel("選擇 segatools.ini 路徑：")
        st_layout = QHBoxLayout()
        self.st_path = LineEdit(self)
        path = self.cfg.get("GENERAL", "segatools_path", fallback="")
        self.st_path.setText(path)

        self.st_btn = PrimaryPushButton(QIcon(get_path("img/folder.svg")), "選擇檔案")
        self.st_btn.clicked.connect(self.pick_st_path)

        st_layout.addWidget(self.st_path)
        st_layout.addWidget(self.st_btn)
        layout.addWidget(st_lbl)
        layout.addLayout(st_layout)
        layout.addSpacing(10)

        self.save_btn = PrimaryPushButton(QIcon(get_path("img/save.svg")), "儲存設定")
        self.save_btn.clicked.connect(self.save_cfg)
        layout.addWidget(self.save_btn)

    def get_cfg_path(self):
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        return os.path.join(app_dir, "config.ini")

    def load_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read(self.cfg_path, encoding="utf-8")
        return cfg

    def save_cfg(self):
        self.cfg.set("DISPLAY", "theme", self.theme_box.currentText())
        self.cfg.set("GENERAL", "segatools_path", self.st_path.text())

        with open(self.cfg_path, "w", encoding="utf-8") as file:
            self.cfg.write(file)

        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='完成',
            content="所有選項已儲存，重新啟動以生效",
            target=self.save_btn,
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP
        )

    def pick_st_path(self):
        dialog = QFileDialog(self)
        path, _ = dialog.getOpenFileName(self, "選擇 segatools.ini", "", "SEGATOOLS配置檔 (segatools.ini)")
        if path:
            self.st_path.setText(path)

    def set_theme(self):
        self.cfg.set("DISPLAY", "theme", self.theme_box.currentText())

    def open_repo(self):
        webbrowser.open("https://github.com/ElliotCHEN37/chunager/releases")
