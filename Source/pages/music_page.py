from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MusicPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("musicPage")
        layout = QVBoxLayout(self)
        label = QLabel("音樂管理", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)