# coding:utf-8
import json
import os

from PyQt6 import QtCore
from PyQt6.QtCore import QEvent, Qt, QTimer
from PyQt6.QtWidgets import QFileDialog, QWidget
from qfluentwidgets import (FluentIcon as FIF, InfoBar, InfoBarPosition,
                            MessageBox)

from config import global_keydist_realtime
from backend.global_variable import GlobalVariable
from ui.recording import (ID_TO_INDEX, ID_TO_PHYSICAL, INDEX_TO_ID,
                          PHYSICAL_TO_ID, Ui_recording)

_translate = QtCore.QCoreApplication.translate

CHORD_WINDOW_MS = 40


class RecordingInterface(Ui_recording, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._parent = parent
        self.setupUi(self, parent)

        self.notes = []
        self.current_index = 0
        self.score_name = None
        self._press_ms = 100
        self._gap_ms = 150
        self.pending_keys = []
        self._syncing_slider = False
        self._play_end = 0

        self.chord_timer = QTimer(self)
        self.chord_timer.setSingleShot(True)
        self.chord_timer.timeout.connect(self._flush_pending)
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._on_play_tick)
        self.active_targets = None
        self.release_timer = QTimer(self)
        self.release_timer.setSingleShot(True)
        self.release_timer.timeout.connect(self._on_release_timeout)

        self.waterfall.columnClicked.connect(self._on_waterfall_clicked)
        for key, button in self.key_buttons.items():
            button.clicked.connect(lambda checked=False, k=key: self._on_key_clicked(k))

        self.notes_per_bar.valueChanged.connect(self._on_notes_per_bar_changed)
        self.press_duration.editingFinished.connect(self._on_timing_edited)
        self.gap_duration.editingFinished.connect(self._on_timing_edited)
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.to_start_button.clicked.connect(self._on_to_start)
        self.prev_button.clicked.connect(self._on_prev)
        self.next_button.clicked.connect(self._on_next)
        self.to_end_button.clicked.connect(self._on_to_end)
        self.play_button.clicked.connect(self._on_play_toggle)
        self.add_button.clicked.connect(self._on_add_column)
        self.remove_button.clicked.connect(self._on_delete_column)
        self.new_button.clicked.connect(self._on_new)
        self.open_button.clicked.connect(self._on_open)
        self.save_button.clicked.connect(self._on_save)

        self.notes_per_bar.installEventFilter(self)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._ensure_column(0)
        self._refresh()

    def _handle_key_event(self, event):
        if event.isAutoRepeat():
            return False
        if event.key() == Qt.Key.Key_Space:
            self._flush_pending()
            self._release_active()
            self._commit_column([])
            return True
        note = PHYSICAL_TO_ID.get(event.text().lower())
        if note is not None:
            if not self.pending_keys:
                self._release_active()
            if note not in self.pending_keys:
                self.pending_keys.append(note)
                self._play_live_note(note)
            self.chord_timer.start(CHORD_WINDOW_MS)
            return True
        return False

    def keyPressEvent(self, event):
        if self._handle_key_event(event):
            return
        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and self._handle_key_event(event):
            return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_keyboard_size()

    def showEvent(self, event):
        super().showEvent(event)
        if self._parent.homeInterface.pushButton.isChecked():
            self._parent.homeInterface.pushButton.setChecked(False)
            self.pushButtonoffinfo()
        self.setFocus()

    def hideEvent(self, event):
        self._stop_play()
        self.chord_timer.stop()
        self.pending_keys = []
        self._release_active()
        super().hideEvent(event)

    def pushButtonoffinfo(self):
        InfoBar.warning(
            title=_translate("recording", "提示"),
            content=_translate("recording", "映射已被关闭"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def _ensure_column(self, index):
        while len(self.notes) <= index:
            self.notes.append([])

    def _current_column(self):
        if self.current_index < len(self.notes):
            return self.notes[self.current_index]
        return []

    def _refresh(self):
        self.waterfall.set_notes(self.notes)
        self.waterfall.set_current(self.current_index)
        current = self._current_column()
        for key, button in self.key_buttons.items():
            button.blockSignals(True)
            button.setChecked(key in current)
            button.blockSignals(False)
        max_index = max(0, len(self.notes) - 1)
        self._syncing_slider = True
        self.slider.setRange(0, max_index)
        self.slider.setValue(min(self.current_index, max_index))
        self._syncing_slider = False
        bar = self.current_index // self.notes_per_bar.value() + 1
        beat = self.current_index % self.notes_per_bar.value() + 1
        self.position_label.setText(
            _translate("recording", "第 {} 小节 · 第 {} 拍").format(bar, beat))
        self._update_stats()

    def _update_stats(self):
        name = self.score_name if self.score_name else _translate("recording", "未命名")
        self.score_name_label.setText(_translate("recording", "乐谱：{}").format(name))
        self.column_count_label.setText(
            _translate("recording", "共 {} 列").format(len(self.notes)))
        seconds = int(round(len(self.notes) * self._gap_ms / 1000.0))
        minutes, sec = divmod(seconds, 60)
        self.duration_label.setText(
            _translate("recording", "预估时长：{}:{:02d}").format(minutes, sec))

    def _flush_pending(self):
        self.chord_timer.stop()
        keys = self.pending_keys
        self.pending_keys = []
        if keys:
            self._commit_column(keys)

    def _commit_column(self, keys):
        self._ensure_column(self.current_index)
        self.notes[self.current_index] = list(keys)
        self.current_index += 1
        self._ensure_column(self.current_index)
        self._refresh()

    def _on_key_clicked(self, key):
        self._ensure_column(self.current_index)
        column = self.notes[self.current_index]
        if key in column:
            column.remove(key)
        else:
            column.append(key)
        self._refresh()

    def _on_waterfall_clicked(self, col, row):
        self._ensure_column(col)
        self.current_index = col
        note = INDEX_TO_ID[row]
        column = self.notes[col]
        if note in column:
            column.remove(note)
        else:
            column.append(note)
        self._refresh()

    def _on_notes_per_bar_changed(self, value):
        self.waterfall.set_notes_per_bar(value)
        self._refresh()

    def _on_slider_changed(self, value):
        if self._syncing_slider or value == self.current_index:
            return
        self.current_index = value
        self._refresh()

    def _on_to_start(self):
        self._flush_pending()
        self.current_index = 0
        self._refresh()

    def _on_to_end(self):
        self._flush_pending()
        self.current_index = max(0, len(self.notes) - 1)
        self._refresh()

    def _on_prev(self):
        self._flush_pending()
        self.current_index = max(0, self.current_index - 1)
        self._refresh()

    def _on_next(self):
        self._flush_pending()
        column = self._current_column()
        if column:
            self._send_note_signal(column)
        self.current_index += 1
        self._ensure_column(self.current_index)
        self._refresh()

    def _on_add_column(self):
        self._flush_pending()
        self.current_index += 1
        self.notes.insert(self.current_index, [])
        self._refresh()

    def _on_delete_column(self):
        self._flush_pending()
        if not self.notes:
            return
        del self.notes[self.current_index]
        if not self.notes:
            self.notes = [[]]
            self.current_index = 0
        elif self.current_index >= len(self.notes):
            self.current_index = len(self.notes) - 1
        self._refresh()

    def _on_play_toggle(self):
        if self.play_timer.isActive():
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        self._flush_pending()
        last = len(self.notes) - 1
        while last >= 0 and not self.notes[last]:
            last -= 1
        self._play_end = last + 1
        if self._play_end <= 0:
            return
        if self.current_index >= self._play_end:
            self.current_index = 0
            self._refresh()
        self.play_timer.start(max(10, self._gap_ms))
        self.play_button.setIcon(FIF.PAUSE)
        self.play_button.setText(_translate("recording", "暂停"))

    def _stop_play(self):
        self.play_timer.stop()
        self.play_button.setIcon(FIF.PLAY)
        self.play_button.setText(_translate("recording", "播放"))

    def _on_play_tick(self):
        if self.current_index >= self._play_end:
            self._stop_play()
            return
        self._refresh()
        column = self.notes[self.current_index]
        if column:
            self._send_note_signal(column)
        if self.current_index + 1 >= self._play_end:
            self._stop_play()
            return
        self.current_index += 1

    def _robot_functions(self):
        if GlobalVariable.cpu_type == 'AMD':
            from backend.playRobot.amd_robot import (send_multiple_key_to_window,
                                                     send_single_key_to_window)
        else:
            from backend.playRobot.intel_robot import (send_multiple_key_to_window,
                                                       send_single_key_to_window)
        return send_single_key_to_window, send_multiple_key_to_window

    def _play_live_note(self, note):
        if not GlobalVariable.window.get("hWnd"):
            return
        target = global_keydist_realtime.get(ID_TO_PHYSICAL.get(note))
        if not target:
            return
        try:
            send_single, send_multiple = self._robot_functions()
        except Exception:
            return
        if len(target) == 1:
            send_single(target, True)
        else:
            send_multiple(target, True)
        if self.active_targets is None:
            self.active_targets = []
        self.active_targets.append(target)
        self.release_timer.start(max(1, self._press_ms))

    def _send_note_signal(self, notes):
        self._release_active()
        if not GlobalVariable.window.get("hWnd"):
            return
        targets = [global_keydist_realtime.get(ID_TO_PHYSICAL.get(note)) for note in notes]
        targets = [target for target in targets if target]
        if not targets:
            return
        try:
            send_single, send_multiple = self._robot_functions()
        except Exception:
            return
        if len(targets) == 1:
            send_single(targets[0], True)
        else:
            send_multiple(targets, True)
        self.active_targets = targets
        self.release_timer.start(max(1, self._press_ms))

    def _release_targets(self, targets):
        if GlobalVariable.window.get("hWnd") is None:
            return
        try:
            send_single, send_multiple = self._robot_functions()
        except Exception:
            return
        if len(targets) == 1:
            send_single(targets[0], False)
        else:
            send_multiple(targets, False)

    def _release_active(self):
        self.release_timer.stop()
        targets = self.active_targets
        self.active_targets = None
        if targets:
            self._release_targets(targets)

    def _on_release_timeout(self):
        self._release_active()

    def _parse_ms(self, line_edit, default):
        text = line_edit.text().strip()
        try:
            return int(text)
        except ValueError:
            return default

    def _validate_timing(self):
        press = max(1, self._parse_ms(self.press_duration, self._press_ms))
        gap = max(10, self._parse_ms(self.gap_duration, self._gap_ms))
        self._press_ms = press
        self._gap_ms = gap
        self.press_duration.setText(str(press))
        self.gap_duration.setText(str(gap))

    def _on_timing_edited(self):
        self._validate_timing()
        if self._gap_ms < self._press_ms + 10:
            self._gap_ms = self._press_ms + 10
            self.gap_duration.setText(str(self._gap_ms))
        self._update_stats()

    def _on_new(self):
        box = MessageBox(
            _translate("recording", "新建乐谱"),
            _translate("recording", "新建会清空当前工作区，未保存的内容将会丢失。确定要放弃当前内容吗？"),
            self.window())
        box.yesButton.setText(_translate("recording", "新建"))
        box.cancelButton.setText(_translate("recording", "取消"))
        if not box.exec():
            return
        self._stop_play()
        self.chord_timer.stop()
        self.pending_keys = []
        self._release_active()
        self.notes = [[]]
        self.current_index = 0
        self.score_name = None
        self.notes_per_bar.setValue(8)
        self.press_duration.setText("100")
        self.gap_duration.setText("150")
        self._validate_timing()
        self._refresh()

    def _on_save(self):
        self._validate_timing()
        path, _ = QFileDialog.getSaveFileName(
            self, _translate("recording", "保存乐谱"), "", "JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        data = {
            "notes_per_bar": self.notes_per_bar.value(),
            "press_duration_ms": self._press_ms,
            "gap_ms": self._gap_ms,
            "notes": self.notes,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            InfoBar.error(
                title=_translate("recording", "保存失败"),
                content=str(e),
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        InfoBar.success(
            title=_translate("recording", "保存成功"),
            content=_translate("recording", "乐谱已保存"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(
            self, _translate("recording", "打开乐谱"), "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            InfoBar.error(
                title=_translate("recording", "打开失败"),
                content=str(e),
                isClosable=False,
                position=InfoBarPosition.TOP_RIGHT,
                duration=3000,
                parent=self
            )
            return
        self._stop_play()
        self.chord_timer.stop()
        self.pending_keys = []
        self.score_name = os.path.splitext(os.path.basename(path))[0]
        self.notes = self._normalize_notes(data.get("notes", []))
        self.notes_per_bar.setValue(int(data.get("notes_per_bar", 8)))
        self.press_duration.setText(str(int(data.get("press_duration_ms", self._press_ms))))
        self.gap_duration.setText(str(int(data.get("gap_ms", self._gap_ms))))
        self._validate_timing()
        self.current_index = 0
        self._ensure_column(0)
        self._refresh()
        InfoBar.success(
            title=_translate("recording", "打开成功"),
            content=_translate("recording", "乐谱已载入"),
            isClosable=False,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    def _normalize_note(self, value):
        if value in ID_TO_INDEX:
            return value
        if isinstance(value, str):
            return PHYSICAL_TO_ID.get(value.lower())
        return None

    def _normalize_notes(self, raw):
        notes = []
        for item in raw:
            if isinstance(item, list):
                converted = [self._normalize_note(value) for value in item]
                notes.append([value for value in converted if value is not None])
            elif isinstance(item, str):
                note = self._normalize_note(item)
                notes.append([note] if note else [])
            else:
                notes.append([])
        return notes
