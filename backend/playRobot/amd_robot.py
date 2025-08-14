import threading
import ctypes

import keyboard
import pyautogui
import win32con

from backend.set_keyLayoutw import set_us_keyboard_layout, reset_keyboard_layout
from backend.global_variable import GlobalVariable

# PostMessageW = ctypes.windll.user32.PostMessageW  # 消息队列
SendMessageW = ctypes.windll.user32.SendMessageW  # 立即处理
MapVirtualKeyW = ctypes.windll.user32.MapVirtualKeyW
VkKeyScanW = ctypes.windll.user32.VkKeyScanW
user32 = ctypes.windll.user32

WM_KEYDOWN = 0x100
WM_KEYUP = 0x101
pyautogui.FAILSAFE = False

def send_single_key_to_window_task(key, bool):
    # 请勿在外部调用
    if bool == True:
        key_down(key)
    else:
        key_up(key)

def send_multiple_key_to_window_task(keys, bool):
    # 请勿在外部调用
    if bool == True:
        for key in keys:
            key_down(key)
    else:
        for key in keys:
            key_up(key)

def execute_in_thread(target, *args, **kwargs):
    """通用线程执行器，采用线程池管理"""
    thread = threading.Thread(target=target, args=args, kwargs=kwargs)
    thread.daemon = True  # 将线程设置为守护线程，程序退出时自动结束线程
    thread.start()
    return thread

def send_single_key_to_window(key, bool):
    # 发送单个按键 T按下 F抬起
    execute_in_thread(send_single_key_to_window_task, key,bool)

def send_multiple_key_to_window(keys, bool):
    # 发送组合按键 T按下 F抬起
    execute_in_thread(send_multiple_key_to_window_task, keys,bool)

#  核心
def key_down(key: str):
    set_us_keyboard_layout()
    key = key.lower()
    if key in special_keys:
        vk_code, scan_code = special_keys[key]
    else:
        # 普通按键的处理
        vk_code = VkKeyScanW(ctypes.c_wchar(key))
        scan_code = keyboard.key_to_scan_codes(key)[0] if key != '/' else keyboard.key_to_scan_codes(key)[1]
    lparam = (scan_code << 16) | 1
    SendMessageW(GlobalVariable.window["hWnd"], win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    SendMessageW(GlobalVariable.window["hWnd"], WM_KEYDOWN, vk_code, lparam)
    reset_keyboard_layout()

def key_up(key: str):
    set_us_keyboard_layout()
    key = key.lower()
    if key in special_keys:
        vk_code, scan_code = special_keys[key]
    else:
        # 普通按键的处理
        vk_code = VkKeyScanW(ctypes.c_wchar(key))
        scan_code = keyboard.key_to_scan_codes(key)[0] if key != '/' else keyboard.key_to_scan_codes(key)[1]
    lparam = (scan_code << 16) | 0XC0000001
    SendMessageW(GlobalVariable.window["hWnd"], win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    SendMessageW(GlobalVariable.window["hWnd"], WM_KEYUP, vk_code, lparam)
    reset_keyboard_layout()


special_keys = {
    'space': (0x20, 0x39),  # 空格键
    'tab': (0x09, 0x0F),    # Tab 键
    'esc': (0x1B, 0x01),    # Escape 键
    'shift': (0x10, 0x2A),  # 左 Shift 键
    'right': (0x27, 0x4D),  # 方向键右
    'left': (0x25, 0x4B),   # 方向键左
    'up': (0x26, 0x48),     # 方向键上
    'down': (0x28, 0x50)    # 方向键下
}
