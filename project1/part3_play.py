from tempfile import tempdir
import numpy as np
import pyaudio
import random


def generateTest():
    with open('./INPUT.TXT', 'a') as f:
        for _ in range(10000):
            f.write(str(random.choice([0, 1])))


#convert bit stream to frame list
def HDLC_framing(bit_stream: str, frame_len: int):
    # seq = [0, 1, 1, 1, 1, 1, 1, 0]
    # return list(map(lambda x: signal0 if x == 0 else signal1, seq))
    temp = [
        bit_stream[i:i + frame_len]
        for i in range(0, len(bit_stream), frame_len)
    ]
    sequence = '01111110'

    # insert 0 after any consecutive 1s
    def add_0(data_str: str):
        count = 0
        res = ''
        for bit in data_str:
            res += bit
            if bit == '1':
                count += 1
            if count == 5:
                res += '0'
                count = 0
        return res

    return list(
        map(lambda data_str: sequence + data_str + sequence,
            map(add_0, temp)))  # add beginning and ending sequence


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

    frame_list = HDLC_framing(bit_stream, frame_len)
    for i, frame in enumerate(frame_list):
        for j, bit in enumerate(frame):
            if bit == '0':
                stream.write(signal0)
            else:
                stream.write(signal1)

    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == '__main__':
    import time
    t1 = time.time()
    Play(bit_rate=2000)
    t2 = time.time()
    print(t2 - t1)
