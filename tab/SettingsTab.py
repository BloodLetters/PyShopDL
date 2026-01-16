from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox
from PySide6.QtCore import QFile

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        title = QLabel("Settings", self)
        title.setObjectName("SettingsTitle")
        qss_file = QFile("qss/tab/title.qss")
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            title.setStyleSheet(bytes(qss_file.readAll()).decode("utf-8"))
            qss_file.close()


        checkbox1 = QCheckBox("Enable dummy option 1", self)
        checkbox2 = QCheckBox("Enable dummy option 2", self)

        layout.addWidget(title)
        layout.addWidget(checkbox1)
        layout.addWidget(checkbox2)
