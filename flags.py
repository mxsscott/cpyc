"""
? indicates the effect is undefined.
* indicates the effect is non-standard (see the notes).
0 indicates the flag is reset.
1 indicates the flag is set.
- indicates the flag is not affected.
S,Z,5,H,3,P,V,N,C indicate the flag is set as above.

r refers to any 8-bit quantity appropriate for that instruction.
s refers to any 16-bit quantity appropriate for that instruction.

Instruction           Flags     Notes
===========           =====     =====
ADD/ADC/SUB/SBC       SZ5H3VNC  
CP r                  SZ*H*VNC  CP is just SUB with the result thrown away
                F5 and F3 are copied from the operand, not the result
INC/DEC r             SZ5H3VN-
16 bit additions are done in two steps: 
First the two lower bytes are added, the two higher bytes.

ADD s                 --***-0C  F5,H,F3 from higher bytes addition
ADC/SBC s             SZ***VNC  F5,H,F3 from higher bytes addition
RLCA/RLA/RRCA/RRA     --503-0C
RRD/RLD               SZ503P0-  Flags set on result in A
BIT n,r               *Z513*0-  PV as Z, S set only if n=7 and b7 of r set
                Behaves much like AND r,2^n
CCF                   --***-0*  C=1-C, H as old C
                F5, F3 from A register
SCF                   --*0*-01  F5, F3 from A register
NEG                   SZ5H3V1C  A=0-A (Zaks gets C wrong)
DAA                   SZ5*3P-*  H from internal correction, C for cascade BCD
LD A,R/LD A,I         SZ503*0-  PV as IFF2 [yaze doesn't affect F?]
LDI/LDIR/LDD/LDIR     --*0**0-  PV set if BC not 0
                F5 is bit 1 of (transferred byte + A)
                F3 is bit 3 of (transferred byte + A)
CPI/CPIR/CPD/CPDR     SZ*H**1-  PV set if BC not 0
                                S,Z,H from (A - (HL) ) as in CP (HL)
                F3 is bit 3 of (A - (HL) - H), H as in F after instruction
                F5 is bit 1 of (A - (HL) - H), H as in F after instruction
INI/INIR/IND/INDR     SZ5?3???  Flags affected as in DEC B
OUTI/OTIR/OUTD/OTDR   SZ5?3???  Flags affected as in DEC B
All others            --------  Except for POP AF and EX AF,AF', of course...
"""

_PARITY_LOOKUP = list()
for i in range(0,256):
    parity = ((i&0x01) + \
        ((i&0x02)>>1) + \
        ((i&0x04)>>2) + \
        ((i&0x08)>>3) + \
        ((i&0x10)>>4) + \
        ((i&0x20)>>5) + \
        ((i&0x40)>>6) + \
        ((i&0x80)>>7))
    parity = False if (parity & 0x01) == 1 else True
    _PARITY_LOOKUP.append(parity)

class Flags(object):
    __slots__ = ['h', 'n', 'five','z','three','s','pv','c']

    def __init__(self):
        self.h = False
        self.n = False
        self.five = False
        self.z = False
        self.three = False
        self.s = False
        self.pv = False
        self.c = False

    def __str__(self):
        return '{:s}{:s}{:s}{:s}{:s}{:s}{:s}{:s}'.format(
            'S' if self.s else ' ',
            'Z' if self.z else ' ',
            '1' if self.five else '0',
            'H' if self.h else ' ',
            '1' if self.three else '0',
            'P' if self.pv else ' ',
            'N' if self.n else ' ',
            'C' if self.c else ' ')

    def as_byte(self):
        return 0x80 if self.s else 0x00 | \
            0x40 if self.z else 0x00 | \
            0x20 if self.five else 0x00 | \
            0x10 if self.h else 0x00 | \
            0x08 if self.three else 0x00 | \
            0x04 if self.pv else 0x00 | \
            0x02 if self.n else 0x00 | \
            0x01 if self.c else 0x00

    def from_byte(self, value):
        self.s = (value & 0x80) != 0
        self.z = (value & 0x40) != 0
        self.five = (value & 0x20) != 0
        self.h = (value & 0x10) != 0
        self.three = (value & 0x08) != 0
        self.pv = (value & 0x04) != 0
        self.n = (value & 0x02) != 0
        self.c = (value & 0x01) != 0

    def set___c1c_1_(self, value):
        self.five = (value & 0x20) != 0x00
        self.h = True
        self.three = (value & 0x08) != 0x00
        self.n = True

    def set___503_0C(self, value, carry):
        self.five = (value & 0x20) != 0x00
        self.h = False
        self.three = (value & 0x08) != 0x00
        self.n = False
        self.c = carry

    def set_SZ503P0_(self, value):
        value = value & 0xFF
        self.s = (value & 0x80) != 0x00
        self.z = (value == 0x00)
        self.five = (value & 0x20) != 0x00
        self.h = False
        self.three = (value & 0x08) != 0x00
        self.pv = _PARITY_LOOKUP[value]
        self.n = False

    def set_SZ503P00(self, value):
        value = value & 0xFF
        self.s = (value & 0x80) != 0x00
        self.z = (value == 0x00)
        self.five = (value & 0x20) != 0x00
        self.h = False
        self.three = (value & 0x08) != 0x00
        self.pv = _PARITY_LOOKUP[value]
        self.n = False
        self.c = False

    def set_SZ503P0C(self, value, carry):
        value = value & 0xFF
        self.s = (value & 0x80) != 0x00
        self.z = (value == 0x00)
        self.five = (value & 0x20) != 0x00
        self.h = False
        self.three = (value & 0x08) != 0x00
        self.pv = _PARITY_LOOKUP[value]
        self.n = False
        self.c = carry

    def set_SZ513P00(self, value):
        value = value & 0xFF
        self.s = (value & 0x80) != 0x00
        self.z = (value == 0x00)
        self.five = (value & 0x20) != 0x00
        self.h = True
        self.three = (value & 0x08) != 0x00
        self.pv = _PARITY_LOOKUP[value]
        self.n = False
        self.c = False
