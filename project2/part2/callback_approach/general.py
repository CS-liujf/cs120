from crc import CrcCalculator, Crc8

from globals import *


def CRC8_encode(data: list[int]):
    # generate crc8 code
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    checksum = crc_calculator.calculate_checksum(data)
    checksum = [int(x) for x in '{0:08b}'.format(checksum)]  # have 8 elements
    return data + checksum


def CRC8_check(frame_body) -> bool:
    data = frame_body[:len(frame_body) - 8]
    checksum = frame_body[len(frame_body) - 8:]
    checksum = int(''.join(map(str, checksum)), 2)
    crc_calculator = CrcCalculator(Crc8.CCITT, True)
    return crc_calculator.verify_checksum(data, checksum)


def write_received_date_to_bin():
    # TODO: store into bin, not .txt
    with open('output.txt', 'w') as f:
        for data in received_data:
            f.write(''.join([str(x) for x in data]))
