from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

import numpy as np


class WaveForms:
  @staticmethod
  def sin(t: np.ndarray) -> np.ndarray:
    return np.sin(t)

  @staticmethod
  def square(t: np.ndarray) -> np.ndarray:
    return np.sign(np.sin(t))

  @staticmethod
  def sawtooth(t: np.ndarray) -> np.ndarray:
    return 2 * (t / (2 * np.pi) - np.floor(t / (2 * np.pi) + 0.5))


@dataclass
class Note:
  pitch: int
  _begin: int
  _duration: int
  _volume: int = 100

  @property
  def frequency(self) -> float:
    return 440.0 * 2 ** ((self.pitch - 69) / 12)

  @classmethod
  def middle_c(cls) -> Self:
    return cls(pitch=60, _begin=0, _duration=1)

  @classmethod
  def get_by_symbol(cls, symbol: str) -> Self:
    """parse a note symbol like 'C4' and return a Note instance.

    octave number can be any integer value, including negative octaves.
    """

    note_map = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}

    if '#' in symbol:
      note, octave = symbol[:-1], int(symbol[-1])
    else:
      note, octave = symbol[0], int(symbol[1])
    pitch = 12 * (octave + 1) + note_map[note]

    return cls(pitch=pitch, _begin=0, _duration=1)

  @property
  def end(self) -> float:
    return self._begin + self._duration

  def get_duration_in_seconds(self, ticks_per_second: float) -> float:
    return self._duration / ticks_per_second

  def get_begin_in_seconds(self, ticks_per_second: float) -> float:
    return self._begin / ticks_per_second

  def get_end_in_seconds(self, ticks_per_second: float) -> float:
    return self.end / ticks_per_second

@dataclass
class NoteSequence:
  _notes: list[Note]
  _ticks_per_beat: int
  _tempo: int

  @property
  def ticks_per_second(self) -> float:
    return self._ticks_per_beat * self._tempo / 60

  def to_waveform(self, from_sec: float = 0, to_sec: float | None = None, sample_rate: int = 44100, bit_depth: int = 16, waveform_func: Callable[[np.ndarray], np.ndarray] = WaveForms.square):
    notes_in_range = [note for note in self._notes if note.get_end_in_seconds(self.ticks_per_second) > from_sec and (to_sec is None or note.get_begin_in_seconds(self.ticks_per_second) < to_sec)]
    duration = to_sec - from_sec if to_sec is not None else max(note.get_end_in_seconds(self.ticks_per_second) for note in notes_in_range) - from_sec
    t = np.linspace(from_sec, from_sec + duration, int(sample_rate * duration), endpoint=False)
    waveform = np.zeros_like(t)

    for note in notes_in_range:
      start_idx = int((note.get_begin_in_seconds(self.ticks_per_second) - from_sec) * sample_rate)
      end_idx = int((note.get_end_in_seconds(self.ticks_per_second) - from_sec) * sample_rate)
      end_idx = min(end_idx, len(t))
      gain = note._volume / 100
      waveform[start_idx:end_idx] += gain * waveform_func(2 * np.pi * note.frequency * t[start_idx:end_idx])

    waveform = np.clip(waveform, -1, 1)
    if bit_depth == 8:
      return (waveform * 127).astype(np.int8).tobytes()
    elif bit_depth == 16:
      return (waveform * 32767).astype(np.int16).tobytes()
    elif bit_depth == 32:
      return waveform.astype(np.float32).tobytes()
    else:
      raise ValueError(f"Unsupported bit depth: {bit_depth}")