import socket


def main():
    addr = ('127.0.0.1', 10000)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(addr)
    count = 0
    while True:
        data, s_addr = udp_socket.recvfrom(100)
        count += 1
        print({'payload': data.decode('utf-8'), 's_addr': s_addr})
        if count == 10:
            break

    udp_socket.close()


if __name__ == '__main__':
    main()