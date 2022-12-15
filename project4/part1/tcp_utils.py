from enum import Enum, unique
from dataclasses import dataclass
import struct


@dataclass(frozen=True)
class SOCKET:
    ip: str
    port: int


@dataclass(frozen=True)
class D_ADDR:
    ip: str
    port: int


# @Enum
class TCP_FLAG(Enum):
    i = 1


def gen_tcp_packet(d_addr: D_ADDR,
                   seq: int,
                   flag,
                   port,
                   ack_num=0,
                   window=1,
                   urg_ptr=0,
                   payload: bytes = None) -> bytes:
    tcp_header = struct.pack('!HHIIBBHHH', port, d_addr.port, seq, ack_num,
                             5 << 4, flag, window, 0, urg_ptr)
    return tcp_header + payload


def check_tcp_flag(tcp_packet: bytes):
    pass


def get_tcp_s_port(tcp_packet: bytes) -> int:
    return struct.unpack_from('!H', tcp_packet)


def get_tcp_d_port(tcp_packet: bytes) -> int:
    return struct.unpack_from('!H', tcp_packet, 2)


def get_tcp_payload(tcp_packet: bytes) -> bytes:
    return tcp_packet[20:]


if __name__ == '__main__':
    # b = struct.pack('!III', 10, 11, 20)
    # print(b[1:])
    print(hash(SOCKET('19', 3020)))
    # print(struct.unpack_from('!I', b, 20))
