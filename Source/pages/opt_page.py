from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class OptPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("optPage")
        layout = QVBoxLayout(self)
        label = QLabel("OPT 管理", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)