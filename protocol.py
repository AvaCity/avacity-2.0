import binascii
import datetime
from bitstring import BitArray


def zero_fill_right_shift(val, n):
    return (val >> n) if val >= 0 else ((val + 0x100000000) >> n)


def processFrame(data, client=False):
    mask = data.read(8).uint
    checksummed_mask = 1 << 3
    if 0 != (mask & checksummed_mask):
        checksummed = True
    else:
        checksummed = False
    if checksummed:
        checksum = data.read(32).uint
        old_pos = data.pos
        message = data.read(len(data)-data.pos)
        data.pos = old_pos
        real_checksum = binascii.crc32(message.bytes) % (1 << 32)
        if checksum != real_checksum:
            return None
    if client:
        data.pos += 32  # message number
    type_ = data.read(8).int
    return {"type": type_, "msg": decodeArray(data)}


def encodeArray(data):
    final_data = BitArray()
    final_data.append(f"int:32={len(data)}")
    for item in data:
        final_data.append(encodeValue(item))
    return final_data


def encodeValue(data, forDict=False):
    final_data = BitArray()
    if data is None:
        final_data.append("int:8=0")
    elif isinstance(data, bool):
        final_data.append("int:8=1")
        final_data.append(f"int:8={int(data)}")
    elif isinstance(data, int):
        if data > 2147483647:
            final_data.append("int:8=3")
            final_data.append(f"int:64={data}")
        else:
            final_data.append("int:8=2")
            final_data.append(f"int:32={data}")
    elif isinstance(data, float):
        final_data.append("int:8=4")
        final_data.append(f"float:64={data}")
    elif isinstance(data, str):
        if not forDict:
            final_data.append("int:8=5")
        if not all(ord(c) < 128 for c in data):  # check for non ASCII chars
            length = len(data.encode().hex())//2
        else:
            length = len(data)
        while (length & 4294967168) != 0:
            final_data.append(f"uint:8={length & 127 | 128}")
            length = zero_fill_right_shift(length, 7)
        final_data.append(f"uint:8={length & 127}")
        final_data.append(data.encode())
    elif isinstance(data, dict):
        final_data.append("int:8=6")
        final_data.append(encodeDictionary(data))
    elif isinstance(data, list):
        final_data.append("int:8=7")
        final_data.append(encodeArray(data))
    elif isinstance(data, datetime.datetime):
        final_data.append("int:8=8")
        final_data.append(f"int:64={int(data.timestamp()*1000)}")
    else:
        raise ValueError("Can't encode "+str(type(data)))
    return final_data


def encodeDictionary(data):
    final_data = BitArray()
    final_data.append(f"int:32={len(data)}")
    for item in data.keys():
        final_data.append(encodeValue(item, forDict=True))
        final_data.append(encodeValue(data[item]))
    return final_data


def decodeArray(data):
    result = []
    length = data.read(32).int
    i = 0
    while i < length:
        result.append(decodeValue(data))
        i += 1
    return result


def decodeDictionary(data):
    fields = data.read(32).int
    obj = {}
    i = 0
    while i < fields:
        key = decodeString(data)
        obj[key] = decodeValue(data)
        i += 1
    return obj


def decodeValue(data):
    dataType = data.read(8).int
    if dataType == 0:  # null
        return None
    elif dataType == 1:  # bool
        if data.read(8).int:
            return True
        else:
            return False
    elif dataType == 2:  # int
        return data.read(32).int
    elif dataType == 3:  # long
        return data.read(64).int
    elif dataType == 4:  # double
        return data.read(64).float
    elif dataType == 5:  # string
        return decodeString(data)
    elif dataType == 6:  # dictionary
        return decodeDictionary(data)
    elif dataType == 7:  # array
        return decodeArray(data)
    elif dataType == 8:  # date
        return datetime.datetime.fromtimestamp(data.read(64).int/1000)
    else:
        raise ValueError(f"Wrong datatype: {dataType}")


def decodeString(data):
    i = 0
    b = data.read(8).uint
    value = 0
    while b & 128 != 0:
        value += (b & 127) << i
        i += 7
        if i > 35:
            raise Exception("Variable length quantity is too long")
        b = data.read(8).uint
    length = value | b << i
    return data.read(length*8).bytes.decode()
