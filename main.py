import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QApplication
from qfluentwidgets import (
    StyleSheetBase,
    Theme,
    qconfig,
    FluentWindow,
    setTheme,
    FluentIcon,
    SubtitleLabel,
    NavigationItemPosition,
)
from enum import Enum

from tab.HomeTab import HomeTab
from tab.ListTab import ListTab
from tab.SettingsTab import SettingsTab


class StyleSheet(StyleSheetBase, Enum):
    WINDOW = "window"
    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"qss/{theme.value.lower()}/{self.value}.qss"

class Window(FluentWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("Window")
        self.setWindowTitle("PyShopDL")

        self.home_tab = HomeTab(self)
        self.list_tab = ListTab(self)
        self.settings_tab = SettingsTab(self)

        self.addSubInterface(
            self.home_tab,
            icon=FluentIcon.HOME.icon(Theme.AUTO),
            text="Home",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.list_tab,
            icon=FluentIcon.LIBRARY.icon(Theme.AUTO),
            text="Downloader",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self.settings_tab,
            icon=FluentIcon.SETTING.icon(Theme.AUTO),
            text="Settings",
            position=NavigationItemPosition.BOTTOM,
        )

        StyleSheet.WINDOW.apply(self)
        qconfig.themeChangedFinished.connect(lambda: StyleSheet.WINDOW.apply(self))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    setTheme(Theme.AUTO)

    window = Window()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())
    
# SteamDepotDownloader> .\DepotDownloaderMod.exe -app 294100 -pubfile 2222935097