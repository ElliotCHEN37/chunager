from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("aboutPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = QLabel("關於 CHUNAGER")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        descriptionLabel = QLabel(
            "CHUNAGER 是一款針對 CHUNITHM HDD (SDHD 2.30.00 VERSE)設計的管理工具\n"
            "提供歌曲管理、角色管理、OPT 管理、解鎖器、補丁管理等功能\n"
            "協助您更輕鬆地整理與優化遊戲內容"
        )
        descriptionFont = QFont()
        descriptionFont.setPointSize(12)
        descriptionLabel.setFont(descriptionFont)
        descriptionLabel.setAlignment(Qt.AlignLeft)
        descriptionLabel.setWordWrap(True)

        authorLabel = QLabel(
            "作者：Elliot\n"
            "版本：INTERNAL VERSION\n"
            "GitHub：https://github.com/ElliotCHEN37/chunager"
        )
        authorFont = QFont()
        authorFont.setPointSize(11)
        authorLabel.setFont(authorFont)
        authorLabel.setAlignment(Qt.AlignLeft)
        authorLabel.setWordWrap(True)

        licenseLabel = QLabel(
            "\n免責聲明：\n"
            "本程式為個人非官方開發，與 SEGA 及 CHUNITHM 官方團隊無任何關係。\n"
            "本程式僅供學術研究及個人學習用途，禁止用於任何商業用途。\n"
            "使用本程式所造成的一切後果，作者不負任何責任。"
        )
        licenseFont = QFont()
        licenseFont.setPointSize(10)
        licenseLabel.setFont(licenseFont)
        licenseLabel.setAlignment(Qt.AlignLeft)
        licenseLabel.setWordWrap(True)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(descriptionLabel)
        layout.addSpacing(10)
        layout.addWidget(authorLabel)
        layout.addSpacing(15)
        layout.addWidget(licenseLabel)
