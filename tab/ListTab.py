import os
import asyncio

from PySide6.QtCore import Qt, QObject, Signal, Slot, QThread
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QHeaderView,
    QAbstractItemView,
)
from qfluentwidgets import PushButton, PrimaryPushButton, FluentIcon
from PySide6.QtCore import QFile
from utils.metadata import Metadata
from utils import downloader as depot_downloader
from utils.workshop import WorkshopDownloader, WorkshopJob
from PySide6.QtWidgets import QGraphicsBlurEffect


class _MetadataFetchWorker(QObject):
    finished = Signal(str, str, str)  # name, size, app_id
    failed = Signal(str)         # error message

    def __init__(self, workshop_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._workshop_id = workshop_id

    @Slot()
    def run(self) -> None:
        try:
            metadata = Metadata()
            name, size, app_id = asyncio.run(metadata.getData(self._workshop_id))
            self.finished.emit(name, size, app_id)
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class _DownloadWorker(QObject):
    """Worker that runs a single Workshop download using WorkshopDownloader."""

    finished = Signal(bool, str)  # success, error message

    def __init__(self, app_id: str, workshop_id: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._app_id = app_id
        self._workshop_id = workshop_id

    @Slot()
    def run(self) -> None:
        try:
            downloader = WorkshopDownloader()
            job = WorkshopJob(app_id=self._app_id, pubfile_id=self._workshop_id)
            proc = downloader.run_job(job)

            completed_marker_found = False

            if proc.stdout is not None:
                for line in proc.stdout:
                    line = line.strip()
                    # Heuristic: consider download complete when Steam disconnects
                    # or when the total downloaded line appears.
                    if (
                        "Disconnected from Steam" in line
                        or line.startswith("Total downloaded:")
                    ):
                        completed_marker_found = True

            proc.wait()

            if proc.returncode != 0 and not completed_marker_found:
                raise RuntimeError(f"Process exited with code {proc.returncode}")

            self.finished.emit(True, "")
        except Exception as e:  # noqa: BLE001
            self.finished.emit(False, str(e))


class ListTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("listInterface")
        self._active_fetches: dict[int, tuple[QThread, _MetadataFetchWorker]] = {}
        self._download_queue: list[int] = []
        self._current_download: tuple[QThread, _DownloadWorker] | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        self.content_widget = QWidget(self)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(8)

        title = QLabel("Downloader", self.content_widget)
        title.setObjectName("ListTitle")
        qss_file = QFile("qss/tab/title.qss")
        if qss_file.open(QFile.ReadOnly | QFile.Text):
            title.setStyleSheet(bytes(qss_file.readAll()).decode("utf-8"))
            qss_file.close()

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.workshop_input = QLineEdit(self.content_widget)
        self.workshop_input.setPlaceholderText("Workshop ID")

        self.add_button = PrimaryPushButton(FluentIcon.ADD, "Add", self.content_widget)
        h = self.add_button.sizeHint().height()
        self.workshop_input.setFixedHeight(h)
        
        self.download_button = PushButton(FluentIcon.DOWNLOAD, "Download", self.content_widget)
        self.download_button.setToolTip("Download Files")
        
        controls_layout.addWidget(self.workshop_input, 1)
        controls_layout.addWidget(self.add_button)
        controls_layout.addWidget(self.download_button)
        self.list_widget = QTableWidget(self.content_widget)
        self.list_widget.verticalHeader().setVisible(False)
        self.list_widget.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.list_widget.setShowGrid(False)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.list_widget.setColumnCount(7)
        self.list_widget.setHorizontalHeaderLabels([
            "No",
            "Workshop ID",
            "Workshop Name",
            "Size",
            "App ID",
            "Status",
            "Action",
        ])

        header = self.list_widget.horizontalHeader()
        
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)

        self.list_widget.setColumnWidth(0, 50)
        self.list_widget.setColumnWidth(1, 125)
        self.list_widget.setColumnWidth(3, 100)
        self.list_widget.setColumnWidth(4, 100)
        self.list_widget.setColumnWidth(5, 100)
        self.list_widget.setColumnWidth(6, 100)

        content_layout.addWidget(title)
        content_layout.addLayout(controls_layout)
        content_layout.addWidget(self.list_widget)

        layout.addWidget(self.content_widget)
        self.add_button.clicked.connect(self.add_workshop)
        self.download_button.clicked.connect(self.start_download_queue)

        self._blur_effect = QGraphicsBlurEffect(self.content_widget)
        self._blur_effect.setBlurRadius(15)

        self.lock_overlay = QWidget(self)
        self.lock_overlay.hide()
        self.lock_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 160);")

        overlay_layout = QVBoxLayout(self.lock_overlay)
        overlay_layout.setContentsMargins(24, 24, 24, 24)
        overlay_layout.setAlignment(Qt.AlignCenter)

        lock_label = QLabel(
            "DepotDownloaderMod tidak ada\n"
            "silakan ikuti panduan di Tab Home",
            self.lock_overlay,
        )
        lock_label.setWordWrap(True)
        lock_label.setAlignment(Qt.AlignCenter)
        lock_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: 500;"
        )

        overlay_layout.addWidget(lock_label)
        depot_exe_path = self._get_depot_exe_path()
        self._set_locked(not os.path.exists(depot_exe_path))

    def add_workshop(self):
        workshop_id = self.workshop_input.text().strip()
        if not workshop_id:
            return

        if self.lock_overlay.isVisible():
            return

        # default value fbefore metadata fetched
        name_text = "Loading..."
        size_text = "Loading..."

        row_number = self.list_widget.rowCount() + 1
        row = self.list_widget.rowCount()
        self.list_widget.insertRow(row)

        no_item = QTableWidgetItem(str(row_number))
        no_item.setFlags(no_item.flags() & ~Qt.ItemIsEditable)
        self.list_widget.setItem(row, 0, no_item)

        id_item = QTableWidgetItem(workshop_id)
        self.list_widget.setItem(row, 1, id_item)

        name_item = QTableWidgetItem(name_text)
        self.list_widget.setItem(row, 2, name_item)

        size_item = QTableWidgetItem(size_text)
        self.list_widget.setItem(row, 3, size_item)
        
        app_item = QTableWidgetItem("Loading...")
        self.list_widget.setItem(row, 4, app_item)

        status_item = QTableWidgetItem("Loading...")
        self.list_widget.setItem(row, 5, status_item)

        no_item.setTextAlignment(Qt.AlignCenter)
        id_item.setTextAlignment(Qt.AlignCenter)
        name_item.setTextAlignment(Qt.AlignCenter)
        status_item.setTextAlignment(Qt.AlignCenter)
        size_item.setTextAlignment(Qt.AlignCenter)
        app_item.setTextAlignment(Qt.AlignCenter)

        delete_button = PushButton(FluentIcon.DELETE, "Delete", self.list_widget)
        delete_button.setToolTip("Hapus baris ini")
        self.list_widget.setCellWidget(row, 6, delete_button)

        delete_button.clicked.connect(self.handle_delete_clicked)
        self.workshop_input.clear()
        self._start_metadata_fetch(workshop_id, row)

    def handle_delete_clicked(self):
        button = self.sender()
        if not button:
            return

        for row in range(self.list_widget.rowCount()):
            if self.list_widget.cellWidget(row, 6) is button:
                self.remove_row(row)
                break

    def remove_row(self, row: int):
        if row < 0 or row >= self.list_widget.rowCount():
            return

        self.list_widget.removeRow(row)
        self.renumber_rows()

    def renumber_rows(self):
        for i in range(self.list_widget.rowCount()):
            item = self.list_widget.item(i, 0)
            if item is not None:
                item.setText(str(i + 1))

    # ==== Metadata Request ==================================================
    def _start_metadata_fetch(self, workshop_id: str, row: int) -> None:
        thread = QThread(self)
        worker = _MetadataFetchWorker(workshop_id)
        worker.moveToThread(thread)
        self._active_fetches[row] = (thread, worker)
        thread.started.connect(worker.run)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)

        worker.finished.connect(
            lambda name, size, app_id, wid=workshop_id, r=row: self._handle_metadata_success(
                r, wid, name, size, app_id
            )
        )
        worker.failed.connect(
            lambda error, wid=workshop_id, r=row: self._handle_metadata_error(r, wid, error)
        )

        thread.start()

    # ==== Download Queue =====================================================

    def start_download_queue(self) -> None:
        """Build a queue from rows and start downloading sequentially."""

        if self.lock_overlay.isVisible():
            return

        # If already downloading, do nothing
        if self._current_download is not None:
            return

        self._download_queue.clear()

        for row in range(self.list_widget.rowCount()):
            status_item = self.list_widget.item(row, 5)
            if status_item is None:
                continue

            status_text = status_item.text()
            if status_text in ("Ready", "Error", "Queue"):
                self._download_queue.append(row)
                status_item.setText("Queue")

        if not self._download_queue:
            return

        self._start_next_download()

    def _start_next_download(self) -> None:
        if not self._download_queue:
            self._current_download = None
            return

        row = self._download_queue.pop(0)
        if row < 0 or row >= self.list_widget.rowCount():
            self._start_next_download()
            return

        app_item = self.list_widget.item(row, 4)
        id_item = self.list_widget.item(row, 1)
        status_item = self.list_widget.item(row, 5)

        if not (app_item and id_item and status_item):
            self._start_next_download()
            return

        app_id = (app_item.text() or "").strip()
        workshop_id = (id_item.text() or "").strip()

        if not app_id or app_id == "None" or not workshop_id:
            status_item.setText("Error")
            self._start_next_download()
            return

        status_item.setText("Process")

        thread = QThread(self)
        worker = _DownloadWorker(app_id, workshop_id)
        worker.moveToThread(thread)

        self._current_download = (thread, worker)

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(worker.deleteLater)

        # Capture row in lambda so we know which row to update
        worker.finished.connect(
            lambda success, error, r=row: self._handle_download_finished(
                r, success, error
            )
        )

        thread.start()

    def _handle_download_finished(self, row: int, success: bool, error_message: str) -> None:
        self._current_download = None

        if row < 0 or row >= self.list_widget.rowCount():
            self._start_next_download()
            return

        status_item = self.list_widget.item(row, 5)
        if status_item is None:
            self._start_next_download()
            return

        if success:
            status_item.setText("Complete")
        else:
            status_item.setText("Error")

        self._start_next_download()

    def _set_locked(self, locked: bool) -> None:
        if locked:
            self.content_widget.setGraphicsEffect(self._blur_effect)
            self.workshop_input.setEnabled(False)
            self.add_button.setEnabled(False)
            self.download_button.setEnabled(False)
            self.lock_overlay.setGeometry(self.rect())
            self.lock_overlay.show()
            self.lock_overlay.raise_()
        else:
            self.content_widget.setGraphicsEffect(None)
            self.workshop_input.setEnabled(True)
            self.add_button.setEnabled(True)
            self.download_button.setEnabled(True)
            self.lock_overlay.hide()

    def _get_depot_exe_path(self) -> str:
        project_root = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(
            project_root,
            depot_downloader.INSTALL_DIR_NAME,
            depot_downloader.EXE_NAME,
        )

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)

        depot_exe_path = self._get_depot_exe_path()
        self._set_locked(not os.path.exists(depot_exe_path))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if hasattr(self, "lock_overlay"):
            self.lock_overlay.setGeometry(self.rect())

    def _handle_metadata_success(
        self,
        row: int,
        workshop_id: str,
        name: str,
        size: str,
        app_id: str,
    ) -> None:
        self._active_fetches.pop(row, None)
        if row < 0 or row >= self.list_widget.rowCount():
            return

        id_item = self.list_widget.item(row, 1)
        if id_item is None or id_item.text() != workshop_id:
            return

        name_item = self.list_widget.item(row, 2)
        size_item = self.list_widget.item(row, 3)
        app_item = self.list_widget.item(row, 4)
        status_item = self.list_widget.item(row, 5)

        if not (name_item and size_item and app_item and status_item):
            return

        name_item.setText(name or "None")
        size_item.setText(size or "0MB")
        app_item.setText(app_id or "None")
        status_item.setText("Ready")

    def _handle_metadata_error(
        self,
        row: int,
        workshop_id: str,
        error_message: str,
    ) -> None:
        self._active_fetches.pop(row, None)

        if row < 0 or row >= self.list_widget.rowCount():
            return

        id_item = self.list_widget.item(row, 1)
        if id_item is None or id_item.text() != workshop_id:
            return

        name_item = self.list_widget.item(row, 2)
        size_item = self.list_widget.item(row, 3)
        app_item = self.list_widget.item(row, 4)
        status_item = self.list_widget.item(row, 5)

        if not (name_item and size_item and app_item and status_item):
            return

        if name_item.text() == "Loading...":
            name_item.setText("None")
        if size_item.text() == "Loading...":
            size_item.setText("0MB")
        if app_item.text() == "Loading...":
            app_item.setText("None")

        status_item.setText("Error")

    def _find_row_by_workshop_id(self, workshop_id: str) -> int | None:
        for row in range(self.list_widget.rowCount()):
            item = self.list_widget.item(row, 1)
            if item is not None and item.text() == workshop_id:
                return row
        return None
