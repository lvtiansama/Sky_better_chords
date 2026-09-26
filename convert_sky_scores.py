# coding:utf-8
import argparse
import glob
import json
import math
import os

INDEX_TO_ID = {index: f'key{index + 1}' for index in range(15)}

MIN_UNIT = 20
MAX_UNIT = 300
TOLERANCE_MS = 18


def key_id_from_source(key):
    suffix = key.split('Key')[-1]
    index = int(suffix)
    if index < 0 or index >= len(INDEX_TO_ID):
        return None
    return INDEX_TO_ID[index]


def group_events(song_notes):
    events = {}
    for note in song_notes:
        note_id = key_id_from_source(note['key'])
        if note_id is None:
            continue
        events.setdefault(note['time'], [])
        if note_id not in events[note['time']]:
            events[note['time']].append(note_id)
    return events


def detect_unit(times):
    deltas = [b - a for a, b in zip(times, times[1:])]
    if not deltas:
        return 100
    overall = 0
    for value in [times[0]] + deltas:
        overall = math.gcd(overall, value)
    if overall >= MIN_UNIT:
        return overall
    best_unit = None
    for unit in range(MIN_UNIT, MAX_UNIT + 1):
        if any(d and round(d / unit) < 1 for d in deltas):
            continue
        error = sum(abs(d - round(d / unit) * unit) for d in deltas) / len(deltas)
        if error <= TOLERANCE_MS:
            best_unit = unit
    if best_unit:
        return best_unit
    best_unit = MIN_UNIT
    best_error = None
    for unit in range(MIN_UNIT, MAX_UNIT + 1):
        if any(d and round(d / unit) < 1 for d in deltas):
            continue
        error = sum(abs(d - round(d / unit) * unit) for d in deltas)
        if best_error is None or error < best_error:
            best_error = error
            best_unit = unit
    return best_unit


def detect_notes_per_bar(times, unit):
    if len(times) < 2:
        return 8
    deltas = [b - a for a, b in zip(times, times[1:])]
    beat = max(set(deltas), key=deltas.count)
    bar = round(beat / unit) * 4
    return max(1, min(32, bar))


def build_columns(times, events, unit):
    columns = []
    lead = max(0, round(times[0] / unit))
    columns.extend([] for _ in range(lead))
    for index, time in enumerate(times):
        if index > 0:
            steps = max(1, round((time - times[index - 1]) / unit))
            columns.extend([] for _ in range(steps - 1))
        columns.append(list(events[time]))
    return columns


def convert_file(path, unit=None, press=100):
    with open(path, 'r', encoding='utf-8-sig') as handle:
        data = json.load(handle)
    song = data[0]
    events = group_events(song.get('songNotes', []))
    if not events:
        return None
    times = sorted(events)
    chosen_unit = unit if unit else detect_unit(times)
    columns = build_columns(times, events, chosen_unit)
    return {
        'name': song.get('name', ''),
        'notes_per_bar': detect_notes_per_bar(times, chosen_unit),
        'press_duration_ms': press,
        'gap_ms': chosen_unit,
        'notes': columns,
    }


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(description='Convert Sky Music scores to Sky_better_chords format')
    parser.add_argument('--src', default=os.path.join(base, '乐谱转换'))
    parser.add_argument('--out', default=os.path.join(base, '乐谱转换输出'))
    parser.add_argument('--unit', type=int, default=0, help='force time grid unit (ms), 0 = auto')
    parser.add_argument('--press', type=int, default=100, help='global long press duration (ms)')
    args = parser.parse_args()

    if not os.path.isdir(args.out):
        os.makedirs(args.out)

    files = sorted(glob.glob(os.path.join(args.src, '*.txt')))
    if not files:
        print('no source files in', args.src)
        return
    for path in files:
        result = convert_file(path, args.unit or None, args.press)
        if result is None:
            print('skip empty:', os.path.basename(path))
            continue
        name = os.path.splitext(os.path.basename(path))[0] + '.json'
        out_path = os.path.join(args.out, name)
        with open(out_path, 'w', encoding='utf-8') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=4)
        print(f'{os.path.basename(path)} -> {name} | unit={result["gap_ms"]} '
              f'press={result["press_duration_ms"]} bars={result["notes_per_bar"]} '
              f'columns={len(result["notes"])}')


if __name__ == '__main__':
    main()
