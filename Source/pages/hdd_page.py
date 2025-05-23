import os
import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import PrimaryPushButton, HeaderCardWidget, BodyLabel, LargeTitleLabel, IconWidget

def get_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class HDDPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("hddPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = LargeTitleLabel(self.tr("下載"))
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        openButton = PrimaryPushButton(QIcon(get_path("img/web.svg")), self.tr("打開 Evil Leaker Data Center"))
        openButton.clicked.connect(self.open_manual)

        notice = HeaderCardWidget()

        notice.setTitle(self.tr("注意"))
        notice.ErrorIcon = IconWidget(QIcon(get_path("img/error.svg")))
        notice.infoLabel = BodyLabel(self.tr("注意控制台輸出"))

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
        QMessageBox.information(self, self.tr("已加密"), self.tr("使用Base64解密兩次即可"))
        print("YUhSMGNITTZMeTl3WlhKbWIzSnRZV2t1WlhacGJHeGxZV3RsY2k1amIyMHZaR0YwWVdObGJuUmxjaTl6Wkdoa0xtaDBiV3c9")
