from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class AboutPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("aboutPage")
        layout = QVBoxLayout(self)
        label = QLabel("關於 CHUNAGER", self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)