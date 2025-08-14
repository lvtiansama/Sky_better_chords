# coding:utf-8
from PyQt6.QtWidgets import QWidget
from ui.about import Ui_about


class InfoInterface(Ui_about, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self, parent)
