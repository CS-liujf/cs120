import socket
import time
import struct
import threading
import os


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
    pseudo = struct.pack(
        '!BBHHH',
        8,
        0,
        0,
        ident,
        seq,
    ) + payload
    checksum = calculate_checksum(pseudo)
    return pseudo[:2] + checksum + pseudo[4:]


def unpack_icmp_echo_reply(icmp):
    _type, code, _, ident, seq, = struct.unpack('!BBHHH', icmp[:8])
    if _type != 0:
        return
    if code != 0:
        return

    payload = icmp[8:]

    return ident, seq, payload


def send_routine(sock, addr, ident, magic):
    # first sequence no
    seq = 1

    while True:
        # currrent time
        sending_ts = time.time()

        # packet current time to payload
        # in order to calculate round trip time from reply
        payload = struct.pack('!d', sending_ts) + magic

        # pack icmp packet
        icmp = pack_icmp_echo_request(ident, seq, payload)

        # send it
        sock.sendto(icmp, (addr, 0))

        seq += 1
        time.sleep(1)


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


def ping():
    addr = '10.20.196.226'
    # create socket for sending and receiving icmp packet
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    addr = ('10.20.196.226', 10000)
    sock.bind(addr)

    # id field
    ident = os.getpid()
    # magic string to pad
    magic = b'1234567890'

    # args = (sock, '182.61.200.7', ident, magic)
    # sender = threading.Thread(target=send_routine, args=args)
    # sender.start()
    recv_routine(sock)


if __name__ == '__main__':
    ping()