import sys
import json

if len(sys.argv) != 3:
    print(f'Usage: {sys.argv[0]} file_in.micro file_out.rom')
    exit(1)

control_line_values = {
        'IO':2**0,
        'II':2**1,
        'AO':2**2,
        'AI':2**3,
        'BO':2**4,
        'BI':2**5,
        'ALU_SEC':2**6,
        'ALU_O':2**7,
        'RI':2**8,
        'RO':2**9,
        'ADDRHI':2**10,
        'ADDRLO':2**11,
        'FL_IN':2**12,
        'PCHI_O':2**13,
        'PCLO_O':2**14,
        'ALU_OP1':2**15,
        'ALU_OP2':2**16,
        'ALU_OP3':2**17,
        'ALU_OP4':2**18,
        'PCHI_LD':2**19,
        'PCHI_LDC':2**20,
        'PCLO_LD':2**21,
        'PCLO_LDC':2**22,
        'PORT_I':2**23,
        'PORT_O':2**24,
        'ALU_CB_I':2**25,
        'PORT_ADDR':2**26,
        'PORT_ACK1':2**27,
        'PORT_ACK2':2**28,
        'FLAG_BITSEL':2**29,
        'PC_INC':2**30,
        'RST':2**31,
        'ABA_I':2**32,
        'ABA_O':2**33,
        'ABB_I':2**34,
        'ABB_O':2**35,
        'HALT':2**36,
        'BUS_O':2**37,
        'BUS0':2**38,
        'BUS1':2**39,
        'BUS2':2**40,
        'BUS3':2**41,
        'BUS4':2**42,
        'BUS5':2**43,
        'BUS6':2**44,
        'BUS7':2**45,
}
t_bits = 4
op_bits = 8

in_file, out_file = sys.argv[1:]
with open(in_file) as f:
    micro = f.read().split('\n')

micro = [x.strip() for x in micro if x.strip() != '']
print(f'{micro=}')

# process includes
'''
Include format
%include relative_file_path/a/b/c
'''

new = []
for line in micro:
    if line.startswith('%include'):
        file_paths = line[len('%include'):].strip().split(' ')
        for fp in file_paths: # included files dont include more files because that requires circular inclusion logic
            with open(fp) as f:
                new += [x.strip() for x in f.read().split('\n') if x.strip() != '']
    
    else:
        new.append(line)

micro = new
print(f'{micro=}')

# process macros
'''
Macro format
%define label @arg1
...abc
...def

$...
%label(arg1_in  , arg2_in
%label ( arg1_in,arg2_in
%label(a, b, c)
'''
processed_micro = []
definition_name = ''
macros = {}
macro_args = {}
last_macro = []
last_macro_args = []
for line_num, line in enumerate(micro):
    if line.startswith('%define'):
        parsed_line = [x.strip() for x in line[len('%define'):].strip().split('@')]
        definition_name = parsed_line[0]
        last_macro_args = ['@'+x for x in parsed_line[1:]]
        if definition_name == '':
            print(f'invalid definition_name: {line}')
            exit(4)

    elif not definition_name:
        processed_micro.append(line)

    elif line == '%end':
        print(f'defined {repr(definition_name)}')
        macros[definition_name] = last_macro
        macro_args[definition_name] = last_macro_args
        definition_name = ''
        last_macro = []

    if line.startswith('%include'):
        print(f'%include not processed, included files cannot include more files')

    if definition_name and not line.startswith('%'):
        last_macro.append(line)

print(f'{macros=}')
print(f'{macro_args=}')
micro = []
for line in processed_micro:
    if line.startswith('%'):
        try:
            print(repr(line[1:].split('(')[0]))
            this_macro = macros[line[1:].split('(')[0]]

            if len(macro_args[line[1:].split('(')[0]]) != 0:
                args = line[1:].split('(')[1].replace(')', '').split(',')
                print(repr(line[1:].split('(')[0]))
                arg_names = macro_args[line[1:].split('(')[0]]

            else:
                args = []
                arg_names = []

            rendered_macro = []
            for line in this_macro:
                rendered_line = line
                for arg_name, value in zip(arg_names, args):
                    print(f'{arg_name=} {value=}')
                    rendered_line = rendered_line.replace(arg_name, value)

                rendered_macro.append(rendered_line)
                print(f'{rendered_line=}')
            
            micro += rendered_macro

        except KeyError:
            print(f'error during macro lookup {repr(line)}')
            exit(4)
    else:
        micro.append(line)

print(f'{micro=}')

'''
Format:
$0:comment
0:HLT OI
1:PCE J PCO
4:... ...
3:... ...
$...
...
'''

#TODO fix line num desync
opcode = 0
ops = {0:{}}
for line_num, line in enumerate(micro):
    print(line_num, repr(line), sep='\t')
    if line.startswith('$'):
        try:
            opcode = int(line.split(':')[0][1:])
        
        except ValueError:
            print(f'invalid opcode: {line=}')
            exit(2)

        if opcode not in ops:
            ops[opcode] = {}
    
    else:
        t, signals = line.split(':')
        try:
            t = int(t)
        
        except ValueError:
            print(f'invalid t symbol in opcode {opcode}: {t=}')
            exit(2)
        
        if t not in ops[opcode]:
            ops[opcode][t] = 0

        signals = signals.split(' ')
        for signal in signals:
            try:
                ops[opcode][t] |= control_line_values[signal]

            except KeyError:
                print(f'{signal} does not appear to be a valid control signal')
                exit(5)

        print(f'{t=}\t{signals=}')
        print(f'{ops[opcode][t]=}')

    print()

print(f'{ops=}')

try:
    if max(ops.keys()) >= 2**op_bits:
        print('opnum is too high')
        exit(3)
except ValueError:
    pass

rom = []
for x in range(2**op_bits):
    if x not in ops.keys():
        rom.append([0]*(2**t_bits))
    
    else:
        try:
            if max(ops[x].keys()) >= 2**t_bits:
                print(f't is too high in op {x}')
                exit(3)

        except ValueError:
            pass

        z = []
        for y in range(2**t_bits):
            if y in ops[x]:
                z.append(ops[x][y])
            else:
                z.append(0)

        rom.append(z)

rom_text = 'v3.0 hex words plain\n'
for x in rom:
    rom_text += ' '.join([f'{y:012x}' for y in x]) + '\n'

#print()
#print(rom_text)

with open(out_file, 'w') as f:
    f.write(rom_text)
