from ftp_utils import check_addr_input, check_cmd_input
from tcp import TCP
from tcp_utils import SOCKET, D_ADDR
import pyfiglet
import time


class FTP:
    def __init__(self, d_addr=None, tcp: TCP = None):
        result = pyfiglet.figlet_format(text="Athernet  FTP".upper(),
                                        font="slant")
        print(result)
        self.CMD_TABLE = {
            'USER': self.user_func,
            'PASS': self.pass_func,
            'PWD': self.pwd_func,
            'CWD': self.cwd_func,
            'PASV': self.pasv_func,
            'LIST': self.list_func,
            'RETR': self.retr_func
        }
        self.tcp = tcp if tcp != None else TCP()
        self.command_socket = SOCKET('192.168.1.2', 10000)
        self.data_socket = None
        self.tcp.start()
        while self.tcp.get_status() != 1:
            pass
        while not check_addr_input(
                server_addr := input('Server IP address: ')):
            pass
        self.server_cmd_addr = D_ADDR(server_addr, 21)
        self.tcp.connect(self.server_cmd_addr, self.command_socket)
        print(f'Connected to {server_addr}.')

        self.server_data_addr = None

    def user_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def pass_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def pwd_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def cwd_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()

    def pasv_func(self, cmd_str: str):
        self.send_ftpcmd(cmd_str)
        response = self.get_ftpcmd_status()
        # get port
        self.data_port = 1
        self.data_socket = SOCKET('192.168.1.2', self.command_socket.port + 1)
        self.server_data_addr = D_ADDR(self.server_cmd_addr.ip,
                                       self.command_socket.port + 1)

    def list_func(self, cmd_str: str):
        if self.data_socket == None:
            self.pass_func('PASV')

        self.tcp.connect(self.server_data_addr, self.data_socket)
        self.send_ftpcmd(cmd_str)
        self.get_ftpcmd_status()
        res = b''
        while True:
            res_buffer = self.tcp.read(self.data_socket)
            if res_buffer != -1:
                res = res + res_buffer
            else:
                break

        print(res)
        self.data_socket = None
        self.server_data_addr = None

    def retr_func(self, cmd_str: str):
        if self.data_socket == None:
            self.pass_func('PASV')
        self.tcp.connect(self.server_data_addr, self.data_socket)
        self.send_ftpcmd(cmd_str)
        res = self.get_ftpcmd_status()
        with open(f'./{cmd_str.split()[1]}', 'wb') as f:
            res = b''
            while True:
                res_buffer = self.tcp.read(self.data_socket)
                if res_buffer != -1:
                    res = res + res_buffer
                else:
                    break
            f.write(res)

        print('downloaded a file')

    def start(self):
        while True:
            command_str = self.command_input() + '\r\n'
            self.send_ftpcmd(command_str)
            self.get_ftpcmd_status()

    def command_input(self) -> str:
        while not check_cmd_input(
                command_str := input('Please input FTP command: ')):
            pass
        temp = command_str.split()
        temp[0] = temp[0].upper()
        return ' '.join(temp)

    def send_ftpcmd(self, command_str: str):
        self.tcp.write(self.command_socket, command_str.encode('utf-8'))

    def get_ftpcmd_status(self):
        res = b''
        while True:
            res_buffer = self.tcp.read(self.command_socket)
            if res_buffer != -1:
                res = res + res_buffer
                if b'\r\n' in res_buffer:
                    print(res.decode('utf-8'))
                    # we should check whether ftp recv an error msg,but now just pass
                    pass
                    return res
            else:
                return -1


if __name__ == '__main__':
    ftp = FTP()
    ftp.start()