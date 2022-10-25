from scipy import integrate
import numpy as np
import sounddevice as sd


def smooth(a, WSZ):
    # a: NumPy 1-D array containing the data to be smoothed
    # WSZ: smoothing window size needs, which must be odd number,
    # as in the original MATLAB implementation
    out0 = np.convolve(a, np.ones(WSZ, dtype=int), 'valid') / WSZ
    r = np.arange(1, WSZ - 1, 2)
    start = np.cumsum(a[:WSZ - 1])[::2] / r
    stop = (np.cumsum(a[:-WSZ:-1])[::2] / r)[::-1]
    return np.concatenate((start, out0, stop))


fs = 44100
duration = 12

t = np.arange(0, 1, 1 / 44100)
fc = (10**3)
carrier = np.sin(2 * np.pi * fc * t)

f_p = np.concatenate([
    np.linspace(10_000 - 8000, 10_000, 220),
    np.linspace(10_000, 10_000 - 8000, 220)
])
omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
preamble = np.sin(omega)

sound_track = sd.rec(int(duration * fs),
                     samplerate=fs,
                     channels=1,
                     blocking=True)
power = 0
power_debug = np.zeros(len(sound_track))
start_index = 0
start_index_debug = np.zeros(len(sound_track))
syncFIFO = np.zeros(440)
syncPower_debug = np.zeros(len(sound_track))
syncPower_localMax = 0

decodeFIFO = []
decodeFIFO_Full = 1

state = 0

final_bits = []

print(len(sound_track))
for i, bit in enumerate(sound_track):
    current_sample = bit

    power = power * (1 - 1 / 64) + (current_sample**2) / 64
    if state == 0:
        syncFIFO = np.append(syncFIFO[1:], current_sample)
        syncPower_debug[i] = np.dot(syncFIFO, preamble) / 200

        if (syncPower_debug[i] >
            (power * 2)) and (syncPower_debug[i] > syncPower_localMax) and (
                syncPower_debug[i] > 0.05):
            syncPower_localMax = syncPower_debug[i]
            start_index = i
        elif (i - start_index > 200) and (start_index != 0):
            start_index_debug[start_index] = 1.5
            syncPower_localMax = 0
            syncFIFO = np.zeros(len(syncFIFO))
            state = 1
            tempBuffer = sound_track[start_index + 1:i]
            decodeFIFO = tempBuffer

    elif state == 1:
        decodeFIFO = np.append(decodeFIFO, current_sample)
        if len(decodeFIFO) == 44 * 100:
            decodeFIFO_removecarrier = smooth(
                decodeFIFO * carrier[:len(decodeFIFO)], 9)
            decodeFIFO_power_bit = np.zeros(100)
            for j in range(100):
                decodeFIFO_power_bit[j] = sum(
                    decodeFIFO_removecarrier[10 + j * 44:30 + j * 44])
            final_bits += [int(x) for x in decodeFIFO_power_bit > 0]
            start_index = 0
            decodeFIFO = []
            state = 0

with open('output.txt', 'w') as f:
    f.write(''.join([str(x) for x in final_bits]))