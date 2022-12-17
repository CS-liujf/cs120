import struct
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


def get_Anet_IP_payload(ip_datagram: bytes):
    # 1byte protocol, 4bytes source ip, 4bytes destination ip
    return ip_datagram[9:]


if __name__ == '__main__':
    s = b'\x06'
    print(s.decode('utf-8'))