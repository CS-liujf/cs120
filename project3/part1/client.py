import socket
import time


def main():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dest_addr = ('127.0.0.1', 10000)
    data = '01234567899876543210'.encode('utf-8')
    for _ in range(10):
        udp_socket.sendto(data, dest_addr)
        time.sleep(1)

    udp_socket.close()
    print('end')


if __name__ == '__main__':
    main()
