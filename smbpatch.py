from collections import defaultdict, namedtuple

########################################
# Utility functions
########################################

def cpu_to_rom(addr: int) -> int:
    return addr - 0x8000 + 0x10

def rom_to_cpu(addr: int) -> int:
    return addr + 0x8000 - 0x10

def text_chr(s: str) -> bytes:
    return bytes(map('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ    -× !'.index, s))

# Read a little-endian u32 from a bytearray.
def u32(b: bytearray, index: int) -> int:
    return sum(b[index+i] * 256**i for i in range(4))

# Return the amount of bytes written.
def write(b: bytearray, index: int, length: int, data) -> int:
    assert len(data) == length
    b[index:index+length] = data
    return length

def write_padding(b: bytearray, index: int, length: int, data) -> int:
    assert len(data) <= length
    return write(b, index, length, data + bytes(length - len(data)))

########################################
# Color patches
########################################

# Background color addresses:
water = 0x5DF
day_sky = 0x5E0
night_sky = 0x5E1

# Object color addresses:
ow_bushes_bright = 0xCDC
ow_bushes_dark = 0xCDD
ow_bushes_outline = 0xCDE
ow_brick_bright = 0xCE0
ow_brick_dark = 0xCE1

mario_hat = 0x5E8
mario_skin = 0x5E9
mario_hair = 0x5EA

def patch_colors(rom: bytearray) -> None:
    pass
    # rom[water] = 0x14
    # rom[day_sky] = 0x2B
    # rom[night_sky] = navy = 0x01
    # rom[ow_bushes_dark] = 0x15
    # rom[ow_bushes_bright] = 0x25
    # rom[ow_brick_dark] = teal = 0x17
    # rom[ow_brick_bright] = bright_teal = 0x27

    # rom[mario_skin] = 0x27
    # rom[mario_hair] = 0x01

########################################
# Famitracker parsing.
########################################

class Chunk:
    "A named chunk of data from a FamiTracker module file."

    def __init__(self, name: str, version: int, contents: bytearray):
        self.name = name
        self.version = version
        self.contents = contents
    def byte(self, index: int) -> int:
        return self.contents[index]
    def u32(self, index: int) -> int:
        return u32(self.contents, index)
    def string(self, index: int, length: int) -> bytes:
        return bytes(self.contents[index:index+length])
    def c_string(self, index: int) -> bytes:
        where = self.contents.index(b'\0', index)
        return bytes(self.contents[index:where])
    def c_strings(self, index: int, count: int): # -> Iterator[bytes]:
        for i in range(count):
            string = self.c_string(index)
            yield string
            index += len(string) + 1

########################################
# Music patches!
# We use strings like "C-5" or "C#5" to represent notes,
# strings "4.", "4", "8.", "8", "8t", "16", "16t", "32t" for note duration opcodes,
# "0" for stop, "x" for rest
########################################

'''
$791D: Mario Dies (A5)
$791E: Game Over (59)
$791F: Princess Rescued! (54)
$7920: Mushroom Retainer Rescued (64)
$7921: Game Over [alternate] (59) (See quote)
$7922: Level Complete (3C)
$7923: Time Running Out! (31)
$7924: Silence #1 (4B)
$7925: ????? (69)
$7926: Underwater Theme (5E)
$7927: Underground Theme (46)
$7928: Castle Theme (4F)
$7929: Cloud Theme (36)
$792A: Pre-pipe Theme [Used at beginning of 1-2, 2-2, 4-2 and 7-2] (8D)
$792B: Starman Theme (36)
$792C: Silence #2 [plays during 'Level X-Y' screen] (4B)
$792D: Overworld Theme Slot #1 (8D)
$792E: Overworld Theme Slot #2 (69)
$792F: Overworld Theme Slot #3 (69)
$7930: Overworld Theme Slot #4 (6F)
$7931: Overworld Theme Slot #5 (75)
$7932: Overworld Theme Slot #6 (6F)
$7933: Overworld Theme Slot #7 (7B)
$7934: Overworld Theme Slot #8 (6F)
$7935: Overworld Theme Slot #9 (75)
$7936: Overworld Theme Slot #10 (6F)
$7937: Overworld Theme Slot #11 (7B)
$7938: Overworld Theme Slot #12 (81)
$7939: Overworld Theme Slot #13 (87)
$793A: Overworld Theme Slot #14 (81)
$793B: Overworld Theme Slot #15 (8D)
$793C: Overworld Theme Slot #16 (69)
$793D: Overworld Theme Slot #17 (69)
$793E: Overworld Theme Slot #18 (93)
$793F: Overworld Theme Slot #19 (99)
$7940: Overworld Theme Slot #20 (93)
$7941: Overworld Theme Slot #21 (9F)
$7942: Overworld Theme Slot #22 (93)
$7943: Overworld Theme Slot #23 (99)
$7944: Overworld Theme Slot #24 (93)
$7945: Overworld Theme Slot #25 (9F)
$7946: Overworld Theme Slot #26 (81)
$7947: Overworld Theme Slot #27 (87)
$7948: Overworld Theme Slot #28 (81)
$7949: Overworld Theme Slot #29 (8D)
$794A: Overworld Theme Slot #30 (93)
$794B: Overworld Theme Slot #31 (99)
$794C: Overworld Theme Slot #32 (93)
$794D: Overworld Theme Slot #33 (9F)
'''

song_table = 0x791D

song_table_size = 49
overworld_pattern_list = 0x792D
underground_song = 0x7927
song_headers = song_table + song_table_size
music_data = 0x79C8 # Adjust as needed.
music_data_size = 1352

# Speed values.
bpm150 = 0x20
bpm100 = 0x18

melody_to_byte = {
    'q.': 0x80, 'q': 0x86, 'i.': 0x85, 'i': 0x84, 'it': 0x87, 's': 0x82, 'st': 0x83, 'z': 0x81,  # (From ZZT #PLAY! ^v^)
    'G-6': 0x58, 'E-6': 0x56, 'D-6': 0x02, 'C-6': 0x54, 'Bb5': 0x52, 'A#5': 0x52, 'Ab5': 0x50, 'G#5': 0x50, 'G-5': 0x4E,
    'F-5': 0x4C, 'E-5': 0x44, 'D#5': 0x4A, 'D-5': 0x48, 'Db5': 0x46, 'C#5': 0x46, 'C-5': 0x64, 'B-4': 0x42, 'Bb4': 0x3E,
    'A#4': 0x3E, 'A-4': 0x40, 'Ab4': 0x3C, 'G#4': 0x3C, 'G-4': 0x3A, 'Gb4': 0x38, 'F#4': 0x38, 'F-4': 0x36, 'E-4': 0x34,
    'Eb4': 0x32, 'D#4': 0x32, 'D-4': 0x30, 'Db4': 0x2E, 'C#4': 0x2E, 'C-4': 0x2C, 'B-3': 0x2A, 'Bb3': 0x28, 'A#3': 0x28,
    'A-3': 0x26, 'Ab3': 0x24, 'G#3': 0x24, 'G-3': 0x22, 'Gb3': 0x20, 'F#3': 0x20, 'F-3': 0x1E, 'E-3': 0x1C, 'Eb3': 0x1A,
    'D#3': 0x1A, 'D-3': 0x18, 'C#3': 0x16, 'C-3': 0x14, 'B-2': 0x12, 'Bb2': 0x10, 'A#2': 0x10, 'A-2': 0x62, 'Ab2': 0x0E,
    'G#2': 0x0E, 'G-2': 0x0C, 'Gb2': 0x0A, 'F#2': 0x0A, 'F-2': 0x08, 'E-2': 0x06, 'Eb2': 0x60, 'D#2': 0x60, 'D-2': 0x5E,
    'C-2': 0x5C, 'G-1': 0x5A, '...': 0x04, '---': 0x00,
}

harmony_to_byte = {
    # Drums (Open hat, Kick, Closed hat):
    'q.O': 0x30, 'qO': 0xB1, 'i.O': 0x71, 'iO': 0x31, 'itO': 0xF1, 'sO': 0xB0, 'stO': 0xF0, 'zO': 0x70,
    'q.K': 0x20, 'qK': 0xA1, 'i.K': 0x61, 'iK': 0x21, 'itK': 0xE1, 'sK': 0xA0, 'stK': 0xE0, 'zK': 0x60,
    'q.C': 0x10, 'qC': 0x91, 'i.C': 0x51, 'iC': 0x11, 'itC': 0xD1, 'sC': 0x90, 'stC': 0xD0, 'zC': 0x50,

    # Square 1 notes:
    'q.Bb4': 0x3E, 'qBb4': 0xBF, 'i.Bb4': 0x7F, 'iBb4': 0x3F, 'itBb4': 0xFF, 'sBb4': 0xBE, 'stBb4': 0xFE, 'zBb4': 0x7E,
    'q.A#4': 0x3E, 'qA#4': 0xBF, 'i.A#4': 0x7F, 'iA#4': 0x3F, 'itA#4': 0xFF, 'sA#4': 0xBE, 'stA#4': 0xFE, 'zA#4': 0x7E,
    'q.Ab4': 0x3C, 'qAb4': 0xBD, 'i.Ab4': 0x7D, 'iAb4': 0x3D, 'itAb4': 0xFD, 'sAb4': 0xBC, 'stAb4': 0xFC, 'zAb4': 0x7C,
    'q.G#4': 0x3C, 'qG#4': 0xBD, 'i.G#4': 0x7D, 'iG#4': 0x3D, 'itG#4': 0xFD, 'sG#4': 0xBC, 'stG#4': 0xFC, 'zG#4': 0x7C,
    'q.G-4': 0x3A, 'qG-4': 0xBB, 'i.G-4': 0x7B, 'iG-4': 0x3B, 'itG-4': 0xFB, 'sG-4': 0xBA, 'stG-4': 0xFA, 'zG-4': 0x7A,
    'q.Gb4': 0x38, 'qGb4': 0xB9, 'i.Gb4': 0x79, 'iGb4': 0x39, 'itGb4': 0xF9, 'sGb4': 0xB8, 'stGb4': 0xF8, 'zGb4': 0x78,
    'q.F#4': 0x38, 'qF#4': 0xB9, 'i.F#4': 0x79, 'iF#4': 0x39, 'itF#4': 0xF9, 'sF#4': 0xB8, 'stF#4': 0xF8, 'zF#4': 0x78,
    'q.F-4': 0x36, 'qF-4': 0xB7, 'i.F-4': 0x77, 'iF-4': 0x37, 'itF-4': 0xF7, 'sF-4': 0xB6, 'stF-4': 0xF6, 'zF-4': 0x76,
    'q.E-4': 0x34, 'qE-4': 0xB5, 'i.E-4': 0x75, 'iE-4': 0x35, 'itE-4': 0xF5, 'sE-4': 0xB4, 'stE-4': 0xF4, 'zE-4': 0x74,
    'q.Eb4': 0x32, 'qEb4': 0xB3, 'i.Eb4': 0x73, 'iEb4': 0x33, 'itEb4': 0xF3, 'sEb4': 0xB2, 'stEb4': 0xF2, 'zEb4': 0x72,
    'q.D#4': 0x32, 'qD#4': 0xB3, 'i.D#4': 0x73, 'iD#4': 0x33, 'itD#4': 0xF3, 'sD#4': 0xB2, 'stD#4': 0xF2, 'zD#4': 0x72,
    'q.D-4': 0x30, 'qD-4': 0xB1, 'i.D-4': 0x71, 'iD-4': 0x31, 'itD-4': 0xF1, 'sD-4': 0xB0, 'stD-4': 0xF0, 'zD-4': 0x70,
    'q.C#4': 0x2E, 'qC#4': 0xAF, 'i.C#4': 0x6F, 'iC#4': 0x2F, 'itC#4': 0xEF, 'sC#4': 0xAE, 'stC#4': 0xEE, 'zC#4': 0x6E,
    'q.C-4': 0x2C, 'qC-4': 0xAD, 'i.C-4': 0x6D, 'iC-4': 0x2D, 'itC-4': 0xED, 'sC-4': 0xAC, 'stC-4': 0xEC, 'zC-4': 0x6C,
    'q.B-3': 0x2A, 'qB-3': 0xAB, 'i.B-3': 0x6B, 'iB-3': 0x2B, 'itB-3': 0xEB, 'sB-3': 0xAA, 'stB-3': 0xEA, 'zB-3': 0x6A,
    'q.Bb3': 0x28, 'qBb3': 0xA9, 'i.Bb3': 0x69, 'iBb3': 0x29, 'itBb3': 0xE9, 'sBb3': 0xA8, 'stBb3': 0xE8, 'zBb3': 0x68,
    'q.A#3': 0x28, 'qA#3': 0xA9, 'i.A#3': 0x69, 'iA#3': 0x29, 'itA#3': 0xE9, 'sA#3': 0xA8, 'stA#3': 0xE8, 'zA#3': 0x68,
    'q.A-3': 0x26, 'qA-3': 0xA7, 'i.A-3': 0x67, 'iA-3': 0x27, 'itA-3': 0xE7, 'sA-3': 0xA6, 'stA-3': 0xE6, 'zA-3': 0x66,
    'q.Ab3': 0x24, 'qAb3': 0xA5, 'i.Ab3': 0x65, 'iAb3': 0x25, 'itAb3': 0xE5, 'sAb3': 0xA4, 'stAb3': 0xE4, 'zAb3': 0x64,
    'q.G#3': 0x24, 'qG#3': 0xA5, 'i.G#3': 0x65, 'iG#3': 0x25, 'itG#3': 0xE5, 'sG#3': 0xA4, 'stG#3': 0xE4, 'zG#3': 0x64,
    'q.G-3': 0x22, 'qG-3': 0xA3, 'i.G-3': 0x63, 'iG-3': 0x23, 'itG-3': 0xE3, 'sG-3': 0xA2, 'stG-3': 0xE2, 'zG-3': 0x62,
    'q.Gb3': 0x20, 'qGb3': 0xA1, 'i.Gb3': 0x61, 'iGb3': 0x21, 'itGb3': 0xE1, 'sGb3': 0xA0, 'stGb3': 0xE0, 'zGb3': 0x60,
    'q.F#3': 0x20, 'qF#3': 0xA1, 'i.F#3': 0x61, 'iF#3': 0x21, 'itF#3': 0xE1, 'sF#3': 0xA0, 'stF#3': 0xE0, 'zF#3': 0x60,
    'q.F-3': 0x1E, 'qF-3': 0x9F, 'i.F-3': 0x5F, 'iF-3': 0x1F, 'itF-3': 0xDF, 'sF-3': 0x9E, 'stF-3': 0xDE, 'zF-3': 0x5E,
    'q.E-3': 0x1C, 'qE-3': 0x9D, 'i.E-3': 0x5D, 'iE-3': 0x1D, 'itE-3': 0xDD, 'sE-3': 0x9C, 'stE-3': 0xDC, 'zE-3': 0x5C,
    'q.Eb3': 0x1A, 'qEb3': 0x9B, 'i.Eb3': 0x5B, 'iEb3': 0x1B, 'itEb3': 0xDB, 'sEb3': 0x9A, 'stEb3': 0xDA, 'zEb3': 0x5A,
    'q.D#3': 0x1A, 'qD#3': 0x9B, 'i.D#3': 0x5B, 'iD#3': 0x1B, 'itD#3': 0xDB, 'sD#3': 0x9A, 'stD#3': 0xDA, 'zD#3': 0x5A,
    'q.D-3': 0x18, 'qD-3': 0x99, 'i.D-3': 0x59, 'iD-3': 0x19, 'itD-3': 0xD9, 'sD-3': 0x98, 'stD-3': 0xD8, 'zD-3': 0x58,
    'q.Db3': 0x16, 'qDb3': 0x97, 'i.Db3': 0x57, 'iDb3': 0x17, 'itDb3': 0xD7, 'sDb3': 0x96, 'stDb3': 0xD6, 'zDb3': 0x56,
    'q.C#3': 0x16, 'qC#3': 0x97, 'i.C#3': 0x57, 'iC#3': 0x17, 'itC#3': 0xD7, 'sC#3': 0x96, 'stC#3': 0xD6, 'zC#3': 0x56,
    'q.C-3': 0x14, 'qC-3': 0x95, 'i.C-3': 0x55, 'iC-3': 0x15, 'itC-3': 0xD5, 'sC-3': 0x94, 'stC-3': 0xD4, 'zC-3': 0x54,
    'q.B-2': 0x12, 'qB-2': 0x93, 'i.B-2': 0x53, 'iB-2': 0x13, 'itB-2': 0xD3, 'sB-2': 0x92, 'stB-2': 0xD2, 'zB-2': 0x52,
    'q.Bb2': 0x10, 'qBb2': 0x91, 'i.Bb2': 0x51, 'iBb2': 0x11, 'itBb2': 0xD1, 'sBb2': 0x90, 'stBb2': 0xD0, 'zBb2': 0x50,
    'q.A#2': 0x10, 'qA#2': 0x91, 'i.A#2': 0x51, 'iA#2': 0x11, 'itA#2': 0xD1, 'sA#2': 0x90, 'stA#2': 0xD0, 'zA#2': 0x50,
    'q.Ab2': 0x0E, 'qAb2': 0x8F, 'i.Ab2': 0x4F, 'iAb2': 0x0F, 'itAb2': 0xCF, 'sAb2': 0x8E, 'stAb2': 0xCE, 'zAb2': 0x4E,
    'q.G#2': 0x0E, 'qG#2': 0x8F, 'i.G#2': 0x4F, 'iG#2': 0x0F, 'itG#2': 0xCF, 'sG#2': 0x8E, 'stG#2': 0xCE, 'zG#2': 0x4E,
    'q.G-2': 0x0C, 'qG-2': 0x8D, 'i.G-2': 0x4D, 'iG-2': 0x0D, 'itG-2': 0xCD, 'sG-2': 0x8C, 'stG-2': 0xCC, 'zG-2': 0x4C,
    'q.Gb2': 0x0A, 'qGb2': 0x8B, 'i.Gb2': 0x4B, 'iGb2': 0x0B, 'itGb2': 0xCB, 'sGb2': 0x8A, 'stGb2': 0xCA, 'zGb2': 0x4A,
    'q.F#2': 0x0A, 'qF#2': 0x8B, 'i.F#2': 0x4B, 'iF#2': 0x0B, 'itF#2': 0xCB, 'sF#2': 0x8A, 'stF#2': 0xCA, 'zF#2': 0x4A,
    'q.F-2': 0x08, 'qF-2': 0x89, 'i.F-2': 0x49, 'iF-2': 0x09, 'itF-2': 0xC9, 'sF-2': 0x88, 'stF-2': 0xC8, 'zF-2': 0x48,
    'q.E-2': 0x06, 'qE-2': 0x87, 'i.E-2': 0x47, 'iE-2': 0x07, 'itE-2': 0xC7, 'sE-2': 0x86, 'stE-2': 0xC6, 'zE-2': 0x46,
    'q....': 0x04, 'q...': 0x85, 'i....': 0x45, 'i...': 0x05, 'it...': 0xC5, 's...': 0x84, 'st...': 0xC4, 'z...': 0x44,
    'q.D-6': 0x02, 'qD-6': 0x83, 'i.D-6': 0x43, 'iD-6': 0x03, 'itD-6': 0xC3, 'sD-6': 0x82, 'stD-6': 0xC2, 'zD-6': 0x42,

    '0': 0x00,
}

byte_to_melody = {v: k for k,v in melody_to_byte.items()}
byte_to_harmony = {v: k for k,v in harmony_to_byte.items()}

def melody(phrase: str) -> bytes:
    return bytes(melody_to_byte[s] for s in phrase.split())

def harmony(phrase: str) -> bytes:
    return bytes(harmony_to_byte[s] for s in phrase.split())

bass = melody
noise = harmony

class Music:
    def __init__(self, rom):
        self.rom = rom
        self.hp = song_headers # Header pointer
        self.dp = music_data # Data pointer

    def write(self, index, length, data) -> int:
        return write(self.rom, index, length, data)

    def write_data(self, buf) -> int:
        '''Write data, advance dp, return old dp.'''
        where = self.dp
        self.dp += self.write(where, len(buf), buf)
        return where

    def write_header(self, buf) -> int:
        '''Write data, advance hp, return old hp.'''
        where = self.hp
        print(hex(where))
        self.hp += self.write(where, len(buf), buf)
        return where

    def song(self, name: str, speed: int, melody: bytes, harmony: bytes, bass: bytes, noise: bytes) -> int:
        '''Write a song header + data. Return (header - song table), to write to the song table.'''
        print('=== Writing song: %r' % name)

        # Write song data.
        noise = noise or b'\4'  # Avoid crash.
        parts = {}
        m = self.write_data(melody + b'\0'); parts[melody] = m
        b = parts.get(bass) or self.write_data(bass); parts[bass] = b
        h = parts.get(harmony) or self.write_data(harmony); parts[harmony] = h
        n = parts.get(noise) or self.write_data(noise + b'\0'); parts[noise] = n
        print('(Mel, Bass, Harm, Noise) at (%04x, %04x, %04x, %04x)' % (m, b, h, n))

        # Compute the header.
        cpu_m = rom_to_cpu(m)
        lo = cpu_m & 0xFF
        hi = cpu_m >> 8
        tr = b - m
        s1 = h - m
        ns = n - m

        # Write header.
        header = bytes([speed, lo, hi, tr, s1] + ([] if ns is None else [ns]))
        addr = self.write_header(header)
        print('Header:', ' '.join('%02x' % c for c in header), 'at', addr)
        print('Use as %02x in the song table.' % (addr - song_table))
        return addr - song_table

    def rows_to_bytes(self, rows: list, is_melodic: bool) -> bytes:
        notes = [r.split()[0] for r in rows]
        rle = [['...', 0]]
        for n in notes:
            if n == '...':
                if rle[-1][1] == 4: rle.append(['...', 1])
                else: rle[-1][1] += 1
            else: rle.append([n, 1])
        rle = [[x,y] for [x,y] in rle if y]
        bs = []
        now_l = -1
        print(rle)
        for [n,l] in rle:
            # 'q.': 0x80, 'q': 0x86, 'i.': 0x85, 'i': 0x84, 'it': 0x87, 's': 0x82, 'st': 0x83, 'z': 0x81,
            if l != now_l:
                now_l = l
                if is_melodic: bs.append([None, 0x82, 0x84, 0x85, 0x86, None, 0x80][l])
            if is_melodic: bs.append(melody_to_byte[n])
            else: bs.append(harmony_to_byte[ [None, 's', 'i', 'i.', 'q', None, 'q.'][l]+n ])
        return bytes(bs)

    def song_from_pattern(self, name: str, speed: int, pattern: dict) -> int:
        len = 0
        while len < 64:
            len += 1
            if any(v[len-1].endswith('D00') for v in pattern.values()): break
        mel_rows = pattern[1][:len]
        mel_bytes = self.rows_to_bytes(mel_rows, True)
        harm_rows = pattern[0][:len]
        harm_bytes = self.rows_to_bytes(harm_rows, False)
        bass_rows = pattern[2][:len]
        bass_bytes = self.rows_to_bytes(bass_rows, True)

        return self.song(name, speed, mel_bytes, harm_bytes, bass_bytes, b'')

    def clear(self) -> None:
        silence = self.song('Silence', 0x18, b'\4', b'\4', b'\4', b'\4')
        # Point everything towards silence.
        self.write(song_table, song_table_size, bytes([silence] * song_table_size))

    def write_new_music(self) -> None:
        # Overworld music!
        # Dict: trk -> pat -> col -> list of notes
        tracks = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        tn = None
        pi = None
        with open('newmario.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('TRACK'):
                    tn = line.split()[-1][1:-1]
                elif line.startswith('PATTERN'):
                    pi = int(line.split()[-1])
                elif line.startswith('ROW'):
                    for ci, x in enumerate(line.split(' : ')[1:]):
                        tracks[tn][pi][ci].append(x)
        print(tracks['overworld'][0][0])

        ow = overworld_pattern_list
        self.rom[ow] = \
            self.song_from_pattern('Overworld Intro', bpm150, tracks['overworld'][0])
        owA = self.song_from_pattern('Overworld A', bpm150, tracks['overworld'][1])
        owB = self.song_from_pattern('Overworld B', bpm150, tracks['overworld'][2])
        self.rom[ow+1] = self.rom[ow+3] = self.rom[ow+5] = owA
        self.rom[ow+2] = self.rom[ow+4] = self.rom[ow+6] = owB
        self.rom[underground_song] = \
            self.song_from_pattern('Underground', bpm150, tracks['underground'][0])

    def patch(self):
        self.clear()
        self.write_new_music()

def patch_music(rom: bytearray) -> None:
    Music(rom).patch()

########################################
# Main
########################################

def patch(rom: bytearray) -> None:
    patch_colors(rom)
    patch_music(rom)
    # Credits (14 bytes):
    # rom[0x09FB5 : 0x09FC3] = text_chr('LYNN VERSION'.center(14))

def main(output_path: str, input_path: str='Super Mario Bros. (JU) (PRG0) [!].nes') -> None:
    with open(input_path, 'rb') as f:
        rom = bytearray(f.read())
    assert bytes(rom[0:3]) == b'NES'
    patch(rom)
    with open(output_path, 'wb') as f:
        f.write(rom)

if __name__ == '__main__':
    main('lynnsmb.nes')

