import os
import sys
import configparser
import winreg
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt
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
from pages.hdd_page import HDDPage

def resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def is_system_dark_theme() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        return False

def load_colored_svg_icon(path: str, color: str) -> QIcon:
    with open(path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    svg_content = svg_content.replace("fill=\"#e3e3e3\"", f"fill=\"{color}\"")

    svg_bytes = QByteArray(svg_content.encode("utf-8"))
    renderer = QSvgRenderer(svg_bytes)
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    return QIcon(pixmap)

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
        app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))
        config_path = os.path.join(app_dir, "config.ini")

        if not os.path.exists(config_path):
            config["GENERAL"] = {"segatools_path": ""}
            config["DISPLAY"] = {"theme": "AUTO"}
            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
            print(f"已建立預設 config.ini：{config_path}")
        else:
            config.read(config_path, encoding="utf-8")

        self.config_path = config_path
        return config

    def setup_theme(self):
        theme_str = self.config.get("DISPLAY", "theme", fallback="AUTO").upper()
        if theme_str == "AUTO":
            is_dark = is_system_dark_theme()
            self.current_theme_color = "#e3e3e3" if is_dark else "#000000"
            setTheme(Theme.DARK if is_dark else Theme.LIGHT)
        else:
            is_dark = theme_str == "DARK"
            self.current_theme_color = "#e3e3e3" if is_dark else "#000000"
            setTheme(Theme.DARK if is_dark else Theme.LIGHT)

    def get_icon(self, name: str) -> QIcon:
        return load_colored_svg_icon(resource_path(f"img/{name}.svg"), self.current_theme_color)

    def init_pages(self):
        self.pages = {
            "首頁": (HomePage(), self.get_icon("home"), NavigationItemPosition.TOP),
            "OPT": (OptPage(), self.get_icon("opt"), NavigationItemPosition.TOP),
            "樂曲": (MusicPage(), self.get_icon("music"), NavigationItemPosition.TOP),
            "角色": (CharacterPage(), self.get_icon("character"), NavigationItemPosition.TOP),
            "下載": (HDDPage(), self.get_icon("download"), NavigationItemPosition.TOP),
            "解鎖": (UnlockerPage(), self.get_icon("unlock"), NavigationItemPosition.TOP),
            "補丁": (PatcherPage(), self.get_icon("pill"), NavigationItemPosition.TOP),
            "PERFORMAI MANUAL": (PFMManualPage(), self.get_icon("manual"), NavigationItemPosition.TOP),
            "設定": (SettingPage(), self.get_icon("setting"), NavigationItemPosition.BOTTOM),
            "關於": (AboutPage(), self.get_icon("info"), NavigationItemPosition.BOTTOM)
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
