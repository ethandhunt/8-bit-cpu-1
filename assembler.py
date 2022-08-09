import sys
import math
import re

if len(sys.argv) != 3:
    print(f'Usage: {sys.argv[0]} infile.s1.asm outfile.s1.rom')

infile, outfile = sys.argv[1:]

print(f'{infile=} {outfile=}')

with open(infile) as f:
    asm = f.read().split('\n')
    asm = [x.split(';')[0].strip() for x in asm if x.strip() != '']
    asm = list(zip([str(x+1) for x in range(len(asm))], asm))

print(f'{asm=}')


# process includes
'''
Include format
%include relative_file_path/a/b/c
'''
new = []
for line_num, line in asm:
    if line.startswith('%include'):
        file_paths = line[len('%include'):].strip().split(' ')
        for fp in file_paths: # included files dont include more files because that requires circular inclusion logic
            with open(fp) as f:
                new += [(f'{fp} {l+1}', x.split(';')[0].strip()) for l, x in enumerate(f.read().split('\n')) if x.split(';')[0].strip() != '']

    else:
        new.append((line_num, line))

asm = new

# process macros
'''
Interpreted Expressions
{[ ]operand1[ ]operator[ ]operand2[}]
or
{[ ]operand1[ ][}]

Inline Expressions
{operand1[ ]operator[ ]operand2}
or
{[ ]operand1[ ]}

expressions will return a value with a byte length equivalent to the maximum of it's two operands

Operators
+ add
- subtract
* multiply
/ divide
% modulo

Variable Formats
&arg (search and replace with argument, use literal format when giving arguments in macro calls)
&&variable (search and replace with global var)

Literal Expression Formats
$[bytes:]0...f  hex
#[bytes:]0...9  dec
"..."           str
'.              chr

[bytes:] is in decimal

Macro Conditionals
term := literal | interpreted_expression
condition := [ ]term[ ]boolean_operator[ ]term[ ]

%if[ ]condition
...
[%else
...]
%endif

%while[ ]condition
...
%end

Boolean Operators
== equivalent
> greater than
< less than
!= not equivalent
| or
&= and

boolean operators return 1 if true and 0 if false
the or operator acts as a bitwise or

Variable Manipulation
%define &lvar|&&gvar expression
%set &lvar|&&gvar expression
variables must be defined before they can be used with %set

Macro Format
%macro name arg1 arg2
ext_lit ext_lit expression
$** $$****
addi arg1
subi {arg1+arg2
muli {arg1*{arg1+arg2}
%end

expression := {op1[operator[ ]op2][}]

Calling Macros
%name[ ]([ ]arg1val[ ],[ ]arg2val[ ][)]
'''

def render_macro(line_num, macro_name, macro_args):
    macro_lines = macros[macro_name]['lines']
    macro_arg_names = macros[macro_name]['arg_names']

    new = []
    local_vars = dict(zip(macro_arg_names, macro_args))
    for this_macro_line_num, line in macro_lines:
        processed_line = []
        in_string = False
        in_expression = False
        d = 0
        last = ''
        this_line_num = f'{line_num} {macro_name} {this_macro_line_num}'
        for x in line:
            if x in ' ' and last.strip() != '' and not in_string and not in_expression:
                processed_line.append(last.strip())

            elif x == '"':
                in_string = not in_string

            elif in_string: # functional
                pass

            elif not in_expression and x == '{':
                d = 1
                in_expression = True
                processed_line.append(last)
                last = '{'

            elif in_expression:
                if x == '}':
                    d -= 1
                    last += x

                elif x == '{':
                    d += 1
                    last += x

                elif d == 0:
                    processed_line += '# '.join(parse_expression(this_line_num, last, local_vars))
                    last = ''
                    in_expression = False

                else:
                    last += x

            else:
                last += x

operators = {
    '+': lambda x, y: x+y,
    '-': lambda x, y: x-y,
    '*': lambda x, y: x*y,
    '/': lambda x, y: x//y,
    '%': lambda x, y: x%y,
    '==':lambda x, y: int(x==y),
    '>': lambda x, y: int(x>y),
    '<': lambda x, y: int(x<y),
    '!=':lambda x, y: int(x!=y),
    '|': lambda x, y: int(x|y),
    '&=':lambda x, y: int(x&y),
    '{': lambda x, y: print('calling \'{\' operator ???'),
}

def parse_expression(line_num, expression, local_vars={}):
    def solve_expression(line_num, tokens, local_vars):
        tokens.pop(0) # remove preceding {

        print()
        print(f'parse_expression> {line_num=}{tokens=}')
        operand1 = []
        d = 1
        while d != 0:
            d -= 1
            x = tokens.pop(0)
            if x == '{':
                d += 3

            operand1.append(x)

        if tokens == []:
            print(f'1operand expression: {operand1=}')
            if len(operand1) != 1:
                operand1 = solve_expression(line_num, operand1, local_vars)

            else:
                operand1 = parse_expression(line_num, operand1[0], local_vars)

            return operand1

        operator = tokens.pop(0)

        operand2 = []
        d = 1
        while d != 0:
            d -= 1
            x = tokens.pop(0)
            if x == '{':
                d += 3

            operand2.append(x)

        print(f'{operand1=} {operator=} {operand2=}')

        if len(operand1) != 1:
            operand1 = solve_expression(line_num, operand1, local_vars)

        else:
            operand1 = parse_expression(line_num, operand1[0], local_vars)


        if len(operand2) != 1:
            operand2 = solve_expression(line_num, operand2, local_vars)

        else:
            operand2 = parse_expression(line_num, operand2[0], local_vars)


        print()
        byte_length = max(len(operand1), len(operand2))
        val1 = sum([y << 8*x for x, y in enumerate(operand1)])
        val2 = sum([y << 8*x for x, y in enumerate(operand2)])

        print(f'{val1=} {operator=} {val2=} ret {operators[operator](val1, val2)}')
        print(f'parse_expression> {line_num} ret {[(operators[operator](val1, val2) >> 8*(byte_length-x-1)) & 0xff for x in range(byte_length)]}')
        return [(operators[operator](val1, val2) >> 8*(byte_length-x-1)) & 0xff for x in range(byte_length)]

    expression = expression.replace('}', '')

    if expression[0] == '{':
        #tokens = re.split(r"(\+|\-|\*|\/|\%|\=|\>|\<|\!\=|\{)", expression[1:]) # strings are annoying
        last = ''
        tokens = []
        in_string = False
        for x in expression:
            last += x if in_string or x != ' ' else ''

            if not in_string:
                for op in operators:
                    if last.endswith(op):
                        tokens.append(last[:-len(op)])
                        tokens.append(op)
                        last = ''

            if x == '"':
                in_string = not in_string

        tokens.append(last)
        tokens = [x for x in tokens if x != '']

        print(f'{tokens=}')

        return solve_expression(line_num, tokens, local_vars)

    else:
        if expression.startswith('$'):
            if expression.count(':') == 0:
                result = []
                value = int(expression[1:], 16)
                length = math.ceil(math.log2(value)/8) if value not in [0, 1] else 1
                for y in range(length):
                    result.append(value >> 8 * (length - y - 1) & 0xff)

                print(f'{value=} {result=} {length=}')
                return result

            elif expression.count(':') == 1:
                result = []
                value = int(expression.split(':')[1], 16)
                byte_length = int(expression[1:].split(':')[0])
                for x in range(byte_length):
                    result.append((value >> 8*x) & 0xff)
                print()

                return result

            else:
                print(f'invalid expression at line {line_num}: {expression}')
                exit(1)

        elif expression.startswith('#'):
            if expression.count(':') == 0:
                result = []
                value = int(expression[1:])
                length = math.ceil(math.log2(value)/8) if value not in [0, 1] else 1
                for y in range(length):
                    result.append(value >> 8 * (length - y - 1) & 0xff)

                return result

            elif expression.count(':') == 1:
                result = []
                value = int(expression.split(':')[1])
                byte_length = int(expression[1:].split(':')[0])
                for x in range(byte_length):
                    result.append((value >> 8*x) & 0xff)

                return result
            
            else:
                print(f'invalid expression at line {line_num}: {expression}')

        elif expression.startswith('"'):
            return [ord(x) for x in expression[1:-1]]

        elif expression.startswith('\''):
            if len(expression) != 2:
                print(f'invalid character literal at line {line_num}: {expression}')
                exit(1)

            return [ord(expression[1])]
        
        elif expression.startswith('&&'):
            return global_vars[expression[2:]]

        elif expression.startswith('&'):
            return local_vars[expression[2:]]

new = []
in_macro = False
macros = {}
this_macro_name = ''
this_macro_arg_names = []
this_macro_lines = []
keyword_dict = {}
for line_num, line in asm:
    if line == '%end':
        if not in_macro:
            print(f'%end without preceding macro definition at line {line_num}')
            exit(1)

        in_macro = False
        macros[this_macro_name] = {'arg_names':this_macro_arg_names, 'lines':this_macro_lines}
        print(f'{line_num:<20}{line}')
        print()


    if line.startswith('%macro'):
        if in_macro:
            print(f'previous macro was not terminated at line {line_num}')
            exit(1)

        this_macro_name = line[len('%macro'):].strip().split(' ')[0]
        this_macro_arg_names = line[len('%macro'):].strip().split(' ')[1:]
        in_macro = True
        print(f'{line_num:<20}{line}')

    if line.startswith('%macro') or line == '%end': # functional
        pass

    elif in_macro:
        this_macro_lines.append((line_num, line))
        print(f'{line_num:<20}{" "*5}{line}')

    else:
        new.append((line_num, line))
        print(f'{line_num:<20}{line}')


asm = new
print(f'{macros=}')

new = []
global_vars = {}
for line_num, line in asm:
    if line.startswith('%define'):
        var_name = line.split(' ')[1]
        expression = ' '.join(line.split(' ')[2:])

        if var_name[:2] != '&&':
            print(f'incorrectly formatted global variable definition at line {line_num}')

            if var_name[0] == '&':
                print(f'are you trying to define a local variable?')

            exit(1)

        global_vars[var_name[2:]] = parse_expression(line_num, expression)

    elif line.startswith('%set'):
        var_name = line.split(' ')[1]
        expression = ' '.join(line.split(' ')[2:])

        if var_name[:2] != '&&':
            print(f'incorrectly formatted global variable set call at line {line_num}')

            if var_name[0] == '&':
                print(f'are you trying to set a local variable in a global scope?')

            exit(1)

        global_vars[var_name[2:]] = parse_expression(line_num, expression)

    elif line.startswith('%keyword'):
        keyword = line[len('%keyword'):].strip().split(' ')[0]
        keyword_dict[keyword] = parse_expression(line_num, ' '.join(line[len('%keyword'):].strip().split(' ')[1:]))

    elif line[0] == '%':
        macro_name = line[1:].split('(')[0]
        macro_args = [x.strip() for x in line.replace(')', '').split('(')[1].split(',')]
        new += render_macro(line_num, macro_name, macro_args)

    else:
        new.append((line_num, line))

asm = new

print(f'{global_vars=}')

'''
Literal Formats
$   1 byte hex
$$  2 byte hex
$$$ n byte hex

#   1 byte dec
##  2 byte dec
### n byte dec

@   1 byte (lo) memory address
@@  2 byte memory address

"..." ascii string

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

print(f'{asm=}')
memory_locations = {}
rom = []
for line_num, line in asm:
    print(f'{line_num:20}{line}')
    print(f'{rom=}')
    print()
    processed_line = []
    in_string = False
    last = ''
    for x in line + ' ':
        if x in ' ' and last.strip() != '' and not in_string:
            processed_line.append(last.strip())
            last = ''

        elif x == '"':
            in_string = not in_string

        elif in_string:
            processed_line.append(f'#{ord(x)}')

        else:
            last += x


    new = []
    print(f'{processed_line=}')
    for x in processed_line:
        if x in keyword_dict:
            rom += keyword_dict[x]
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

        if x[-1] == ':':
            memory_locations[x[:-1]] = len(rom)

print(f'{rom=}')
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
