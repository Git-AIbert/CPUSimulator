import array
class MyError(Exception):
    pass


# 指令内存
class IMemory:
    # 构造函数
    def __init__(self, size):
        self.mem = array.array('I', [0] * size)

    def __len__(self):
        return len(self.mem)

    def loadProgram(self, program):
        for i in range(len(program)):
            self.mem[i] = program[i]

    # 访问内存
    def access(self, address):
        if address >= len(self.mem) * 4:
            raise MyError(f"imem_error: address({address}) out of length of imem({len(self.mem) * 4})")

        addr_mod4 = address % 4
        if addr_mod4 != 0:
            raise MyError(f"imem_error: address({address}) is not a multiple of four")

        addr_div4 = address // 4
        IR = self.mem[addr_div4]

        # TODO：从内存中分离
        opcode = IR >> 26
        rs = (IR & 0b00000011111000000000000000000000) >> 21
        rt = (IR & 0b00000000000111110000000000000000) >> 16
        rd = (IR & 0b00000000000000001111100000000000) >> 11
        shamt = (IR & 0b00000000000000000000011111000000) >> 6
        funct = (IR & 0b00000000000000000000000000111111)
        imm = (IR & 0b00000000000000001111111111111111)
        target_address = (IR & 0b00000011111111111111111111111111)

        return opcode, rs, rt, rd, shamt, funct, imm, target_address


# 数据内存
class DMemory:
    # 构造函数
    def __init__(self, size):
        self.mem = array.array('I', [0] * size)

    def __len__(self):
        return len(self.mem)

    def loadData(self, data):
        for i in range(len(data)):
            self.mem[i] = data[i]

    # 访问内存
    def access(self, read, write, address, data):
        if read == 0 and write == 0:
            return

        if address >= len(self.mem) * 4:
            raise MyError(f"dmem_error: address({address}) out of length of dmem({len(self.mem) * 4})")

        addr_mod4 = address % 4
        if addr_mod4 != 0:
            raise MyError(f"dmem_error: address({address}) is not a multiple of four")

        addr_div4 = address // 4
        if read:
            return self.mem[addr_div4]
        if write:
            self.mem[addr_div4] = data
            return data

    def emit(self):
        print("\nDMemory:")
        for i in range(len(self.mem)):
            print(f"0x{format(i * 4, '08x')}: {self.mem[i]}")
        print("")


class RegFile:
    # 构造函数
    def __init__(self):
        self.reg = array.array('I', [0] * 32)

    def read(self, srcA, srcB):
        valA = valB = None
        if srcA != None:
            valA = self.reg[srcA]
        if srcB != None:
            valB = self.reg[srcB]
        return valA, valB

    def write(self, dstE, valE, dstM, valM):
        if dstE != 0:
            self.reg[dstE] = valE
        if dstM != 0:
            self.reg[dstM] = valM

    def emit(self):
        print("\nRegisters:")
        for i, value in enumerate(self.reg):
            print(f"R{i}: {value}")
        print("")


class ConditionCode:
    def __init__(self):
        self.ZF = False
        self.SF = False
        self.OF = False

    @property
    def ZF(self):
        return self._ZF

    @ZF.setter
    def ZF(self, value):
        self._ZF = value

    @property
    def SF(self):
        return self._SF

    @SF.setter
    def SF(self, value):
        self._SF = value

    @property
    def OF(self):
        return self._OF

    @OF.setter
    def OF(self, value):
        self._OF = value

    def set(self, ZF, SF, OF):
        self.ZF = ZF
        self.SF = SF
        self.OF = OF


# 操作码定义
RTYPE = 0b000000
IADDI = 0b001000
ILW   = 0b100011
ISW   = 0b101011
IBNE  = 0b000101
IJ    = 0b000010
IJAL  = 0b000011

# 函数码定义
FADD  = 0b100000
FJR   = 0b001000

# 定义ALU的运算
ALUNOP = 0
ALUADD = 1
ALUSUB = 2


# *****************************
# 取指过程
# *****************************
def Fetch(mem, PC):
    opcode, rs, rt, rd, shamt, funct, imm, address = mem.access(PC)
    return PC+4, opcode, rs, rt, rd, shamt, funct, imm, address


# *****************************
# 译码阶段
# *****************************
def SrcA(opcode, funct, rs):
    if (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [ILW, ISW, IADDI, IBNE]:
        return rs
    elif opcode in [IJ, IJAL]:
        return None
    else:
        raise MyError("invalid operation in Decode")


def SrcB(opcode, funct, rt):
    if (opcode == RTYPE and funct == FADD) \
    or opcode in [ISW, IBNE]:
        return rt
    elif (opcode == RTYPE and funct == FJR) \
    or opcode in [IADDI, ILW, IJ, IJAL]:
        return None
    else:
        raise MyError("invalid operation in Decode")


def Decode(opcode, funct, regFile, rs, rt):
    # 寄存器控制
    srcA = SrcA(opcode, funct, rs)
    srcB = SrcA(opcode, funct, rt)
    # 寄存器读
    valA, valB = regFile.read(srcA, srcB)
    return valA, valB


# *****************************
# 执行阶段
# *****************************
def ALU_A(opcode, funct, valA, valP):
    if (opcode == RTYPE and funct == FADD) \
    or opcode in [IADDI, ILW, ISW, IBNE]:
        return valA
    elif opcode == IJAL:
        return valP
    elif (opcode == RTYPE and funct == FJR) \
    or opcode == IJ:
        return None
    else:
        raise MyError("invalid operation in Execute")


def ALU_B(opcode, funct, valB, imm):
    if (opcode == RTYPE and funct == FADD) \
    or opcode == IBNE:
        return valB
    elif opcode in [IADDI, ILW, ISW]:
        return imm
    elif opcode == IJAL:
        return 0
    elif (opcode == RTYPE and funct == FJR) \
    or opcode == IJ:
        return None
    else:
        raise MyError("invalid operation in Execute")


def ALU_fun(opcode, funct):
    if (opcode == RTYPE and funct == FADD) \
    or opcode in [IADDI, ILW, ISW, IJAL]:
        return ALUADD
    if opcode == IBNE:
        return ALUSUB
    elif (opcode == RTYPE and funct == FJR) \
    or opcode == IJ:
        return ALUNOP
    else:
        raise MyError("invalid operation in Execute")


# 定义算数逻辑单元
def ALU(aluA, aluB, aluFun):
    valE = None
    ZF = SF = OF = False
    if aluFun == ALUADD:
        valE = aluA + aluB
    elif aluFun == ALUSUB:
        valE = aluA - aluB
    elif aluFun == ALUNOP:
        valE = None
    if valE != None:
        if valE > (1 << 31) - 1:
            OF = True
            valE -= 1 << 32
        elif valE < -(1 << 31):
            OF = True
            valE += 1 << 32
        if valE == 0:
            ZF = True
        if valE < 0:
            SF = True
    return valE, ZF, SF, OF


# 是否设置条件码寄存器
def SetCC(opcode, funct):
    if opcode == IBNE:
        return True
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ILW, ISW, IJ, IJAL]:
        return False
    else:
        raise MyError("invalid operation in Execute")


# 分支信号
def Cond(opcode, funct, CC):
    if opcode == IBNE:
        return CC.ZF == False
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ILW, ISW, IJ, IJAL]:
        return False
    else:
        raise MyError("invalid operation in Execute")


def Execute(opcode, funct, valA, valB, valP, imm, CC):
    # ALU控制
    aluA = ALU_A(opcode, funct, valA, valP)
    aluB = ALU_B(opcode, funct, valB, imm)
    aluFun = ALU_fun(opcode, funct)
    # ALU计算
    valE, ZF, SF, OF = ALU(aluA, aluB, aluFun)
    # 设置条件码寄存器
    if SetCC(opcode, funct):
        CC.set(ZF, SF, OF)
    # 设置分支信号
    cnd = Cond(opcode, funct, CC)
    return valE, cnd


# *****************************
# 访存阶段
# *****************************
# 内存读控制
def MReadControl(opcode, funct):
    if opcode == ILW:
        return True
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ISW, IJ, IJAL, IBNE]:
        return False
    else:
        raise MyError("invalid operation in AccessMemory")


# 内存写控制
def MWriteControl(opcode, funct):
    if opcode == ISW:
        return True
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ILW, IJ, IJAL, IBNE]:
        return False
    else:
        raise MyError("invalid operation in AccessMemory")


def MemAddr(opcode, funct, valE):
    if opcode in [ILW, ISW]:
        return valE
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, IJ, IJAL, IBNE]:
        return None
    else:
        raise MyError("invalid operation in AccessMemory")


def MemData(opcode, funct, valB):
    if opcode == ISW:
        return valB
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ILW, IJ, IJAL, IBNE]:
        return None
    else:
        raise MyError("invalid operation in AccessMemory")


def AccessMemory(opcode, funct, mem, valE, valB):
    # 内存控制
    read = MReadControl(opcode, funct)
    write = MWriteControl(opcode, funct)
    memAddr = MemAddr(opcode, funct, valE)
    memData = MemData(opcode, funct, valB)
    # 内存访问
    return mem.access(read, write, memAddr, memData)


# *****************************
# 写回阶段
# *****************************
# 寄存器dstE控制
def DstE(opcode, funct, rt, rd):
    if opcode == RTYPE and funct == FADD:
        return rd
    elif opcode == IADDI:
        return rt
    elif opcode == IJAL:
        return 31
    elif (opcode == RTYPE and funct == FJR) \
    or opcode in [ILW, ISW, IJ, IBNE]:
        return 0
    else:
        raise MyError("invalid operation in WriteBack")


# 寄存器dstM控制
def DstM(opcode, funct, rt, rd):
    if opcode == ILW:
        return rt
    elif (opcode == RTYPE and funct in [FADD, FJR]) \
    or opcode in [IADDI, ISW, IJ, IJAL, IBNE]:
        return 0
    else:
        raise MyError("invalid operation in WriteBack")


def WriteBack(opcode, funct, regFile, rt, rd, valE, valM):
    # 寄存器控制
    dstE = DstE(opcode, funct, rt, rd)
    dstM = DstM(opcode, funct, rt, rd)
    # 寄存器写
    regFile.write(dstE, valE, dstM, valM)


# *****************************
# 更新PC
# *****************************
def UpdatePC(opcode, funct, valP, valA, address, imm, cnd):
    if (opcode == RTYPE and funct == FADD) \
            or opcode in [IADDI, ILW, ISW]:
        return valP
    elif opcode == RTYPE and funct == FJR:
        return valA
    elif opcode in [IJ, IJAL]:
        return valP & 0b11110000000000000000000000000000 | (address << 2)
    elif opcode == IBNE:
        if imm > (1 << 15):
            imm -= (1 << 16)
        return valP + (imm << 2) if cnd else valP
    else:
        raise MyError("invalid operation in UpdatePC")


# *****************************
# 定义处理器运行过程
# *****************************
def run(PC, imem, dmem, regFile, CC):
    try:
        while(PC < len(program) * 4):
            valP, opcode, rs, rt, rd, shamt, funct, imm, address = Fetch(imem, PC)
            valA, valB = Decode(opcode, funct, regFile, rs, rt)
            valE, cnd = Execute(opcode, funct, valA, valB, valP, imm, CC)
            valM = AccessMemory(opcode, funct, dmem, valE, valB)
            WriteBack(opcode, funct, regFile, rt, rd, valE, valM)
            PC = UpdatePC(opcode, funct, valP, valA, address, imm, cnd)
            # print("==================================================")
            print(f"PC:{PC}")
            # dmem.emit()
            # regFile.emit()
    except Exception as e:
        print(f"PC:{PC}")
        print(e)
        dmem.emit()
        regFile.emit()


# 初始化寄存器和内存
PC = 0
CC = ConditionCode()
regFile = RegFile()
imem = IMemory(16)
dmem = DMemory(16)

# 加载指令和数据
program = [
    0b00100000000001000000000000001100,  # addi $4, $0, 12
    0b00001100000000000000000000000100,  # jal 16

    0b00001000000000000000000000000011,  # j 12

    0b00000000100000000000000000001000,  # jr $4

    0b10001100000000010000000000000000,  # lw $1, 0($0)
    0b10001100000000100000000000000100,  # lw $2, 4($0)
    0b00000000001000100000100000100000,  # add $1, $1, $2
    0b10101100000000010000000000000000,  # sw $1, 0($0)
    0b00010100001001001111111111111011   # bne $1, $4, -20
]
data = [3, 3, 4, 90]
imem.loadProgram(program)
dmem.loadData(data)

# 运行程序
run(PC, imem, dmem, regFile, CC)

# 输出内存
dmem.emit()
regFile.emit()