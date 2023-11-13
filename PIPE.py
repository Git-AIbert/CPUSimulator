import array

# 操作码定义
RTYPE = 0b000000
IADDI = 0b001000
ILW = 0b100011
ISW = 0b101011
IBNE = 0b000101
IBEQ = 0b000100
IBGT = 0b001101  # 以下四个均不是MIPS中的编码规则
IBGE = 0b001100  #
IBLT = 0b000111  #
IBLE = 0b000110  #
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

# 定义寄存器
zero = 0  # 对zero写 等于 没有写操作
at = 1
v1 = 2
v2 = 3
a0 = 4
a1 = 5
a2 = 6
a3 = 7
t0 = 8
t1 = 9
t2 = 10
t3 = 11
t4 = 12
t5 = 13
t6 = 14
t7 = 15
s0 = 16
s1 = 17
s2 = 18
s3 = 19
s4 = 20
s5 = 21
s6 = 22
s7 = 23
t8 = 24
t9 = 25
k0 = 26
k1 = 27
gp = 28
sp = 29
s8 = fp = 30
ra = 31

ITYPE = [IADDI, ILW, ISW, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]
JTYPE = [IJ, IJAL]


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

        return IR


# 不是译码阶段
def decode(IR):
    opcode = IR >> 26
    rs = (IR & 0b00000011111000000000000000000000) >> 21
    rt = (IR & 0b00000000000111110000000000000000) >> 16
    rd = (IR & 0b00000000000000001111100000000000) >> 11
    shamt = (IR & 0b00000000000000000000011111000000) >> 6
    funct = (IR & 0b00000000000000000000000000111111)
    imm = (IR & 0b00000000000000001111111111111111)
    address = (IR & 0b00000011111111111111111111111111)

    if opcode == RTYPE:
        imm = address = None
        if funct == FADD:
            shamt = None
        elif funct == FJR:
            rt = rd = shamt = None
        elif funct == FSLL:
            rs = None
        elif funct == FSYS:
            rs = rt = rd = shamt = None
    elif opcode in ITYPE:
        rd = shamt = funct = address = None
    elif opcode in JTYPE:
        rs = rt = rd = shamt = funct = imm = None
    return opcode, rs, rt, rd, shamt, funct, imm, address


def i2u(val):
    if val < 0:  # 负数
        val = val + (1 << 32)
    elif val >= (1 << 32):  # 溢出
        val = val - (1 << 32)
    return val


def u2i(val):
    if val >= (1 << 31):  # 负数
        val = val - (1 << 32)
    return val

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
        if not read and not write:
            return

        if address >= len(self.mem) * 4:
            raise MyError(f"dmem_error: address({address}) out of length of dmem({len(self.mem) * 4})")

        addr_mod4 = address % 4
        if addr_mod4 != 0:
            raise MyError(f"dmem_error: address({address}) is not a multiple of four")

        addr_div4 = address // 4
        if read:
            return u2i(self.mem[addr_div4])
        if write:
            self.mem[addr_div4] = i2u(data)
            return data

    def emit(self, length):
        if length > len(self.mem):
            length = len(self.mem)
        print("\nDMemory:")
        for i in range(length):
            print(f"0x{format(i * 4, '08x')}: {u2i(self.mem[i])}")
        print("")


class RegFile:
    # 构造函数
    def __init__(self):
        self.reg = array.array('I', [0] * 32)

    def read(self, srcA, srcB):
        valA = valB = None
        if srcA is not None:
            valA = u2i(self.reg[srcA])
        if srcB is not None:
            valB = u2i(self.reg[srcB])
        return valA, valB

    def write(self, dstE, valE, dstM, valM):
        if dstE is not None:
            self.reg[dstE] = i2u(valE)
        if dstM is not None:
            self.reg[dstM] = i2u(valM)

    def emit(self):
        print("\nRegisters:")
        for i in range(len(self.reg)//8):
            i = i*8
            print(f"R{i}:{u2i(self.reg[i])}\tR{i+1}:{u2i(self.reg[i+1])}\t"
                  f"R{i+2}:{u2i(self.reg[i+2])}\tR{i+3}:{u2i(self.reg[i+3])}\t"
                  f"R{i+4}:{u2i(self.reg[i+4])}\tR{i+5}:{u2i(self.reg[i+5])}\t"
                  f"R{i+6}:{u2i(self.reg[i+6])}\tR{i+7}:{u2i(self.reg[i+7])}")
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


def SelectPC(D_IR, d_valA, d_cnd, d_bAddr, D_NPC, f_IR, f_NPC):
    D_opcode, _, _, _, _, D_funct, _, _ = decode(D_IR)
    if D_opcode == RTYPE and D_funct == FJR:
        return d_valA
    elif D_opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return d_bAddr if d_cnd else D_NPC  # d_valA是D_NPC
    elif (D_opcode == RTYPE and D_funct in [FADD, FSLL, FSYS]) \
            or D_opcode in [IADDI, ILW, ISW, IJ, IJAL]:
        f_opcode, _, _, _, _, f_funct, _, address = decode(f_IR)
        if (f_opcode == RTYPE and f_funct == FADD) \
                or f_opcode in [IADDI, ILW, ISW]:
            return f_NPC
        elif f_opcode in [IJ, IJAL]:
            return f_NPC & 0b11110000000000000000000000000000 | (address << 2)
        # 当无法预测下一个PC的时候，应该如何选择
        elif f_opcode == RTYPE and f_funct in [FJR, FSLL, FSYS] \
                or f_opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
            return f_NPC - 4
        else:
            raise MyError("invalid operation in SelectPC:f_IR")
    else:
        raise MyError("invalid operation in SelectPC:D_IR")


# 取指过程
def Fetch(mem, PC, D_IR, d_valA, d_cnd, d_bAddr, D_NPC):
    f_IR = mem.access(PC)
    f_NPC = PC + 4
    f_PC = SelectPC(D_IR, d_valA, d_cnd, d_bAddr, D_NPC, f_IR, f_NPC)
    return f_IR, f_NPC, f_PC


# *****************************
# 译码阶段
# *****************************
def SrcA(opcode, funct, rs):
    if (opcode == RTYPE and funct in [FADD, FJR]) \
            or opcode in [ILW, ISW, IADDI, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return rs
    elif (opcode == RTYPE and funct in [FSLL, FSYS]) \
            or opcode in [IJ, IJAL]:
        return None
    else:
        raise MyError("invalid operation in Decode")


def SrcB(opcode, funct, rt):
    if (opcode == RTYPE and funct == FADD) \
            or opcode in [ISW, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return rt
    elif (opcode == RTYPE and funct in [FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ILW, IJ, IJAL]:
        return None
    else:
        raise MyError("invalid operation in Decode")


# 寄存器dstE控制
def DstE(opcode, funct, rt, rd):
    if opcode == RTYPE and funct == FADD:
        return rd
    elif opcode == IADDI:
        return rt
    elif opcode == IJAL:
        return ra
    elif (opcode == RTYPE and funct in [FJR, FSLL, FSYS]) \
            or opcode in [ILW, ISW, IJ, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return None
    else:
        raise MyError("invalid operation in Decode")


# 寄存器dstM控制
def DstM(opcode, funct, rt, rd):
    if opcode == ILW:
        return rt
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ISW, IJ, IJAL, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return None
    else:
        raise MyError("invalid operation in Decode")


def SignExtend(imm):
    if imm is None:
        return None
    if imm > (1 << 15):
        imm -= (1 << 16)
    return imm


def FwdA(valA, d_srcA, e_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE):
    if d_srcA is not None:
        # 从执行阶段进行转发
        if d_srcA == e_dstE:
            return e_valE
        # 从访存阶段进行转发
        if d_srcA == M_dstM:
            return m_valM
        if d_srcA == M_dstE:
            return M_valE
        # 从写回阶段进行转发
        if d_srcA == W_dstM:
            return W_valM
        if d_srcA == W_dstE:
            return W_valE
    return valA


# 转发B
def FwdB(valB, d_srcB, e_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE):
    if d_srcB is not None:
        # 从执行阶段进行转发
        if d_srcB == e_dstE:
            return e_valE
        # 从访存阶段进行转发
        if d_srcB == M_dstM:
            return m_valM
        if d_srcB == M_dstE:
            return M_valE
        # 从写回阶段进行转发
        if d_srcB == W_dstM:
            return W_valM
        if d_srcB == W_dstE:
            return W_valE
    return valB


def Comp(opcode, funct, valA, valB):
    ZF = SF = OF = False
    if opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        result = valA - valB
        # 溢出
        if result > (1 << 31) - 1 or result < -(1 << 31):
            OF = True
        # 零
        if result == 0:
            ZF = True
        # 负数
        if result < 0:
            SF = True
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [ILW, ISW, IADDI, IJ, IJAL]:
        pass
    else:
        raise MyError("invalid operation in Decode")
    return ZF, SF, OF


# 分支信号
def Cond(opcode, funct, ZF, SF, OF):
    if opcode == IBNE:
        return not ZF
    elif opcode == IBEQ:
        return ZF
    elif opcode == IBGT:
        return not (SF ^ OF) and not ZF
    elif opcode == IBGE:
        return not (SF ^ OF)
    elif opcode == IBLT:
        return SF ^ OF
    elif opcode == IBLE:
        return (SF ^ OF) or ZF
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ILW, ISW, IJ, IJAL]:
        return False
    else:
        raise MyError("invalid operation in Decode")


def Add(opcode, NPC, sImm):
    bAddr = None
    if opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        bAddr = NPC + (sImm << 2)
    return bAddr


def SelA(IR, valA, NPC):
    opcode, _, _, _, _, funct, _, _ = decode(IR)
    if (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ILW, ISW, IJ, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return valA
    elif opcode == IJAL:
        return NPC
    # elif (opcode == RTYPE and funct in [FSLL, FSYS]) \
    #         or opcode in [IJ, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
    #     return None
    else:
        raise MyError("invalid operation in Decode")


def Decode(IR, regFile, NPC, E_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE):
    opcode, rs, rt, rd, _, funct, imm, _ = decode(IR)
    # 寄存器控制
    d_srcA = SrcA(opcode, funct, rs)
    d_srcB = SrcB(opcode, funct, rt)
    d_dstE = DstE(opcode, funct, rt, rd)
    d_dstM = DstM(opcode, funct, rt, rd)
    # 寄存器读
    valA, valB = regFile.read(d_srcA, d_srcB)
    # 有符号扩展
    sImm = SignExtend(imm)
    # 转发A和B
    valA = FwdA(valA, d_srcA, E_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE)
    d_valB = FwdB(valB, d_srcB, E_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE)
    # 对转发后的valA和valB进行比较
    ZF, SF, OF = Comp(opcode, funct, valA, d_valB)
    # 判断是否跳转
    cnd = Cond(opcode, funct, ZF, SF, OF)
    # 计算分支跳转地址
    bAddr = Add(opcode, NPC, sImm)
    # 选择A
    d_valA = SelA(IR, valA, NPC)
    return d_valA, d_valB, sImm, cnd, bAddr, d_srcA, d_srcB, d_dstE, d_dstM


# *****************************
# 执行阶段
# *****************************
def ALU_A(opcode, funct, valA):
    if (opcode == RTYPE and funct in [FADD]) \
            or opcode in [IADDI, ILW, ISW, IJAL]:
        return valA
    elif opcode == RTYPE and funct in [FJR, FSLL, FSYS] \
            or opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE, IJ]:
        return None
    else:
        raise MyError("invalid operation in Execute")


def ALU_B(opcode, funct, valB, imm):
    if (opcode == RTYPE and funct == FADD):
        return valB
    elif opcode in [IADDI, ILW, ISW]:
        return imm
    elif opcode == IJAL:
        return 0
    elif (opcode == RTYPE and funct in [FJR, FSLL, FSYS]) \
            or opcode in [IJ, IBNE, IBGT, IBGE, IBLT, IBLE, IBEQ]:
        return None
    else:
        raise MyError("invalid operation in Execute")


def ALU_fun(opcode, funct):
    if (opcode == RTYPE and funct == FADD) \
            or opcode in [IADDI, ILW, ISW, IJAL]:
        return ALUADD
    elif (opcode == RTYPE and funct in [FJR, FSLL, FSYS]) \
            or opcode in [IJ, IBNE, IBGT, IBGE, IBLT, IBLE, IBEQ]:
        return ALUNOP
    else:
        raise MyError("invalid operation in Execute")


# 定义算数逻辑单元，计算结果为补码（其表示为无符号数）
def ALU(aluA, aluB, aluFun):
    if aluFun == ALUADD:
        return aluA + aluB
    elif aluFun == ALUSUB:
        return aluA - aluB
    elif aluFun == ALUNOP:
        return None


def Execute(IR, valA, valB, sImm):
    opcode, _, _, _, _, funct, _, _ = decode(IR)
    # ALU控制
    aluA = ALU_A(opcode, funct, valA)
    aluB = ALU_B(opcode, funct, valB, sImm)
    aluFun = ALU_fun(opcode, funct)
    # ALU计算
    valE = ALU(aluA, aluB, aluFun)
    return valE


# *****************************
# 访存阶段
# *****************************
# 内存读控制
def MReadControl(opcode, funct):
    if opcode == ILW:
        return True
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ISW, IJ, IJAL, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return False
    else:
        raise MyError("invalid operation in AccessMemory")


# 内存写控制
def MWriteControl(opcode, funct):
    if opcode == ISW:
        return True
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ILW, IJ, IJAL, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return False
    else:
        raise MyError("invalid operation in AccessMemory")


def MemAddr(opcode, funct, valE):
    if opcode in [ILW, ISW]:
        return valE
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, IJ, IJAL, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return None
    else:
        raise MyError("invalid operation in AccessMemory")


def MemData(opcode, funct, valB):
    if opcode == ISW:
        return valB
    elif (opcode == RTYPE and funct in [FADD, FJR, FSLL, FSYS]) \
            or opcode in [IADDI, ILW, IJ, IJAL, IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]:
        return None
    else:
        raise MyError("invalid operation in AccessMemory")


def AccessMemory(IR, mem, valE, valB):
    opcode, _, _, _, _, funct, _, _ = decode(IR)
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
def WriteBack(regFile, valE, valM, dstE, dstM):
    # 寄存器写
    regFile.write(dstE, valE, dstM, valM)


# *****************************
# 流水线控制逻辑
# *****************************
def FetchControl(E_IR, E_dstM, d_srcA, d_srcB):
    F_stall = False
    E_opcode, _, _, _, _, E_funct, _, _ = decode(E_IR)
    if E_opcode == ILW and E_dstM in [d_srcA, d_srcB]:
        F_stall = True

    F_bubble = False

    if F_stall and F_bubble:
        raise MyError("Control Condition Error in FetchControl")

    return F_stall, F_bubble


def DecodeControl(D_IR, E_IR, E_dstM, d_srcA, d_srcB):
    D_stall = False
    E_opcode, _, _, _, _, _, _, _ = decode(E_IR)
    if E_opcode == ILW and E_dstM in [d_srcA, d_srcB]:
        D_stall = True

    D_bubble = False
    D_opcode, _, _, _, _, D_funct, _, _ = decode(D_IR)
    if ((D_opcode == RTYPE and D_funct == FJR) or D_opcode in [IBNE, IBEQ, IBGT, IBGE, IBLT, IBLE]) \
            and not (E_opcode == ILW and E_dstM in [d_srcA, d_srcB]):
        D_bubble = True

    if D_stall and D_bubble:
        raise MyError("Control Condition Error in DecodeControl")

    return D_stall, D_bubble


def ExcuteControl(E_IR, E_dstM, d_srcA, d_srcB):
    E_stall = False

    E_bubble = False
    E_opcode, _, _, _, _, E_funct, _, _ = decode(E_IR)
    if E_opcode == ILW and E_dstM in [d_srcA, d_srcB]:
        E_bubble = True

    if E_stall and E_bubble:
        raise MyError("Control Condition Error in DecodeControl")

    return E_stall, E_bubble


def AccessMemoryControl(M_IR, W_IR):
    M_stall = False

    M_bubble = False
    M_opcode, _, _, _, _, M_funct, _, _ = decode(M_IR)
    if M_opcode == RTYPE and M_funct == FSYS:
        M_stall = True
    W_opcode, _, _, _, _, W_funct, _, _ = decode(W_IR)
    if W_opcode == RTYPE and W_funct == FSYS:
        M_stall = True

    if M_stall and M_bubble:
        raise MyError("Control Condition Error in AccessMemoryControl")

    return False, False


def WriteBackControl(W_IR):
    W_stall = False
    W_opcode, _, _, _, _, W_funct, _, _ = decode(W_IR)
    if W_opcode == RTYPE and W_funct == FSYS:
        W_stall = True

    W_bubble = False

    if W_stall and W_bubble:
        raise MyError("Control Condition Error in WriteBackControl")

    return W_stall, W_bubble


# 打印流水线寄存器的值
def printPipelineRegisters(clock,W_PC, W_valE, W_valM, W_dstE, W_dstM,
                           M_PC, M_valE, M_valB, M_dstE, M_dstM,
                           E_PC, E_valA, E_valB, E_sImm, E_dstE, E_dstM,
                           D_PC, D_NPC, F_PC):
    print("=" * 60)
    print(f"clock:{clock}")
    # IR:{format(W_IR, '032b')}\t
    # IR:{format(M_IR, '032b')}\t
    # IR:{format(E_IR, '032b')}\t
    # IR:{format(D_IR, '032b')}\t
    print(f"W:[PC:{W_PC}\tW_dstE:{W_dstE}\tW_dstM:{W_dstM}\tW_valE:{W_valE}\tW_valM:{W_valM}]")
    print(f"M:[PC:{M_PC}\tM_dstE:{M_dstE}\tM_dstM:{M_dstM}\tM_valE:{M_valE}\tM_valB:{M_valB}]")
    print(f"E:[PC:{E_PC}\tE_dstE:{E_dstE}\tE_dstM:{E_dstM}\tE_valA:{E_valA}\tE_valB:{E_valB}\tE_sImm:{E_sImm}]")
    print(f"D:[PC:{D_PC}\tD_NPC:{D_NPC}]")
    print(f"F:[PC:{F_PC}]")


# *****************************
# 定义处理器运行过程
# *****************************
def run(PC, imem, dmem, regFile):
    clock = 0
    # 流水线寄存器
    W_IR = 0
    W_PC = W_valE = W_valM = W_dstE = W_dstM = None
    M_IR = 0
    M_PC = M_valE = M_valB = M_dstE = M_dstM = None
    E_IR = 0
    E_PC = E_valA = E_valB = E_sImm = E_dstE = E_dstM = None
    D_IR = 0
    D_PC = D_NPC = None
    F_PC = PC
    clock = clock + 1
    printPipelineRegisters(clock, W_PC, W_valE, W_valM, W_dstE, W_dstM,
                           M_PC, M_valE, M_valB, M_dstE, M_dstM,
                           E_PC, E_valA, E_valB, E_sImm, E_dstE, E_dstM,
                           D_PC, D_NPC, F_PC)
    # try:
    while W_IR != FSYS and clock < 10000:
        # ============================================================
        # 时钟低电平
        WriteBack(regFile, W_valE, W_valM, W_dstE, W_dstM)
        m_valM = AccessMemory(M_IR, dmem, M_valE, M_valB)
        e_valE = Execute(E_IR, E_valA, E_valB, E_sImm)
        d_valA, d_valB, d_sImm, d_cnd, d_bAddr, d_srcA, d_srcB, d_dstE, d_dstM = \
            Decode(D_IR, regFile, D_NPC, E_dstE, e_valE, M_dstM, m_valM, M_dstE, M_valE, W_dstM, W_valM, W_dstE, W_valE)
        f_IR, f_NPC, f_PC = Fetch(imem, F_PC, D_IR, d_valA, d_cnd, d_bAddr, D_NPC)
        # ============================================================
        # 时钟高电平
        # 确定控制信号
        W_stall, W_bubble = WriteBackControl(W_IR)
        M_stall, M_bubble = AccessMemoryControl(M_IR, W_IR)
        E_stall, E_bubble = ExcuteControl(E_IR, E_dstM, d_srcA, d_srcB)
        D_stall, D_bubble = DecodeControl(D_IR, E_IR, E_dstM, d_srcA, d_srcB)
        F_stall, F_bubble = FetchControl(E_IR, E_dstM, d_srcA, d_srcB)
        # 更新写回寄存器
        if W_bubble:
            W_IR = 0
            W_PC = W_valE = W_valM = W_dstE = W_dstM = None
        elif not W_stall:
            W_IR = M_IR
            W_PC = M_PC
            W_valE = M_valE
            W_valM = m_valM
            W_dstE = M_dstE
            W_dstM = M_dstM
        # 更新访存寄存器
        if M_bubble:
            M_IR = 0
            M_PC = M_valE = M_valB = M_dstE = M_dstM = None
        elif not M_stall:
            M_IR = E_IR
            M_PC = E_PC
            M_valE = e_valE
            M_valB = E_valB
            M_dstE = E_dstE
            M_dstM = E_dstM
        # 更新执行寄存器
        if E_bubble:
            E_IR = 0
            E_PC = E_valA = E_valB = E_sImm = E_dstE = E_dstM = None
        elif not E_stall:
            E_IR = D_IR
            E_PC = D_PC
            E_valA = d_valA
            E_valB = d_valB
            E_sImm = d_sImm
            E_dstE = d_dstE
            E_dstM = d_dstM
        # 更新译码寄存器
        if D_bubble:
            D_IR = 0
            D_PC = D_NPC = None
        elif not D_stall:
            D_IR = f_IR
            D_PC = F_PC
            D_NPC = f_NPC
        # 更新取指寄存器
        if F_bubble:
            F_PC = None
        elif not F_stall:
            F_PC = f_PC
        clock = clock + 1
        printPipelineRegisters(clock, W_PC, W_valE, W_valM, W_dstE, W_dstM,
                               M_PC, M_valE, M_valB, M_dstE, M_dstM,
                               E_PC, E_valA, E_valB, E_sImm, E_dstE, E_dstM,
                               D_PC, D_NPC, F_PC)
    print(f"\nTotal Clock:{clock}")
    # except Exception as e:
    #     print(f"F_PC:{F_PC}")
    #     print(e)
    #     dmem.emit()
    #     regFile.emit()


# 初始化寄存器和内存
PC = 0
CC = ConditionCode()
regFile = RegFile()
imem = IMemory(256)
dmem = DMemory(1024)

# 加载指令和数据
program_test = [
    0b00100000000001000000000000001100,  # 0    addi $4, $0, 12
    0b00001100000000000000000000000100,  # 4    jal 16
    0b00001000000000000000000000000011,  # 8    j 12
    0b00000000100000000000000000001000,  # 12   jr $4
    0b10001100000000010000000000000000,  # 16   lw $1, 0($0)
    0b10001100000000100000000000000100,  # 20   lw $2, 4($0)
    0b00000000001000100000100000100000,  # 24   add $1, $1, $2
    0b10101100000000010000000000000000,  # 28   sw $1, 0($0)
    0b00011100001001001111111111111011,  # 32   blt $1, $4, -20
    0b00000000000000000000000000001100   # 36   syscall 目前作为halt指令
]
program_loop = [
    0b00100000000000010000001111100111,  # addi $1, $0, 999
    0b00100000000000100000000000000101,  # addi $2, $0, 1
    0b00011100001000000000000000000111,  # blt $1, $0, 28
    0b00100000000001000000111110011100,  # addi $4, $0, 3996
    0b00000000011001000010000000100000,  # add $4, $3, $4

    0b10001100100001010000000000000000,  # lw $5, 0($4)
    0b00000000101000100010100000100000,  # add $5, $5, $2
    0b10101100100001010000000000000000,  # sw $5, 0($4)
    0b00100000100001001111111111111100,  # addi $4, $4, -4
    0b00110000100000111111111111111011,  # bge $4, $3, -20
    0b00000000000000000000000000001100,  # syscall
]
program_unrolling4 = [
    0b00100000000000100000000000000101,  # addi $2, $0, 5
    0b00100000000001000000111110011100,  # addi $4, $0, 3996
    0b00000000011001000010000000100000,  # add $4, $3, $4

    0b10001100100001010000000000000000,  # lw $5, 0($4)
    0b10001100100001101111111111111100,  # lw $6, -4($4)
    0b10001100100001111111111111111000,  # lw $7, -8($4)
    0b10001100100010001111111111110100,  # lw $8, -12($4)
    0b00000000101000100010100000100000,  # add $5, $5, $2
    0b00000000110000100011000000100000,  # add $6, $6, $2
    0b00000000111000100011100000100000,  # add $7, $7, $2
    0b00000001000000100100000000100000,  # add $8, $8, $2
    0b10101100100001010000000000000000,  # sw $5, 0($4)
    0b10101100100001101111111111111100,  # sw $6, -4($4)
    0b10101100100001111111111111111000,  # sw $7, -8($4)
    0b10101100100010001111111111110100,  # sw $8, -12($4)
    0b00100000100001001111111111110000,  # addi $4, $4, -16
    0b00110000100000111111111111110010,  # bge $4, $3, -56
    0b00000000000000000000000000001100,  # syscall
]
program_unrolling10 = [
    0b00100000000000100000000000000101,  # addi $2, $0, 5
    0b00100000000001000000111110011100,  # addi $4, $0, 3996
    0b00000000011001000010000000100000,  # add $4, $3, $4

    0b10001100100001010000000000000000,  # lw $5, 0($4)
    0b10001100100001101111111111111100,  # lw $6, -4($4)
    0b10001100100001111111111111111000,  # lw $7, -8($4)
    0b10001100100010001111111111110100,  # lw $8, -12($4)
    0b10001100100010011111111111110000,  # lw $9, -16($4)
    0b10001100100010101111111111101100,  # lw $10, -20($4)
    0b10001100100010111111111111101000,  # lw $11, -24($4)
    0b10001100100011001111111111100100,  # lw $12, -28($4)
    0b10001100100011011111111111100000,  # lw $13, -32($4)
    0b10001100100011101111111111011100,  # lw $14, -36($4)
    0b00000000101000100010100000100000,  # add $5, $5, $2
    0b00000000110000100011000000100000,  # add $6, $6, $2
    0b00000000111000100011100000100000,  # add $7, $7, $2
    0b00000001000000100100000000100000,  # add $8, $8, $2
    0b00000001001000100100100000100000,  # add $9, $9, $2
    0b00000001010000100101000000100000,  # add $10, $10, $2
    0b00000001011000100101100000100000,  # add $11, $11, $2
    0b00000001100000100110000000100000,  # add $12, $12, $2
    0b00000001101000100110100000100000,  # add $13, $13, $2
    0b00000001110000100111000000100000,  # add $14, $14, $2
    0b10101100100001010000000000000000,  # sw $5, 0($4)
    0b10101100100001101111111111111100,  # sw $6, -4($4)
    0b10101100100001111111111111111000,  # sw $7, -8($4)
    0b10101100100010001111111111110100,  # sw $8, -12($4)
    0b10101100100010011111111111110000,  # sw $9, -16($4)
    0b10101100100010101111111111101100,  # sw $10, -20($4)
    0b10101100100010111111111111101000,  # sw $11, -24($4)
    0b10101100100011001111111111100100,  # sw $12, -28($4)
    0b10101100100011011111111111100000,  # sw $13, -32($4)
    0b10101100100011101111111111011100,  # sw $14, -36($4)
    0b00100000100001001111111111011000,  # addi $4, $4, -40
    0b00110000100000111111111111100000,  # bge $4, $3, -128
    0b00000000000000000000000000001100,  # syscall
]
imem.loadProgram(program_unrolling10)
# data = [3, 3, 4, 90]
# dmem.loadData(data)

# 运行程序
run(PC, imem, dmem, regFile)

# 输出内存和寄存器
dmem.emit(32)
regFile.emit()
