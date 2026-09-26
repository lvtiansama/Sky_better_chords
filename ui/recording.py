# coding:utf-8
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, pyqtSignal, QLineF, QRectF
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (QGridLayout, QHBoxLayout, QSizePolicy, QVBoxLayout,
                             QWidget)
from qfluentwidgets import (BodyLabel, FluentIcon as FIF, LineEdit,
                            PrimaryPushButton, PushButton, Slider, SpinBox,
                            TogglePushButton, TransparentToolButton,
                            isDarkTheme, themeColor)

KEY_ROWS = [
    ['y', 'u', 'i', 'o', 'p'],
    ['h', 'j', 'k', 'l', ';'],
    ['n', 'm', ',', '.', '/'],
]
PHYSICAL_KEYS = [key for row in KEY_ROWS for key in row]
NOTE_IDS = [f'key{i}' for i in range(1, len(PHYSICAL_KEYS) + 1)]
NOTE_LABELS = ['1', '2', '3', '4', '5', '6', '7',
               '1', '2', '3', '4', '5', '6', '7', '1']
ID_TO_INDEX = {note_id: index for index, note_id in enumerate(NOTE_IDS)}
INDEX_TO_ID = {index: note_id for index, note_id in enumerate(NOTE_IDS)}
PHYSICAL_TO_ID = {physical: note_id for physical, note_id in zip(PHYSICAL_KEYS, NOTE_IDS)}
ID_TO_PHYSICAL = {note_id: physical for physical, note_id in zip(PHYSICAL_KEYS, NOTE_IDS)}
GROUP_SPLIT = 5


class WaterfallWidget(QWidget):
    columnClicked = pyqtSignal(int, int)

    MAX_ROW_HEIGHT = 28
    MIN_ROW_HEIGHT = 16
    COL_WIDTH = 26
    GUTTER_WIDTH = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes = []
        self.current_index = 0
        self.notes_per_bar = 8
        self.scroll_col = 0
        self.setMinimumHeight(self.MIN_ROW_HEIGHT * len(NOTE_IDS))
        self.setMaximumHeight(self.MAX_ROW_HEIGHT * len(NOTE_IDS))
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def row_height(self):
        return max(self.MIN_ROW_HEIGHT,
                   min(self.MAX_ROW_HEIGHT, self.height() / len(NOTE_IDS)))

    def set_notes(self, notes):
        self.notes = list(notes)
        self._follow_current()
        self.update()

    def set_current(self, index):
        self.current_index = max(0, index)
        self._follow_current()
        self.update()

    def set_notes_per_bar(self, count):
        self.notes_per_bar = max(1, int(count))
        self.update()

    def visible_columns(self):
        return max(1, (self.width() - self.GUTTER_WIDTH) // self.COL_WIDTH)

    def _follow_current(self):
        columns = self.visible_columns()
        if self.current_index < self.scroll_col:
            self.scroll_col = self.current_index
        elif self.current_index >= self.scroll_col + columns:
            self.scroll_col = self.current_index - columns + 1
        self.scroll_col = max(0, self.scroll_col)

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0:
            return super().wheelEvent(event)
        step = 1 if delta < 0 else -1
        self.scroll_col = max(0, self.scroll_col + step * 3)
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        pos = event.position()
        if pos.x() < self.GUTTER_WIDTH:
            return
        col = self.scroll_col + int((pos.x() - self.GUTTER_WIDTH) // self.COL_WIDTH)
        row = int(pos.y() // self.row_height())
        if 0 <= row < len(NOTE_IDS):
            self.columnClicked.emit(col, row)
        event.accept()

    def _octave_color(self, row, label_color, accent, dark):
        if row < 7:
            return label_color
        if row < 14:
            return accent
        return QColor('#F2B84B') if dark else QColor('#C87A1E')

    def paintEvent(self, event):
        painter = QPainter(self)
        width = self.width()
        dark = isDarkTheme()
        accent = QColor(themeColor())
        row_height = self.row_height()
        rows_height = len(NOTE_IDS) * row_height
        columns = self.visible_columns()

        if dark:
            row_alt = QColor(255, 255, 255, 12)
            grid_pen = QColor(255, 255, 255, 30)
            bar_pen = QColor(255, 255, 255, 80)
            label_color = QColor(255, 255, 255, 150)
        else:
            row_alt = QColor(0, 0, 0, 8)
            grid_pen = QColor(0, 0, 0, 22)
            bar_pen = QColor(0, 0, 0, 70)
            label_color = QColor(0, 0, 0, 150)

        current_color = QColor(accent)
        current_color.setAlpha(45)

        for row in range(len(NOTE_IDS)):
            if row % 2 == 1:
                painter.fillRect(QRectF(self.GUTTER_WIDTH, row * row_height,
                                        width - self.GUTTER_WIDTH, row_height), row_alt)

        current_x = self.GUTTER_WIDTH + (self.current_index - self.scroll_col) * self.COL_WIDTH
        if self.GUTTER_WIDTH <= current_x < width:
            painter.fillRect(QRectF(current_x, 0, self.COL_WIDTH, rows_height), current_color)

        painter.setPen(QPen(grid_pen, 1))
        for i in range(columns + 1):
            x = self.GUTTER_WIDTH + i * self.COL_WIDTH
            painter.drawLine(QLineF(x, 0, x, rows_height))
        for row in range(len(NOTE_IDS) + 1):
            y = row * row_height
            painter.drawLine(QLineF(self.GUTTER_WIDTH, y, width, y))

        painter.setPen(QPen(bar_pen, 2))
        for col in range(self.scroll_col, self.scroll_col + columns):
            if col % self.notes_per_bar == 0:
                x = self.GUTTER_WIDTH + (col - self.scroll_col) * self.COL_WIDTH
                painter.drawLine(QLineF(x, 0, x, rows_height))
        for row in range(GROUP_SPLIT, len(NOTE_IDS), GROUP_SPLIT):
            y = row * row_height
            painter.drawLine(QLineF(self.GUTTER_WIDTH, y, width, y))

        label_font = QFont(self.font())
        label_font.setPointSize(8)
        painter.setFont(label_font)
        for index in range(len(NOTE_IDS)):
            rect = QRectF(0, index * row_height, self.GUTTER_WIDTH, row_height)
            painter.setPen(self._octave_color(index, label_color, accent, dark))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, NOTE_LABELS[index])

        note_font = QFont(self.font())
        note_font.setPointSize(8)
        note_font.setBold(True)
        painter.setFont(note_font)
        for col in range(self.scroll_col, self.scroll_col + columns):
            column = self.notes[col] if col < len(self.notes) else None
            if not column:
                continue
            for note in column:
                row = ID_TO_INDEX.get(note)
                if row is None:
                    continue
                x = self.GUTTER_WIDTH + (col - self.scroll_col) * self.COL_WIDTH
                y = row * row_height
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(accent)
                painter.drawRoundedRect(QRectF(x + 2, y + 2, self.COL_WIDTH - 4,
                                               row_height - 4), 3, 3)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(QRectF(x, y, self.COL_WIDTH, row_height),
                                 Qt.AlignmentFlag.AlignCenter, NOTE_LABELS[row])

        painter.setPen(QPen(bar_pen, 2))
        painter.drawLine(QLineF(self.GUTTER_WIDTH, 0, self.GUTTER_WIDTH, rows_height))


class Ui_recording(object):
    def setupUi(self, recording, parent=None):
        self._parent = parent
        self._key_size = 0
        recording.setObjectName("recording")
        recording.resize(1000, 600)

        self.verticalLayout = QVBoxLayout(recording)
        self.verticalLayout.setContentsMargins(24, 20, 24, 20)
        self.verticalLayout.setSpacing(10)

        self.statsLayout = QHBoxLayout()
        self.statsLayout.setSpacing(16)
        self.score_name_label = BodyLabel(recording)
        self.column_count_label = BodyLabel(recording)
        self.duration_label = BodyLabel(recording)
        self.statsLayout.addWidget(self.score_name_label)
        self.statsLayout.addWidget(self.column_count_label)
        self.statsLayout.addWidget(self.duration_label)
        self.statsLayout.addStretch(1)
        self.verticalLayout.addLayout(self.statsLayout)

        self.verticalLayout.addStretch(1)

        self.waterfall = WaterfallWidget(recording)
        self.verticalLayout.addWidget(self.waterfall, 6)

        self.slider = Slider(recording)
        self.slider.setOrientation(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.verticalLayout.addWidget(self.slider)

        self.optionLayout = QHBoxLayout()
        self.optionLayout.setSpacing(8)
        self.bar_label = BodyLabel(recording)
        self.optionLayout.addWidget(self.bar_label)
        self.notes_per_bar = SpinBox(recording)
        self.notes_per_bar.setRange(1, 32)
        self.notes_per_bar.setValue(8)
        self.notes_per_bar.setFixedWidth(120)
        self.optionLayout.addWidget(self.notes_per_bar)
        self.optionLayout.addSpacing(16)
        self.press_label = BodyLabel(recording)
        self.optionLayout.addWidget(self.press_label)
        self.press_duration = LineEdit(recording)
        self.press_duration.setFixedWidth(140)
        self.press_duration.setText("100")
        self.optionLayout.addWidget(self.press_duration)
        self.optionLayout.addSpacing(16)
        self.gap_label = BodyLabel(recording)
        self.optionLayout.addWidget(self.gap_label)
        self.gap_duration = LineEdit(recording)
        self.gap_duration.setFixedWidth(140)
        self.gap_duration.setText("150")
        self.optionLayout.addWidget(self.gap_duration)
        self.optionLayout.addStretch(1)
        self.new_button = PushButton(FIF.DOCUMENT, "", recording)
        self.open_button = PushButton(FIF.FOLDER, "", recording)
        self.save_button = PrimaryPushButton(FIF.SAVE, "", recording)
        self.new_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.open_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.save_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.optionLayout.addWidget(self.new_button)
        self.optionLayout.addWidget(self.open_button)
        self.optionLayout.addWidget(self.save_button)
        self.verticalLayout.addLayout(self.optionLayout)

        self.transportLayout = QHBoxLayout()
        self.transportLayout.setSpacing(8)
        self.transportLayout.addStretch(1)
        self.to_start_button = TransparentToolButton(FIF.LEFT_ARROW, recording)
        self.prev_button = PushButton(FIF.PAGE_LEFT, "", recording)
        self.play_button = PrimaryPushButton(FIF.PLAY, "", recording)
        self.next_button = PushButton(FIF.PAGE_RIGHT, "", recording)
        self.to_end_button = TransparentToolButton(FIF.RIGHT_ARROW, recording)
        self.add_button = PushButton(FIF.ADD, "", recording)
        self.remove_button = PushButton(FIF.DELETE, "", recording)
        self.position_label = BodyLabel(recording)
        for button in (self.to_start_button, self.prev_button, self.play_button,
                       self.next_button, self.to_end_button, self.add_button,
                       self.remove_button):
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.transportLayout.addWidget(self.to_start_button)
        self.transportLayout.addWidget(self.prev_button)
        self.transportLayout.addWidget(self.play_button)
        self.transportLayout.addWidget(self.next_button)
        self.transportLayout.addWidget(self.to_end_button)
        self.transportLayout.addSpacing(20)
        self.transportLayout.addWidget(self.add_button)
        self.transportLayout.addWidget(self.remove_button)
        self.transportLayout.addSpacing(16)
        self.transportLayout.addWidget(self.position_label)
        self.transportLayout.addStretch(1)
        self.verticalLayout.addLayout(self.transportLayout)

        self.keyboardWidget = QWidget(recording)
        self.keyboardLayout = QGridLayout(self.keyboardWidget)
        self.keyboardLayout.setContentsMargins(0, 0, 0, 0)
        self.keyboardLayout.setSpacing(8)
        self.key_buttons = {}
        for row, keys in enumerate(KEY_ROWS):
            for col, physical in enumerate(keys):
                button = TogglePushButton(physical.upper(), self.keyboardWidget)
                button.setFixedSize(48, 48)
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                self.keyboardLayout.addWidget(button, row, col)
                self.key_buttons[PHYSICAL_TO_ID[physical]] = button
        self.update_keyboard_size()
        self.verticalLayout.addStretch(1)

        self.keyboardContainer = QHBoxLayout()
        self.keyboardContainer.addStretch(1)
        self.keyboardContainer.addWidget(self.keyboardWidget)
        self.keyboardContainer.addStretch(1)
        self.verticalLayout.addLayout(self.keyboardContainer)

        self.verticalLayout.addStretch(1)

        self.retranslateUi(recording)

    def update_keyboard_size(self):
        by_height = int(self.height() * 0.075)
        by_width = int(self.width() * 0.55) // 5
        size = max(40, min(72, by_height, by_width))
        if size == self._key_size:
            return
        self._key_size = size
        for button in self.key_buttons.values():
            button.setFixedSize(size, size)
        self.keyboardLayout.activate()
        self.keyboardWidget.updateGeometry()
        self.keyboardWidget.adjustSize()

    def retranslateUi(self, recording):
        _translate = QtCore.QCoreApplication.translate
        recording.setWindowTitle(_translate("recording", "录制"))
        self.bar_label.setText(_translate("recording", "每小节音符数"))
        self.press_label.setText(_translate("recording", "长按(ms)"))
        self.gap_label.setText(_translate("recording", "列后延迟(ms)"))
        self.new_button.setText(_translate("recording", "新建乐谱"))
        self.open_button.setText(_translate("recording", "打开乐谱"))
        self.save_button.setText(_translate("recording", "保存乐谱"))
        self.prev_button.setText(_translate("recording", "上一列"))
        self.play_button.setText(_translate("recording", "播放"))
        self.next_button.setText(_translate("recording", "下一列"))
        self.add_button.setText(_translate("recording", "新增列"))
        self.remove_button.setText(_translate("recording", "删除列"))
        self.position_label.setText(_translate("recording", "第 1 小节 · 第 1 拍"))
        self.score_name_label.setText(_translate("recording", "乐谱：未命名"))
        self.column_count_label.setText(_translate("recording", "共 1 列"))
        self.duration_label.setText(_translate("recording", "预估时长：0:00"))
