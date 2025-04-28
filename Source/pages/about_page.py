from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from qfluentwidgets import LargeTitleLabel, StrongBodyLabel, CaptionLabel

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("aboutPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = LargeTitleLabel("關於 CHUNAGER")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        descriptionLabel = StrongBodyLabel(
            "CHUNAGER 是一款針對 CHUNITHM HDD (SDHD 2.30.00 VERSE)設計的管理工具\n"
            "提供歌曲管理、角色管理、OPT 管理、解鎖器、補丁管理等功能\n"
            "協助您更輕鬆地整理與優化遊戲內容"
        )
        descriptionFont = QFont()
        descriptionFont.setPointSize(12)
        descriptionLabel.setFont(descriptionFont)
        descriptionLabel.setAlignment(Qt.AlignLeft)
        descriptionLabel.setWordWrap(True)

        authorLabel = CaptionLabel(
            "作者：Elliot<br>"
            "版本：INTERNAL VERSION<br>"
            'GitHub：<a href="https://github.com/ElliotCHEN37/chunager">https://github.com/ElliotCHEN37/chunager</a>'
        )
        authorFont = QFont()
        authorFont.setPointSize(10)
        authorLabel.setFont(authorFont)
        authorLabel.setAlignment(Qt.AlignLeft)
        authorLabel.setWordWrap(True)
        authorLabel.setTextFormat(Qt.RichText)
        authorLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        authorLabel.setOpenExternalLinks(True)

        licenseLabel = CaptionLabel(
            "\n免責聲明：\n"
            "本程式為個人非官方開發，與 SEGA 及 CHUNITHM 官方團隊無任何關係。\n"
            '本程式使用MIT授權，詳見<a href="https://raw.githubusercontent.com/ElliotCHEN37/chunager/refs/heads/main/LICENSE.txt">許可證</a>。\n'
            "使用本程式所造成的一切後果，作者不負任何責任。"
        )
        licenseFont = QFont()
        licenseFont.setPointSize(10)
        licenseLabel.setFont(licenseFont)
        licenseLabel.setAlignment(Qt.AlignLeft)
        licenseLabel.setWordWrap(True)
        licenseLabel.setTextFormat(Qt.RichText)
        licenseLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        licenseLabel.setOpenExternalLinks(True)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(descriptionLabel)
        layout.addSpacing(15)
        layout.addWidget(authorLabel)
        layout.addSpacing(10)
        layout.addWidget(licenseLabel)
