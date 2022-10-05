import struct
import pyaudio
import numpy as np
import time
import wave
from numpy._typing import NDArray

CARRIER_WAVE_FREQ = 10_000  # Hz
CARRIER_ANGLE_FREQ = 2 * np.pi * CARRIER_WAVE_FREQ  # angle=2·pi·w
BIT_RATE = 1000
BIT_DURATION = 1 / BIT_RATE
DAC_SAMPLE_RATE = 48_000  # fs

CHANNELS = 1
FORMAT = pyaudio.paFloat32
CHUNK = 1024
WAV_FILE = 'record_part3.wav'
OUTPUT_FILE = 'OUTPUT.TXT'

BIT_NUMBER = 10_000  # total 10000 bits
SEQUENCE_LENGTH = 8  # begin seq=end seq=01111110
HEADER_LENGTH = 7  # 7 bit to represent effective bits in body
INCREASE_RATE = 1.2  # the increase rate after 0 is added after five 1
INCASE_TIME = 1.0  # incase time
BODY_BIT_NUMBER = 100
TOTAL_DURATION = 8  # tmp
# BIT_DURATION * (
# BIT_NUMBER * INCREASE_RATE +
# SEQUENCE_LENGTH * 2 * BIT_NUMBER / BODY_BIT_NUMBER)

HEADER_FIND_FRAMES = 500


def sig_carrier_wave():
    return np.sin(CARRIER_ANGLE_FREQ *
                  np.arange(0, BIT_DURATION, 1 / DAC_SAMPLE_RATE))


def sig_zero() -> NDArray:
    '''return the `np.float32` type signal 0 with PSK, sin signal'''
    return sig_carrier_wave().astype(np.float32)


def sig_one() -> NDArray:
    '''return the `np.float32` type signal 1 with PSK, cos signal'''
    return (-sig_carrier_wave()).astype(np.float32)


def generate_being_seq() -> NDArray:
    '''
    generate the header and tail signal `01111110`

    Return the header signal in `np.float32` type
    '''
    one = sig_one()
    zero = sig_zero()
    return np.concatenate([zero] + [one] * 6 + [zero])


def record(pa: pyaudio.PyAudio, duration):
    '''
    Record audio and store into wav file.
    '''
    stream = pa.open(rate=DAC_SAMPLE_RATE,
                     channels=CHANNELS,
                     format=FORMAT,
                     input=True,
                     frames_per_buffer=CHUNK)
    frames = []
    print('Recording...')
    for _ in range(0, int(DAC_SAMPLE_RATE * duration / CHUNK)):
        frames.append(stream.read(CHUNK))
    print('Recording finished.')

    stream.stop_stream()
    stream.close()

    with wave.open(WAV_FILE, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(DAC_SAMPLE_RATE)
        wf.writeframes(b''.join(frames))


def decode():
    '''
    decode the WAV_FILE and store the 0,1 bit information into OUTPUT_FILE
    '''
    def get_begin_seq_offset(wf: wave.Wave_read, seq_frames: int) -> int:
        try_frames = wf.readframes(seq_frames)
        unpacked_data = np.asarray(struct.unpack('f'*seq_frames, try_frames))
        begin_seq_data = generate_being_seq()
        corr = np.correlate(unpacked_data, begin_seq_data, mode='full')
        return np.argmax(corr)-len(begin_seq_data)+1

    def get_next_bit(wf: wave.Wave_read, sig_length: int) -> int:
        data = wf.readframes(sig_length)
        unpacked_data = np.asarray(struct.unpack('f'*sig_length, data))
        product_sum = sum(sig_one()*unpacked_data)
        return 1 if product_sum > 0 else 0

    def get_effective_bits_number(wf, sig_length) -> int:
        # header's 7 bits means the effective length of body
        return int(''.join([str(get_next_bit(wf, sig_length)) for _ in range(HEADER_LENGTH)]), 2)

    wf = wave.open(WAV_FILE, 'rb')
    nframes = wf.getnframes()
    header = generate_being_seq()
    header_len = len(header)
    bit_frame_len = len(sig_one())

    # get body of each packed frame(beginSeq+header+data+endSeq)
    final_data = []
    for _ in range(int(1.2*BIT_NUMBER/BODY_BIT_NUMBER)):
        print(_)
        if wf.tell()+115*bit_frame_len >= nframes:
            break
        # current wf pointer
        cur_tell = wf.tell()
        # find the begin seq
        begin_seq_offset = get_begin_seq_offset(wf, HEADER_FIND_FRAMES)
        cur_pos = cur_tell + begin_seq_offset + header_len
        # set position to real data starts
        wf.setpos(cur_pos)
        # get total effective bit number
        effe_bits_num = get_effective_bits_number(wf, bit_frame_len)
        # decode following effective bits
        for i in range(BODY_BIT_NUMBER):
            if i < effe_bits_num:
                final_data.append(get_next_bit(wf, bit_frame_len))

    # decode the bodys
    def decode_body(data: str) -> str:
        cnt = 0
        res = ''
        for bit in data:
            if bit == '0':
                if cnt < 5:
                    res += bit
                cnt = 0
            else:
                cnt += 1
                res += bit
        return res

    with open(OUTPUT_FILE, 'w') as f:
        f.write(decode_body(''.join([str(x) for x in final_data])))


if __name__ == '__main__':
    start_time = time.time()

    # record and store into WAV_FILE
    pa = pyaudio.PyAudio()
    record(pa, TOTAL_DURATION)
    pa.terminate()

    # decode and store result
    decode()

    print('total time:', time.time() - start_time)
