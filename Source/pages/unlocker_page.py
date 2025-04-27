from qfluentwidgets import PrimaryPushButton, HeaderCardWidget, BodyLabel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import subprocess
import os

class UnlockerPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("unlockerPage")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        titleLabel = QLabel("解鎖工具")
        titleFont = QFont()
        titleFont.setPointSize(20)
        titleFont.setBold(True)
        titleLabel.setFont(titleFont)
        titleLabel.setAlignment(Qt.AlignLeft)

        unlockerButton = PrimaryPushButton("啟動 Unlocker")
        unlockerButton.clicked.connect(self.launch_unlocker)

        notice = HeaderCardWidget()
        notice.setTitle("警告")
        notice.infoLabel = BodyLabel("Unlocker並非由本人編寫，如有疑慮請勿使用。")
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
        layout.addWidget(unlockerButton)
        layout.addSpacing(10)
        layout.addWidget(notice)

    def launch_unlocker(self):
        unlocker_path = os.path.abspath("./extra/unlocker.exe")
        if os.path.exists(unlocker_path):
            try:
                subprocess.Popen(unlocker_path, shell=True)
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"啟動 Unlocker 時發生錯誤：\n{str(e)}")
        else:
            QMessageBox.warning(self, "找不到檔案", "找不到 unlocker.exe，請確認路徑是否正確。")
