import numpy as np
from numpy.typing import NDArray
from scipy import integrate
import pyaudio
import random


def read_data():
    with open('./INPUT.TXT', 'r') as f:
        bit_stream = f.read()

    temp = [int(bit) for bit in bit_stream]
    # print(temp[:10])
    return [temp[i:i + 100] for i in range(0, len(temp), 100)]


frames = read_data()

second = 0.001
f = 44100
fc = 10_000

output_track: list[NDArray] = []
t = np.arange(0, 1, 1 / f)
carrier = np.sin(2 * np.pi * fc * t)

f_p = np.concatenate([
    np.linspace(10_000 - 8000, 10_000, 220),
    np.linspace(10_000, 10_000 - 8000, 220)
])
omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
preamble = np.sin(omega)

for frame in frames:
    frame_wave = np.zeros(100 * 44)
    for j in range(len(frame)):
        frame_wave[j * 44:44 +
                   j * 44] = carrier[j * 44:44 + j * 44] * (frame[j] * 2 - 1)

    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(random.randint(0, 100))
    output_frame = np.concatenate([inter_space, frame_wave])
    inter_space = np.zeros(random.randint(0, 100))
    output_frame: NDArray = np.concatenate([output_frame, inter_space])
    output_track.append(output_frame.astype(np.float32))

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paFloat32, channels=1, rate=f, output=True)
for i, frame in enumerate(output_track):
    stream.write(frame.tobytes())

if __name__ == '__main__':
    pass