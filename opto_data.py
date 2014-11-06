
import struct

'''
Opto Packet is structured like this:
    index   :    bytes   :   Description         :   structure
    0       :    2       :   packet length       :   H -- unsigned short
    1       :    1       :   zero filled byte    :   B -- unsigned char
    2       :    1       :   transaction code    :   B
    3       :    4*64    :   floats              :   f -- 4 byte float
    67      :    4*64    :   ints                :   l -- 4 byte int (long)
    131     :    1*64    :   bools               :   B -- unsigned char (and then broken up)

'''

_start = [
    'H',
    'B',
    'B',
]

format = _start + [
    '64f',
    '64l',
    '8B'
]
endy = "!"
start_str = endy + ''.join(_start)
format_str = endy + ''.join(format)


def convert_opto(format, data, expected_len=None):
    if expected_len is not None:
        assert len(data) >= expected_len
        # format += str(len(data) - expected_len) + B
        data = data[:expected_len]
    return struct.unpack(format, data)

def test():
    _test = b"\x02\\\x00\xa8"
    _sample =(b"\x02\\\x00\xa8B\xed\x19\x9a?Z\x1c\xacB\xb4\x00\x00B\xc9\x00\x00@\x82\x8f\\\xbcD"
              b"\x9b\xa6\x00\x00\x00\x00\x00\x00\x00\x00\xbd\x13t\xbc=\x13t\xbc\x00\x00\x00\x00"
              b"\x00\x00\x00\x00A?\x16\x87A@\xe7m\x00\x00\x00\x00\xba\xd1\xc0\x00<e`\x00\x00\x00"
              b"\x00\x009\xd1\x80\x00\xbf\x07\x93\xe0A\xcd1\x07A\xb8t\xab\x00\x00\x00\x00\x00\x00"
              b"\x00\x00A\xfc3?A\xd9\xba'\x00\x00\x00\x00\x00\x00\x00\x00\xbf\x80\x00\x00\xbf\x80"
              b"\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
              b"\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
              b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
              b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
              b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"
              b"\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\xc0\xcc\xc0\x0c\xc0\x00\x00\x00\xc0\xcc\xc0\x0c\xc0"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
              b"\x00\x00\x00\x00\x00\x00\x00")



    print(convert_opto(format_str, _sample, expected_len=524))

if __name__ == '__main__':
    test()
