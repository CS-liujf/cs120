import numpy as np
from scipy import integrate
import pyaudio
import random
import matplotlib.pyplot as plt


second = 0.001
f = 44100
fc = 10_000

output_tract = np.asarray([])
t = np.arange(0, 1, 1/f)
carrier = np.sin(2*np.pi*fc*t)

f_p = np.concatenate([np.linspace(10_000-8000, 10_000, 220),
                     np.linspace(10_000, 10_000-8000, 220)])
omega = 2*np.pi*integrate.cumtrapz(f_p, t[0:440])
preamble = np.sin(omega)

for i in range(100):
    frame = 