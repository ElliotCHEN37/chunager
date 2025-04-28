import configparser
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class ConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("configPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = QLabel("設定")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        self.config = self.load_config()

        auto_update_label = QLabel("啟用自動更新：")
        self.auto_update_checkbox = QCheckBox(self)
        self.auto_update_checkbox.setChecked(self.config.getboolean("GENERAL", "auto_update"))
        self.auto_update_checkbox.stateChanged.connect(self.on_auto_update_changed)

        theme_label = QLabel("選擇主題：")
        self.theme_combobox = QComboBox(self)
        self.theme_combobox.addItem("AUTO")
        self.theme_combobox.addItem("DARK")
        self.theme_combobox.addItem("LIGHT")
        current_theme = self.config.get("DISPLAY", "theme")
        self.theme_combobox.setCurrentText(current_theme)
        self.theme_combobox.currentTextChanged.connect(self.on_theme_changed)

        save_button = QPushButton("儲存設定", self)
        save_button.clicked.connect(self.save_config)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(auto_update_label)
        layout.addWidget(self.auto_update_checkbox)
        layout.addSpacing(10)
        layout.addWidget(theme_label)
        layout.addWidget(self.theme_combobox)
        layout.addSpacing(10)
        layout.addWidget(save_button)

    def load_config(self):
        config = configparser.ConfigParser()

        config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        config.read(config_path)

        return config

    def save_config(self):
        self.config.set("GENERAL", "auto_update", str(self.auto_update_checkbox.isChecked()))
        self.config.set("DISPLAY", "theme", self.theme_combobox.currentText())

        config_path = os.path.join(os.path.dirname(__file__), "..", "config.ini")
        with open(config_path, "w") as configfile:
            self.config.write(configfile)

    def on_auto_update_changed(self):
        self.config.set("GENERAL", "auto_update", str(self.auto_update_checkbox.isChecked()))

    def on_theme_changed(self):
        self.config.set("DISPLAY", "theme", self.theme_combobox.currentText())
