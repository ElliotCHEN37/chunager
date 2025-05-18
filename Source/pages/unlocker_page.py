from qfluentwidgets import PrimaryPushButton, HeaderCardWidget, BodyLabel, LargeTitleLabel, IconWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
import subprocess
import os
import sys

def get_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

class UnlockerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("unlockerPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = LargeTitleLabel("解鎖工具")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        unlockerButton = PrimaryPushButton(QIcon(get_path("img/launch.svg")), "啟動 Unlocker")
        unlockerButton.clicked.connect(self.launch_unlocker)

        notice = HeaderCardWidget()

        notice.setTitle("警告")
        notice.ErrorIcon = IconWidget(QIcon(get_path("img/error.svg")))
        notice.infoLabel = BodyLabel("Unlocker 並非由本人編寫，如有疑慮請勿使用")

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
        layout.addWidget(unlockerButton)
        layout.addSpacing(10)
        layout.addWidget(notice)

    def launch_unlocker(self):
        unlocker_path = os.path.abspath(get_path("extra/unlocker.exe"))
        if os.path.exists(unlocker_path):
            try:
                subprocess.Popen(unlocker_path, shell=True)
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"啟動 Unlocker 時發生錯誤：\n{str(e)}")
        else:
            QMessageBox.warning(self, "找不到檔案", "找不到 unlocker.exe，請確認路徑是否正確。")
