import string
import struct
from dataclasses import dataclass


@dataclass
class Message:
    msg_code: int
    msg_id: int
    id_sender: int
    id_receiver: int
    next_receiver: int
    msg: string
    ttl: int
    check_sum: int

    @staticmethod
    def get_byte_pattern():
        return 'h h h h h 112s h h'


def code_new_msg(msg_code: int, id_sender: int, id_receiver: int, next_receiver: int, id: int, msg: string):
    checksum = sum(map(ord, msg))  # change to crc lib: hashlib
    ttl = 10
    coded = struct.pack(Message.get_byte_pattern(), msg_code, id, id_sender, id_receiver, next_receiver,
                        str.encode(msg), ttl, checksum)
    return coded


def code_msg(msg: Message):
    if msg.msg_code == 0xAA or msg.check_sum == sum(map(ord, msg.msg)):
        coded = struct.pack(Message.get_byte_pattern(), msg.msg_code, msg.msg_id, msg.id_sender, msg.id_receiver,
                            msg.next_receiver, str.encode(msg.msg), msg.ttl, msg.check_sum)
        return coded
    else:
        print(f'WRONG check sum old: {msg.check_sum} != new:  {sum(map(ord, msg.msg))}')


def decode_msg(coded_msg):
    decoded = struct.unpack(Message.get_byte_pattern(), coded_msg)
    msg = Message(decoded[0], decoded[1], decoded[2], decoded[3], decoded[4], decoded[5].decode().rstrip('\x00'),
                  decoded[6], decoded[7])
    msg.ttl = msg.ttl - 1
    return msg

# typ rozgłoszenia: fizyczny odbiorca na podstawie grafu : port // odległy o jeden

# typ rozgłoszeni: fizyczny odbiorca na podstawie grafu : port // odległy o jeden done
# dodac grafy done
# rozszerzyc wiadomość o odbiorce done
# poprawić
