import numpy as np
from scipy import integrate
import pyaudio
import random


def generateTest():
    with open('./INPUT.TXT', 'a') as f:
        for _ in range(10000):
            f.write(str(random.choice([0, 1])))


def preamble(fs=48 * 10**3):
    t = np.arange(0, 1, 1 / fs)
    # f_p = np.concatenate([
    #     np.arange(10 * 10**3 - 8 * 10**3, 10 * 10**3, 240 / 8000),
    #     np.arange(10 * 10**3, 10 * 10**3 - 8 * 10**3, 240 / 8000)
    # ])
    f_p = np.concatenate(
        [np.linspace(2000, 10000, 240),
         np.linspace(10000, 2000, 240)])
    # print(len(f_p))
    omega = 2 * np.pi * integrate.cumulative_trapezoid(f_p, t[0:480])
    return np.sin(omega).astype(np.float32).tobytes()


#convert bit stream to frame list
def framing(
    bit_stream: str,
    frame_len: int,
    signal0: bytes,
    signal1: bytes,
):
    # seq = [0, 1, 1, 1, 1, 1, 1, 0]
    # return list(map(lambda x: signal0 if x == 0 else signal1, seq))
    temp = [
        bit_stream[i:i + frame_len]
        for i in range(0, len(bit_stream), frame_len)
    ]
    preamble_ = preamble()

    def frame2bytes(str_frame: str, signal0: bytes, signal1: bytes):
        temp = b''
        for bit in str_frame:
            temp += signal0 if bit == '0' else signal1
        return temp

    #preamble
    return list(
        map(
            lambda frame_str: preamble_ + frame2bytes(frame_str, signal0,
                                                      signal1), temp))


def Play(bit_rate=1000, carrier_wave_frequency=10000, frame_len=100):
    duration = 1 / bit_rate
    fs = 48 * 10**3  # set 48KHz
    samples = np.arange(0, duration, 1 / fs)
    signal0 = np.sin(2 * np.pi * carrier_wave_frequency * samples).astype(
        np.float32).tobytes()
    signal1 = -1 * np.sin(2 * np.pi * carrier_wave_frequency * samples).astype(
        np.float32).tobytes()
    # print(signal0[0:10])
    with open('./INPUT.TXT', 'r') as f:
        bit_stream = f.read()

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=fs, output=True)

    frame_list = framing(bit_stream, frame_len, signal0, signal1)

    for i, frame in enumerate(frame_list):
        stream.write(frame)
        # for j, bit in enumerate(frame):
        #     if bit == '0':
        #         stream.write(signal0)
        #     else:
        #         stream.write(signal1)

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == '__main__':
    import time
    t1 = time.time()
    Play(bit_rate=2000)
    t2 = time.time()
    print(t2 - t1)
    # b = b''
    # b += b'r'
    # b += b
    # print(b)
