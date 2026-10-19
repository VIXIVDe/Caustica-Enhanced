"""Validate one current capture set without requiring a historical baseline."""
from pathlib import Path
import argparse
import json
import numpy as np
from exr_reader import read_exr


def check(folder, expected=None):
    report = {}
    for directory in sorted(Path(folder).iterdir()):
        if not directory.is_dir() or not (directory / 'raw.exr').exists():
            continue
        raw, final = [read_exr(directory / (name + '.exr')) for name in ('raw', 'reconstructed')]
        entry = {'finite': bool(np.isfinite(raw).all() and np.isfinite(final).all()),
                 'raw_mean': raw[..., :3].mean(axis=(0, 1)).tolist(),
                 'reconstructed_mean': final[..., :3].mean(axis=(0, 1)).tolist()}
        if not entry['finite']:
            raise ValueError(f'{directory.name}: nonfinite lighting signal')
        if directory.name.startswith('nrd'):
            signals = [read_exr(directory / (name + '.exr')) for name in ('diffuse', 'specular', 'independent')]
            if any(signal.shape != raw.shape or not np.isfinite(signal).all() for signal in signals):
                raise ValueError(f'{directory.name}: invalid split lighting signal')
            total = np.clip(sum(signals)[..., :3], 0, 65504)
            error = np.abs(total - raw[..., :3]) / np.maximum(raw[..., :3], .001)
            entry['sum_max_relative'] = float(error.max())
            entry['sum_mean_relative'] = float(error.mean())
            if entry['sum_max_relative'] >= .004:
                raise ValueError(f'{directory.name}: recomposition error {entry["sum_max_relative"]}')
            for name, signal in zip(('diffuse', 'specular', 'independent'), signals):
                entry[name + '_mean'] = signal[..., :3].mean(axis=(0, 1)).tolist()
        report[directory.name] = entry
    if not report:
        raise ValueError('No capture folders containing raw.exr were found.')
    if expected is not None and len(report) != expected:
        raise ValueError(f'Expected {expected} captures, found {len(report)}.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path, help='The instance/signals-locked directory.')
    parser.add_argument('--expected', type=int, help='Full synthetic suite: 10; colour subset: 3.')
    parser.add_argument('--output', type=Path, help='Defaults to the instance signal-validation.json.')
    args = parser.parse_args()
    report = check(args.folder, args.expected)
    output = args.output or args.folder.parent / 'signal-validation.json'
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {len(report)} capture sets; {output}')


if __name__ == '__main__':
    main()
