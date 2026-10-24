import pyaudio as pa
import wave

class WaveformPlayer:
  def __init__(self):
    self.p = pa.PyAudio()
    self.stream: pa.Stream | None = None

  def open(self, rate: int, channels: int, format: int):
    self.stream = self.p.open(
      rate=rate,
      channels=channels,
      format=format,
      output=True,
    )
    self.stream.start_stream()
    return self

  def close(self):
    if self.stream is not None:
      self.stream.stop_stream()
      self.stream.close()
      self.stream = None
    self.p.terminate()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.close()

  def play(self, data: bytes):
    if self.stream is not None:
      self.stream.write(data)

  def save_wav(self, filename: str, data: bytes, rate: int, channels: int, format: int):
    with wave.open(filename, 'wb') as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(self.p.get_sample_size(format))
      wf.setframerate(rate)
      wf.writeframes(data)
