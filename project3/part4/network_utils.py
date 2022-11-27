'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''
import struct
from dataclasses import dataclass
import time


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


def float2list(f: float):
    return binstr2list(float2bin(f))

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


def get_ICMP_payload(ip_datagram: list[int]) -> list[float]:
    res = []
    ip_datagram = ip_datagram[IP_HEADER_LEN:]
    for i in range(0, len(ip_datagram), 32):
        res.append(bin2float(''.join(map(str, ip_datagram[i*32: (i+1)*32]))))
    return res


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
    pseudo = struct.pack('!BBHHH', 8, 0, 0, ident, seq) + payload
    checksum = calculate_checksum(pseudo)
    return pseudo[:2] + checksum + pseudo[4:]


def send_routine(sock, addr, ident, magic, data: list[float]):
    seq = 1
    # packet current time to payload
    # in order to calculate round trip time from reply
    payload = struct.pack('!'+'d'*len(data), *data) + magic
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


def recv_routine(sock):
    # wait for another icmp packet
    icmp_packet, src_addr = sock.recvfrom(46)

    # unpack it
    result = unpack_icmp_echo_reply(icmp_packet[20:])
    # print('收到了')

    # print info
    _ident, seq, payload = result

    chars, = struct.unpack('!'+'d'*(len(payload)//4), payload)
    return float2list(chars), SOCKET(*src_addr)


def gen_IP_ICMP_datagram(payload: list[int], _socket: SOCKET):
    s_ip_int = ip2int(_socket.ip)
    d_ip_int = ip2int('192.168.1.2')
    s_addr_list = dec_to_bin_list(s_ip_int, 32)
    d_addr_list = dec_to_bin_list(d_ip_int, 32)
    return s_addr_list + d_addr_list + payload


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
