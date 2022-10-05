'''
reference:
[1]https://stackoverflow.com/questions/30675731/howto-stream-numpy-array-into-pyaudio-stream
'''
import pyaudio
import numpy as np

duration = 3  # set the duration of the signal
fs = 48 * 10**3  # set 48KHz
samples = np.arange(0, duration, 1 / fs)
signal = np.sin(2 * np.pi * 1000 * samples) + np.sin(
    2 * np.pi * 10000 * samples)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)
data = (signal / 2).astype(np.float32).tobytes()
stream.write(data)
stream.stop_stream()
stream.close()
p.terminate()
