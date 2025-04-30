import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from qfluentwidgets import LargeTitleLabel, TitleLabel, StrongBodyLabel, CaptionLabel

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("homePage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        logoLabel = TitleLabel(self)
        pixmap = QPixmap(resource_path("img/logo.jpg"))
        logoLabel.setPixmap(pixmap)
        logoLabel.setAlignment(Qt.AlignCenter)

        titleLabel = LargeTitleLabel("歡迎使用 CHUNAGER")
        titleFont = QFont()
        titleFont.setPointSize(24)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignCenter)

        descriptionLabel = StrongBodyLabel(
            "CHUNAGER 是一款針對 CHUNITHM HDD (SDHD 2.30.00 VERSE)設計的管理工具\n"
            "提供歌曲管理、角色管理、OPT 管理、解鎖器、補丁管理等功能\n"
            "協助您更輕鬆地整理與優化遊戲內容"
        )
        descFont = QFont()
        descFont.setPointSize(14)
        descriptionLabel.setFont(descFont)
        descriptionLabel.setAlignment(Qt.AlignCenter)

        authorLabel = CaptionLabel("作者：Elliot")
        authorFont = QFont()
        authorFont.setPointSize(12)
        authorFont.setItalic(True)
        authorLabel.setFont(authorFont)
        authorLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(logoLabel)
        layout.addSpacing(20)
        layout.addWidget(titleLabel)
        layout.addSpacing(20)
        layout.addWidget(descriptionLabel)
        layout.addSpacing(10)
        layout.addWidget(authorLabel)
