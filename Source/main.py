import os
import sys
import configparser
import winreg
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt, QTranslator
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

def get_path(rel_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base, rel_path)

def is_dark_mode() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        return False


def svg_to_icon(path: str, color: str) -> QIcon:
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
        self.setWindowIcon(QIcon(get_path("icon.ico")))
        self.setWindowTitle("CHUNAGER")
        self.resize(1000, 750)

        self.config = self.load_config()
        self.apply_theme()
        self.setup_pages()
        self.setup_nav()

    def load_config(self):
        config = configparser.ConfigParser()
        app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(
            os.path.dirname(__file__))
        config_path = os.path.join(app_dir, "config.ini")

        if not os.path.exists(config_path):
            config["GENERAL"] = {"segatools_path": ""}
            config["DISPLAY"] = {"theme": "AUTO"}
            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
        else:
            config.read(config_path, encoding="utf-8")

        self.config_path = config_path
        return config

    def apply_theme(self):
        theme_setting = self.config.get("DISPLAY", "theme", fallback="AUTO").upper()
        use_dark = is_dark_mode() if theme_setting == "AUTO" else theme_setting == "DARK"

        self.theme_color = "#e3e3e3" if use_dark else "#000000"
        setTheme(Theme.DARK if use_dark else Theme.LIGHT)

    def get_icon(self, name: str) -> QIcon:
        return svg_to_icon(get_path(f"img/{name}.svg"), self.theme_color)

    def setup_pages(self):
        self.pages = {
            self.tr("首頁"): (HomePage(), self.get_icon("home"), NavigationItemPosition.TOP),
            self.tr("OPT"): (OptPage(), self.get_icon("opt"), NavigationItemPosition.TOP),
            self.tr("樂曲"): (MusicPage(), self.get_icon("music"), NavigationItemPosition.TOP),
            self.tr("角色"): (CharacterPage(), self.get_icon("character"), NavigationItemPosition.TOP),
            self.tr("解鎖"): (UnlockerPage(), self.get_icon("unlock"), NavigationItemPosition.TOP),
            self.tr("補丁"): (PatcherPage(), self.get_icon("pill"), NavigationItemPosition.TOP),
            self.tr("手冊"): (PFMManualPage(), self.get_icon("manual"), NavigationItemPosition.TOP),
            self.tr("設定"): (SettingPage(), self.get_icon("setting"), NavigationItemPosition.BOTTOM),
            self.tr("關於"): (AboutPage(), self.get_icon("info"), NavigationItemPosition.BOTTOM)
        }

    def setup_nav(self):
        for name, (page, icon, position) in self.pages.items():
            self.addSubInterface(page, icon, name, position)
        self.navigationInterface.setCurrentItem("首頁")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    translator = QTranslator()
    config = configparser.ConfigParser()
    app_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(app_dir, "config.ini")
    config.read(config_path, encoding="utf-8")

    qm_path = config.get("DISPLAY", "translation_path", fallback="")
    if os.path.isfile(qm_path):
        if translator.load(qm_path):
            app.installTranslator(translator)
        else:
            print(f"can not load translation：{qm_path}")
    else:
        print("translation not exist")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
