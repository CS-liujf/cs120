from ftp_utils import check_address_input, check_command_input
from tcp import TCP
from tcp_utils import SOCKET, D_ADDR
import pyfiglet
import time


class FTP:
    def __init__(self, d_addr=None, tcp: TCP = None):
        result = pyfiglet.figlet_format(text="Athernet  FTP".upper(),
                                        font="slant")
        print(result)
        self.tcp = tcp if tcp != None else TCP()
        self.command_socket = SOCKET('192.168.1.2', 10000)
        self.tcp.start()
        while self.tcp.get_status() != 1:
            pass
        while not check_address_input(
                server_addr := input('Server IP address: ')):
            pass
        self.server_command_addr = D_ADDR(server_addr, 21)
        self.tcp.connect(self.server_command_addr, self.command_socket)
        print(f'Connected to {server_addr}.')

    def start(self):
        while True:
            command_str = self.command_input() + '\r\n'
            self.send_ftpcmd()
            self.get_ftpcmd_status()

    def command_input(self) -> str:
        while not check_command_input(
                command_str := input('Please input FTP command: ')):
            pass
        temp = command_str.split()
        temp[0].upper()
        return ' '.join(temp)

    def send_ftpcmd(self, _socket: SOCKET, command_str: str):
        self.tcp.write(self.command_socket, command_str.encode('utf-8'))

    def get_ftpcmd_status(self) -> int:
        res = b''
        while True:
            res_buffer = self.tcp.read(self.command_socket)
            if res_buffer != -1:
                res = res + res_buffer
                if b'\r\n' in res_buffer:
                    print(res.decode('utf-8'))
                    # we should check whether ftp recv an error msg,but now just pass
                    pass
                    return 1
            else:
                return -1


if __name__ == '__main__':
    # ftp = FTP()
    # ftp.start()
    b = b'\r\n'
    if b'\r\n' in b:
        print('yes')