import configparser
import os
import webbrowser
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import ComboBox, StrongBodyLabel, TitleLabel, PrimaryPushButton, Flyout, InfoBarIcon, FlyoutAnimationType, LineEdit, PushButton

class ConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("configPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = TitleLabel("設定")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        self.config = self.load_config()

        update_label = StrongBodyLabel("檢查更新：")
        self.update_button = PushButton(QIcon("./img/web.svg"), "訪問GitHub發佈頁")
        self.update_button.clicked.connect(self.open_github)

        theme_label = StrongBodyLabel("選擇主題：")
        self.theme_combobox = ComboBox(self)
        self.theme_combobox.addItems(["AUTO", "DARK", "LIGHT"])
        current_theme = self.config.get("DISPLAY", "theme", fallback="AUTO")
        self.theme_combobox.setCurrentText(current_theme)
        self.theme_combobox.currentTextChanged.connect(self.on_theme_changed)

        segatools_layout = QHBoxLayout()
        segatools_label = StrongBodyLabel("選擇 segatools.ini 路徑：")
        self.segatoools_lineedit = LineEdit(self)
        current_path = self.config.get("GENERAL", "segatools_path", fallback="")
        self.segatoools_lineedit.setText(current_path)

        self.segatoools_button = PrimaryPushButton(QIcon("./img/folder.svg"), "選擇檔案")
        self.segatoools_button.clicked.connect(self.choose_segatoools_path)

        segatools_layout.addWidget(self.segatoools_lineedit)
        segatools_layout.addWidget(self.segatoools_button)

        self.save_button = PrimaryPushButton(QIcon("./img/save.svg"), "儲存設定")
        self.save_button.clicked.connect(self.save_config)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(update_label)
        layout.addWidget(self.update_button)
        layout.addSpacing(10)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combobox)
        layout.addSpacing(10)
        layout.addWidget(segatools_label)
        layout.addLayout(segatools_layout)
        layout.addSpacing(10)
        layout.addWidget(self.save_button)

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        config.read(config_path)
        return config

    def save_config(self):
        self.config.set("DISPLAY", "theme", self.theme_combobox.currentText())
        self.config.set("GENERAL", "segatools_path", self.segatoools_lineedit.text())

        config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

        Flyout.create(
            icon=InfoBarIcon.SUCCESS,
            title='完成',
            content="所有選項已儲存，重新啟動以生效",
            target=self.save_button,
            parent=self,
            isClosable=True,
            aniType=FlyoutAnimationType.PULL_UP
        )

    def choose_segatoools_path(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "選擇 segatools.ini", "", "SEGATOOLS配置檔 (segatools.ini)")

        if file_path:
            self.segatoools_lineedit.setText(file_path)

    def on_theme_changed(self):
        self.config.set("DISPLAY", "theme", self.theme_combobox.currentText())

    def open_github(self):
        webbrowser.open("https://github.com/ElliotCHEN37/chunager/releases")
