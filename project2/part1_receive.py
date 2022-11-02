import time
import numpy as np
from scipy import integrate
import sounddevice as sd
import soundfile as sf

sd.default.device = 1

F = 48000
CHANNELS = 1
total_duration = 16

BIT_NUMBER = 50_000
BODY_BIT_NUMBER = 100

second = 0.001
fc = 4_000

t = np.arange(0, 1, 1 / F)
carrier = np.sin(2 * np.pi * fc * t)


def gene_preamble():
    f_p = np.concatenate([
        np.linspace(10_000 - 8000, 10_000, 220),
        np.linspace(10_000, 10_000 - 8000, 220)
    ])
    t = np.arange(0, 1, 1 / F)
    omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
    return np.sin(omega)


def record():
    '''
    Record audio and store into wav file.
    '''
    print('Recording...')
    data = sd.rec(int(F*total_duration), samplerate=F,
                  channels=CHANNELS, blocking=True, dtype='float32')
    print('Recording finished.')

    sf.write('tmp_received.wav', data, 48000)

    with sf.SoundFile('tmp_received.wav') as wf:
        data = wf.read(dtype=np.float32)
    return data


def smooth(a, WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    out0 = np.convolve(a, np.ones(WSZ, dtype=int), 'valid')/WSZ
    r = np.arange(1, WSZ-1, 2)
    start = np.cumsum(a[:WSZ-1])[::2]/r
    stop = (np.cumsum(a[:-WSZ:-1])[::2]/r)[::-1]
    return np.concatenate((start, out0, stop))


PREAMBLE_TRY_LENGTH = 500
PREAMBLE_SIMILAR = 0.6

start_time = time.time()

bit_len = 4

preamble = gene_preamble()
preamble_len = len(preamble)  # 440
data = record()
data_len = len(data)
print('datalen:', data_len)
corr = np.correlate(preamble, data)
max_energy = max(corr)
print("max_energy:", max_energy)

index = 0
final_bits = []
for _ in range(BIT_NUMBER//BODY_BIT_NUMBER):
    if data_len - index < 0:
        break
    # package sync
    while True:
        if index+PREAMBLE_TRY_LENGTH > data_len:
            break
        corr = np.correlate(data[index:index+PREAMBLE_TRY_LENGTH], preamble)
        offset = -1
        max_index = np.argmax(corr)
        if corr[max_index]/max_energy >= PREAMBLE_SIMILAR:
            print("similarity:", corr[max_index]/max_energy, _)
            offset = max_index
        if offset == -1:
            # continue match
            index += PREAMBLE_TRY_LENGTH-preamble_len
        else:
            # matched
            index += offset + preamble_len
            break

    body_data = data[index:index+bit_len*100]
    decode_removecarrier = body_data*carrier[:len(body_data)]
    decode_power_bit = np.zeros(100)
    for j in range(100):
        decode_power_bit[j] = sum(decode_removecarrier[j*bit_len:2+j*bit_len])
    final_bits += [int(x) for x in decode_power_bit > 0]


with open('output.txt', 'w') as f:
    f.write(''.join([str(x) for x in final_bits]))
print("total time:", time.time()-start_time)
