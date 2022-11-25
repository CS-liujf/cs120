'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''
from dataclasses import dataclass


@dataclass(frozen=True)
class SOCKET():
    ip: str
    port: int


@dataclass(frozen=True)
class TRANSPORT_ITEM():
    data: list[int]
    socket: SOCKET


IP_HEADER_LEN = 32 + 32
IP_SRC_LEN = 32
IP_DEST_LEN = 32
IP_PORT_LEN = 16
IP_DATA_LEN = 320


def ip2int(ip: str) -> int:
    return sum(int(v) * 256**(3 - i) for i, v in enumerate(ip.split(".")))


def int2ip(number: int) -> str:
    result = []
    for i in range(4):
        number, mod = divmod(number, 256)
        result.insert(0, mod)
    return ".".join(str(i) for i in result)


def dec_to_bin_list(number: int, length: int) -> list[int]:
    return [int(x) for x in f'{{0:0{length}b}}'.format(number)]


def bin_list_to_dec(bin_list: list[int]) -> int:
    return int(''.join(map(str, bin_list)), 2)


def gen_IP_datagram(payload: list[int], _socket: SOCKET):
    s_ip_int = ip2int('192.168.1.2')
    d_ip_int = ip2int(_socket.ip)
    s_addr_list = dec_to_bin_list(s_ip_int, 32)
    d_addr_list = dec_to_bin_list(d_ip_int, 32)
    tot_len = len(payload)
    return s_addr_list + d_addr_list + payload


def bytes_to_01_list(data: bytes) -> list[int]:
    res = []
    for byte in data:
        res += [*bin(byte)][2:]
    return res


def get_IP_dest(ip_datagram: list[int]) -> str:
    return int2ip(bin_list_to_dec(ip_datagram[IP_SRC_LEN:IP_SRC_LEN + IP_DEST_LEN]))


def get_IP_port(ip_datagram: list[int]) -> int:
    return bin_list_to_dec(ip_datagram[IP_HEADER_LEN:IP_HEADER_LEN + IP_PORT_LEN])


def get_IP_data(ip_datagram: list[int]) -> str:
    payload_bits = ip_datagram[IP_HEADER_LEN+IP_PORT_LEN:]
    payload = [payload_bits[i:i + 8] for i in range(0, IP_DATA_LEN, 8)]
    return ''.join(map(lambda x: chr(bin_list_to_dec(x)), payload))


if __name__ == '__main__':
    temp = [0 for _ in range(320 + 64)]
    temp = [0 for _ in range(64)] + 40 * dec_to_bin_list(74, 8)
    get_IP_data(temp)
    # print(chr(48))
