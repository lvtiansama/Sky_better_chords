import ctypes

user32 = ctypes.windll.user32
# 设置键盘布局的函数
def set_us_keyboard_layout():
    # LoadKeyboardLayoutW 函数的定义
    user32.LoadKeyboardLayoutW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
    user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
    user32.LoadKeyboardLayoutW("00000409", 1)  # 0409 是美国键盘布局标识符，1 表示激活

def reset_keyboard_layout():
    user32.LoadKeyboardLayoutW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
    user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
    user32.LoadKeyboardLayoutW("00000804", 1)  # 0808是中国键盘布局标识符