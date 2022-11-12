from signal import signal
import numpy as np
from scipy import integrate
import random
from crc import CrcCalculator, Crc8
from queue import Queue


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
carrier = np.sin(2 * np.pi * 1000 * t)
# baseband = np.array([1, 1, 1, -1, -1, -1])
baseband = carrier[:6]
bit_len = len(baseband)
SIGNAL_ONE = baseband / 2
CHUNK = 20480
DUMMY = np.zeros(10).astype(np.float32)


def read_data():
    with open('./INPUT.bin', 'rb') as f:
        res = f.read()
        bit_stream = ''.join(['{0:08b}'.format(x) for _, x in enumerate(res)])

        temp = [int(bit) for bit in bit_stream]
        return [
            temp[i:i + MAC_PAYLOAD_LEN]
            for i in range(0, len(temp), MAC_PAYLOAD_LEN)
        ]


PREAMBLE_LEN = 440
MAC_DEST_LEN = 4
MAC_SRC_LEN = 4
MAC_TYPE_LEN = 4
MAC_SEQ_LEN = 10
MAC_PAYLOAD_LEN = 1000
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


def dec_to_bin_list(number: int, length: int) -> list[int]:
    return [int(x) for x in f'{{0:0{length}b}}'.format(number)]


def gen_Mac_frame(payload: list[int] = None,
                  frame_dest=0,
                  frame_src=0,
                  frame_seq: int = 0,
                  is_ACK=False,
                  mac_frame_received=None):
    if not is_ACK:
        dest_with_src = [0 for _ in range(MAC_DEST_LEN + MAC_SRC_LEN)]
        frame_type = [0 for _ in range(MAC_TYPE_LEN)]  #0000 for not ACK
        seq = dec_to_bin_list(frame_seq, MAC_SEQ_LEN)
        return dest_with_src + frame_type + seq + payload
    else:
        dest_with_src = [0 for _ in range(MAC_DEST_LEN + MAC_SRC_LEN)]
        frame_type = [1 for _ in range(MAC_TYPE_LEN)]
        seq = [0 for _ in range(MAC_SEQ_LEN)]
        ack_payload = dec_to_bin_list(
            frame_seq, 10)  #get seq numbe Like [0,0,0,0,0,0,0,0,0,1]
        return dest_with_src + frame_type + seq + ack_payload


def gen_PHY_frame(mac_frame: list[int]) -> np.ndarray:
    mac_len = dec_to_bin_list(
        len(mac_frame), 10)  # 10-bit list to show the length of mac_frame
    mac_frame_CRC8 = CRC8_encode(mac_len + mac_frame)
    frame_wave = np.zeros(len(mac_frame_CRC8) * bit_len)
    for j in range(len(mac_frame_CRC8)):
        frame_wave[j * bit_len:(j + 1) *
                   bit_len] = 1 * (mac_frame_CRC8[j] * 2 - 1) * baseband
    frame_wave_pre = np.concatenate([preamble, frame_wave])
    inter_space = np.zeros(20)
    return np.concatenate([frame_wave_pre, inter_space]).astype(np.float32)


def decode_phy_frame(frame: np.ndarray) -> list[int]:
    frame_len = int(len(frame) / bit_len)
    decoded_frame = [
        (1 if (frame[i * bit_len:(i + 1) * bit_len] @ SIGNAL_ONE) > 0 else 0)
        for i in range(frame_len)
    ]
    return decoded_frame


def bin_list_to_dec(bin_list: list[int]) -> int:
    return int(''.join(map(str, bin_list)), 2)


def input_process(input_queue: Queue, Rx_ACK_queue: Queue,
                  Rx_MAC_queue: Queue):
    class Rx_MAC_Item(NamedTuple):
        seq: int
        data: list[int]

    SIMILARITY = 0.45  #about 0.45
    REF: float = np.correlate(preamble, preamble)[0]
    while True:
        if not input_queue.empty():
            stream_data = input_queue.get_nowait()
            data: np.ndarray = np.frombuffer(stream_data, dtype=np.float32)
            cor_arr = np.correlate(data, preamble)
            max_idx = np.argmax(cor_arr)
            if (cor_arr[max_idx] / REF < SIMILARITY):
                continue
            elif (CHUNK - max_idx) > (PREAMBLE_LEN + 10 * bit_len):
                len_list = data[max_idx + PREAMBLE_LEN:max_idx + PREAMBLE_LEN +
                                10 * bit_len]
                len_list = decode_phy_frame(len_list)
                length = bin_list_to_dec(len_list)
                phy_frame_len = PREAMBLE_LEN + (
                    10 + length +
                    8) * bit_len  # preamble+(len+payload+crc)*bit_len
                if (CHUNK - max_idx) <= phy_frame_len:
                    stream_data2 = input_queue.get()
                    data2: np.ndarray = np.frombuffer(stream_data2,
                                                      dtype=np.float32)
                    data = np.concatenate((data, data2))
            else:
                stream_data2 = input_queue.get()
                data2: np.ndarray = np.frombuffer(stream_data2,
                                                  dtype=np.float32)
                data = np.concatenate((data, data2))
                len_list = data[max_idx + PREAMBLE_LEN:max_idx + PREAMBLE_LEN +
                                10 * bit_len]
                len_list = decode_phy_frame(len_list)
                length = bin_list_to_dec(len_list)
                phy_frame_len = PREAMBLE_LEN + (
                    10 + length +
                    8) * bit_len  # preamble+(len+payload+crc)*bit_len
            phy_frame = data[max_idx:max_idx + phy_frame_len]
            print('提取到phy_frame')
            if (mac_frame := extract_MAC_frame(phy_frame)) is not None:
                # chech whther it is an ACK
                if (ACK_id := get_ACK_id(mac_frame)) >= 0:
                    Rx_ACK_queue.put_nowait(ACK_id)

                else:
                    payload = get_MAC_payload(mac_frame)
                    seq = get_MAC_seq(mac_frame)
                    Rx_MAC_queue.put_nowait(Rx_MAC_Item(seq, payload))


def extract_PHY_frame(stream_data: bytes) -> np.ndarray | None:
    SIMILARITY = 0.45  #about 0.45
    REF: float = np.correlate(preamble, preamble)[0]
    PHY_FRAME_LEN = len(preamble) + (MAC_FRAME_LEN + 8) * bit_len  # 8 for CRC8
    # print(f'phy_frame_len: {PHY_FRAME_LEN}')
    data: np.ndarray = np.frombuffer(stream_data, dtype=np.float32)
    # print(f'len(data): {len(data)}')
    # currently data_len=2048 since we set the CHUNK=2048
    # preamble length is 440
    cor_arr = np.correlate(data, preamble)
    max_idx = np.argmax(cor_arr)
    # print(f'max_id: {max_idx}')
    # print(max_cor)
    # print(f'similarity:{cor_arr[max_idx] / REF}')
    # print(
    # f'location: {(CHUNK - max_idx)} Compare: {(CHUNK - max_idx) > PHY_FRAME_LEN}'
    # )
    if (cor_arr[max_idx] / REF > SIMILARITY) and (CHUNK - max_idx) > (
            PREAMBLE_LEN + 10 * bit_len):  # preamble+len,
        # print(f'similarity:{cor_arr[max_idx] / REF}')
        # this means that we detec a frame
        # print(f'max_id: {max_idx}')
        len_list = data[max_idx + PREAMBLE_LEN:max_idx + PREAMBLE_LEN +
                        10 * bit_len]
        len_list = decode_phy_frame(len_list)
        length = bin_list_to_dec(len_list)
        phy_frame_len = PREAMBLE_LEN + (
            10 + length + 8) * bit_len  # preamble+(len+payload+crc)*bit_len
        if (CHUNK - max_idx) > phy_frame_len:
            return data[max_idx:max_idx + phy_frame_len]
    return None


def extract_MAC_frame(phy_frame: np.ndarray) -> list[int] | None:
    # this function first decode phy_frame to binary form
    SIGNAL_ONE = baseband / 2
    frame_without_preamble = phy_frame[len(preamble):]
    decoded_frame = decode_phy_frame(frame_without_preamble)
    # print(len(decoded_frame))
    # then we should check whether this frame is correct by CRC or Hamming
    print('开始校验CRC')
    # print(decoded_frame)
    if CRC8_check(decoded_frame):
        print('CRC校验成功')
        # print(decoded_frame)
        # after that, the CRC or Hamming code must be removed and return
        return decoded_frame[10:len(decoded_frame) - 8]
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
        ACK_id = bin_list_to_dec(ACK_id)
        # print(f'ACK_id:{ACK_id}')
        return ACK_id


def get_MAC_payload(mac_frame: list[int]) -> list[int]:
    return mac_frame[MAC_HEAD_LEN:]


def get_MAC_seq(mac_frame: list[int]) -> int:
    seq_list = mac_frame[MAC_HEAD_LEN - MAC_SEQ_LEN:MAC_HEAD_LEN]
    return bin_list_to_dec(seq_list)


if __name__ == '__main__':
    # # frame = [1 for _ in range(122)]
    # # res = CRC8_encode(frame)
    # # # res[len(res) - 8:]
    # # temp = [1 for _ in range(121)] + [0] + res[len(res) - 8:]
    # # print(CRC8_check(temp))
    # leng = 10
    # a = f'{{0:0{leng}b}}'.format(2)
    # print(a)
    from typing import NamedTuple

    # class A(NamedTuple):
    #     age: int
    #     name: str
    a = np.array([1, 2, 3, 4, 5])
    print(type(np.where(a > 3)[0]))
