# 8-bit-cpu-1

## How to run
Install logisim-evolution from the github [repo](https://github.com/logisim-evolution/logisim-evolution)

After installation open logisim-evolution, open the [circuit file](https://github.com/ethandhunt/8-bit-cpu-1/blob/main/custom_cpu.circ)

Use the [instruction set reference](https://github.com/ethandhunt/8-bit-cpu-1/blob/main/instruction_set1.txt) to create programs in RAM

To change instruction sets you can load another microcode rom into the microcode rom inside the cpu subcircuit

To attach more devices to the device bus you can just add a comparator comparing the portaddr line to the device address and use buffer gates to set the bus lines when the device is selected

## Specs
16 bit addressing

8 bit opcodes

Up to 16 microcode steps

83 implemented opcodes
