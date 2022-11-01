import numpy as np
from scipy import integrate
import random

from project1.lcq_part3_decode import Preamble

second = 0.001
f = 48000
fc = 4_000
bit_len = 2
t = np.arange(0, 1, 1 / f)
carrier = np.sin(2 * np.pi * fc * t)


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
    inter_space = np.zeros(random.randint(0, 50))
    return np.concatenate([frame_wave_pre, inter_space])
