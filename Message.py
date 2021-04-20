import string
import struct
from dataclasses import dataclass


@dataclass
class Message:
    msg_id: int
    id_sender: int
    id_receiver: int
    msg: string
    ttl: int
    check_sum: int


def code_new_msg(id_sender, id_receiver, id, msg):
    checksum = sum(map(ord, msg))  # change to crc
    ttl = 10
    coded = struct.pack('h h h 114s h h',  id, id_sender, id_receiver, str.encode(msg), ttl, checksum)
    return coded


def code_msg(msg):
    if msg.check_sum == sum(map(ord, msg.msg)):
        coded = struct.pack('h h h 114s h h', msg.msg_id, msg.id_sender, msg.id_receiver,
                            str.encode(msg.msg), msg.ttl, msg.check_sum)
        return coded
    else:
        print(f'WRONG check sum old: {msg.check_sum} != new:  {sum(map(ord, msg.msg))}')


def decode_msg(coded_msg):
    decoded = struct.unpack('h h h 114s h h', coded_msg)
    msg = Message(decoded[0], decoded[1], decoded[2], decoded[3].decode("utf-8"), decoded[4], decoded[5])
    msg.ttl = msg.ttl - 1
    return msg
