'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''
import struct
from dataclasses import dataclass
import time
from scapy.all import *


@dataclass(frozen=True)
class SOCKET():
    ip: str
    port: int


@dataclass(frozen=True)
class TRANSPORT_ITEM():
    data: list[int]
    socket: SOCKET


S_IP_LEN = 32
D_IP_LEN = 32
IP_HEADER_LEN = S_IP_LEN + D_IP_LEN


def ip2int(ip: str) -> int:
    return sum(int(v) * 256 ** (3 - i) for i, v in enumerate(ip.split(".")))


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


def bin2float(b: str) -> float:
    ''' Convert binary string to a float.

    Attributes:
        :b: Binary string to transform.
    '''
    h = int(b, 2).to_bytes(8, byteorder="big")
    return struct.unpack('>d', h)[0]


def float2bin(f: float):
    ''' Convert float to 64-bit binary string.

    Attributes:
        :f: Float number to transform.
    '''
    [d] = struct.unpack(">Q", struct.pack(">d", f))
    return f'{d:064b}'


def binstr2list(bin_string: str) -> list[int]:
    return list(map(int, bin_string))


def get_IP_source(ip_datagram: list[int]) -> str:
    s_ip = ip_datagram[:S_IP_LEN]
    ip_num = bin_list_to_dec(s_ip)
    return int2ip(ip_num)


def get_IP_dest(ip_datagram: list[int]):
    s_ip = ip_datagram[S_IP_LEN:S_IP_LEN + D_IP_LEN]
    ip_num = bin_list_to_dec(s_ip)
    return int2ip(ip_num)


def get_IP_payload(ip_datagram: list[int]):
    payload = ip_datagram[IP_HEADER_LEN:]
    payload = [payload[i:i + 8] for i in range(0, len(payload), 8)]
    res = ''.join(map(lambda x: chr(bin_list_to_dec(x)), payload))
    print(res)
    return [1]


def get_ICMP_payload(ip_datagram: list[int]) -> str:
    res = []
    ip_datagram = ip_datagram[IP_HEADER_LEN+16+32:]
    for i in range(0, len(ip_datagram), 8):
        res.append(chr(int(''.join(map(str, ip_datagram[i: (i+8)])), 2)))
    return ''.join(res)


def get_ICMP_id(ip_datagram: list[int]):
    return bin_list_to_dec(ip_datagram[80:96])

def get_ICMP_checksum(ip_datagram):
    return bin_list_to_dec(ip_datagram[64:80])

def get_ICMP_seq(ip_datagram):
    return bin_list_to_dec(ip_datagram[96:112])

def calculate_checksum(icmp):
    highs = icmp[0::2]
    lows = icmp[1::2]

    checksum = ((sum(highs) << 8) + sum(lows))

    while True:
        carry = checksum >> 16
        if carry:
            checksum = (checksum & 0xffff) + carry
        else:
            break

    checksum = ~checksum & 0xffff

    return struct.pack('!H', checksum)


def pack_icmp_echo_request(ident, seq, payload):
    pseudo = struct.pack('!BBHHH', 0, 0, 0, ident, seq) + payload
    checksum = calculate_checksum(pseudo)
    return pseudo[:2] + checksum + pseudo[4:]


def send_routine(sock, addr, ident, magic, data: str, checksum, seq):
    # packet current time to payload
    # in order to calculate round trip time from reply
    payload = data.encode('utf-8')
    # pack icmp packet
    icmp = pack_icmp_echo_request(ident, seq, payload)
    # send it
    sock.sendto(icmp, (addr, 0))


def unpack_icmp_echo_reply(icmp):
    _type, code, _, ident, seq, = struct.unpack('!BBHHH', icmp[:8])
    if _type != 0:
        return
    if code != 0:
        return

    payload = icmp[8:]

    return ident, seq, payload


def bytes2list(payload: bytes) -> list[int]:
    res = []
    for byte in payload:
        res += list(map(int, [*f'{byte:08b}']))
    return res


def recv_routine(sock):
    data = None
    src = None
    id = None
    seq = None
    checksum = None
    def callback(x):
        nonlocal data
        nonlocal src
        nonlocal id
        nonlocal seq
        nonlocal checksum
        data = x['Raw'].load
        src = x['IP'].src
        id = x['ICMP'].id
        seq = x['ICMP'].seq
        checksum = x['ICMP'].chksum
    # wait for another icmp packet
    sni = sniff(filter='icmp && src host 10.20.192.96', prn=callback, count=1)

    return bytes2list(data), SOCKET(src, 0), id, seq, checksum


def gen_IP_ICMP_datagram(payload: list[int], _socket: SOCKET, id, seq, checksum):
    s_ip_int = ip2int(_socket.ip)
    d_ip_int = ip2int('192.168.1.2')
    s_addr_list = dec_to_bin_list(s_ip_int, 32)
    d_addr_list = dec_to_bin_list(d_ip_int, 32)
    return s_addr_list + d_addr_list + dec_to_bin_list(checksum, 16) +dec_to_bin_list(id, 16) + dec_to_bin_list(seq, 16) + payload


def gen_IP_datagram(payload: list[int], _socket: SOCKET):
    s_ip_int = ip2int('192.168.1.2')
    d_ip_int = ip2int(_socket.ip)
    s_addr_list = dec_to_bin_list(s_ip_int, 32)
    d_addr_list = dec_to_bin_list(d_ip_int, 32)
    return s_addr_list + d_addr_list + payload


if __name__ == '__main__':
    temp = [0 for _ in range(320 + 64)]
    temp = [0 for _ in range(64)] + 40 * dec_to_bin_list(74, 8)
    get_IP_payload(temp)
    # print(chr(48))
