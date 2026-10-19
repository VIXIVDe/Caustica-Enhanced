"""Read Caustica's uncompressed scanline RGBA half-float signal exports."""
from pathlib import Path
import struct
import numpy as np


def read_exr(path):
    data = Path(path).read_bytes()
    if len(data) < 8 or struct.unpack_from('<I', data)[0] != 20000630:
        raise ValueError(f'Invalid EXR file: {path}')
    position = 8
    attrs = {}

    def string():
        nonlocal position
        end = data.index(0, position)
        value = data[position:end].decode('ascii')
        position = end + 1
        return value

    while data[position]:
        name, kind = string(), string()
        size = struct.unpack_from('<I', data, position)[0]
        position += 4
        attrs[name] = kind, data[position:position + size]
        position += size
    position += 1
    if attrs.get('compression', ('', b''))[1] != b'\0':
        raise ValueError('Only uncompressed Caustica signal EXRs are supported.')
    channels = attrs['channels'][1]
    cursor, names = 0, []
    while channels[cursor]:
        end = channels.index(0, cursor)
        names.append(channels[cursor:end].decode('ascii'))
        cursor = end + 1
        pixel_type, _, x_sampling, y_sampling = struct.unpack_from('<i4sii', channels, cursor)
        cursor += 16
        if pixel_type != 1 or x_sampling != 1 or y_sampling != 1:
            raise ValueError('Expected full-resolution half-float channels.')
    if set(names) != set('RGBA') or len(names) != 4:
        raise ValueError(f'Expected RGBA channels, got {names}')
    x0, y0, x1, y1 = struct.unpack('<4i', attrs['dataWindow'][1])
    width, height = x1 - x0 + 1, y1 - y0 + 1
    out = np.zeros((height, width, 4), np.float32)
    order = [names.index(channel) for channel in 'RGBA']
    for index in range(height):
        offset = struct.unpack_from('<Q', data, position + 8 * index)[0]
        row, size = struct.unpack_from('<iI', data, offset)
        if size != width * 8 or not y0 <= row <= y1:
            raise ValueError('Unexpected scanline size or coordinate.')
        values = np.frombuffer(data, dtype='<f2', count=width * 4, offset=offset + 8)
        out[row - y0] = values.reshape(4, width)[order].T
    return out
