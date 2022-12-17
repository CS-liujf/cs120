COMMAND_LIST = ['USER', 'PASS', 'PWD', 'CWD', 'PASV', 'LIST', 'RETR']


def check_addr_input(address: str) -> bool:
    temp = address.split('.')
    if len(temp) != 4:
        return False
    try:
        temp = list(map(int, temp))
        for x in temp:
            if x > 255:
                return False
    except:
        return False
    return True


def recursive_lcs(str_a: str, str_b: str):
    str_a, str_b = str_a.upper(), str_b.upper()
    if len(str_a) == 0 or len(str_b) == 0:
        return 0
    if str_a[0] == str_b[0]:
        return recursive_lcs(str_a[1:], str_b[1:]) + 1
    else:
        return max(
            [recursive_lcs(str_a[1:], str_b),
             recursive_lcs(str_a, str_b[1:])])


def check_cmd_input(command_str: str) -> bool:
    if len(command_str) == 0:
        return False
    command = command_str.split()[0]
    lcs_value_list = [recursive_lcs(command, x) for x in COMMAND_LIST]
    max_lcs_value = max(lcs_value_list)
    max_lcs_index = lcs_value_list.index(max_lcs_value)
    idx_list = []
    for idx, val in enumerate(lcs_value_list):
        if max_lcs_value == val and (max_lcs_value / len(COMMAND_LIST[idx]) >=
                                     0.5):
            idx_list.append(idx)

    if len(idx_list) == 1 and COMMAND_LIST[max_lcs_index] == command.upper():
        return True
    elif len(idx_list) != 0:
        print(f'ERROR: unknown command \"{command}\"')

        if len(idx_list) == 1:
            print(f'Maybe you meant \"{COMMAND_LIST[max_lcs_index]}\"')
        else:
            print('Did you mean one of these?')
            for idx in idx_list:
                print(f'\t{COMMAND_LIST[idx]}')

    else:
        print(f'ERROR: unknown command \"{command}\"')

    print('\n')
    return False


if __name__ == '__main__':
    # print(recursive_lcs('wd', 'pwd'))
    # temp = [1, 2, 3, 4, 3]
    # print(temp.index(3))
    # check_input('user fsdf')
    import struct
    b = struct.pack('!cc', b'a', b'\n')
    if '\n' in b.decode('utf-8'):
        print('yes')
