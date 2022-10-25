import struct
from unicodedata import name


def byte_to_str(byte):
    temp = int.from_bytes(byte, 'big')
    b = bin(temp)[2:]
    len_add = 8 - len(b)
    return len_add * "0" + b


def read_data():
    with open('./INPUT.bin', 'rb') as f:
        res = f.read()
        bit_stream = ''.join([str(format(x, 'b')) for _, x in enumerate(res)])

    temp = [int(bit) for bit in bit_stream]
    return [temp[i:i + 100] for i in range(0, len(temp), 100)]

    # print(res[:10])


if __name__ == '__main__':
    import time
    t1 = time.time()
    read_data()
    t2 = time.time()
    print(t2 - t1)
