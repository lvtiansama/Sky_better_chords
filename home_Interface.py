# coding:utf-8
from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

from ui.home import Ui_home
from backend.backend import KeyboardMonitor

_translate = QtCore.QCoreApplication.translate

class HomeInterface(Ui_home, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent
        self.setupUi(self, parent)
        self.pushButton.checkedChanged.connect(self.on_switch_checked_changed)
        self.km = KeyboardMonitor()

    def update_display(self,bool=False):
        # 更新信息到gui界面
        self.connection_status.setText(_translate("home", f"{self._parent.find_bool_str}"))
        self.windows_title_name.setText(_translate("home", f"{self._parent.title}"))
        self.hwnd_id.setText(_translate("home", f"{self._parent.hWnd_id}"))
        self.pid_id.setText(_translate("home", f"{self._parent.pid_id}"))
        if bool == True:
            self.pushButton.setChecked(False)

    def pushButtonoffinfo(self):
        InfoBar.warning(
            title=_translate("home", "提示"),
            content=_translate("home", "映射已被关闭"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )
    def pushButtononinfo(self):
        InfoBar.info(
            title=_translate("home", "提示"),
            content=_translate("home", "映射已启动，可使用ctrl+c快捷关闭"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self
        )

    @pyqtSlot(bool)
    def on_switch_checked_changed(self, checked: bool):
        if checked:
            self.km.start()
            self.pushButtononinfo()
        else:
            self.km.stop()
            self.pushButtonoffinfo()