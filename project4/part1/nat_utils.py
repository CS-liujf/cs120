'''
https://blog.csdn.net/weixin_42000303/article/details/122182539
'''
import struct
from dataclasses import dataclass
from tcp_utils import SOCKET, D_ADDR
import time


def ip2int(ip: str) -> int:
    return sum(int(v) * 256**(3 - i) for i, v in enumerate(ip.split(".")))


def int2ip(number: int) -> str:
    result = []
    for i in range(4):
        number, mod = divmod(number, 256)
        result.insert(0, mod)
    return ".".join(str(i) for i in result)


def gen_Anet_IP_datagram(
    s_ip: str,
    d_ip: str,
    protocol: str,
    payload: bytes,
) -> bytes:
    s_ip_int = ip2int(s_ip)
    d_ip_int = ip2int(d_ip)
    if protocol == 'TCP':
        protocol = 6
    header = struct.pack('!BII', protocol, s_ip_int, d_ip_int)
    return header + payload


def gen_tcp_packet(d_addr: D_ADDR,
                   seq: int,
                   flag,
                   s_port,
                   ack_num=0,
                   window=1,
                   urg_ptr=0,
                   payload: bytes = None) -> bytes:
    tcp_header = struct.pack('!HHIIBBHHH', s_port, d_addr.port, seq, ack_num,
                             5 << 4, flag, window, 0, urg_ptr)
    return tcp_header + payload


def get_tcp_payload_from_IP(data: bytes) -> str:
    exclude_IP_header = data[1 * 1 + 4 * 2:]
    extract_from_tcp_packed = exclude_IP_header[2 * 2 + 4 * 2 + 1 * 2 + 2 * 3:]
    return extract_from_tcp_packed.decode('utf-8')


def split_ftp_data(data: bytes) -> list[bytes]:
    """split string data to 64 bytes string in list"""
    frame_len = 64
    res = [data[i:i + frame_len] for i in range(0, len(data), frame_len)]
    # if len(data) < frame_len:
    #     return [data]
    # res = []
    # for i in range(len(data) // frame_len):
    #     res.append(data[i * frame_len:(i + 1) * frame_len])
    # if x := data[frame_len * (len(data) // frame_len):]:
    #     res.append(x)
    return res


if __name__ == '__main__':
    # s = b'\x06'
    s = 'a' * 13
    b = [s[i:i + 6] for i in range(0, len(s), 6)]
    print(b)