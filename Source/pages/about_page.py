import configparser
import os
import sys

import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QTableWidgetItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qfluentwidgets import LargeTitleLabel, StrongBodyLabel, CaptionLabel, TableWidget

def get_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("aboutPage")

        self.cfg_path = self.get_cfg_path()
        self.cfg = self.load_cfg()
        self.current_version = self.cfg.get("GENERAL", "version")

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setAlignment(Qt.AlignTop)

        layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(inner)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

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

        layout.addWidget(styled_label(LargeTitleLabel, self.tr("關於 CHUNAGER"), 20))
        layout.addSpacing(10)

        layout.addWidget(styled_label(StrongBodyLabel, self.tr("感謝名單"), 12))

        self.table = TableWidget()
        self.table.setColumnCount(2)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels([self.tr("名稱"), self.tr("贊助金額")])
        self.table.setEditTriggers(TableWidget.NoEditTriggers)
        self.table.setSelectionMode(TableWidget.NoSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.load_thanks_list()

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

        layout.addWidget(styled_label(
            CaptionLabel,
            self.tr('<br>贊助 20 元及以上即可出現在感謝名單中, 名單每個月更新一次<br><img src="img/wc_spon.JPG" width=300>'),
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

    def load_thanks_list(self):
        url = "https://raw.githubusercontent.com/ElliotCHEN37/chunager/main/sp_thk.json"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.table.setRowCount(len(data))
                for row, person in enumerate(data):
                    name_item = QTableWidgetItem(person.get("name", ""))
                    donate_item = QTableWidgetItem(person.get("donate", ""))
                    self.table.setItem(row, 0, name_item)
                    self.table.setItem(row, 1, donate_item)
        except Exception as e:
            print("載入感謝名單失敗：", e)
