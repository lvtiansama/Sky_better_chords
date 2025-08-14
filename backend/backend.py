import json
import keyboard
import time
from threading import Lock, Thread
from typing import Optional

from config import global_keydist_realtime
from function import get_resource_path

from backend.global_variable import GlobalVariable
if GlobalVariable.cpu_type == 'AMD':
    from backend.playRobot.amd_robot import send_single_key_to_window, send_multiple_key_to_window
else:
    from backend.playRobot.intel_robot import send_single_key_to_window, send_multiple_key_to_window


with open(get_resource_path('data/json/key_json.json'), 'r', encoding='utf-8') as f:
    key_qt_keyboard = json.load(f)
key_keyboard_qt = {v: k for k, v in key_qt_keyboard.items()}

class KeyboardMonitor:
    def __init__(self):
        self.key_states = {}
        self.lock = Lock()
        self.running = False # 运行状态 与GlobalVariable.Backend_status是一个东西 更新需要同时赋值
        self.thread: Optional[Thread] = None

    def _on_key_event(self, e):
        # 获取当前配置的映射
        find_keydist_realtime = {v: k for k, v in global_keydist_realtime.items()}
        # 判断是否为强退快捷键
        if 29 in self.key_states:
            if e.event_type == 'down' and e.name.lower() == 'c' and self.key_states[29]:
                print("检测到 Ctrl+C，退出映射")
                self.stop()
                return
        with self.lock:
            key_name = e.name.lower()
            if e.is_keypad:
                # 映射数字键盘按键
                numpad_mapping = {
                    '0': 'numpad 0',
                    '1': 'numpad 1',
                    '2': 'numpad 2',
                    '3': 'numpad 3',
                    '4': 'numpad 4',
                    '5': 'numpad 5',
                    '6': 'numpad 6',
                    '7': 'numpad 7',
                    '8': 'numpad 8',
                    '9': 'numpad 9',
                    '+': 'numpad add',
                    '-': 'numpad subtract',
                    '*': 'numpad multiply',
                    '/': 'numpad divide',
                    '.': 'numpad decimal',
                    'decimal': 'numpad decimal',
                    'enter': 'numpad enter',
                }
                # 使用映射后的键名，如果不存在则保留原名称
                key_name = numpad_mapping.get(e.name, key_name)
            # 转换为qt可读的名称
            if key_name in key_keyboard_qt:
                key_name = key_keyboard_qt[key_name]
            else:
                print(f"未知按键{key_name},不会被处理")
                return
            # 处理强退快捷键 确保ctrl的状态会被更新
            if key_name == "LCtrl":
                if e.event_type == 'down':
                    self.key_states[29] = True
                elif e.event_type == 'up':
                    self.key_states[29] = False
            # 查询当前按下键是否是实时配置的被映射键
            if key_name in find_keydist_realtime:
                # 获取该键被映射的目标键
                Target_Button = find_keydist_realtime[key_name]
                # 单键处理
                if len(Target_Button) == 1:
                    if e.event_type == 'down':
                            self.key_states[e.scan_code] = True
                            send_single_key_to_window(Target_Button, True)
                    elif e.event_type == 'up':
                        if self.key_states.get(e.scan_code, False):
                            self.key_states[e.scan_code] = False
                            send_single_key_to_window(Target_Button, False)
                # 多键处理（和弦，一般是两个键）
                else:
                    if e.event_type == 'down':
                        if not self.key_states.get(e.scan_code, False):
                            self.key_states[e.scan_code] = True
                            send_multiple_key_to_window(Target_Button, True)
                    elif e.event_type == 'up':
                        if self.key_states.get(e.scan_code, False):
                            self.key_states[e.scan_code] = False
                            send_multiple_key_to_window(Target_Button, False)
    #             按下和抬起信号分开模拟（用来适配长音乐器）

    def _main_loop(self):
        # 主循环
        while self.running:
            time.sleep(0.01)

    def start(self):
        if self.running:
            return
        GlobalVariable.Backend_status = True
        self.running = True

        # 注册键盘钩子
        keyboard.hook(self._on_key_event, suppress=True)
        # 启动主循环线程
        self.thread = Thread(target=self._main_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.running:
            return
        GlobalVariable.Backend_status = False
        self.running = False

        # 移除钩子
        keyboard.unhook_all()

    def is_running(self):
        # 判断映射线程是否在运行
        return self.running


if __name__ == "__main__":
    monitor = KeyboardMonitor()
    monitor.start()
    time.sleep(100)
    # 启动100s的映射（仅测试，现在可能起不来了，部分变量依赖main