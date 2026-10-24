import argparse
import sys

import pyaudio as pa

from playmml.mml import parse_mml
from playmml.waveform import WaveformPlayer


def main():
    parser = argparse.ArgumentParser(
        prog="playmml",
        description="Play or convert MML (Music Macro Language) files",
    )
    parser.add_argument("file", help="MML file to play")
    parser.add_argument("-o", "--output", help="Output WAV file path (omit to play directly)")
    parser.add_argument("--sample-rate", type=int, default=44100, help="Sample rate in Hz (default: 44100)")
    parser.add_argument("--ticks-per-beat", type=int, default=480, help="Ticks per beat (default: 480)")
    parser.add_argument("--bit-depth", type=int, default=16, choices=[8, 16, 32], help="Bit depth (default: 16)")
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            mml_text = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    format_map = {8: pa.paInt8, 16: pa.paInt16, 32: pa.paFloat32}
    audio_format = format_map[args.bit_depth]

    sequence = parse_mml(mml_text, ticks_per_beat=args.ticks_per_beat)
    waveform = sequence.to_waveform(sample_rate=args.sample_rate, bit_depth=args.bit_depth)

    player = WaveformPlayer()
    try:
        if args.output:
            player.save_wav(args.output, waveform, rate=args.sample_rate, channels=1, format=audio_format)
            print(f"Saved: {args.output}")
        else:
            with player.open(rate=args.sample_rate, channels=1, format=audio_format):
                player.play(waveform)
    finally:
        player.close()


if __name__ == "__main__":
    main()
