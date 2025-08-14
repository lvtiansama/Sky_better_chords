## *Sky_better_chords*
光遇和弦助手

## 特别鸣谢
PyQt-Fluent-Widgets（作者：zhiyiYo）

SkyMusicPlay-for-Windows（作者：windhide）

## 版本更新内容

### `1.0`

实现基本功能：

1、按键映射（自定义弹琴键位）

2、和弦快捷键

## 开源协议
本项目采用`GNU General Public License v3.0`许可证开源，详情请参阅license文件

## 免责声明

本项目为开源、离线的项目，开发者对本项目的分支及衍生品没有控制力。

此项目完全离线运行，不会收集任何用户信息或获取用户输入数据。所有数据处理均在用户本地设备上完成，确保用户隐私和数据安全。

开发者不对因使用、修改或分发本项目及其衍生作品所引起的任何直接或间接损失承担责任。用户在使用本项目时，应遵守相关法律法规，并自行承担使用过程中可能产生的风险。
## Python 版本

本项目使用`Python 3.10.6`编译


## 使用说明

### `编译版本`

1、在`Releases`中下载文件名含有`win`或类似标识的压缩包

2、解压

3、双击打开程序

### `运行版本`

确保电脑已安装 `Python`（建议 3.10.6）。

以管理员身份运行命令行（必要）

克隆项目：
```bash
   git clone https://github.com/lvtiansama/Sky_better_chords.git
```
进入项目目录：
```bash
   cd Sky_better_chords
```
安装依赖
```bash
   pip install -r requirements.txt
```
运行
```bash
   python main.py
```

### `使用须知`
点击设置，进入设置菜单，选择合适的键位配置，或者自行设置并保存。

保存键是用来将配置存储到本地，映射采用的是文本框实时的配置，也就是说不点保存也能够成功设置映射，但是不保存程序重启配置会丢失。

设置提供了三套配置，你保存的配置会被存在`用户配置`，其他两套为默认配置，不可修改。

回到主页，确保游戏窗口正常运行，主页会显示游戏窗口的相关信息，点击启用映射按钮即可启用键盘映射。

启用后，你的键盘除了设置的键位，其他键会失效，这是正常的。

如果遇到无法停止映射的情况，请尝试使用 `ctrl+c` 结束，或者使用`ctrl+alt+del`呼出任务管理器结束。

## 关于作者

`Github`**https://github.com/lvtiansama**

`CSDN`**https://blog.csdn.net/lvtiansama**

