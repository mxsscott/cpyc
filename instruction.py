import time
import pprint
import alu
from flags import Flags

opt = dict((i,0) for i in range(0, 256))


def _setb(cpu, value):
    cpu.b = value

def _setc(cpu, value):
    cpu.c = value

def _setd(cpu, value):
    cpu.d = value

def _sete(cpu, value):
    cpu.e = value

def _seth(cpu, value):
    cpu.h = value

def _setl(cpu, value):
    cpu.l = value

def _sethl(cpu, value):
    cpu.mem[cpu.h << 8 | cpu.l] = value

def _seta(cpu, value):
    cpu.a = value

REGISTER = ['B','C','D','E','H','L','(HL)','A']
REGSET = [_setb, _setc, _setd, _sete, _seth, _setl, _sethl, _seta]
REGGET = [
    lambda x : x.b,
    lambda x : x.c,
    lambda x : x.d,
    lambda x : x.e,
    lambda x : x.h,
    lambda x : x.l,
    lambda x : x.mem[x.h << 8 | x.l],
    lambda x : x.a]

def twos_decode(number):
    if number < 0x80:
        return number
    else:
        return number - 256

def trace(instruction):
    pass
    #print instruction

def _ins_adc(cpu, source):
    #trace("- ADC {:s}".format(REGISTER[source]))
    value = cpu.a + REGGET[source](cpu) + (1 if cpu.f.c else 0)
    cpu.f.s = (value & 0x80) != 00
    cpu.f.z = value == 0
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) != 0x00) and ((value & 0x08) == 0x00)
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (value > 0x7F) and (cpu.a < 0x80)
    cpu.f.n = False
    cpu.f.c = (value & 0x100) != 0x00
    cpu.a = (value & 0xFF)

def _ins_adc_n(cpu, data):
    #trace("- ADC 0x{:02X}".format(data[0]))
    value = cpu.a + data[0] + (1 if cpu.f.c else 0)
    cpu.f.s = (value & 0x80) != 00
    cpu.f.z = value == 0
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) != 0x00) and ((value & 0x08) == 0x00)
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (value > 0x7F) and (cpu.a < 0x80)
    cpu.f.n = False
    cpu.f.c = (value & 0x100) != 0x00
    cpu.a = (value & 0xFF)

def _ins_add(cpu, source):
    #trace("- ADD {:s}".format(REGISTER[source]))
    value = cpu.a + REGGET[source](cpu)
    cpu.f.s = (value & 0x80) != 00
    cpu.f.z = value == 0
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) != 0x00) and ((value & 0x08) == 0x00)
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (value > 0x7F) and (cpu.a < 0x80)
    cpu.f.n = False
    cpu.f.c = (value & 0x100) != 0x00
    cpu.a = (value & 0xFF)

def _ins_add_n(cpu, data):
    #trace("- ADD 0x{:02X}".format(data[0]))
    value = cpu.a + data[0]
    cpu.f.s = (value & 0x80) != 00
    cpu.f.z = value == 0
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) != 0x00) and ((value & 0x08) == 0x00)
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (value > 0x7F) and (cpu.a < 0x80)
    cpu.f.n = False
    cpu.f.c = (value & 0x100) != 0x00
    cpu.a = (value & 0xFF)

def _ins_add_hl_bc(cpu, data):
    #trace("- ADD HL,BC")
    lower = cpu.l + cpu.c
    cpu.l = (lower & 0xFF)
    bytecarry = (lower & 0x100) >> 8
    upper = cpu.h + cpu.b + bytecarry

    cpu.f.h = ((cpu.h & 0x08) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.h = (upper & 0xFF)

def _ins_add_hl_de(cpu, data):
    #trace("- ADD HL,DE")
    lower = cpu.l + cpu.e
    cpu.l = (lower & 0xFF)
    bytecarry = (lower & 0x100) >> 8
    upper = cpu.h + cpu.d + bytecarry

    cpu.f.h = ((cpu.h & 0x08) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.h = (upper & 0xFF)

def _ins_add_hl_hl(cpu, data):
    #trace("- ADD HL,HL")
    lower = cpu.l + cpu.l
    cpu.l = (lower & 0xFF)
    bytecarry = (lower & 0x100) >> 8
    upper = cpu.h + cpu.h + bytecarry

    cpu.f.h = ((cpu.h & 0x08) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.h = (upper & 0xFF)

def _ins_add_ix_bc(cpu, data):
    #trace("- ADD IX,BC")
    lower = (cpu.ix & 0x00FF) + cpu.c
    bytecarry = (lower & 0x100) >> 8
    upper = ((cpu.ix & 0xFF00) >> 8) + cpu.b + bytecarry

    cpu.f.h = ((cpu.ix & 0x0800) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.ix = ((upper << 8) | (lower & 0x00FF)) & 0xFFFF 

def _ins_add_ix_de(cpu, data):
    #trace("- ADD IX,DE")
    lower = (cpu.ix & 0x00FF) + cpu.e
    bytecarry = (lower & 0x100) >> 8
    upper = ((cpu.ix & 0xFF00) >> 8) + cpu.d + bytecarry

    cpu.f.h = ((cpu.ix & 0x0800) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.ix = ((upper << 8) | (lower & 0x00FF)) & 0xFFFF 

def _ins_add_ix_ix(cpu, data):
    #trace("- ADD IX,IX")
    lower = (cpu.ix & 0x00FF) + (cpu.ix & 0x00FF)
    bytecarry = (lower & 0x100) >> 8
    upper = ((cpu.ix & 0xFF00) >> 8) + ((cpu.ix & 0xFF00) >> 8) + bytecarry

    cpu.f.h = ((cpu.ix & 0x0800) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.ix = ((upper << 8) | (lower & 0x00FF)) & 0xFFFF 

def _ins_add_ix_sp(cpu, data):
    #trace("- ADD IX,SP")
    lower = (cpu.ix & 0x00FF) + (cpu.sp & 0xFFFF)
    bytecarry = (lower & 0x100) >> 8
    upper = ((cpu.ix & 0xFF00) >> 8) + ((cpu.sp & 0xFF00) >> 8) + bytecarry

    cpu.f.h = ((cpu.ix & 0x0800) != 0x00) and ((upper & 0x08) == 0x00)
    cpu.f.n = False
    cpu.f.c = (upper & 0x100) != 0x00
    cpu.f.five = (upper & 0x20) != 0x00
    cpu.f.three = (upper & 0x08) != 0x00
    cpu.ix = ((upper << 8) | (lower & 0x00FF)) & 0xFFFF 

def _ins_and(cpu, source):
    #trace("- AND {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    cpu.a = cpu.a & value
    cpu.f.set_SZ513P00(cpu.a)

def _ins_and_n(cpu, data): #
    #trace("- AND 0x{:02X}".format(data[0]))
    cpu.a = cpu.a & data[0]
    cpu.f.set_SZ513P00(cpu.a)

def _ins_call_c(cpu, data):
    #trace("- CALL C,0x{:02X}{:02X}".format(data[1], data[0]))
    if cpu.f.c:
        cpu.sp = (cpu.sp - 2) & 0xffff
        cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
        cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
        cpu.pc = data[1] << 8 | data[0]

def _ins_call_nn(cpu, data):
    #trace("- CALL 0x{:02X}{:02X}".format(data[1], data[0]))
    cpu.sp = sp = (cpu.sp - 2) & 0xffff
    cpu.mem[sp] = (cpu.pc & 0x00ff)
    cpu.mem[sp+1] = (cpu.pc & 0xff00) >> 8
    cpu.pc = data[1] << 8 | data[0]

def _ins_call_m(cpu, data):
    #trace("- CALL NEGATIVE,0x{:02X}{:02X}".format(data[1], data[0]))
    if cpu.f.s:
        cpu.sp = (cpu.sp - 2) & 0xffff
        cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
        cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
        cpu.pc = data[1] << 8 | data[0]

def _ins_call_nc_nn(cpu, data):
    #trace("- CALL NC,0x{:02X}{:02X}".format(data[1], data[0]))
    if not cpu.f.c:
        cpu.sp = (cpu.sp - 2) & 0xffff
        cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
        cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
        cpu.pc = data[1] << 8 | data[0]

def _ins_call_nz(cpu, data):
    #trace("- CALL NZ,0x{:02X}{:02X}".format(data[1], data[0]))
    if not cpu.f.z:
        cpu.sp = (cpu.sp - 2) & 0xffff
        cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
        cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
        cpu.pc = data[1] << 8 | data[0]

def _ins_ccf(cpu, data):
    #trace("- CCF")
    cpu.f.h = cpu.f.c
    cpu.f.c = not cpu.f.c
    cpu.f.n = False
    cpu.f.five = (cpu.a & 0x20) != 0x00
    cpu.f.three = (cpu.a & 0x08) != 0x00

def _ins_cp(cpu, source):
    #trace("- CP {:s}".format(REGISTER[source]))

    operand2 = REGGET[source](cpu)
    old_a = cpu.a
    new_a = (cpu.a - twos_decode(operand2)) & 0xFF
    
    cpu.f.s = (new_a & 0x80) != 0x00
    cpu.f.z = (new_a == 0x00)
    cpu.f.five = (new_a & 0x20) != 0x00
    cpu.f.h = ((old_a & 0x08) == 0x00) and ((new_a & 0x08) != 0x00)
    cpu.f.three = (new_a & 0x08) != 0x00
    cpu.f.pv = old_a > 0x7F and new_a < 0x80
    cpu.f.n = True
    cpu.f.c = old_a < new_a

def _ins_cp_n(cpu, data):
    #trace("- CP 0x{:02X}".format(data[0]))
    old_a = cpu.a
    new_a = (cpu.a - twos_decode(data[0])) & 0xFF
    cpu.f.s = (new_a & 0x80) != 0x00
    cpu.f.z = (new_a == 0x00)
    cpu.f.five = (new_a & 0x20) != 0x00
    cpu.f.h = ((old_a & 0x08) == 0x00) and ((new_a & 0x08) != 0x00)
    cpu.f.three = (new_a & 0x08) != 0x00
    cpu.f.pv = old_a > 0x7F and new_a < 0x80
    cpu.f.n = True
    cpu.f.c = old_a < new_a

def _ins_cpl(cpu, data):
    #trace("- CPL")
    cpu.a = cpu.a ^ 0xFF
    cpu.f.set___c1c_1_(cpu.a)

def _ins_dec(cpu, source):
    #trace("- DEC {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    backup = value
    value = (value - 1) & 0xff
    REGSET[source](cpu, value)
    cpu.f.s = (value & 0x80) != 0x00
    cpu.f.z = (value == 0x00)
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((backup & 0x08) == 0x00) and ((value & 0x08) != 0x00) 
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (value == 0x80)
    cpu.f.n = True
    #cpu.f.c unaffected
    return True

def _ins_dec_bc(cpu, data):
    #trace("- DEC BC")
    cpu.c = (cpu.c - 1) & 0xff
    if cpu.c == 0xff:
        cpu.b = (cpu.b - 1) & 0xff

def _ins_dec_de(cpu, data):
    #trace("- DEC DE")
    cpu.e = (cpu.e - 1) & 0xff
    if cpu.e == 0xff:
        cpu.d = (cpu.d - 1) & 0xff

def _ins_dec_hl(cpu, data):
    #trace("- DEC HL")
    cpu.l = (cpu.l - 1) & 0xff
    if cpu.l == 0xff:
        cpu.h = (cpu.h - 1) & 0xff

def _ins_di(cpu, data):
    #trace("- DI")
    cpu.interrupts = False

def _ins_djnz(cpu, data):
    #trace("- DJNZ 0x{:02X}".format(data[0]))
    cpu.b = (cpu.b - 1) & 0xff
    if cpu.b != 0x00:
        cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_ei(cpu, data):
    #trace("- EI")
    cpu.interrupts = True

def _ins_ex_af_afa(cpu, data):
    #trace("- EX AF,AF'")
    a = cpu.a
    f = cpu.f
    cpu.a = cpu.aa
    cpu.f = cpu.fa
    cpu.aa = a
    cpu.fa = f

def _ins_ex_de_hl(cpu, data):
    #trace("- EX DE,HL")
    h = cpu.h
    l = cpu.l
    cpu.h = cpu.d
    cpu.l = cpu.e
    cpu.d = h
    cpu.e = l

def _ins_ex_sp_hl(cpu, data):
    #trace("- EX (SP), HL")
    l = cpu.mem[cpu.sp]
    h = cpu.mem[cpu.sp+1]
    cpu.mem[cpu.sp] = cpu.l
    cpu.mem[cpu.sp+1] = cpu.h
    cpu.l = l
    cpu.h = h

def _ins_exx(cpu, data):
    #trace("- EXX")
    h = cpu.h
    l = cpu.l
    cpu.h = cpu.ha
    cpu.l = cpu.la
    cpu.ha = h
    cpu.la = l
    d = cpu.d
    e = cpu.e
    cpu.d = cpu.da
    cpu.e = cpu.ea
    cpu.da = d
    cpu.ea = e
    b = cpu.b
    c = cpu.c
    cpu.b = cpu.ba
    cpu.c = cpu.ca
    cpu.ba = b
    cpu.ca = c

def _ins_im1(cpu, data):
    #trace("- IM 1")
    cpu.immode = 1

def _ins_in_a_c(cpu, data):
    """ Input data from port BC to register A """
    #trace("- IN A,(C)")
    cpu.a = cpu.input(cpu.b, cpu.c)
    cpu.f.set_SZ503P0_(cpu.a)

def _ins_in_c_c(cpu, data):
    """ Input data from port BC to register C """
    #trace("- IN C,(C)")
    cpu.c = cpu.input(cpu.b, cpu.c)
    cpu.f.set_SZ503P0_(cpu.c)

def _ins_inc(cpu, source):
    #trace("- INC {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    backup = value
    value = (value + 1) & 0xff
    REGSET[source](cpu, value)

    cpu.f.s = (value & 0x80) != 0x00
    cpu.f.z = (value == 0x00)
    cpu.f.five = (value & 0x20) != 0x00
    cpu.f.h = ((backup & 0x08) != 0x00) and ((value & 0x08) == 0x00) 
    cpu.f.three = (value & 0x08) != 0x00
    cpu.f.pv = (backup == 0x7F)
    cpu.f.n = False
    #cpu.f.c unaffected

def _ins_inc_bc(cpu, data):
    #trace("- INC BC")
    cpu.c = (cpu.c + 1) & 0xff
    if cpu.c == 0x00:
        cpu.b = (cpu.b + 1) & 0xff

def _ins_inc_de(cpu, data):
    #trace("- INC DE")
    cpu.e = (cpu.e + 1) & 0xff
    if cpu.e == 0x00:
        cpu.d = (cpu.d + 1) & 0xff

def _ins_inc_hl(cpu, data):
    #trace("- INC HL")
    cpu.l = (cpu.l + 1) & 0xff
    if cpu.l == 0x00:
        cpu.h = (cpu.h + 1) & 0xff

def _ins_jp_c(cpu, data):
    #trace("- JP C,0x{:02X}{:02X}".format(data[1], data[0]))
    if cpu.f.c:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jp_hl(cpu, data):
    #trace("- JP (HL)")
    cpu.pc = cpu.h << 8 | cpu.l

def _ins_jp_m(cpu, data):
    #trace("- JP NEGATIVE,0x{:02X}{:02X}".format(data[1], data[0]))
    if cpu.f.s:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jp_nc(cpu, data):
    #trace("- JP NC,0x{:02X}{:02X}".format(data[1], data[0]))
    if not cpu.f.c:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jp_nn(cpu, data): #
    #trace("- JP 0x{:02X}{:02X}".format(data[1], data[0]))
    cpu.pc = data[1] << 8 | data[0]

def _ins_jp_nz(cpu, data):
    #trace("- JP NZ,0x{:02X}{:02X}".format(data[1], data[0]))
    if not cpu.f.z:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jp_p_nn(cpu, data):
    #trace("- JP POSITIVE,0x{:02X}{:02X}".format(data[1], data[0]))
    if not cpu.f.s:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jp_z(cpu, data):
    #trace("- JP Z,0x{:02X}{:02X}".format(data[1], data[0]))
    if cpu.f.z:
        cpu.pc = data[1] << 8 | data[0]

def _ins_jr(cpu, data):
    #trace("- JR 0x{:02X}".format(data[0]))
    cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_jr_c(cpu, data):
    #trace("- JR C,0x{:02X}".format(data[0]))
    if cpu.f.c:
        cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_jr_nc(cpu, data):
    #trace("- JR NC,0x{:02X}".format(data[0]))
    if not cpu.f.c:
        cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_jr_nz(cpu, data):
    #trace("- JR NZ,0x{:02X}".format(data[0]))
    if not cpu.f.z:
        cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_jr_z(cpu, data):
    #trace("- JR Z,0x{:02X}".format(data[0]))
    if cpu.f.z:
        cpu.pc = (cpu.pc + twos_decode(data[0])) & 0xffff

def _ins_ld(cpu, destination, source):
    #trace("- LD {:s},{:s}".format(REGISTER[destination], REGISTER[source]))
    REGSET[destination](cpu, REGGET[source](cpu))

def _ins_ld_a_de(cpu, data):
    #trace("- LD A,(DE)")
    addr = cpu.d << 8 | cpu.e
    cpu.a = cpu.mem[addr]

def _ins_ld_a_ix_n(cpu, data):
    #trace("- LD A,(IX+0x{:02X})".format(data[0]))
    addr = (cpu.ix + data[0]) & 0xffff
    cpu.a = cpu.mem[addr]

def _ins_ld_a_iy_n(cpu, data):
    #trace("- LD A,(IY+0x{:02X})".format(data[0]))
    addr = (cpu.iy + data[0]) & 0xffff
    cpu.a = cpu.mem[addr]

def _ins_ld_a_n(cpu, data):
    #trace("- LD A,0x{:02X}".format(data[0]))
    cpu.a = data[0]

def _ins_ld_a_nn(cpu, data):
    #trace("- LD A,(0x{:02X}{:02X})".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.a = cpu.mem[addr]

def _ins_ld_b_n(cpu, data):
    #trace("- LD B,0x{:02X}".format(data[0]))
    cpu.b = data[0]

def _ins_ld_bc_cnn(cpu, data):
    #trace("- LD BC,(0x{:02X}{:02X})".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.c = cpu.mem[addr]
    addr = (addr+1) & 0xffff
    cpu.b = cpu.mem[addr]

def _ins_ld_bc_nn(cpu, data):
    #trace("- LD BC,0x{:02X}{:02X}".format(data[1],data[0]))
    cpu.c = data[0]
    cpu.b = data[1]

def _ins_ld_c_n(cpu, data):
    #trace("- LD C,0x{:02X}".format(data[0]))
    cpu.c = data[0]

def _ins_ld_d_n(cpu, data):
    #trace("- LD D,0x{:02X}".format(data[0]))
    cpu.d = data[0]

def _ins_ld_de_a(cpu, data):
    #trace("- LD (DE),A")
    addr = cpu.d << 8 | cpu.e
    cpu.mem[addr] = cpu.a

def _ins_ld_de_nn(cpu, data):
    #trace("- LD DE,0x{:02X}{:02X}".format(data[1],data[0]))
    cpu.e = data[0]
    cpu.d = data[1]

def _ins_ld_de_cnn(cpu, data):
    #trace("- LD DE,(0x{:02X}{:02X})".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.e = cpu.mem[addr]
    addr = (addr+1) & 0xffff
    cpu.d = cpu.mem[addr]

def _ins_ld_e_n(cpu, data):
    #trace("- LD E,0x{:02X}".format(data[0]))
    cpu.e = data[0]

def _ins_ld_hl_n(cpu, data):
    #trace("- LD (HL),0x{:02X}".format(data[0]))
    addr = cpu.h << 8 | cpu.l
    cpu.mem[addr] = data[0]

def _ins_ld_hl_cnn(cpu, data):
    #trace("- LD HL,(0x{:02X}{:02X})".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.l = cpu.mem[addr]
    cpu.h = cpu.mem[(addr+1)&0xffff]

def _ins_ld_hl_nn(cpu, data): #
    #trace("- LD HL,0x{:02X}{:02X}".format(data[1],data[0]))
    cpu.l = data[0]
    cpu.h = data[1]

def _ins_ld_ix_nn(cpu, data): #
    #trace("- LD IX,0x{:02X}{:02X}".format(data[1],data[0]))
    cpu.ix = (data[1] << 8) | data[0]

def _ins_ld_ix_n_n(cpu, data):
    #trace("- LD (IX+0x{:02X}), 0x{:02X}".format(data[0], data[1]))
    addr = (cpu.ix + data[0]) & 0xFFFF
    cpu.mem[addr] = data[1]

def _ins_ld_iy_n_n(cpu, data):
    #trace("- LD (IY+0x{:02X}), 0x{:02X}".format(data[0], data[1]))
    addr = (cpu.iy + data[0]) & 0xFFFF
    cpu.mem[addr] = data[1]

def _ins_ld_l_n(cpu, data):
    #trace("- LD L,0x{:02X}".format(data[0]))
    cpu.l = data[0]

def _ins_ld_nn_a(cpu, data):
    #trace("- LD (0x{:02X}{:02X}),A".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.mem[addr] = cpu.a

def _ins_ld_nn_de(cpu, data):
    #trace("- LD (0x{:02X}{:02X}),DE".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.mem[addr] = cpu.e
    addr = (addr+1) & 0xffff
    cpu.mem[addr] = cpu.d

def _ins_ld_nn_hl(cpu, data):
    #trace("- LD (0x{:02X}{:02X}),HL".format(data[1],data[0]))
    addr = data[1] << 8 | data[0]
    cpu.mem[addr] = cpu.l
    addr = (addr+1) & 0xffff
    cpu.mem[addr] = cpu.h

def _ins_ld_sp_nn(cpu, data):
    #trace("- LD SP,0x{:02X}{:02X}".format(data[1],data[0]))
    cpu.sp = data[1] << 8 | data[0]

def _ins_ldi(cpu, data):
    #trace("- LDI")
    addr_hl = cpu.h << 8 | cpu.l
    addr_de = cpu.d << 8 | cpu.e
    value = cpu.mem[addr_de] = cpu.mem[addr_hl]
    cpu.l = (cpu.l + 1) & 0xff
    if cpu.l == 0x00:
        cpu.h = (cpu.h + 1) & 0xff
    cpu.e = (cpu.e + 1) & 0xff
    if cpu.e == 0x00:
        cpu.d = (cpu.d + 1) & 0xff
    cpu.c = (cpu.c - 1) & 0xff
    if cpu.c == 0xff:
        cpu.b = (cpu.b - 1) & 0xff
    cpu.r = (cpu.r + 2) & 0xff
    if cpu.b == 0 and cpu.c == 0:
        cpu.f.pv = False
    else:
        cpu.f.pv = True
    cpu.f.h = False
    cpu.f.five = ((value+cpu.a) & 0x02) != 0x00
    cpu.f.three = ((value+cpu.a) & 0x08) != 0x00
    cpu.f.n = False

def _ins_ldir(cpu, data):
    #trace("- LDIR")
    while True:
        addr_hl = cpu.h << 8 | cpu.l
        addr_de = cpu.d << 8 | cpu.e
        value = cpu.mem[addr_de] = cpu.mem[addr_hl]
        cpu.l = (cpu.l + 1) & 0xff
        if cpu.l == 0x00:
            cpu.h = (cpu.h + 1) & 0xff
        cpu.e = (cpu.e + 1) & 0xff
        if cpu.e == 0x00:
            cpu.d = (cpu.d + 1) & 0xff
        cpu.c = (cpu.c - 1) & 0xff
        if cpu.c == 0xff:
            cpu.b = (cpu.b - 1) & 0xff
        cpu.r = (cpu.r + 2) & 0xff
        if cpu.b == 0 and cpu.c == 0:
            break
    cpu.f.h = False
    cpu.f.five = ((value+cpu.a) & 0x02) != 0x00
    cpu.f.three = ((value+cpu.a) & 0x08) != 0x00
    cpu.f.pv = False
    cpu.f.n = False

def _ins_nop(cpu, data):
    #trace("NOP")
    return True

def _ins_or(cpu, source):
    #trace("- OR {:s}".format(REGISTER[source]))
    operand2 = REGGET[source](cpu)
    cpu.a = cpu.a | operand2
    cpu.f.set_SZ503P00(cpu.a)

def _ins_or_ix_n(cpu, data):
    #trace("- OR (IX+0x{:02X})".format(data[0]))
    addr = (cpu.ix + data[0]) & 0xffff
    cpu.a = (cpu.a | cpu.mem[addr]) & 0xff
    cpu.f.set_SZ503P00(cpu.a)

def _ins_or_iy_n(cpu, data):
    #trace("- OR (IY+0x{:02X})".format(data[0]))
    addr = (cpu.iy + data[0]) & 0xffff
    cpu.a = (cpu.a | cpu.mem[addr]) & 0xff
    cpu.f.set_SZ503P00(cpu.a)

def _ins_or_n(cpu, data):
    #trace("- OR 0x{:02X}".format(data[0]))
    cpu.a = (cpu.a | data[0]) & 0xff
    cpu.f.set_SZ503P00(cpu.a)

def _ins_out_c_a(cpu, data):
    """ Output register A to the port BC """
    #trace("- OUT (C),A")
    cpu.output(cpu.b, cpu.c, cpu.a)

def _ins_out_c_c(cpu, data): #
    """ Output register C to the port BC """
    #trace("- OUT (C),C")
    cpu.output(cpu.b, cpu.c, cpu.c)

def _ins_pop_af(cpu, data):
    #trace("- POP AF")
    cpu.f.from_byte(cpu.mem[cpu.sp])
    cpu.a = cpu.mem[cpu.sp+1]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_pop_bc(cpu, data):
    #trace("- POP BC")
    cpu.c = cpu.mem[cpu.sp]
    cpu.b = cpu.mem[cpu.sp+1]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_pop_de(cpu, data):
    #trace("- POP DE")
    cpu.e = cpu.mem[cpu.sp]
    cpu.d = cpu.mem[cpu.sp+1]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_pop_hl(cpu, data):
    #trace("- POP HL")
    cpu.l = cpu.mem[cpu.sp]
    cpu.h = cpu.mem[cpu.sp+1]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_pop_ix(cpu, data):
    #trace("- POP IX")
    cpu.ix = cpu.mem[cpu.sp+1] << 8 | cpu.mem[cpu.sp]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_pop_iy(cpu, data):
    #trace("- POP IY")
    cpu.iy = cpu.mem[cpu.sp+1] << 8 | cpu.mem[cpu.sp]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_push_af(cpu, data):
    #trace("- PUSH AF")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.f.as_byte()
    cpu.mem[cpu.sp+1] = cpu.a

def _ins_push_bc(cpu, data):
    #trace("- PUSH BC")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.c
    cpu.mem[cpu.sp+1] = cpu.b

def _ins_push_de(cpu, data):
    #trace("- PUSH DE")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.e
    cpu.mem[cpu.sp+1] = cpu.d

def _ins_push_hl(cpu, data):
    #trace("- PUSH HL")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.l
    cpu.mem[cpu.sp+1] = cpu.h

def _ins_push_ix(cpu, data):
    #trace("- PUSH IX")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.ix & 0x00FF
    cpu.mem[cpu.sp+1] = (cpu.ix & 0xFF00) >> 8

def _ins_push_iy(cpu, data):
    #trace("- PUSH IY")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = cpu.iy & 0x00FF
    cpu.mem[cpu.sp+1] = (cpu.iy & 0xFF00) >> 8

def _ins_reset(cpu, bit, register):
    #trace("- RESET {:d},{:s}".format(bit, REGISTER[register]))

    value = REGGET[register](cpu)
    value = value & (0xFF ^ (0x01 << bit))
    REGSET[register](cpu, value)

def _ins_ret(cpu, data):
    #trace("- RET")
    high_addr = (cpu.sp+1) & 0xffff
    cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
    cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_c(cpu, data):
    #trace("- RET C")
    if cpu.f.c:
        high_addr = (cpu.sp+1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_m(cpu, data):
    #trace("- RET NEGATIVE")
    if cpu.f.s:
        high_addr = (cpu.sp+1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_nc(cpu, data):
    #trace("- RET NC")
    if not cpu.f.c:
        high_addr = (cpu.sp+1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_nz(cpu, data):
    #trace("- RET NZ")
    if not cpu.f.z:
        high_addr = (cpu.sp + 1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_p(cpu, data):
    #trace("- RET POSITIVE")
    if not cpu.f.s:
        high_addr = (cpu.sp+1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_ret_z(cpu, data):
    #trace("- RET Z")
    if cpu.f.z:
        high_addr = (cpu.sp+1) & 0xffff
        cpu.pc = cpu.mem[high_addr] << 8 | cpu.mem[cpu.sp]
        cpu.sp = (cpu.sp + 2) & 0xffff

def _ins_rla(cpu, data):
    #trace("- RLA")
    value = cpu.a << 1 | (0x01 if cpu.f.c else 0x00)
    carry = (value & 0x100) >> 8
    cpu.f.set___503_0C(value, carry != 0)
    cpu.a = value & 0xFF

def _ins_rlca(cpu, data):
    #trace("- RLCA")
    value = cpu.a << 1
    carry = (value & 0x100) >> 8
    cpu.f.set___503_0C(value, carry != 0)
    cpu.a = (value | carry) & 0xFF

def _ins_rotate(cpu, direction, carry, register):
    #trace("- ROTATE {:s} {:s} {:s}".format('RIGHT' if direction else 'LEFT', 'W/CARRY' if carry else '', REGISTER[register]))

    # Get value
    value = REGGET[register](cpu)

    # Manipulate
    if not direction:
        # LEFT
        old_carry = cpu.f.c
        new_carry = (value & 0x80) != 0x00
        value = ((value << 1) & 0xFE) | \
            (0x01 if (new_carry if carry else old_carry) else 0x00)
    else:
        # RIGHT
        old_carry = cpu.f.c
        new_carry = (value & 0x01) != 0x00
        value = ((value >> 1) & 0x7F) | \
            (0x80 if (new_carry if carry else old_carry) else 0x00)

    cpu.f.set_SZ503P0C(value, new_carry)

    # Writeback
    REGSET[register](cpu, value)

def _ins_rst08(cpu, data):
    #trace("- RST 0x08")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
    cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
    cpu.pc = 0x0008

def _ins_rst18(cpu, data):
    #trace("- RST 0x18")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
    cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
    cpu.pc = 0x0018

def _ins_rst28(cpu, data):
    #trace("- RST 0x28")
    cpu.sp = (cpu.sp - 2) & 0xffff
    cpu.mem[cpu.sp] = (cpu.pc & 0x00ff)
    cpu.mem[cpu.sp+1] = (cpu.pc & 0xff00) >> 8
    cpu.pc = 0x0028

def _ins_rra(cpu, data):
    #trace("- RRA")
    carry = cpu.a & 0x01
    value = cpu.a >> 1 | (0x80 if cpu.f.c else 0x00)
    cpu.f.set___503_0C(value, carry != 0)
    cpu.a = value & 0xFF

def _ins_rrca(cpu, data):
    #trace("- RRCA")
    carry = cpu.a & 0x01
    value = cpu.a >> 1 | (carry << 7)
    cpu.f.set___503_0C(value, carry != 0)
    cpu.a = value & 0xFF

def _ins_sbc(cpu, source):
    #trace("- SBC {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    temp = (cpu.a - value - (1 if cpu.f.c else 0)) & 0xFF
    cpu.f.s = (temp & 0x80) != 0x00
    cpu.f.z = (temp == 0x00)
    cpu.f.five = (temp & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) == 0x00) and ((value & 0x08) != 0x00)
    cpu.f.three = (temp & 0x08) != 0x00
    cpu.f.pv = cpu.a > 0x7F and temp < 0x80
    cpu.f.n = True
    cpu.f.c = cpu.a < temp
    cpu.a = temp

def _ins_sbc_hl_de(cpu, source):
    #trace("- SBC HL,DE")

    op1 = cpu.h << 8 | cpu.l
    op2 = cpu.d << 8 | cpu.e

    temp = (op1 - op2 - (1 if cpu.f.c else 0)) & 0xFFFF
    cpu.f.s = (temp & 0x8000) != 0x00
    cpu.f.z = (temp == 0x0000)
    cpu.f.five = (temp & 0x2000) != 0x00
    cpu.f.h = ((op1 & 0x0800) == 0x00) and ((temp & 0x0800) != 0x00)
    cpu.f.three = (temp & 0x0800) != 0x00
    cpu.f.pv = op1 > 0x7FFF and temp < 0x8000
    cpu.f.n = True
    cpu.f.c = op1 < temp
    cpu.h = (temp & 0xFF00) >> 8
    cpu.l = (temp & 0x00FF)

def _ins_sbc_n(cpu, data):
    #trace("- SBC 0x{:02X}".format(data[0]))
    old_a = cpu.a
    cpu.a = (cpu.a - twos_decode(data[0]) - (1 if cpu.f.c else 0)) & 0xFF
    cpu.f.s = (cpu.a & 0x80) != 0x00
    cpu.f.z = (cpu.a == 0x00)
    cpu.f.five = (cpu.a & 0x20) != 0x00
    cpu.f.h = ((old_a & 0x08) == 0x00) and ((cpu.a & 0x08) != 0x00)
    cpu.f.three = (cpu.a & 0x08) != 0x00
    cpu.f.pv = old_a > 0x7F and cpu.a < 0x80
    cpu.f.n = True
    cpu.f.c = old_a < cpu.a

def _ins_scf(cpu, data):
    #trace("- SCF")
    cpu.f.c = True
    cpu.f.h = False
    cpu.f.n = False
    cpu.f.five = (cpu.a & 0x20) != 0x00
    cpu.f.three = (cpu.a & 0x08) != 0x00

def _ins_set(cpu, bit, register):
    #trace("- SET {:d},{:s}".format(bit, REGISTER[register]))

    value = REGGET[register](cpu)
    value = value | (0x01 << bit)
    REGSET[register](cpu, value)

def _ins_shift(cpu, direction, carry, register):
    #trace("- SHIFT {:s} {:s} {:s}".format('RIGHT' if direction else 'LEFT', 'W/CARRY' if carry else '', REGISTER[register]))

    # Get value
    value = REGGET[register](cpu)

    # Manipulate
    if not direction:
        # LEFT
        new_carry = (value & 0x80) != 0x00
        value = (value << 1) & 0xFE
        if carry:
            value = value | 0x01
    else:
        # RIGHT
        new_carry = (value & 0x01) != 0x00
        value = (value >> 1) & 0x7F
        if carry:
            value = value | ((value & 0x40) << 1)

    cpu.f.set_SZ503P0C(value, new_carry)

    # Writeback
    REGSET[register](cpu, value)

def _ins_sub(cpu, source):
    #trace("- SUB {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    temp = (cpu.a - value) & 0xFF
    cpu.f.s = (temp & 0x80) != 0x00
    cpu.f.z = (temp == 0x00)
    cpu.f.five = (temp & 0x20) != 0x00
    cpu.f.h = ((cpu.a & 0x08) == 0x00) and ((value & 0x08) != 0x00)
    cpu.f.three = (temp & 0x08) != 0x00
    cpu.f.pv = cpu.a > 0x7F and temp < 0x80
    cpu.f.n = True
    cpu.f.c = cpu.a < temp
    cpu.a = temp

def _ins_sub_n(cpu, data):
    #trace("- SUB 0x{:02X}".format(data[0]))
    old_a = cpu.a
    cpu.a = (cpu.a - twos_decode(data[0])) & 0xFF
    cpu.f.s = (cpu.a & 0x80) != 0x00
    cpu.f.z = (cpu.a == 0x00)
    cpu.f.five = (cpu.a & 0x20) != 0x00
    cpu.f.h = ((old_a & 0x08) == 0x00) and ((cpu.a & 0x08) != 0x00)
    cpu.f.three = (cpu.a & 0x08) != 0x00
    cpu.f.pv = old_a > 0x7F and cpu.a < 0x80
    cpu.f.n = True
    cpu.f.c = old_a < cpu.a

def _ins_xor(cpu, source):
    #trace("- XOR {:s}".format(REGISTER[source]))
    value = REGGET[source](cpu)
    cpu.a = cpu.a ^ value
    cpu.f.set_SZ503P00(cpu.a)

INSTR = {
    0x00: (1, _ins_nop),
    0x01: (3, _ins_ld_bc_nn),
    0x03: (1, _ins_inc_bc),
    # 0x04, 0x05: _ins_inc, _ins_dec
    0x06: (2, _ins_ld_b_n),
    0x07: (1, _ins_rlca),
    0x08: (1, _ins_ex_af_afa),
    0x09: (1, _ins_add_hl_bc),
    0x0B: (1, _ins_dec_bc),
    # 0x0C, 0x0D: _ins_inc, _ins_dec
    0x0E: (2, _ins_ld_c_n),
    0x0F: (1, _ins_rrca),
    0x10: (2, _ins_djnz),
    0x11: (3, _ins_ld_de_nn),
    0x12: (1, _ins_ld_de_a),
    0x13: (1, _ins_inc_de),
    # 0x14, 0x15: _ins_inc, _ins_dec
    0x16: (2, _ins_ld_d_n),
    0x17: (1, _ins_rla),
    0x18: (2, _ins_jr),
    0x19: (1, _ins_add_hl_de),
    0x1A: (1, _ins_ld_a_de),
    0x1B: (1, _ins_dec_de),
    # 0x1C, 0x1D: _ins_inc, _ins_dec
    0x1E: (2, _ins_ld_e_n),
    0x1F: (1, _ins_rra),
    0x20: (2, _ins_jr_nz),
    0x21: (3, _ins_ld_hl_nn),
    0x22: (3, _ins_ld_nn_hl),
    0x23: (1, _ins_inc_hl),
    # 0x24, 0x25: _ins_inc, _ins_dec
    0x28: (2, _ins_jr_z),
    0x29: (1, _ins_add_hl_hl),
    0x2A: (3, _ins_ld_hl_cnn),
    0x2B: (1, _ins_dec_hl),
    # 0x2C, 0x2D: _ins_inc, _ins_dec
    0x2E: (2, _ins_ld_l_n),
    0x2F: (1, _ins_cpl),
    0x30: (2, _ins_jr_nc),
    0x31: (3, _ins_ld_sp_nn),
    0x32: (3, _ins_ld_nn_a),
    # 0x34, 0x35: _ins_inc, _ins_dec
    0x36: (2, _ins_ld_hl_n),
    0x37: (1, _ins_scf),
    0x38: (2, _ins_jr_c),
    0x3A: (3, _ins_ld_a_nn),
    # 0x3C, 0x3D: _ins_inc, _ins_dec
    0x3E: (2, _ins_ld_a_n),
    0x3F: (1, _ins_ccf),
    # 0x40 - 0x7F handled by _ins_ld
    # 0x80 - 0x87 handled by _ins_add
    # 0x88 - 0x8F handled by _ins_adc
    # 0x90 - 0x97 handled by _ins_sub
    # 0x98 - 0x9F handled by _ins_sbc
    # 0xA0 - 0xA7 handled by _ins_and
    # 0xA8 - 0xAF handled by _ins_xor
    # 0xB0 - 0xB7 handled by _ins_or
    # 0xB8 - 0xBF handled by _ins_cp
    
    0xC0: (1, _ins_ret_nz),
    0xC1: (1, _ins_pop_bc),
    0xC2: (3, _ins_jp_nz),
    0xC3: (3, _ins_jp_nn),
    0xC4: (3, _ins_call_nz),
    0xC5: (1, _ins_push_bc),
    0xC6: (2, _ins_add_n),
    0xC8: (1, _ins_ret_z),
    0xC9: (1, _ins_ret),
    0xCA: (3, _ins_jp_z),
    # 0xCB mapped below
    0xCD: (3, _ins_call_nn),
    0xCE: (2, _ins_adc_n),
    0xCF: (1, _ins_rst08),

    0xD0: (1, _ins_ret_nc),
    0xD1: (1, _ins_pop_de),
    0xD2: (3, _ins_jp_nc),
    0xD4: (3, _ins_call_nc_nn),
    0xD5: (1, _ins_push_de),
    0xD6: (2, _ins_sub_n),
    0xD8: (1, _ins_ret_c),
    0xD9: (1, _ins_exx),
    0xDA: (3, _ins_jp_c),
    0xDC: (3, _ins_call_c),
    # 0xDD mapped below
    0xDE: (2, _ins_sbc_n),
    0xDF: (1, _ins_rst18),
    
    0xE1: (1, _ins_pop_hl),
    0xE3: (1, _ins_ex_sp_hl),
    0xE5: (1, _ins_push_hl),
    0xE6: (2, _ins_and_n),
    0xE9: (1, _ins_jp_hl),
    0xEB: (1, _ins_ex_de_hl),
    0xEF: (1, _ins_rst28),
    
    0xF0: (1, _ins_ret_p),
    0xF1: (1, _ins_pop_af),
    0xF2: (3, _ins_jp_p_nn),
    0xF3: (1, _ins_di),
    0xF5: (1, _ins_push_af),
    0xF6: (2, _ins_or_n),
    0xF8: (1, _ins_ret_m),
    0xFA: (3, _ins_jp_m),
    0xFB: (1, _ins_ei),
    0xFC: (3, _ins_call_m),
    # 0xFD mapped below
    0xFE: (2, _ins_cp_n),
    }

INSTR_DD = {
    0x09: (2, _ins_add_ix_bc),
    0x19: (2, _ins_add_ix_de),
    0x21: (4, _ins_ld_ix_nn),
    0x29: (2, _ins_add_ix_ix),
    0x36: (4, _ins_ld_ix_n_n),
    0x39: (2, _ins_add_ix_sp),
    0x7E: (3, _ins_ld_a_ix_n),
    0xB6: (3, _ins_or_ix_n),
    0xE1: (2, _ins_pop_ix),
    0xE5: (2, _ins_push_ix),
    }

INSTR_FD = {
    0x36: (4, _ins_ld_iy_n_n),
    0x7E: (3, _ins_ld_a_iy_n),
    0xB6: (3, _ins_or_iy_n),
    0xE1: (2, _ins_pop_iy),
    0xE5: (2, _ins_push_iy),
    }

INSTR_ED = {
    0x48: (2, _ins_in_c_c),
    0x49: (2, _ins_out_c_c),
    0x4B: (4, _ins_ld_bc_cnn),
    0x52: (2, _ins_sbc_hl_de),
    0x53: (4, _ins_ld_nn_de),
    0x56: (2, _ins_im1),
    0x5B: (4, _ins_ld_de_cnn),
    0x78: (2, _ins_in_a_c),
    0x79: (2, _ins_out_c_a),
    0xA0: (2, _ins_ldi),
    0xB0: (2, _ins_ldir),
    }

class Cpu(object):
    __slots__ = ['mem', 'iodevices', 'interrupts', 'immode',

        'a','b','c','d','e','f','h','l',
        'aa','ba','ca','da','ea','fa','ha','la',
        'ix','iy','sp','pc','i','r'
        ]

    def __init__(self, memorymap):
        self.mem = memorymap
        self.iodevices = list()
        self.interrupts = True
        self.immode = 0

        self.a = 0x00
        self.b = 0x00
        self.c = 0x00
        self.d = 0x00
        self.e = 0x00
        self.f = Flags()
        self.h = 0x00
        self.l = 0x00
        self.aa = 0x00
        self.ba = 0x00
        self.ca = 0x00
        self.da = 0x00
        self.ea = 0x00
        self.fa = Flags()
        self.ha = 0x00
        self.la = 0x00
        self.ix = 0x0000
        self.iy = 0x0000
        self.pc = 0x0000
        self.sp = 0x0000
        self.i = 0x00
        self.r = 0x00

    def dump(self, mem):
        print "            A {:02X}  F {:s}             A' {:02X}  F' {:s}".format(self.a, self.f, self.aa, self.fa)
        print "            B {:02X}  C {:02X}                   B' {:02X}  C' {:02X}".format(self.b, self.c, self.ba, self.ca)
        print "            D {:02X}  E {:02X}  (DE)={:02X} {:02X}       D' {:02X}  E' {:02X}".format(self.d, self.e, mem[self.d << 8 | self.e], mem[(self.d << 8 | self.e) + 1], self.da, self.ea)
        print "            H {:02X}  L {:02X}  (HL)={:02X} {:02X}       H' {:02X}  L' {:02X}".format(self.h, self.l, mem[self.h << 8 | self.l], mem[(self.h << 8 | self.l) + 1], self.ha, self.la)
        print "           IX {:04X}  IY {:04X}".format(self.ix, self.iy)
        print "            I {:02X}  R {:02X}".format(self.i, self.r)
        print "           SP {:04X}:".format(self.sp),' '.join(['{:02X}'.format(mem[sp]) for sp in range(self.sp, self.sp+4)])
        print "           PC {:04X}:".format(self.pc),' '.join(['{:02X}'.format(mem[pc]) for pc in range(self.pc, self.pc+4)])

    def execute(self, screen):
        x = 10000
        instruction = [0,0,0,0,0,0]
        while True:
            x = x - 1
            if x == 0:
                screen.blit()
                x = 10000
                pprint.pprint(opt)
            #self.dump(self.mem)
            #print '{:04X}'.format(self.pc),

            another = True
            inslen = 0
            while another:
                instruction[inslen] = self.mem[self.pc]
                inslen = inslen + 1
                self.pc = (self.pc + 1) & 0xFFFF
                another = self.decode(instruction, inslen)

    def decode(self, instruction, inslen):
        if (instruction[0] & 0b11000110) == 0x04:
            return self._decodeIncDec(instruction)
        elif instruction[0] >= 0x40 and instruction[0] <= 0x7F:
            return self._decodeLD(instruction)
        elif instruction[0] >= 0x80 and instruction[0] <= 0xBF:
            return self._decodeLOGIC(instruction)
        elif instruction[0] == 0xCB:
            return self._decodeCB(instruction, inslen)
        elif instruction[0] == 0xDD:
            return self._decodeDD(instruction, inslen)
        elif instruction[0] == 0xED:
            return self._decodeED(instruction, inslen)
        elif instruction[0] == 0xFD:
            return self._decodeFD(instruction, inslen)

        try:
            if inslen < INSTR[instruction[0]][0]:
                return True
        except KeyError as e:
            formatted = ''.join(['{:02X}'.format(i) for i in instruction])
            raise RuntimeError("Opcode {:s} is not supported... yet".format(formatted))

        opt[instruction[0]] = opt[instruction[0]] + 1

        INSTR[instruction[0]][1](self, instruction[1:])
            
        return False

    def _decodeIncDec(self, instruction):
        """ Handle Inc/Dec r opcodes 0x[0123][45CD] """
        action = instruction[0] & 0x01
        source = (instruction[0] & 0x38) >> 3

        if action == 0:
            _ins_inc(self, source)
        elif action == 1:
            _ins_dec(self, source)
        return False

    def _decodeLOGIC(self, instruction):
        """ Handle ADD/ADC/SUB/SBC/AND/XOR/OR/CP r opcodes 0x80-0xBF """
        action = (instruction[0] & 0x38) >> 3
        source = instruction[0] & 0x07

        if action == 0:
            _ins_add(self, source)
        elif action == 1:
            _ins_adc(self, source)
        elif action == 2:
            _ins_sub(self, source)
        elif action == 3:
            _ins_sbc(self, source)
        elif action == 4:
            _ins_and(self, source)
        elif action == 5:
            _ins_xor(self, source)
        elif action == 6:
            _ins_or(self, source)
        elif action == 7:
            _ins_cp(self, source)
        return False

    def _decodeLD(self, instruction):
        """ Handle LD r,r opcodes 0x40-0x7F """
        destination = (instruction[0] & 0x38) >> 3
        source = instruction[0] & 0x07

        _ins_ld(self, destination, source)
        return False


    def _decodeCB(self, instruction, inslen):
        """ Handle opcodes 11001011 """
        if inslen < 2:
            return True

        #decode
        action = instruction[1] & 0xC0
        if action == 0x00:
            direction = True if (instruction[1] & 0x08) >> 3 else False
            carry = False if (instruction[1] & 0x10) >> 4 else True
            register = (instruction[1] & 0x07)
            if (instruction[1] & 0x20) >> 5:
                _ins_shift(self, direction, carry, register)
            else:
                _ins_rotate(self, direction, carry, register)
        elif action == 0x40:
            raise RuntimeError("BIT not supported... yet")
        elif action == 0x80:
            register = (instruction[1] & 0x07)
            bit = (instruction[1] & 0x38) >> 3
            _ins_reset(self, bit, register)
        elif action == 0xC0:
            register = (instruction[1] & 0x07)
            bit = (instruction[1] & 0x38) >> 3
            _ins_set(self, bit, register)

        return False

    def _decodeDD(self, instruction, inslen):
        """ Handle opcodes 11011101 """
        if inslen < 2:
            return True

        try:
            if inslen < INSTR_DD[instruction[1]][0]:
                return True
        except KeyError as e:
            formatted = ''.join(['{:02X}'.format(i) for i in instruction])
            raise RuntimeError("Opcode {:s} is not supported... yet".format(formatted))

        INSTR_DD[instruction[1]][1](self, instruction[2:])
        return False

    def _decodeED(self, instruction, inslen):
        """ Handle opcodes 11101101 """
        if inslen < 2:
            return True

        try:
            if inslen < INSTR_ED[instruction[1]][0]:
                return True
        except KeyError as e:
            formatted = ''.join(['{:02X}'.format(i) for i in instruction])
            raise RuntimeError("Opcode {:s} is not supported... yet".format(formatted))

        INSTR_ED[instruction[1]][1](self, instruction[2:])
        return False

    def _decodeFD(self, instruction, inslen):
        """ Handle opcodes 11111101 """
        if inslen < 2:
            return True

        try:
            if inslen < INSTR_DD[instruction[1]][0]:
                return True
        except KeyError as e:
            formatted = ''.join(['{:02X}'.format(i) for i in instruction])
            raise RuntimeError("Opcode {:s} is not supported... yet".format(formatted))

        INSTR_FD[instruction[1]][1](self, instruction[2:])
        return False

    def register_io(self, iodevice):
        self.iodevices.append(iodevice)

    def input(self, high, low):
        for device in self.iodevices:
            result = device.accept_input(high, low)
            if result is not None:
                return result
        raise RuntimeError('No I/O device responded to OUT instruction')

    def output(self, high, low, data):
        found_one = False
        for device in self.iodevices:
            if device.accept_output(high, low, data):
                found_one = True
        if not found_one:
            raise RuntimeError('No I/O device responded to OUT instruction')
