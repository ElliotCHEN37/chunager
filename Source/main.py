from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentWindow, setTheme, Theme, NavigationItemPosition
import sys
from pages.home_page import HomePage
from pages.opt_page import OptPage
from pages.music_page import MusicPage
from pages.character_page import CharacterPage
from pages.unlocker_page import UnlockerPage
from pages.patcher_page import PatcherPage
from pages.pfm_manual_page import PFMManualPage
from pages.config_page import ConfigPage
from pages.about_page import AboutPage

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CHUNAGER")
        self.resize(1000, 750)

        setTheme(Theme.AUTO)

        self.homePage = HomePage()
        self.optPage = OptPage()
        self.musicPage = MusicPage()
        self.characterPage = CharacterPage()
        self.unlockerPage = UnlockerPage()
        self.patcherPage = PatcherPage()
        self.pfmManualPage = PFMManualPage()
        self.configPage = ConfigPage()
        self.aboutPage = AboutPage()

        self.initNavigation()

    def initNavigation(self):
        self.addSubInterface(self.homePage, QIcon("img/home.svg"), "首頁")
        self.addSubInterface(self.optPage, QIcon("img/opt.svg"), "OPT")
        self.addSubInterface(self.musicPage, QIcon("img/music.svg"), "樂曲")
        self.addSubInterface(self.characterPage, QIcon("img/character.svg"), "角色")
        self.addSubInterface(self.unlockerPage, QIcon("img/unlock.svg"), "解鎖")
        self.addSubInterface(self.patcherPage, QIcon("img/pill.svg"), "補丁")
        self.addSubInterface(self.pfmManualPage, QIcon("img/manual.svg"), "PERFORMAI MANUAL")
        self.addSubInterface(self.configPage, QIcon("img/setting.svg"), "設定", NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutPage, QIcon("img/info.svg"), "關於", NavigationItemPosition.BOTTOM)

        self.navigationInterface.setCurrentItem(self.homePage.objectName())

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
