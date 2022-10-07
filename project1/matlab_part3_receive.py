import struct
import numpy as np
from scipy import integrate
import pyaudio

F = 44100
CHUNK = 1024
FORMAT = pyaudio.paFloat32
CHANNELS = 1
total_duration = 12

BIT_NUMBER = 10_000  # total 10000 bits
BODY_BIT_NUMBER = 100

second = 0.001
f = 44100
fc = 10_000

t = np.arange(0, 1, 1 / f)
carrier = np.sin(2 * np.pi * fc * t)


def gene_preamble():
    f_p = np.concatenate([
        np.linspace(10_000 - 8000, 10_000, 220),
        np.linspace(10_000, 10_000 - 8000, 220)
    ])
    t = np.arange(0, 1, 1 / F)
    omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
    return np.sin(omega)


def record(pa: pyaudio.PyAudio):
    '''
    Record audio and store into wav file.
    '''
    stream = pa.open(rate=F,
                     channels=CHANNELS,
                     format=FORMAT,
                     input=True,
                     frames_per_buffer=CHUNK)
    frames = []
    print('Recording...')
    for _ in range(0, int(F * total_duration / CHUNK)):
        frames.append(stream.read(CHUNK))
    print('Recording finished.')

    stream.stop_stream()
    stream.close()

    data = b''.join(frames)
    print(len(data))
    return np.asarray(struct.unpack_from('f'*(len(data)//4), data))


def smooth(a, WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    out0 = np.convolve(a, np.ones(WSZ, dtype=int), 'valid')/WSZ
    r = np.arange(1, WSZ-1, 2)
    start = np.cumsum(a[:WSZ-1])[::2]/r
    stop = (np.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    return np.concatenate((start, out0, stop))


PREAMBLE_TRY_LENGTH = 4500
PREAMBLE_SIMILAR = 0.99

preamble = gene_preamble()
preamble_len = len(preamble)  # 440
pa = pyaudio.PyAudio()
data = record(pa)
data_len = len(data)
max_energy = np.correlate(preamble, preamble)[0]

index = 0
final_bits = []
for _ in range(BIT_NUMBER//BODY_BIT_NUMBER):
    if data_len - index < 4840:
        break
    # package sync
    while True:
        if index >= data_len-preamble_len-44*100:
            raise
        corr = np.correlate(data[index:index+PREAMBLE_TRY_LENGTH], preamble)
        offset = -1
        for i, cor in enumerate(corr):
            if cor/max_energy >= PREAMBLE_SIMILAR:
                offset = i
                break
        if offset == -1:
            # continue match
            index += PREAMBLE_TRY_LENGTH-preamble_len
        else:
            # matched
            index += offset + preamble_len
            break

    body_data = data[index:index+44*100]
    decode_removecarrier = smooth(body_data*carrier[:len(body_data)], 9)
    decode_power_bit = np.zeros(100)
    for j in range(100):
        decode_power_bit[j] = sum(decode_removecarrier[10+j*44:30+j*44])
    final_bits += [int(x) for x in decode_power_bit > 0]

with open('output.txt', 'w') as f:
    f.write(''.join([str(x) for x in final_bits]))
