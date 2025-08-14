import os
import time
import platform
import psutil
import win32gui
import win32process

from backend.global_variable import GlobalVariable


def cpu_check():
    cpu_info = platform.processor()
    if "Intel" in cpu_info:
        GlobalVariable.cpu_type = 'Intel'
    elif "AMD" in cpu_info:
        GlobalVariable.cpu_type = 'AMD'

def get_exe_name_from_hwnd(hwnd):
    # 获取窗口的 PID
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        # 使用 psutil 获取进程的 exe 路径
        process = psutil.Process(pid)
        exe_path = process.exe()  # 获取 exe 路径
        exe_name = os.path.basename(exe_path)  # 只获取文件名
        return exe_name
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None

def find_window_by_class(class_name):
    # 根据窗口类名查找窗口句柄
    hwnd = win32gui.FindWindow(class_name, None)
    return hwnd

def update_window_handle():
    # 查找目标进程，并更新全局变量
    class_name = "TgcMainWindow"
    hwnd = find_window_by_class(class_name)
    if hwnd:
        GlobalVariable.find_bool = True
        GlobalVariable.hwnd_title = get_exe_name_from_hwnd(hwnd)
        GlobalVariable.window["hWnd"] = hwnd
    else:
        GlobalVariable.find_bool = False
        GlobalVariable.hwnd_title = None
        GlobalVariable.window["hWnd"] = None


def start_thread():
    # 后台线程循环更新窗口句柄
    while True:
        update_window_handle()
        time.sleep(2) # 每两秒获取一次hwnd