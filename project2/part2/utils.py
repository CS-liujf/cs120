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
DUMMY = np.zeros(10).astype(np.float32)


def read_data():
    with open('./INPUT.bin', 'rb') as f:
        res = f.read()
        bit_stream = ''.join(['{0:08b}'.format(x) for _, x in enumerate(res)])

        temp = [int(bit) for bit in bit_stream]
        return [temp[i:i + 100] for i in range(0, len(temp), 100)]


PREAMBLE_LEN = 440
MAC_DEST_LEN = 4
MAC_SRC_LEN = 4
MAC_TYPE_LEN = 4
MAC_SEQ_LEN = 10
MAC_PAYLOAD_LEN = 100
MAC_HEAD_LEN = MAC_DEST_LEN + MAC_SRC_LEN + MAC_TYPE_LEN + MAC_SEQ_LEN
MAC_FRAME_LEN = MAC_HEAD_LEN + MAC_PAYLOAD_LEN


def gen_preamble():
    f_p = np.concatenate([
        np.linspace(10_000 - 8000, 10_000, 220),
        np.linspace(10_000, 10_000 - 8000, 220)
    ])
    omega = 2 * np.pi * integrate.cumtrapz(f_p, t[0:440], initial=0)
    return np.sin(omega)


preamble = gen_preamble()


def gen_Mac_frame(payload: list[int] = None,
                  frame_dest=0,
                  frame_src=0,
                  frame_seq: int = 0,
                  is_ACK=False,
                  mac_frame_received=None):
    if not is_ACK:
        dest_with_src = [0 for _ in range(MAC_DEST_LEN + MAC_SRC_LEN)]
        frame_type = [0 for _ in range(MAC_TYPE_LEN)]  #0000 for not ACK
        seq = [int(x) for x in f'{{0:0{MAC_SEQ_LEN}b}}'.format(frame_seq)]
        return dest_with_src + frame_type + seq + payload
    else:
        dest_with_src = [0 for _ in range(MAC_DEST_LEN + MAC_SRC_LEN)]
        frame_type = [1 for _ in range(MAC_TYPE_LEN)]
        seq = [0 for _ in range(MAC_SEQ_LEN)]
        ack_payload = mac_frame_received[MAC_HEAD_LEN -
                                         MAC_SEQ_LEN:MAC_HEAD_LEN]
        payload = ack_payload + [
            0 for _ in range(MAC_PAYLOAD_LEN - len(ack_payload))
        ]
        return dest_with_src + frame_type + seq + payload


def gen_PHY_frame(mac_frame: list[int]) -> np.ndarray:
    mac_frame_CRC8 = CRC8_encode(mac_frame)  #128bit
    frame_wave = np.zeros(len(mac_frame_CRC8) * bit_len)
    for j in range(len(mac_frame_CRC8)):
        frame_wave[j * bit_len:(j + 1) *
                   bit_len] = 0.5 * (mac_frame_CRC8[j] * 2 - 1) * baseband
    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(20)
    return np.concatenate([frame_wave_pre, inter_space]).astype(np.float32)


def extract_PHY_frame(stream_data: bytes) -> np.ndarray | None:
    SIMILARITY = 0.45  #about 0.45
    REF: float = np.correlate(preamble, preamble)[0]
    PHY_FRAME_LEN = len(preamble) + (MAC_FRAME_LEN + 8) * bit_len  # 8 for CRC8
    # print(f'phy_frame_len{PHY_FRAME_LEN}')
    data: np.ndarray = np.frombuffer(stream_data, dtype=np.float32)
    # print(f'len(data): {len(data)}')
    # currently data_len=2048 since we set the CHUNK=2048
    # preamble length is 440
    cor_arr = np.correlate(data, preamble)
    max_idx = np.argmax(cor_arr)
    # print(f'max_id: {max_idx}')
    # print(max_cor)
    # print(f'similarity:{cor_arr[max_idx] / REF}')
    if (cor_arr[max_idx] / REF >
            SIMILARITY) and (CHUNK - max_idx) > PHY_FRAME_LEN:
        print(f'similarity:{cor_arr[max_idx] / REF}')
        # this means that we detec a frame
        # print(f'max_id: {max_idx}')
        return data[max_idx:max_idx + PHY_FRAME_LEN]
    else:
        return None


def extract_MAC_frame(phy_frame: np.ndarray) -> list[int] | None:
    # this function first decode phy_frame to binary form
    SIGNAL_ONE = np.array([-0.5, -0.5, -0.5, 0.5, 0.5, 0.5])
    frame_without_preamble = phy_frame[len(preamble):]
    frame_len = int(len(frame_without_preamble) / bit_len)
    decoded_frame = [
        (1 if
         (frame_without_preamble[i * bit_len:(i + 1) * bit_len] @ SIGNAL_ONE) >
         0 else 0) for i in range(frame_len)
    ]
    print(len(decoded_frame))
    # then we should check whether this frame is correct by CRC or Hamming
    print('开始校验CRC')
    print(decoded_frame)
    if CRC8_check(decoded_frame):
        print('CRC校验成功')
        # after that, the CRC or Hamming code must be removed and return
        return decoded_frame[:len(decoded_frame) - 8]
    else:
        return None


def get_ACK_id(mac_frame: list[int]) -> int:
    #this function will return a positive number only if mac_frame is an ACK frame. Otherwise, it will return -1
    ACK_type = [1, 1, 1, 1]
    if not (mac_frame[MAC_DEST_LEN + MAC_SRC_LEN:MAC_HEAD_LEN - MAC_SEQ_LEN]
            == ACK_type):
        return -1
    else:
        payload = mac_frame[MAC_HEAD_LEN:]
        ACK_id = payload[:10]  # like [0,1,1,0,0,1]
        ACK_id = int(''.join(map(str, ACK_id)), 2)
        print(f'ACK_id:{ACK_id}')
        return ACK_id


def get_MAC_payload(mac_frame: np.ndarray) -> list[int]:
    payload: np.ndarray = mac_frame[MAC_HEAD_LEN:]
    return payload.tolist()


if __name__ == '__main__':
    # # frame = [1 for _ in range(122)]
    # # res = CRC8_encode(frame)
    # # # res[len(res) - 8:]
    # # temp = [1 for _ in range(121)] + [0] + res[len(res) - 8:]
    # # print(CRC8_check(temp))
    # leng = 10
    # a = f'{{0:0{leng}b}}'.format(2)
    # print(a)
    payload = [1 for _ in range(100)]
    mac_frame = gen_Mac_frame(payload)
    # print(len(mac_frame))
    print(CRC8_encode(mac_frame))