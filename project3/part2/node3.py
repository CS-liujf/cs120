import socket
import time


def main():
    addr = ('', 10000)
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(addr)
    count = 0
    while True:
        data, s_addr = udp_socket.recvfrom(100)
        count += 1
        print({'payload': data.decode('utf-8'), 's_addr': s_addr})
        if count == 30:
            break

    with open('./INPUT.txt', 'r') as f:
        data = f.readlines()

    data = [i.rstrip() for i in data]  # remove \n
    for message in data:
        udp_socket.sendto(message.encode('utf-8'), s_addr)
        time.sleep(0.1)

    udp_socket.close()


if __name__ == '__main__':
    main()