from crc import CrcCalculator, Crc8

from globals import *


def CRC8_encode(data: str):
    # generate crc8 code
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    checksum = crc_calculator.calculate_checksum([int(x) for x in data])
    return data + '{0:08b}'.format(checksum)


def CRC8_check(frame_body) -> bool:
    data = frame_body[:len(frame_body) - 8]
    print(f'crc package index {int(data[:8],2)}')
    data = [int(x) for x in data]
    checksum = int('0' + frame_body[len(frame_body) - 8:], 2)
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    res: bool = crc_calculator.verify_checksum(data, checksum)
    if not res:
        print(f"crc: {int(frame_body[len(frame_body)-8:],2)} data: {''.join([str(x) for x in data])}")
    return res


def write_received_date_to_bin():
    # TODO: store into bin, not .txt
    with open('output.txt', 'w') as f:
        for data in received_data:
            if data:
                f.write(''.join([str(x) for x in data]))
