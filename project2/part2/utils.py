from signal import signal
import numpy as np
from scipy import integrate
import random


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
        # return the fault bit's index
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


second = 0.001
f = 48000
fc = 4_000
bit_len = 2
t = np.arange(0, 1, 1 / f)
carrier = np.sin(2 * np.pi * fc * t)


def read_data():
    with open('./INPUT.bin', 'rb') as f:
        res = f.read()
        bit_stream = ''.join(['{0:08b}'.format(x) for _, x in enumerate(res)])

        temp = [int(bit) for bit in bit_stream]
        return [temp[i:i + 100] for i in range(0, len(temp), 100)]


def gen_preamble():
    f_p = np.concatenate([
        np.linspace(10_000 - 8000, 10_000, 220),
        np.linspace(10_000, 10_000 - 8000, 220)
    ])
    omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
    return np.sin(omega)


preamble = gen_preamble()


def gen_PHY_frame(mac_frame: list[int]) -> np.ndarray:
    frame_wave = np.zeros(len(mac_frame) * bit_len)
    for j in range(len(mac_frame)):
        frame_wave[j * bit_len:(j + 1) *
                   bit_len] = carrier[j * bit_len:(j + 1) *
                                      bit_len] * (mac_frame[j] * 2 - 1)
    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(random.randint(50, 50))
    return np.concatenate([frame_wave_pre, inter_space]).astype(np.float32)


def temp(stream_data: bytes):
    data: np.ndarray = np.frombuffer(stream_data, dtype=np.float32)
    data_len = len(data)
    # currently data_len=1024 since we set the CHUNK=1024
    # the origninal phyframe length is 730
    # preamble length is 440
    max_cor = max(
        np.correlate(data, preamble) / np.correlate(preamble, preamble))
    # print(max_cor)
    if max_cor > 0:
        # this means that we detec a frame
        pass


# def check_

if __name__ == '__main__':
    pass
