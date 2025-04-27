from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ConfigPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("configPage")
        layout = QVBoxLayout(self)
        label = QLabel("設定", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)