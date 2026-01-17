import json
from pathlib import Path

from PySide6.QtCore import Qt, QFile
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QFrame,
)

from utils.config import Config
from utils.loader import loader

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsInterface")
        self.config_path = Path("config.json")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- Main settings panel ---
        panel = QFrame(self)
        panel.setObjectName("SettingsPanel")
        panel.setFrameShape(QFrame.StyledPanel)
        panel.setFrameShadow(QFrame.Raised)

        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(12)

        title = QLabel("Settings", panel)
        title.setObjectName("SettingsTitle")
        qss_file = QFile("qss/tab/title.qss")
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            title.setStyleSheet(bytes(qss_file.readAll()).decode("utf-8"))
            qss_file.close()

        self.auto_rename_checkbox = QCheckBox("Auto rename folder to mod name", panel)

        account_layout = QHBoxLayout()
        account_label = QLabel("Account", self)
        account_label.setObjectName("AccountLabel")

        self.account_combo = QComboBox(panel)
        try:
            accounts = loader().accounts
        except Exception:
            accounts = []

        for acc in accounts:
            self.account_combo.addItem(str(acc))

        account_layout.addWidget(account_label)
        account_layout.addWidget(self.account_combo)
        account_layout.addStretch()

        panel_layout.addWidget(title)
        panel_layout.addWidget(self.auto_rename_checkbox)
        panel_layout.addLayout(account_layout)

        # --- Bottom bar with Save button ---
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        save_button = QPushButton("Save", self)
        save_button.setObjectName("SettingsSaveButton")
        save_button.clicked.connect(self.save_settings)
        bottom_bar.addWidget(save_button)

        layout.addWidget(panel)
        layout.addLayout(bottom_bar)
        self.load_settings()

    # --- Config handling ---
    def load_settings(self):
        if not self.config_path.exists():
            return

        auto_rename = Config().get("auto_rename", False)
        self.auto_rename_checkbox.setChecked(bool(auto_rename))

        selected_account = Config().get("account", "Anonymous")
        if selected_account is not None:
            index = self.account_combo.findText(str(selected_account))
            if index >= 0:
                self.account_combo.setCurrentIndex(index)

    def save_settings(self):
        config = {
            "auto_rename": self.auto_rename_checkbox.isChecked(),
            "account": self.account_combo.currentText() or None,
        }

        try:
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass

