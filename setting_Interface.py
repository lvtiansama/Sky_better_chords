# coding:utf-8
import json
import shutil
import appdirs
import os

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSlot, QEvent, Qt
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QKeySequence
from qfluentwidgets import MessageBox, InfoBar, InfoBarPosition

from function import get_resource_path
from ui.setting import Ui_setting

from backend.set_keyLayoutw import set_us_keyboard_layout, reset_keyboard_layout

_translate = QtCore.QCoreApplication.translate

app_name = "Sky_better_chords"
app_author = "Lvtiansama"
data_dir = os.path.join(appdirs.user_data_dir(appname=app_name, appauthor=app_author), "Key_config")
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
template_dir = get_resource_path('data/json/Key_config')

config_files = ["official.json", "piano.json", "user.json"]

for filename in config_files:
    dest_file = os.path.join(data_dir, filename)
    source_file = os.path.join(template_dir, filename)

    if not os.path.exists(dest_file):
        if os.path.exists(source_file):
            try:
                shutil.copy(source_file, dest_file)
                print(f"配置文件初始化成功: {filename}")
            except Exception as e:
                print(f"配置文件初始化失败 {filename}: {e}")
        else:
            print(f"错误！资源缺失: {source_file}")


class SettingInterface(Ui_setting, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent
        self.setupUi(self, parent)
        self.data_dir = data_dir

        # 连接信号
        # self.list.currentIndexChanged.connect(self.on_config_selected)
        self.list.activated.connect(self.on_config_selected)

        self.on_config_selected(0)  # 加载第一个配置

        # 所有文本框
        self.all_line_edits = [
            self.key1, self.key1_h, self.key1_hh,
            self.key2, self.key2_h,
            self.key3, self.key3_h,
            self.key4, self.key4_h,
            self.key5, self.key5_h,
            self.key6, self.key6_h,
            self.key7, self.key7_h,
            self.chord_1, self.chord_2, self.chord_3, self.chord_4, self.chord_5, self.chord_6
        ]

        # 为每个文本框设置事件
        for edit in self.all_line_edits:
            edit.original_value = ""  # 存储原始值
            edit.is_waiting_key = False  # 是否在等待按键

            def make_focus_in_handler(edit):
                def handler(event):
                    self.on_focus_in(event, edit)

                return handler

            def make_focus_out_handler(edit):
                def handler(event):
                    self.on_focus_out(event, edit)

                return handler

            edit.focusInEvent = make_focus_in_handler(edit)
            edit.focusOutEvent = make_focus_out_handler(edit)

        # 安装事件过滤器到每个文本框
        for edit in self.all_line_edits:
            edit.installEventFilter(self)

    def showEvent(self, event):
        # 显示setting时 关闭home的开关
        super().showEvent(event)  # 调用父类的 showEvent 以确保正常显示
        if self._parent.homeInterface.pushButton.isChecked():
            self._parent.homeInterface.pushButton.setChecked(False)
            self.pushButtonoffinfo()

    def pushButtonoffinfo(self):
        InfoBar.warning(
            title=_translate("setting", "提示"),
            content=_translate("setting", "映射已被关闭"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def eventFilter(self, obj, event):
        # 检查是否是键盘按下事件 且 对象是文本框 且 在等待按键状态
        if (event.type() == QEvent.Type.KeyPress and
                hasattr(obj, 'is_waiting_key') and
                obj.is_waiting_key):

            # 获取按键信息
            key = event.key()
            modifiers = event.modifiers()

            # 获取扫描码和虚拟键码
            scan_code = event.nativeScanCode()
            virtual_key = event.nativeVirtualKey()

            # 特殊键处理
            key_text = self.get_key_name(key, modifiers, scan_code, virtual_key)
            if key_text is False:
                obj.setText(_translate("setting", "不被支持的按键"))

            # 检查是否与其他文本框的值冲突
            current_values = [e.text() for e in self.all_line_edits if e != obj and not e.is_waiting_key]
            if key_text in current_values:
                obj.setText(_translate("setting", "键位冲突请重试"))
            else:
                obj.setText(key_text)
                self.get_keydist_realtime()
                obj.is_waiting_key = False
                obj.setReadOnly(False)  # 重新启用输入
                obj.clearFocus()  # 失去焦点
                reset_keyboard_layout()
            return True

        # 对于其他事件，正常处理
        return super().eventFilter(obj, event)

    def get_key_name(self, key, modifiers, scan_code, virtual_key):
        # 处理数字键盘
        if modifiers & Qt.KeyboardModifier.KeypadModifier:
            numpad_mapping = {
                Qt.Key.Key_0: "Num0",
                Qt.Key.Key_1: "Num1",
                Qt.Key.Key_2: "Num2",
                Qt.Key.Key_3: "Num3",
                Qt.Key.Key_4: "Num4",
                Qt.Key.Key_5: "Num5",
                Qt.Key.Key_6: "Num6",
                Qt.Key.Key_7: "Num7",
                Qt.Key.Key_8: "Num8",
                Qt.Key.Key_9: "Num9",
                Qt.Key.Key_Enter: "NumEnter",
                Qt.Key.Key_Plus: "Num+",
                Qt.Key.Key_Minus: "Num-",
                Qt.Key.Key_Asterisk: "Num*",
                Qt.Key.Key_Slash: "Num/",
                Qt.Key.Key_Period: "Num.",
                Qt.Key.Key_Comma: "Num,",
            }
            if key in numpad_mapping:
                return numpad_mapping[key]
        # 处理左右修饰键（通过扫描码区分）
        # Windows扫描码：左Shift=42, 右Shift=54, 左Ctrl=29, 右Ctrl=285, 左Alt=56, 右Alt=312
        if key == Qt.Key.Key_Shift:
            return "LShift" if scan_code == 42 else "RShift"
        elif key == Qt.Key.Key_Control:
            return "LCtrl" if scan_code == 29 else "RCtrl"
        elif key == Qt.Key.Key_Alt:
            return "LAlt" if scan_code == 56 else "RAlt"
        elif key == Qt.Key.Key_Meta:
            return "Win"
        # 处理其他特殊键
        special_mapping = {
            Qt.Key.Key_Print: "PrintScreen",
            Qt.Key.Key_ScrollLock: "ScrollLock",
            Qt.Key.Key_Pause: "Pause",
            Qt.Key.Key_Insert: "Insert",
            Qt.Key.Key_Home: "Home",
            Qt.Key.Key_PageUp: "PageUp",
            Qt.Key.Key_PageDown: "PageDown",
            Qt.Key.Key_End: "End",
            Qt.Key.Key_Delete: "Delete",
            Qt.Key.Key_NumLock: "NumLock",
            Qt.Key.Key_CapsLock: "CapsLock",
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Escape: "Esc",
            Qt.Key.Key_Space: "Space",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Right: "Right",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Down: "Down",
            Qt.Key.Key_Menu: "Menu",  # 上下文菜单键
            Qt.Key.Key_Help: "Help",
        }
        # F1-F24
        for i in range(1, 25):
            f_key = getattr(Qt.Key, f"Key_F{i}", None)
            if f_key and key == f_key:
                return f"F{i}"
        # 已知的特殊键
        if key in special_mapping:
            return special_mapping[key]

        # 处理组合键
        key_text = ""
        # if modifiers & Qt.KeyboardModifier.ControlModifier:
        #     key_text += "Ctrl+"
        # if modifiers & Qt.KeyboardModifier.AltModifier:
        #     key_text += "Alt+"
        # if modifiers & Qt.KeyboardModifier.ShiftModifier:
        #     key_text += "Shift+"
        # if modifiers & Qt.KeyboardModifier.MetaModifier:
        #     key_text += "Win+"
        # 产品逻辑不支持组合键！！！

        # 处理主按键
        if key >= Qt.Key.Key_A and key <= Qt.Key.Key_Z:
            key_text += chr(key - Qt.Key.Key_A + ord('A'))
        elif key >= Qt.Key.Key_0 and key <= Qt.Key.Key_9:
            key_text += chr(key - Qt.Key.Key_0 + ord('0'))
        else:
            # 尝试获取按键序列
            key_seq = QKeySequence(key)
            key_name = key_seq.toString()
            if key_name:
                key_text += key_name
            else:
                # 无法识别的键，使用虚拟键码
                # key_text += f"Key_{virtual_key}"
                # 没用 后端服务识别不了 没写这个功能qwq 返F要求重新输入
                return False
        return key_text

    def on_focus_in(self, event, edit):
        # 记录原始值
        edit.original_value = edit.text()
        # 设置等待状态
        edit.setText(_translate("setting", "请按任意键"))
        edit.is_waiting_key = True
        # 禁用输入功能
        edit.setReadOnly(True)
        # 设置美式键盘布局
        try:
            set_us_keyboard_layout()
        except Exception as e:
            print(f"设置键盘布局失败: {e}")
        super(type(edit), edit).focusInEvent(event)  # 调用原始focusInEvent

    def on_focus_out(self, event, edit):
        if edit.is_waiting_key:
            # 恢复原始值
            edit.setText(edit.original_value)
            edit.is_waiting_key = False
            # 重新启用输入功能
            edit.setReadOnly(False)
            # 设置中文键盘布局
            try:
                reset_keyboard_layout()
            except Exception as e:
                print(f"设置键盘布局失败: {e}")
        super(type(edit), edit).focusOutEvent(event)  # 调用原始focusOutEvent

    def msg(self, title, content, yesbutton):
        w = MessageBox(title, content, self.window())
        w.yesButton.setText(yesbutton)
        w.cancelButton.hide()
        w.buttonLayout.insertStretch(1)
        w.exec()

    @pyqtSlot()
    def on_save_clicked(self):
        lineedit_data = {
            "1": self.key1.text(),  # 1
            "2": self.key2.text(),  # 2
            "3": self.key3.text(),  # 3
            "4": self.key4.text(),  # 4
            "5": self.key5.text(),  # 5
            "6": self.key6.text(),  # 6
            "7": self.key7.text(),  # 7
            "1h": self.key1_h.text(),  # 1h
            "2h": self.key2_h.text(),  # 2h
            "3h": self.key3_h.text(),  # 3h
            "4h": self.key4_h.text(),  # 4h
            "5h": self.key5_h.text(),  # 5h
            "6h": self.key6_h.text(),  # 6h
            "7h": self.key7_h.text(),  # 7h
            "1hh": self.key1_hh.text(),  # 1hh
            "chord1": self.chord_1.text(),  # chord1
            "chord2": self.chord_2.text(),  # chord2
            "chord3": self.chord_3.text(),  # chord3
            "chord4": self.chord_4.text(),  # chord4
            "chord5": self.chord_5.text(),  # chord5
            "chord6": self.chord_6.text()  # chord6
        }
        # 保存到用户配置文件
        user_config_path = os.path.join(self.data_dir, "user.json")
        try:
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(lineedit_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存失败: {str(e)}")
            return
        self.msg(_translate("setting", "成功！"),
                 _translate("setting", "成功保存了用户数据到\"用户配置\""),
                 _translate("setting", "我知道了"))
        self.get_keydist_realtime()

    @pyqtSlot(int)
    def on_config_selected(self, index):
        config_name = self.list.itemText(index)
        file_map = {
            "官方[默认]": "official.json",
            "模拟钢琴[默认]": "piano.json",
            "用户配置": "user.json"
        }
        filename = file_map.get(config_name)
        if not filename:
            return
        config_path = os.path.join(self.data_dir, filename)

        # 如果文件不存在，使用空字典（理论不可能，因为每次程序启动时会检查配置，但是不排除有用户手贱
        config_data = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                print(f"加载配置失败: {str(e)}")

        # 将配置数据设置到文本框
        self.key1.setText(config_data.get("1", ""))
        self.key2.setText(config_data.get("2", ""))
        self.key3.setText(config_data.get("3", ""))
        self.key4.setText(config_data.get("4", ""))
        self.key5.setText(config_data.get("5", ""))
        self.key6.setText(config_data.get("6", ""))
        self.key7.setText(config_data.get("7", ""))
        self.key1_h.setText(config_data.get("1h", ""))
        self.key2_h.setText(config_data.get("2h", ""))
        self.key3_h.setText(config_data.get("3h", ""))
        self.key4_h.setText(config_data.get("4h", ""))
        self.key5_h.setText(config_data.get("5h", ""))
        self.key6_h.setText(config_data.get("6h", ""))
        self.key7_h.setText(config_data.get("7h", ""))
        self.key1_hh.setText(config_data.get("1hh", ""))
        self.chord_1.setText(config_data.get("chord1", ""))
        self.chord_2.setText(config_data.get("chord2", ""))
        self.chord_3.setText(config_data.get("chord3", ""))
        self.chord_4.setText(config_data.get("chord4", ""))
        self.chord_5.setText(config_data.get("chord5", ""))
        self.chord_6.setText(config_data.get("chord6", ""))

        self.get_keydist_realtime()

    def get_keydist_realtime(self):
        key_list = {
            "y": self.key1.text(),
            "u": self.key2.text(),
            "i": self.key3.text(),
            "o": self.key4.text(),
            "p": self.key5.text(),
            "h": self.key6.text(),
            "j": self.key7.text(),
            "k": self.key1_h.text(),
            "l": self.key2_h.text(),
            ";": self.key3_h.text(),
            "n": self.key4_h.text(),
            "m": self.key5_h.text(),
            ",": self.key6_h.text(),
            ".": self.key7_h.text(),
            "/": self.key1_hh.text(),
            "yi": self.chord_1.text(),
            "uo": self.chord_2.text(),
            "ip": self.chord_3.text(),
            "yo": self.chord_4.text(),
            "up": self.chord_5.text(),
            "ih": self.chord_6.text()
        }
        # self._parent.keydist = key_list
        self._parent.keydist.clear()  # 清空原有内容
        self._parent.keydist.update(key_list)
        return key_list
