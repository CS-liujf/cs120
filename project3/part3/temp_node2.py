import struct
import socket
import time


def unpack_icmp_echo_reply(icmp_packet: bytes) -> tuple[int, int, bytes]:
    _type, code, _, ident, seq = struct.unpack('!BBHHH', icmp_packet[:8])
    if _type != 0:
        return
    if code != 0:
        return

    payload = icmp_packet[8:]

    return ident, seq, payload


def recv_routine(sock: socket.socket):
    while True:
        # wait for another icmp packet
        icmp_packet, (src_addr, _) = sock.recvfrom(46)

        # unpack it
        result = unpack_icmp_echo_reply(icmp_packet[20:])
        print('收到了')
        if not result:
            continue

        # print info
        _ident, seq, payload = result

        sending_ts, = struct.unpack('!d', payload[:8])
        print('%s seq=%d %5.2fms' % (
            src_addr,
            seq,
            (time.time() - sending_ts) * 1000,
        ))


def main():
    sc = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    addr = ('10.20.196.226', 10000)
    sc.bind(addr)
    recv_routine(sc)


if __name__ == '__main__':
    main()