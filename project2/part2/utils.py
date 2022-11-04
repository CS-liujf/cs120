from signal import signal
import numpy as np
from scipy import integrate
import random
from crc import CrcCalculator, Crc8


def CRC8_encode(data: list[int]):
    #generate crc8 code
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    checksum = crc_calculator.calculate_checksum(data)
    checksum = [int(x) for x in '{0:08b}'.format(checksum)]  # have 8 elements
    return data + checksum


def CRC8_check(frame_body) -> bool:
    data = frame_body[:len(frame_body) - 8]
    checksum = frame_body[len(frame_body) - 8:]
    checksum = int(''.join(map(str, checksum)),
                   2)  #convet [1,0,0,1,1,1,0,1] to decimal number
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    return crc_calculator.verify_checksum(data, checksum)


second = 0.001
f = 48000
fc = 4_000
t = np.arange(0, 1, 1 / f)
baseband = np.array([-1, -1, -1, 1, 1, 1])
bit_len = len(baseband)
CHUNK = 2048


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


def gen_Mac_frame(payload: list[int],
                  frame_dest=0,
                  frame_src=0,
                  frame_seq: int = 0,
                  is_ACK=False):
    if not is_ACK:
        dest_with_src = [0 for _ in range(8)]
        frame_type = [0 for _ in range(4)]  #0000 for not ACK
        seq = [int(x) for x in '{0:08b}'.format(frame_seq)]
        return dest_with_src + frame_type + seq + payload
    else:
        pass


def gen_PHY_frame(mac_frame: list[int]) -> np.ndarray:
    frame_wave = np.zeros(len(mac_frame) * bit_len)
    for j in range(len(mac_frame)):
        frame_wave[j * bit_len:(j + 1) *
                   bit_len] = 0.5 * (mac_frame[j] * 2 - 1) * baseband
    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(20)
    return np.concatenate([frame_wave_pre, inter_space]).astype(np.float32)


def extract_PHY_frame(stream_data: bytes) -> np.ndarray | None:
    SIMILARITY = 0.4
    REF: float = np.correlate(preamble, preamble)[0]
    preamble_len = len(preamble)
    data: np.ndarray = np.frombuffer(stream_data, dtype=np.float32)
    # data_len = len(data)
    # print(len(data))
    # currently data_len=2048 since we set the CHUNK=2048
    # the origninal phyframe length is 1180
    # preamble length is 440
    cor_arr = np.correlate(data, preamble)
    max_idx = np.argmax(cor_arr)
    # print(f'max_id: {max_idx}')
    # print(max_cor)
    print(f'similarity:{cor_arr[max_idx] / REF}')
    if (cor_arr[max_idx] / REF > SIMILARITY) and (CHUNK - max_idx) > 1160:
        # this means that we detec a frame
        # print(f'max_id: {max_idx}')
        return data[max_idx:max_idx + 1160]
    else:
        return None


def extract_MAC_frame(phy_frame: np.ndarray) -> np.ndarray | None:
    # this function first decode phy_frame to binary form
    SIGNAL_ONE = np.array([-0.5, -0.5, -0.5, 0.5, 0.5, 0.5])
    frame_without_preamble = phy_frame[len(preamble):]
    frame_len = int(len(frame_without_preamble) / bit_len)
    decoded_frame = [
        (1 if
         (frame_without_preamble[i * bit_len:(i + 1) * bit_len] @ SIGNAL_ONE) >
         0 else 0) for i in range(frame_len)
    ]
    # then we should check whether this frame is correct by CRC or Hamming
    pass
    # after that, the CRC or Hamming code must be removed and return
    pass
    return np.array(decoded_frame)


def get_ACK_id(mac_frame: np.ndarray) -> int:
    #this function will return a positive number only if mac_frame is an ACK frame. Otherwise, it will return -1
    ACK_type = [0, 0, 0, 0]
    if not (all(mac_frame[8:12] == ACK_type)):
        return -1
    else:
        payload = mac_frame[20:]
        #calculate ACK_id
        pass
        return payload[3]


if __name__ == '__main__':
    # print(len(preamble))
    data = [1 for _ in range(120)]
    frame = CRC8_encode(data)
    print(len(frame))
    data2 = [1 for _ in range(128)]
    print(CRC8_check(frame))
