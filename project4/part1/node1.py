from ftp_utils import check_input


class FTP:
    def __init__(self):
        pass

    def start(self):
        pass

    def command_input(self):
        flag = False
        while not flag:
            command_str = input('Please input FTP command: ')
            flag = check_input(command_str)


if __name__ == '__main__':
    ftp = FTP()
    ftp.command_input()