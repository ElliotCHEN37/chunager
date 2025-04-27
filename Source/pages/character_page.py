from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class CharacterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("characterPage")
        layout = QVBoxLayout(self)
        label = QLabel("角色管理", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)