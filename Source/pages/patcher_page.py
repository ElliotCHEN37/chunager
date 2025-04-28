from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from qfluentwidgets import PrimaryPushButton, HeaderCardWidget, BodyLabel
import webbrowser

class PatcherPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("patcherPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = QLabel("補丁管理")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        openButton = PrimaryPushButton(QIcon("./img/web.svg"), "打開 CHUNITHM VERSE Modder")
        openButton.clicked.connect(self.open_manual)

        notice = HeaderCardWidget()
        notice.setTitle("WOOPS")
        notice.infoLabel = BodyLabel("由於某些技術原因，暫時不支援內嵌網站")
        notice.vBoxLayout = QVBoxLayout()
        notice.hBoxLayout = QHBoxLayout()
        notice.hBoxLayout.setSpacing(10)
        notice.vBoxLayout.setSpacing(16)
        notice.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        notice.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        notice.hBoxLayout.addWidget(notice.infoLabel)
        notice.vBoxLayout.addLayout(notice.hBoxLayout)
        notice.viewLayout.addLayout(notice.vBoxLayout)

        layout.addWidget(titleLabel)
        layout.addSpacing(10)
        layout.addWidget(openButton)
        layout.addSpacing(10)
        layout.addWidget(notice)

    def open_manual(self):
        webbrowser.open("https://performai.evilleaker.com/patcher/chusanvrs.html")
