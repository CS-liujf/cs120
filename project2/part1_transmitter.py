'''
https://www.cnpython.com/qa/934257
'''
import time
import random
import numpy as np
from scipy import integrate
import sounddevice as sd

NDArray = int


def read_data():
    with open('./INPUT.bin', 'rb') as f:
        res = f.read()
        bit_stream = ''.join(['{0:08b}'.format(x) for _, x in enumerate(res)])

    temp = [int(bit) for bit in bit_stream]
    return [temp[i:i + 100] for i in range(0, len(temp), 100)]

    # print(res[:10])


t1 = time.time()
frames = read_data()
frames.append([random.random() for _ in range(100)])
frames.append([random.random() for _ in range(100)])

second = 0.001
f = 48000
fc = 4_000
bit_len = 6

output_track: list[NDArray] = []
output_track.append(np.zeros(random.randint(200, 201)))
t = np.arange(0, 1, 1 / f)
# carrier = np.sin(2 * np.pi * fc * t)
carrier = np.array([-1, -1, -1, 1, 1, 1])

f_p = np.concatenate([
    np.linspace(10_000 - 8000, 10_000, 220),
    np.linspace(10_000, 10_000 - 8000, 220)
])
omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
preamble = np.sin(omega)

for i, frame in enumerate(frames):
    frame_wave = np.zeros(len(frame) * bit_len)
    for j in range(len(frame)):
        frame_wave[j * bit_len:(j + 1) *
                   bit_len] = carrier * (frame[j] * 2 - 1) * 0.5

    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(random.randint(0, 50))
    output_frame: NDArray = np.concatenate([frame_wave_pre, inter_space])
    output_track.append(output_frame.astype(np.float32))

output_track.append(np.array([random.random() for _ in range(200)]))

# sf.write('temp_out.wav', np.concatenate(output_track), samplerate=f)
print('start')
sd.play(np.concatenate(output_track), samplerate=f, blocking=True)
# p = pyaudio.PyAudio()
# stream = p.open(format=pyaudio.paFloat32, channels=1, rate=f, output=True)
# for i, frame in enumerate(output_track):
#     stream.write(frame.tobytes())
t2 = time.time()
print(f'time:{t2-t1}')

# if __name__ == '__main__':
#     import time
#     t1 = time.time()
#     res = read_data()
#     t2 = time.time()
#     print(t2 - t1)
#     # print(len(res))
#     print(bytes(2))