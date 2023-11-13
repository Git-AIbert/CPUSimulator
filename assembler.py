# 操作码定义
# R-type
RTYPE = 0b000000
# I-type
IADDI = 0b001000
ILW = 0b100011
ISW = 0b101011
IBNE = 0b000101
IBEQ = 0b000100
IBGT = 0b001101  # 以下四个均不是MIPS中的编码规则
IBGE = 0b001100  #
IBLT = 0b000111  #
IBLE = 0b000110  #
# J-type
IJ = 0b000010
IJAL = 0b000011

# 函数码定义
FADD = 0b100000
FJR = 0b001000
FSLL = 0b000000  # nop = sll $0,$0,0
FSYS = 0b001100

# 定义ALU的运算
ALUNOP = 0
ALUADD = 1
ALUSUB = 2

# 指令操作码
opcodes = {
    # R-type
    'add': RTYPE,
    'jr': RTYPE,
    'sll': RTYPE,
    'syscall': RTYPE,

    # I-type
    'addi': IADDI,
    'lw': ILW,
    'sw': ISW,
    'bne': IBNE,
    'beq': IBEQ,
    'bgt': IBGT,
    'bge': IBGE,
    'blt': IBLT,
    'ble': IBLE,

    # J-type
    'j': IJ,
    'jal': IJAL
}

ITYPE = [IADDI, ILW, ISW, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]
JTYPE = [IJ, IJAL]

# 指令功能码
functs = {
    'add': FADD,
    'jr': FJR,
    'sll': FSLL,
    'syscall': FSYS
}


# 汇编指令的函数
def assemble_instruction(instruction):
    instruction_code = 0
    # 解析指令字符串
    parts = instruction.split(" ", 1)
    if isinstance(parts, list):
        opcode = opcodes[parts[0]]
    else:
        opcode = opcodes[parts]
    if opcode == RTYPE:
        funct = functs[parts[0]]
        rs = rt = rd = shamt = 0
        if funct == FADD:
            arguments = parts[1].split(",")
            rd = int(arguments[0].strip("$ "))
            rs = int(arguments[1].strip("$ "))
            rt = int(arguments[2].strip("$ "))
        if funct == FJR:
            rs = int(parts[1].strip(" "))
        if funct == FSLL:
            arguments = parts[1].split(",")
            rd = int(arguments[0].strip("$ "))
            rt = int(arguments[1].strip("$ "))
            shamt = int(arguments[2].strip(" "))
        if funct == FSYS:
            pass
        instruction_code = rs << 21 | rt << 16 | rd << 11 | shamt << 6 | funct
    if opcode in ITYPE:
        rs = rt = imm = 0
        if opcode in [IADDI]:
            arguments = parts[1].split(",")
            rt = int(arguments[0].strip("$ "))
            rs = int(arguments[1].strip("$ "))
            imm = int(arguments[2])
        if opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
            arguments = parts[1].split(",")
            rt = int(arguments[1].strip("$ "))
            rs = int(arguments[0].strip("$ "))
            imm = int(arguments[2]) >> 2
        if opcode in [ILW, ISW]:
            arguments = parts[1].split(",")
            rt = int(arguments[0].strip("$ "))
            arguments = arguments[1].split("(")
            imm = int(arguments[0])
            rs = int(arguments[1].strip("$) "))
        if imm < 0:
            imm = (1 << 16) + imm
        instruction_code = opcode << 26 | rs << 21 | rt << 16 | imm
    if opcode in JTYPE:
        address = int(parts[1]) >> 2
        instruction_code = opcode << 26 | address

    return instruction_code


# 汇编程序
def assemble(program):
    assembled_code = []
    for instruction in program:
        instruction_code = assemble_instruction(instruction)
        assembled_code.append(instruction_code)
    return assembled_code


def remove_comments_and_get_instructions(input_string):
    instructions = []

    lines = input_string.split("\n")
    for line in lines:
        line = line.strip()
        if "#" in line:
            line = line[:line.index("#")].strip()
        if line:
            instructions.append(line)

    return instructions


loop_loop = """
    addi $1, $0, 999 # i = 999
    addi $2, $0, 1   # s = 1
    blt $1, $0, 28  # if i < 0 goto end
    addi $4, $0, 3996    # addr = 999 << 2
    add $4, $3, $4   # addr = x + addr
    
    lw $5, 0($4)     # val = (addr)
    add $5, $5, $2   # val = val + s
    sw $5, 0($4)     # (addr) = val
    addi $4, $4, -4  # addr = addr - 4
    bge $4, $3, -20 # if addr >= x goto loop

    syscall
"""

loop_unrolling4 = """
    addi $2, $0, 1   # s = 1
    addi $4, $0, 3996    # addr = 999 << 2
    add $4, $3, $4   # addr = x + addr

    lw $5, 0($4)     # val1 = (addr)
    lw $6, -4($4)    # val2 = (addr - 4)
    lw $7, -8($4)    # val3 = (addr - 8)
    lw $8, -12($4)   # val4 = (addr - 12)
    add $5, $5, $2   # val1 = val1 + s
    add $6, $6, $2   # val2 = val2 + s
    add $7, $7, $2   # val3 = val3 + s
    add $8, $8, $2   # val4 = val4 + s
    sw $5, 0($4)     # (addr) = val1
    sw $6, -4($4)    # (addr - 4) = val2
    sw $7, -8($4)    # (addr - 8) = val3
    sw $8, -12($4)   # (addr - 12) = val4
    addi $4, $4, -16 # addr = addr - 16
    bge $4, $3, -56 # if addr >= x goto loop
    
    syscall
"""

loop_unrolling10 = """
    addi $2, $0, 1   # s = 1
    addi $4, $0, 3996    # addr = 999 << 2
    add $4, $3, $4   # addr = x + addr

    lw $5, 0($4)     # val1 = (addr)
    lw $6, -4($4)    # val2 = (addr - 4)
    lw $7, -8($4)    # val3 = (addr - 8)
    lw $8, -12($4)   # val4 = (addr - 12)
    lw $9, -16($4)
    lw $10, -20($4)
    lw $11, -24($4)
    lw $12, -28($4)
    lw $13, -32($4)
    lw $14, -36($4)
    add $5, $5, $2   # val1 = val1 + s
    add $6, $6, $2   # val2 = val2 + s
    add $7, $7, $2   # val3 = val3 + s
    add $8, $8, $2   # val4 = val4 + s
    add $9, $9, $2
    add $10, $10, $2
    add $11, $11, $2
    add $12, $12, $2
    add $13, $13, $2
    add $14, $14, $2
    sw $5, 0($4)     # (addr) = val1
    sw $6, -4($4)    # (addr - 4) = val2
    sw $7, -8($4)    # (addr - 8) = val3
    sw $8, -12($4)   # (addr - 12) = val4
    sw $9, -16($4)
    sw $10, -20($4)
    sw $11, -24($4)
    sw $12, -28($4)
    sw $13, -32($4)
    sw $14, -36($4)
    addi $4, $4, -40 # addr = addr - 16
    bge $4, $3, -128 # if addr >= x goto loop
    
    syscall
"""

# 将字符串转换为汇编指令数组
assembled_program = remove_comments_and_get_instructions(loop_unrolling10)

# 转换为二进制指令
binary_program = assemble(assembled_program)

# 打印汇编结果
for i in range(len(binary_program)):
    print(f"0b{format(binary_program[i], '032b')},  # {assembled_program[i]}")
