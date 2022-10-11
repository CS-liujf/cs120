import numpy as np
from numpy.typing import NDArray
from scipy import integrate
# import pyaudio
import random
import time
import soundfile as sf
import sounddevice as sd


def read_data():
    with open('input.txt', 'r') as f:
        bit_stream = f.read()

    temp = [int(bit) for bit in bit_stream]
    return [temp[i:i + 100] for i in range(0, len(temp), 100)]


t1 = time.time()
frames = read_data()
frames.append([random.random() for _ in range(100)])
frames.append([random.random() for _ in range(100)])

second = 0.001
f = 48000
fc = 4_000

output_track: list[NDArray] = []
output_track.append(np.zeros(random.randint(200, 201)))
t = np.arange(0, 1, 1 / f)
carrier = np.sin(2 * np.pi * fc * t)

f_p = np.concatenate([
    np.linspace(10_000 - 8000, 10_000, 220),
    np.linspace(10_000, 10_000 - 8000, 220)
])
omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
preamble = np.sin(omega)

for i, frame in enumerate(frames):
    frame_wave = np.zeros(100 * 44)
    for j in range(len(frame)):
        frame_wave[j * 44:44 +
                   j * 44] = carrier[j * 44:44 + j * 44] * (frame[j] * 2 - 1)

    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(random.randint(200, 200))
    output_frame: NDArray = np.concatenate([frame_wave_pre, inter_space])
    output_track.append(output_frame.astype(np.float32))

output_track.append(np.array([random.random() for _ in range(200)]))

sf.write('temp_out.wav', np.concatenate(output_track), samplerate=f)

sd.play(np.concatenate(output_track), samplerate=f, blocking=True)
# p = pyaudio.PyAudio()
# stream = p.open(format=pyaudio.paFloat32, channels=1, rate=f, output=True)
# for i, frame in enumerate(output_track):
#     stream.write(frame.tobytes())
t2 = time.time()
print(f'time:{t2-t1}')

if __name__ == '__main__':
    pass
