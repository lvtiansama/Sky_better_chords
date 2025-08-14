# coding:utf-8
import sys
import threading
import appdirs
import os

import win32process

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, toggleTheme, setThemeColor)
from qfluentwidgets import FluentIcon as FIF

from function import get_resource_path
from home_Interface import HomeInterface
from setting_Interface import SettingInterface
from info_Interface import InfoInterface

from backend.global_variable import GlobalVariable
from backend.hwnd_check_thread import start_thread as hwnd_check_thread, cpu_check


_translate = QtCore.QCoreApplication.translate

Version = '1.0000'
app_name = "Sky_better_chords"
app_author = "Lvtiansama"
# 获取用户缓存目录
cache_dir = appdirs.user_data_dir(appname=app_name, appauthor=app_author)
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(MSFluentWindow):

    def __init__(self):
        super().__init__()

        self.version = Version
        self.app_name = app_name

        from config import global_keydist_realtime
        self.keydist = global_keydist_realtime

        self.hWnd_id = None
        self.title = None
        self.pid_id = None
        self.find_bool_str =_translate("main", '未找到目标进程')
        self.Backend_status = False

        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.settingInterface = SettingInterface(self)
        self.infoInterface = InfoInterface(self)

        self.hwnd_timer = QTimer(self)
        self.hwnd_timer.timeout.connect(self.hwnd_update)
        self.hwnd_timer.start(2000)

        self.initNavigation()
        self.initWindow()

    def hwnd_update(self):
        old_values = {
            'hWnd_id': self.hWnd_id,
            'title': self.title,
            'find_bool_str': self.find_bool_str,
            'pid_id': self.pid_id,
            'Backend_status': self.Backend_status
        }
        self.hWnd_id = GlobalVariable.window["hWnd"]
        self.title = GlobalVariable.hwnd_title
        self.Backend_status = GlobalVariable.Backend_status
        if self.hWnd_id is not None:
            _, self.pid_id = win32process.GetWindowThreadProcessId(self.hWnd_id)
        else:
            self.pid_id = None
        if GlobalVariable.find_bool is True:
            self.find_bool_str = _translate("main", '已连接到目标')
        else:
            self.find_bool_str = _translate("main", '未找到目标进程')
        if (old_values['hWnd_id'] != self.hWnd_id or
                old_values['title'] != self.title or
                old_values['find_bool_str'] != self.find_bool_str or
                old_values['pid_id'] != self.pid_id):
            self.homeInterface.update_display()
        if old_values['Backend_status'] == True and self.Backend_status == False:
            self.homeInterface.update_display(True)



    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, _translate("main", '主页'), FIF.HOME_FILL)
        self.addSubInterface(self.settingInterface, FIF.SETTING, _translate("main", '设置'), FIF.SETTING)

        self.addSubInterface(self.infoInterface, FIF.INFO, _translate("main", '关于'), FIF.INFO, NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(
            routeKey='Light',
            icon=FIF.CONSTRACT,
            text=_translate("main", '灯泡'),
            onClick=self.Light_bulb,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1000, 600)
        self.setWindowIcon(QIcon(get_resource_path('icon.ico')))
        self.setWindowTitle(app_name)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def Light_bulb(self):
        toggleTheme()


if __name__ == '__main__':
    setTheme(Theme.AUTO)
    setThemeColor('#8569BE')

    cpu_check() # 获取cpu配置

    # 获取目标进程
    hwnd_thread = threading.Thread(target=hwnd_check_thread)
    hwnd_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    hwnd_thread.start()

    app = QApplication(sys.argv)
    w = Window()
    w.show()

    app.exec()
