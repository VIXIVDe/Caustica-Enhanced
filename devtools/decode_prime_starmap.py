"""Verify and unpack pinned Prime BC6H mips; no runtime compression dependency."""
import hashlib
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent / 'dependencies'))
import zstandard

root = pathlib.Path(__file__).resolve().parent.parent
source = root / 'reference/prime-starmap-0.1.0.ktx2'
target = root / 'mod/src/main/resources/assets/caustica/sky/prime-starmap.bin'
data = source.read_bytes()
assert hashlib.sha256(data).hexdigest() == '64bcda4bf9068dae0591bf26f7bd363ec289d3cc95eb528e687a21cc2c355a02'
assert data[:12] == b'\xabKTX 20\xbb\r\n\x1a\n'
fmt, _, width, height, depth, layers, faces, levels, compression = struct.unpack_from('<9I', data, 12)
assert (fmt, width, height, depth, layers, faces, levels, compression) == (143, 16384, 8192, 0, 0, 1, 15, 2)
payload = []
index = []
cursor = 0
for mip in range(levels):
    offset, length, raw_length = struct.unpack_from('<3Q', data, 80 + mip * 24)
    expected = ((max(1, width >> mip) + 3) // 4) * ((max(1, height >> mip) + 3) // 4) * 16
    assert raw_length == expected and offset + length <= len(data)
    raw = zstandard.ZstdDecompressor().decompress(data[offset:offset + length], max_output_size=expected)
    assert len(raw) == expected
    index.append((cursor, expected))
    payload.append(raw)
    cursor += expected
target.parent.mkdir(parents=True, exist_ok=True)
temporary = target.with_suffix('.tmp')
with temporary.open('wb') as output:
    output.write(struct.pack('<4I', 0x52415453, width, height, levels))
    for record in index:
        output.write(struct.pack('<2I', *record))
    for raw in payload:
        output.write(raw)
temporary.replace(target)
print(f'Validated {levels} BC6H mips: {target.stat().st_size} bytes')
