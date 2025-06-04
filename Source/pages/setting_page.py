import configparser
import os
import sys
import webbrowser
import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import ComboBox, StrongBodyLabel, TitleLabel, LineEdit, PrimaryPushButton

GITHUB_REPO_API = "https://api.github.com/repos/ElliotCHEN37/chunager/releases/latest"
GITHUB_RELEASE_URL = "https://github.com/ElliotCHEN37/chunager/releases"
CURRENT_VERSION = "v1.3"


def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)


class SettingPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("configPage")
        self.cfg_path = self.get_cfg_path()
        self.cfg = self.load_cfg()
        self.check_config()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = TitleLabel(self.tr("設定"))
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel(self.tr("所有選項即時儲存, 重啟後生效")))

        layout.addWidget(StrongBodyLabel(self.tr("檢查更新：")))
        check_btn = PrimaryPushButton(self.tr(f"檢查更新 (當前版本： {CURRENT_VERSION})"))
        check_btn.clicked.connect(self.check_update)
        layout.addWidget(check_btn)

        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel(self.tr("選擇主題：")))
        self.theme_box = ComboBox(self)
        self.theme_box.addItems(["AUTO", "DARK", "LIGHT"])
        self.theme_box.setCurrentText(self.cfg.get("DISPLAY", "theme", fallback="AUTO"))
        self.theme_box.currentTextChanged.connect(self.update_theme)
        layout.addWidget(self.theme_box)
        layout.addSpacing(10)

        layout.addWidget(StrongBodyLabel(self.tr("選擇翻譯檔 (.qm)：")))
        qm_layout = QHBoxLayout()
        self.qm_path = LineEdit(self)
        self.qm_path.setText(self.cfg.get("DISPLAY", "translation_path", fallback=""))
        self.qm_path.textChanged.connect(self.update_qm_path)

        qm_btn = PrimaryPushButton(QIcon(get_path("img/folder.svg")), self.tr("選擇檔案"))
        qm_btn.clicked.connect(self.pick_qm_path)

        reset_qm_btn = PrimaryPushButton(self.tr("重置翻譯"))
        reset_qm_btn.clicked.connect(self.reset_qm_path)

        qm_layout.addWidget(self.qm_path)
        qm_layout.addWidget(qm_btn)
        qm_layout.addWidget(reset_qm_btn)
        layout.addLayout(qm_layout)

        layout.addWidget(StrongBodyLabel(self.tr("選擇 segatools.ini 路徑：")))
        st_layout = QHBoxLayout()
        self.st_path = LineEdit(self)
        self.st_path.setText(self.cfg.get("GENERAL", "segatools_path", fallback=""))
        self.st_path.textChanged.connect(self.update_segatools_path)

        st_btn = PrimaryPushButton(QIcon(get_path("img/folder.svg")), self.tr("選擇檔案"))
        st_btn.clicked.connect(self.pick_st_path)

        st_layout.addWidget(self.st_path)
        st_layout.addWidget(st_btn)
        layout.addLayout(st_layout)

    def check_update(self):
        try:
            response = requests.get(GITHUB_REPO_API, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest = data.get("tag_name", CURRENT_VERSION)
                release_notes = data.get("body", self.tr("（無更新日誌）"))

                if latest > CURRENT_VERSION:
                    msg = QMessageBox(self)
                    msg.setWindowTitle(self.tr("發現新版本"))
                    msg.setIcon(QMessageBox.Information)
                    msg.setText(self.tr(f"發現新版本 {latest}，是否前往下載？"))
                    msg.setInformativeText(release_notes)
                    msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                    msg.setDefaultButton(QMessageBox.Yes)
                    reply = msg.exec()

                    if reply == QMessageBox.Yes:
                        webbrowser.open(GITHUB_RELEASE_URL)
                else:
                    QMessageBox.information(self, self.tr("已是最新"), self.tr(f"目前已是最新版本 {CURRENT_VERSION}。"))
            else:
                QMessageBox.warning(self, self.tr("更新失敗"), self.tr("無法取得更新資訊。"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("錯誤"), self.tr(f"檢查更新時發生錯誤：{str(e)}"))

    def get_cfg_path(self):
        app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
            os.path.dirname(sys.argv[0]))
        return os.path.join(app_dir, "config.ini")

    def load_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read(self.cfg_path, encoding="utf-8")
        return cfg

    def check_config(self):
        modified = False
        if not self.cfg.has_section("DISPLAY"):
            self.cfg.add_section("DISPLAY")
            self.cfg.set("DISPLAY", "theme", "AUTO")
            self.cfg.set("DISPLAY", "translation_path", "")
            modified = True

        if not self.cfg.has_section("GENERAL"):
            self.cfg.add_section("GENERAL")
            self.cfg.set("GENERAL", "version", CURRENT_VERSION)
            self.cfg.set("GENERAL", "segatools_path", "")
            modified = True
        else:
            current_cfg_version = self.cfg.get("GENERAL", "version", fallback="")
            if current_cfg_version != CURRENT_VERSION:
                self.cfg.set("GENERAL", "version", CURRENT_VERSION)
                modified = True

            if not self.cfg.has_option("GENERAL", "segatools_path"):
                self.cfg.set("GENERAL", "segatools_path", "")
                modified = True

            if not self.cfg.has_option("DISPLAY", "translation_path"):
                self.cfg.set("DISPLAY", "translation_path", "")
                modified = True

        if modified:
            self.save_cfg()

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
        path, _ = QFileDialog.getOpenFileName(self, self.tr("選擇 segatools.ini"), "", self.tr("SEGATOOLS配置檔 (segatools.ini)"))
        if path:
            self.st_path.setText(path)

    def update_qm_path(self, text):
        self.cfg.set("DISPLAY", "translation_path", text)
        self.save_cfg()

    def pick_qm_path(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("選擇翻譯檔"), "", self.tr("QT翻譯檔案 (*.qm)"))
        if path:
            self.qm_path.setText(path)

    def reset_qm_path(self):
        self.qm_path.clear()
        self.cfg.set("DISPLAY", "translation_path", "")
        self.save_cfg()
