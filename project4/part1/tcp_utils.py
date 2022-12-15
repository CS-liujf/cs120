from enum import Enum, unique
from dataclasses import dataclass


@dataclass(frozen=True)
class SOCKET:
    ip: str
    port: int


# @Enum
class TCP_FLAG(Enum):
    i = 1


def gen_tcp_packet() -> bytes:
    for a in TCP_FLAG:
        print(a)


def check_tcp_flag():
    pass


def get_tcp_s_port(tcp_packet: bytes) -> int:
    return 0


def get_tcp_payload(tcp_packet: bytes) -> bytes:
    pass


if __name__ == '__main__':
    gen_tcp_packet()