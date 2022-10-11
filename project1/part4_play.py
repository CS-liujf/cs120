import numpy as np
from numpy.typing import NDArray
from scipy import integrate
# import pyaudio
import random
import time
import soundfile as sf
import sounddevice as sd


class Hamming():
    @classmethod
    def calcRedundantBits(self, m: int):

        # Use the formula 2 ^ r >= m + r + 1
        # to calculate the no of redundant bits.
        # Iterate over 0 .. m and return the value
        # that satisfies the equation

        for i in range(m):
            if (2**i >= m + i + 1):
                return i

    @classmethod
    def posRedundantBits(self, data: str, r: int):

        # Redundancy bits are placed at the positions
        # which correspond to the power of 2.
        j = 0
        k = 1
        m = len(data)
        res = ''

        # If position is power of 2 then insert '0'
        # Else append the data
        for i in range(1, m + r + 1):
            if (i == 2**j):
                res = res + '0'
                j += 1
            else:
                res = res + data[-1 * k]
                k += 1

    # The result is reversed since positions are
    # counted backwards. (m + r+1 ... 1)
        return res[::-1]

    @classmethod
    def calcParityBits(self, arr, r) -> str:
        n = len(arr)

        # For finding rth parity bit, iterate over
        # 0 to r - 1
        for i in range(r):
            val = 0
            for j in range(1, n + 1):

                # If position has 1 in ith significant
                # position then Bitwise OR the array value
                # to find parity bit value.
                if (j & (2**i) == (2**i)):
                    val = val ^ int(arr[-1 * j])
                # -1 * j is given since array is reversed

        # String Concatenation
        # (0 to n - 2^r) + parity bit + (n - 2^r + 1 to n)
            arr = arr[:n - (2**i)] + str(val) + arr[n - (2**i) + 1:]
        return arr

    @classmethod
    def detectError(self, data: str):
        n = len(data)
        nr = Hamming.calcRedundantBits(n)
        res = 0

        # Calculate parity bits again
        for i in range(nr):
            val = 0
            for j in range(1, n + 1):
                if (j & (2**i) == (2**i)):
                    val = val ^ int(data[-1 * j])

        # Create a binary no by appending
        # parity bits together.

            res = res + val * (10**i)

    # Convert binary to decimal
        return n - int(str(res), 2)

    @classmethod
    def encode(self, data: str):
        m = len(data)
        r = Hamming.calcRedundantBits(m)
        arr = Hamming.posRedundantBits(data, r)
        arr = Hamming.calcParityBits(arr, r)
        return arr


# Hamming.calcRedundantBits()
print(Hamming.encode('1011001'))
print(Hamming.detectError('11101001110'))


def read_data():
    with open('input.txt', 'r') as f:
        bit_stream = f.read()

    temp = [bit_stream[i:i + 100] for i in range(0, len(bit_stream), 100)]
    temp = list(map(lambda x: Hamming.encode(x), temp))
    return [[int(bit) for bit in code] for code in temp]


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
    frame_wave = np.zeros(len(frame) * 44)
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