import configparser
import os
import sys

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qfluentwidgets import LargeTitleLabel, StrongBodyLabel, CaptionLabel


class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("aboutPage")

        self.cfg_path = self.get_cfg_path()
        self.cfg = self.load_cfg()
        self.current_version = self.cfg.get("GENERAL", "version")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        def styled_label(label_class, text, point_size, rich=False):
            label = label_class(text)
            font = QFont()
            font.setPointSize(point_size)
            label.setFont(font)
            label.setAlignment(Qt.AlignLeft)
            label.setWordWrap(True)
            if rich:
                label.setTextFormat(Qt.RichText)
                label.setTextInteractionFlags(Qt.TextBrowserInteraction)
                label.setOpenExternalLinks(True)
            return label

        layout.addWidget(styled_label(LargeTitleLabel, "關於 CHUNAGER", 20))
        layout.addSpacing(10)

        layout.addWidget(styled_label(
            StrongBodyLabel,
            self.tr("CHUNAGER 是一款針對 CHUNITHM HDD (SDHD 2.30.00 VERSE) 設計的管理工具\n提供歌曲管理、角色管理、OPT 管理、解鎖器、補丁管理等功能\n協助您更輕鬆地整理與優化遊戲內容"),
            12
        ))
        layout.addSpacing(15)

        layout.addWidget(styled_label(
            CaptionLabel,
            self.tr(f'作者：Elliot<br>版本：{self.current_version}<br>GitHub：<a href="https://github.com/ElliotCHEN37/chunager">https://github.com/ElliotCHEN37/chunager</a>'),
            10,
            rich=True
        ))
        layout.addSpacing(10)

        layout.addWidget(styled_label(
            CaptionLabel,
            self.tr('<br>免責聲明：<br>本程式為個人開發，與任何和 Evil Leaker、SEGA、CHUNITHM 官方團隊或相關人物及事項無任何關係。<br>請遵守當地法律使用。<br>本程式使用 MIT 授權，詳見<a href="https://raw.githubusercontent.com/ElliotCHEN37/chunager/refs/heads/main/LICENSE.txt">許可證</a>。<br>使用本程式所造成的一切後果，作者不承擔任何責任。'),
            10,
            rich=True
        ))

    def get_cfg_path(self):
        app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
            os.path.dirname(sys.argv[0]))
        return os.path.join(app_dir, "config.ini")

    def load_cfg(self):
        cfg = configparser.ConfigParser()
        cfg.read(self.cfg_path, encoding="utf-8")
        for section in ["DISPLAY", "GENERAL"]:
            if not cfg.has_section(section):
                cfg.add_section(section)
        return cfg
