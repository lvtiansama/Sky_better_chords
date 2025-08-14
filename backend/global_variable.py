class GlobalVariable:
    # 运行环境配置
    cpu_type = None

    # 窗口相关
    find_bool = False   # 是否找到目标进程
    hwnd_title = "Sky.exe"  # 目标进程窗口名称
    window = {
        "hWnd": None,
    }

    # 映射状态
    Backend_status = False
