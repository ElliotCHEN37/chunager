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
from pages.setting_page import SettingPage
from pages.about_page import AboutPage

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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

        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
        else:
            app_dir = os.path.abspath(os.path.dirname(__file__))

        config_path = os.path.join(app_dir, "config.ini")

        if not os.path.exists(config_path):
            config["GENERAL"] = {
                "segatools_path": ""
            }
            config["DISPLAY"] = {
                "theme": "AUTO"
            }
            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
            print(f"已建立預設 config.ini：{config_path}")
        else:
            config.read(config_path, encoding="utf-8")

        self.config_path = config_path
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
            "首頁": (HomePage(), QIcon(resource_path("img/home.svg")), NavigationItemPosition.TOP),
            "OPT": (OptPage(), QIcon(resource_path("img/opt.svg")), NavigationItemPosition.TOP),
            "樂曲": (MusicPage(), QIcon(resource_path("img/music.svg")), NavigationItemPosition.TOP),
            "角色": (CharacterPage(), QIcon(resource_path("img/character.svg")), NavigationItemPosition.TOP),
            "解鎖": (UnlockerPage(), QIcon(resource_path("img/unlock.svg")), NavigationItemPosition.TOP),
            "補丁": (PatcherPage(), QIcon(resource_path("img/pill.svg")), NavigationItemPosition.TOP),
            "PERFORMAI MANUAL": (PFMManualPage(), QIcon(resource_path("img/manual.svg")), NavigationItemPosition.TOP),
            "設定": (SettingPage(), QIcon(resource_path("img/setting.svg")), NavigationItemPosition.BOTTOM),
            "關於": (AboutPage(), QIcon(resource_path("img/info.svg")), NavigationItemPosition.BOTTOM)
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
