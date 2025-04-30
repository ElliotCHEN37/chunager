import os
import sys
import configparser
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentWindow, setTheme, Theme, NavigationItemPosition
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

        self.config = self.load_config()
        self.setup_theme()
        self.init_pages()
        self.init_navigation()

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), ".", "config.ini")
        config.read(config_path)
        return config

    def setup_theme(self):
        theme = self.config.get("DISPLAY", "theme", fallback="AUTO").upper()
        theme_map = {
            "AUTO": Theme.AUTO,
            "LIGHT": Theme.LIGHT,
            "DARK": Theme.DARK
        }
        setTheme(theme_map.get(theme, Theme.AUTO))

    def init_pages(self):
        self.pages = {
            "首頁": (HomePage(), QIcon("./img/home.svg"), NavigationItemPosition.TOP),
            "OPT": (OptPage(), QIcon("./img/opt.svg"), NavigationItemPosition.TOP),
            "樂曲": (MusicPage(), QIcon("./img/music.svg"), NavigationItemPosition.TOP),
            "角色": (CharacterPage(), QIcon("./img/character.svg"), NavigationItemPosition.TOP),
            "解鎖": (UnlockerPage(), QIcon("./img/unlock.svg"), NavigationItemPosition.TOP),
            "補丁": (PatcherPage(), QIcon("./img/pill.svg"), NavigationItemPosition.TOP),
            "PERFORMAI MANUAL": (PFMManualPage(), QIcon("./img/manual.svg"), NavigationItemPosition.TOP),
            "設定": (ConfigPage(), QIcon("./img/setting.svg"), NavigationItemPosition.BOTTOM),
            "關於": (AboutPage(), QIcon("./img/info.svg"), NavigationItemPosition.BOTTOM)
        }

    def init_navigation(self):
        for name, (page, icon, position) in self.pages.items():
            self.addSubInterface(page, icon, name, position)

        self.navigationInterface.setCurrentItem("首頁")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
