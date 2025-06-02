import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import PrimaryPushButton, HeaderCardWidget, BodyLabel, LargeTitleLabel, IconWidget
import webbrowser

def get_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class PFMManualPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("pfmManualPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = LargeTitleLabel(self.tr("手冊"))
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        openButton = PrimaryPushButton(QIcon(get_path("img/web.svg")), self.tr("打開 PERFORMAI MANUAL"))
        openButton.clicked.connect(self.open_manual)

        notice = HeaderCardWidget()

        notice.setTitle(self.tr("注意"))
        notice.ErrorIcon = IconWidget(QIcon(get_path("img/error.svg")))
        notice.infoLabel = BodyLabel(self.tr("將打開外部連結"))

        notice.vBoxLayout = QVBoxLayout()
        notice.hBoxLayout = QHBoxLayout()

        notice.ErrorIcon.setFixedSize(16, 16)
        notice.hBoxLayout.setSpacing(10)
        notice.vBoxLayout.setSpacing(16)

        notice.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        notice.vBoxLayout.setContentsMargins(0, 0, 0, 0)

        notice.hBoxLayout.addWidget(notice.ErrorIcon)
        notice.hBoxLayout.addWidget(notice.infoLabel)
        notice.vBoxLayout.addLayout(notice.hBoxLayout)
        notice.viewLayout.addLayout(notice.vBoxLayout)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(openButton)
        layout.addSpacing(10)
        layout.addWidget(notice)

    def open_manual(self):
        webbrowser.open("https://performai.evilleaker.com/manual/")