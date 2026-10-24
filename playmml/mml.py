from playmml.note import Note, NoteSequence


def parse_mml(mml: str, ticks_per_beat: int = 480) -> NoteSequence:
  """Parse a Music Macro Language (MML) string and return a NoteSequence instance.

  MML directives:
    'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B' for notes
    'L' for default note length
    'O' for octave
    'T' for tempo
    'R' for rest
    '>' to increase octave
    '<' to decrease octave
    'V' for volume
    'BEGIN' to start a chord
    'END' to end a chord
    'REM' for comments, skip parsing until the following ';'

  Example:
    parse_mml("T120 O4 L480 C D E F G A B")
    parse_mml("T120 O4 L480 C D E F G A B BEGIN C E G END")
  """

  # Sequence of notes as tuples (note, octave, length, volume, tempo)
  seq: list[tuple[str, int, int, int, int] | list[tuple[str, int, int, int, int]]] = []
  chord_notes: list[tuple[str, int, int, int, int]] | None = None
  comment: bool = False
  tempo: int = 120
  octave: int = 4
  default_length: int = 4
  volume: int = 100

  for token in mml.split():
    if comment:
      if token.endswith(";"):
        comment = False
      continue
    if token.startswith("REM"):
      comment = True
      continue
    if token.startswith("T"):
      # Set tempo
      tempo = int(token[1:])
      continue
    if token.startswith("O"):
      # Set octave
      octave = int(token[1:])
      continue
    if token.startswith("L"):
      # Set default note length
      default_length = int(token[1:])
      continue
    if token.startswith("V"):
      # Set volume
      volume = int(token[1:])
      continue
    if token in ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"):
      # Add note
      if chord_notes is not None:
        chord_notes.append((token, octave, default_length, volume, tempo))
      else:
        seq.append((token, octave, default_length, volume, tempo))
      continue
    if token == "R":
      # Add rest
      if chord_notes is not None:
        chord_notes.append(("R", octave, default_length, volume, tempo))
      else:
        seq.append(("R", octave, default_length, volume, tempo))
      continue
    if token == ">":
      octave += 1
      continue
    if token == "<":
      octave -= 1
      continue
    if token == "BEGIN":
      chord_notes = []
      continue
    if token == "END":
      if chord_notes is not None:
        seq.append(chord_notes)
        chord_notes = None
      continue
  
  notes: list[Note] = []
  # find the universal tempo across all notes
  universal_tempo = max(ev[4] if isinstance(ev, tuple) else max(n[4] for n in ev) for ev in seq)
  # cumulative time in ticks
  current_time = 0

  for ev in seq:
    if isinstance(ev, tuple):
      note, octave, length, volume, tempo = ev

      # adjust length according to tempo
      length = length * universal_tempo // tempo

      if note == "R":
        current_time += length
        continue

      note = Note.get_by_symbol(f"{note}{octave}")
      note._begin = current_time
      note._duration = length
      note._volume = volume
      current_time += length
      notes.append(note)
    else:
      max_dur = max(n[2] * universal_tempo // n[4] for n in ev)
      for n in ev:
        note, octave, length, volume, tempo = n
        if note == "R":
          continue
        note = Note.get_by_symbol(f"{note}{octave}")
        note._begin = current_time
        # adjust length according to tempo
        length = length * universal_tempo // tempo
        note._duration = length
        note._volume = volume
        notes.append(note)

      current_time += max_dur

  return NoteSequence(notes, ticks_per_beat, universal_tempo)
