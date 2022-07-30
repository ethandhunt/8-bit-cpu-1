import op
import sys
import math

if len(sys.argv) != 3:
    print(f'Usage: {sys.argv[0]} infile.s1.asm outfile.s1.rom')

infile, outfile = sys.argv[1:]

print(f'{infile=} {outfile=}')

with open(infile) as f:
    asm = f.read().split('\n')
    asm = [x.split(';')[0].strip() for x in asm if x.strip() != '']
    asm = list(zip(range(len(asm)), asm))

print(f'{asm=}')

keyword_dict = op.code

'''
$   1 byte hex
$$  2 byte hex
$$$ n byte hex

#   1 byte dec
##  2 byte dec
### n byte dec

@   1 byte (lo) memory address
@@  2 byte memory address

Format:
add8 #1; comment
addi #12        ;comment
sub16 $$8fe2
subi $4a

x02 x12

label:
add8 @memory_location
sub16 @@memory_location
jmp @label
memory_location: x02
'''

memory_locations = {}
rom = []
for line_num, line in asm:
    # label handling
    if line[-1] == ':':
        memory_locations[line.split(' ')[-1].replace(':', '')] = len(rom)
    
    # operation handling
    else:
        processed_line = [x for x in line.split(' ') if x != '']
        new = []
        for x in processed_line:
            if x in keyword_dict:
                rom.append(keyword_dict[x])
                continue
            
            try:
                if x.startswith('$$$'):
                    value = int(x[3:], 16)
                    length = math.ceil(math.log2(value)/8)
                    for y in range(length):
                        rom.append(value >> 8 * (length - y - 1) & 0xff)
                    continue

                if x.startswith('$$'):
                    value = int(x[2:], 16)
                    rom.append(value >> 8 & 0xff)
                    rom.append(value & 0xff)
                    continue

                if x.startswith('$'):
                    value = int(x[1:], 16)
                    rom.append(value & 0xff)
                    continue

                if x.startswith('###'):
                    value = int(x[3:])
                    length = math.ceil(math.log2(value)/8)
                    for y in range(length):
                        rom.append(value >> 8 * (length - y - 1) & 0xff)
                    continue

                if x.startswith('##'):
                    value = int(x[2:])
                    rom.append(value & 0xff)
                    rom.append(value >> 8 & 0xff)
                    continue

                if x.startswith('#'):
                    value = int(x[1:])
                    rom.append(value & 0xff)
                    continue

            except ValueError:
                print(f'invalid integer literal at line {line_num}: {x:r}')
                exit(1)

            try:
                if x.startswith('@@'):
                    value = memory_locations[x[2:]]
                    rom.append(value >> 8 & 0xff)
                    rom.append(value & 0xff)
                    continue

                if x.startswith('@'):
                    value = memory_locations[x[1:]]
                    rom.append(value & 0xff)
                    continue

            except KeyError:
                print(f'invalid memory reference at line {line_num}: {x:r}')

print(' '.join([hex(x) for x in rom]))

rom_text = 'v3.0 hex words plain\n'

for x in range(0, 2**16, 16):
    words = []
    for y in range(16):
        if x + y < len(rom):
            words.append(f'{rom[x+y]:02x}')
        else:
            words.append('00')

    rom_text += ' '.join(words) + '\n'

with open(outfile, 'w') as f:
    f.write(rom_text[:-1])
