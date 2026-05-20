import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'prop_bench_control'))

from prop_bench_control.throttle_profile import generate_sine_profile, generate_cosine_profile, generate_step_profile
import csv
import argparse

parser = argparse.ArgumentParser(description='Generate a throttle profile CSV.')
parser.add_argument('waveform', choices=['sine', 'cosine', 'step'], help='Waveform type')
parser.add_argument('--amplitude', type=float, default=10)
parser.add_argument('--frequency', type=float, default=0.5)
parser.add_argument('--mean', type=float, default=20)
parser.add_argument('--sampling-rate', type=int, default=100)
parser.add_argument('--duration', type=float, default=10)
parser.add_argument('--output', type=str, default=None, help='Output CSV filename')
parser.add_argument('--steps', type=float, nargs='+', default = None, help='List of step values separated by spaces')
parser.add_argument('--pulse_length', type=float, default=3.0)
args = parser.parse_args()

generators = {
    'sine': generate_sine_profile, 
    'cosine': generate_cosine_profile,
    'step': generate_step_profile}
if args.waveform == 'step':
    data = generators['step'](
        steps = args.steps,
        pulse_length = args.pulse_length,
        sampling_rate = args.sampling_rate
    )
else:
    data = generators[args.waveform](
        amplitude=args.amplitude,
        frequency_hz=args.frequency,
        mean=args.mean,
        sampling_rate=args.sampling_rate,
        duration=args.duration,
    )

profile_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'prop_bench_control', 'throttle_profile')
if args.waveform == 'step':
    n = len(args.steps) if args.steps else 1
    default_name = f'step_{n}pulses_{args.pulse_length}s.csv'
else:
    default_name = f'{args.waveform}_{args.duration}s.csv'
filename = args.output or os.path.join(profile_dir, default_name)
with open(filename, 'w', newline='') as f:
    writer = csv.writer(f)
    for v in data:
        writer.writerow([round(v, 1)])

print(f'Wrote {len(data)} samples to {filename}')
