import os
import asyncio

from PySide6.QtCore import Qt, QFile, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from qfluentwidgets import PrimaryPushButton, PushButton, FluentIcon

from utils import downloader as depot_downloader


class HomeTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("homeInterface")

        root_layout = QVBoxLayout(self)
        root_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(8)

        title = QLabel("Home", self)
        title.setObjectName("HomeTitle")

        qss_file = QFile("qss/tab/title.qss")
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            title.setStyleSheet(bytes(qss_file.readAll()).decode("utf-8"))
            qss_file.close()

        subtitle = QLabel(
            "A simple Steam Workshop downloader with "
            "DepotDownloaderMod integration.",
            self,
        )
        subtitle.setObjectName("HomeSubtitle")
        subtitle.setWordWrap(True)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(24)

        info_frame = QFrame(self)
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setObjectName("HomeInfoCard")

        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 16, 16, 16)
        info_layout.setSpacing(6)

        info_title = QLabel("How to use", info_frame)
        info_title.setObjectName("HomeSectionTitle")

        info_text = QLabel(
            "1. Open the Downloader tab.\n"
            "2. Enter the Workshop ID.\n"
            "3. Click Add and wait for the metadata to load.\n"
            "4. Click Download to fetch the files.",
            info_frame,
        )
        info_text.setWordWrap(True)

        tips_title = QLabel("Tips", info_frame)
        tips_title.setObjectName("HomeSectionTitle")

        tips_text = QLabel(
            "• Make sure your internet connection is stable during downloads.\n"
            "• Once DepotDownloaderMod is installed, the Downloader tab will be ready to use.\n"
            "• You can remove and re-add Workshop items at any time.",
            info_frame,
        )
        tips_text.setWordWrap(True)

        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)
        info_layout.addSpacing(8)
        info_layout.addWidget(tips_title)
        info_layout.addWidget(tips_text)
        info_layout.addStretch(1)

        actions_frame = QFrame(self)
        actions_frame.setFrameShape(QFrame.StyledPanel)
        actions_frame.setObjectName("HomeActionsCard")

        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(16, 16, 16, 16)
        actions_layout.setSpacing(12)

        actions_title = QLabel("DepotDownloaderMod", actions_frame)
        actions_title.setObjectName("HomeSectionTitle")

        desc_label = QLabel(
            "An external component used to download Steam Workshop content. "
            "This app will download and install the latest version for you.",
            actions_frame,
        )
        desc_label.setWordWrap(True)

        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        self.depot_status_icon = QLabel("●", actions_frame)
        self.depot_status_icon.setFixedWidth(12)

        self.depot_status_text = QLabel("", actions_frame)
        self.depot_status_text.setWordWrap(True)

        status_layout.addWidget(self.depot_status_icon)
        status_layout.addWidget(self.depot_status_text, 1)

        open_downloader_btn = PrimaryPushButton(
            FluentIcon.DOWNLOAD, "Download", actions_frame
        )
        open_downloader_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        check_update_btn = PushButton(
            FluentIcon.SYNC, "Refresh Status", actions_frame
        )
        check_update_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        open_settings_btn = PushButton(
            FluentIcon.SETTING, "Open Settings tab", actions_frame
        )
        open_settings_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        open_install_dir_btn = PushButton(
            FluentIcon.FOLDER, "Open Mod Folder", actions_frame
        )
        open_install_dir_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        actions_layout.addWidget(actions_title)
        actions_layout.addWidget(desc_label)
        actions_layout.addLayout(status_layout)
        actions_layout.addWidget(open_downloader_btn)
        actions_layout.addWidget(check_update_btn)
        actions_layout.addWidget(open_settings_btn)
        actions_layout.addWidget(open_install_dir_btn)
        actions_layout.addStretch(1)

        content_layout.addWidget(info_frame, 2)
        content_layout.addWidget(actions_frame, 1)

        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)
        root_layout.addLayout(content_layout)

        self._update_depot_status()
        open_downloader_btn.clicked.connect(self._on_download_depot_clicked)
        check_update_btn.clicked.connect(self._on_check_update_clicked)
        open_install_dir_btn.clicked.connect(self._on_open_dir_clicked)

    def _get_depot_exe_path(self) -> str:
        """Return path to DepotDownloaderMod.exe next to the app/.exe.

        Uses the same logic as utils.downloader so that when the app is
        packaged (PyInstaller), the DepotDownloaderMod folder is created
        in the same directory as the bundled .exe.
        """

        install_dir = depot_downloader.get_install_dir()
        return str(install_dir / depot_downloader.EXE_NAME)

    def _get_depot_version(self) -> str | None:
        install_dir = os.path.dirname(self._get_depot_exe_path())
        version_file = os.path.join(install_dir, "version.txt")
        if not os.path.isfile(version_file):
            return None

        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip() or None
        except OSError:
            return None

    def _update_depot_status(self) -> None:
        exists = os.path.exists(self._get_depot_exe_path())
        if exists:
            version = self._get_depot_version()
            self.depot_status_icon.setStyleSheet(
                "color: #27ae60; font-size: 14px;"
            )
            if version:
                self.depot_status_text.setText(
                    f"DepotDownloaderMod installed (v{version}). Ready to use in the Downloader tab."
                )
            else:
                self.depot_status_text.setText(
                    "DepotDownloaderMod installed. Ready to use in the Downloader tab."
                )
        else:
            self.depot_status_icon.setStyleSheet(
                "color: #e74c3c; font-size: 14px;"
            )
            self.depot_status_text.setText(
                "DepotDownloaderMod is not installed. Press the \"Download & Install\" button "
                "to download the latest version."
            )

    def _on_download_depot_clicked(self) -> None:
        self.depot_status_text.setText(
            "Downloading and installing the latest version of DepotDownloaderMod..."
        )

        try:
            asyncio.run(depot_downloader.download_and_install())
        except Exception as e:  # noqa: BLE001
            self.depot_status_text.setText(
                f"Failed to download DepotDownloaderMod: {e}"
            )
            self._update_depot_status()
            return

        self._update_depot_status()

    def _on_check_update_clicked(self) -> None:
        self._update_depot_status()

    def _on_open_dir_clicked(self) -> None:
        exe_path = self._get_depot_exe_path()
        install_dir = os.path.dirname(exe_path)
        depots_dir = os.path.join(install_dir, "depots")

        if not os.path.isdir(depots_dir):
            try:
                os.makedirs(depots_dir, exist_ok=True)
            except OSError:
                depots_dir = install_dir

        QDesktopServices.openUrl(QUrl.fromLocalFile(depots_dir))
