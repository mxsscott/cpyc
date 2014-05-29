class Crtc(object):
    # http://www.cpcwiki.eu/index.php/CRTC

    __slots__ = ['current_reg', 'registers', 'screen']
    def __init__(self, cpu, screen):
        cpu.register_io(self)
        self.current_reg = 0
        self.registers = [0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00]
        self.screen = screen
        screen.init(self)

    def __str__(self):
        return """ CRTC: Active reg: {:d}
 CRTC: Registers:
     0: {:3d}  Width
     1: {:3d}  Width displayed
     2: {:3d}  Horizontal sync pos
     3: {:3d}  HSync width
     3: {:3d}  VSync width
     4: {:3d}  Height
     5: {:3d}  Vertical adjustment
     6: {:3d}  Height displayed
     7: {:3d}  Vertical sync pos
     8: {:3d}  Interlace/skew
     9: {:3d}  Max Raster Address
    10: {:3d}  Cursor Start Raster
    11: {:3d}  Cursor End Raster
 12/13: {:04X} Display Start
 12/13: {:s} Display Length
 12/13: {:04X} Display Offset
 14/15: {:04X} Cursor Address
 16/17: {:04X} Light Pen Address""".format(
    self.current_reg,
    self.registers[0],
    self.registers[1],
    self.registers[2],
    self.registers[3] & 0x0F,
    (self.registers[3] & 0xF0) >> 4,
    self.registers[4],
    self.registers[5],
    self.registers[6],
    self.registers[7],
    self.registers[8],
    self.registers[9],
    self.registers[10],
    self.registers[11],
    ((self.registers[12] << 8 | self.registers[13]) & 0x3000) << 2,
    "32kB" if ((self.registers[12] << 8 | self.registers[13]) & 0x0C00) == 0x0300 else "16kB",
    (self.registers[12] << 8 | self.registers[13]) & 0x03FF,
    self.registers[14] << 8 | self.registers[15],
    self.registers[16] << 8 | self.registers[17])

    def accept_output(self, address_high, address_low, data):
        # Active when A14 is low. A8 and A9 define the function
        if (address_high & 0x40):
            return False

        function = address_high & 0x03
        if function == 0:
            # register select
            self.current_reg = data
            print self
            return True
        if function == 1:
            # register write
            self.registers[self.current_reg] = data
            print self
            self.screen.reconfigure(self)
            return True
        raise RuntimeError("Unimplemented CRTC operation")


class GateArray(object):

    __slots__ = ['memory', 'screen', 'screenmode', 'interrupts', 'palette_index', 'palette']

    def __init__(self, cpu, memory, screen):
        cpu.register_io(self)
        self.memory = memory

        self.screenmode = 0
        self.screen = screen
        self.interrupts = False
        self.palette_index = 0
        self.palette = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

    def accept_input(self, address_high, address_low):
        # Active when A14 is high and A15 is low
        if (address_high & 0xC0) != 0x40:
            return None

        raise RuntimeError()

    def accept_output(self, address_high, address_low, data):
        # Active when A14 is high and A15 is low
        if (address_high & 0xC0) != 0x40:
            return False
        mode = (data & 0xC0) >> 6
        if mode == 0:
            # Pen selection
            value = data & 0x1F
            if value & 0x10:
                self.palette_index = 16
            else:
                self.palette_index = data & 0x0F
            print " GateArray: pen {:d} selected".format(self.palette_index)
        elif mode == 1:
            # Pen colour selection
            self.palette[self.palette_index] = data & 0x1F
            print " GateArray: pen {:d} set to 0x{:02X}".format(self.palette_index, data&0x1F)
            self.screen.update_palette(self.palette)
        elif mode == 2:
            self.screenmode = data & 0x03
            self.memory._lowerrom = (data & 0x04) == 0x00
            self.memory._upperrom = (data & 0x08) == 0x00
            self.interrupts = (data & 0x10) != 0x00
            print " Mode {:d}. Lower ROM {:d} Upper ROM {:d} Interrupts {:d}".format(self.screenmode, self.memory._lowerrom, self.memory._upperrom, self.interrupts)
        elif mode == 3:
            self.memory.apply_ram_map(data & 0x07)
            print " GateArray: applied RAM map {:d}".format(data & 0x07)
            self.memory.dump_map()
        return True

class Floppy(object):
    __slots__ = ['motor']

    def __init__(self, cpu):
        cpu.register_io(self)
        self.motor = False

    def __str__(self):
        return """ Floppy Disk Drive Controller
    Motor: {:s}""".format("On" if self.motor else "Off")

    def accept_output(self, address_high, address_low, data):
        if (address_high & 0x05) != 0x00 or \
                (address_low & 0x80) != 0x00:
            return False

        if (address_high & 0x01) == 0x00:
            if (address_low & 0x7F) == 0x7E:
                if data == 0x00:
                    self.motor = False
                else:
                    self.motor = True
                print self
            return True
        else:
            if (address_low & 0x7F) == 0x7E:
                print " Floppy Main Status Register"
                raise RuntimeError()
            elif (address_low & 0x7F) == 0x7F:
                print " Floppy Data Register"
                raise RuntimeError()
 
class PrinterPort(object):

    __slots__ = ['port']

    def __init__(self, cpu):
        cpu.register_io(self)
        self.port = 0x00

    def __str__(self):
        return " Printer Port: 0x{:02X}".format(self.port)

    def accept_input(self, address_high, address_low):
        # Active when A12 is low
        if (address_high & 0x10) != 0x00:
            return None

        raise RuntimeError()

    def accept_output(self, address_high, address_low, data):
        # Active when A12 is low
        if (address_high & 0x10) != 0x00:
            return False

        self.port = data
        print self
        return True

class PPI8255(object):

    __slots__ = [
        'dir_a',
        'dir_b',
        'dir_c_lower',
        'dir_c_upper',
        'mode_a',
        'mode_b',
        'mode_c_upper',
        'mode_c_lower',
        'a',
        'b',
        'c']

    def __init__(self, cpu):
        cpu.register_io(self)
        self.dir_a = 'I'
        self.mode_a = 0
        self.dir_b = 'I'
        self.mode_b = 0
        self.dir_c_upper = 'I'
        self.dir_c_lower = 'O'
        self.mode_c_upper = 0
        self.mode_c_lower = 0
        self.a = 0x00
        self.b = 0x00
        self.c = 0x00

    def __str__(self):
        return """ 8255 Port A      : direction {:s} mode {:d} value 0x{:02X}
 8255 Port B      : direction {:s} mode {:d} value 0x{:02X}
 8255 Port C upper: direction {:s} mode {:d} value 0x{:0X}
 8255 Port C lower: direction {:s} mode {:d} value 0x{:0X}""".format(
    self.dir_a, self.mode_a, self.a,
    self.dir_b, self.mode_b, self.b,
    self.dir_c_upper, self.mode_c_upper, (self.c & 0xF0) >> 4,
    self.dir_c_lower, self.mode_c_lower, (self.c & 0x0F))

    def accept_input(self, address_high, address_low):
        # Active when A11 is low
        if (address_high & 0x08) != 0x00:
            return None

        function = address_high & 0x03
        if function == 1: # port B
            return 0b01011110 # :TODO: http://www.cpcwiki.eu/index.php/8255#PPI_Port_B
        if function == 2: # port C
            return self.c

        raise RuntimeError()

    def accept_output(self, address_high, address_low, data):
        # Active when A11 is low.
        if (address_high & 0x08) != 0x00:
            return False

        function = address_high & 0x03

        # http://www.cpcwiki.eu/index.php/8255
        if function == 3:
            # Control
            if data & 0x80:
                # Initialize
                self.dir_c_lower = 'I' if data & 0x01 else 'O'
                self.dir_b = 'I' if data & 0x02 else 'O'
                self.mode_b = 1 if data & 0x04 else 0
                self.mode_c_lower = 1 if data & 0x04 else 0
                self.dir_c_upper = 'I' if data & 0x08 else 'O'
                self.dir_a = 'I' if data & 0x10 else 'O'
                self.mode_a = (data & 0x60) >> 5
                self.mode_c_upper = (data & 0x60) >> 5
                print " 8255 Control Register changed"
                print self
            else:
                # Port C flip a single bit
                mask = 0x01 << (data & 0x0E >> 1)
                value = (0xFF if data & 0x01 else 0x00) & mask
                mask = ~ mask
                self.c = self.c & mask | value
                print " 8255 Port C flip"
                print self
            return True
        elif function == 0:
            # Write A [to PSG]
            self.a = data
            print " 8255 Port A write"
            print self
            return True
        elif function == 2:
            # Write C
            self.c = ((data if self.dir_c_upper=='O' else self.c) & 0xF0) | ((data if self.dir_c_lower=='O' else self.c) & 0x0F)
            print " 8255 Port C write"
            print self
            return True

        raise RuntimeError()

class RomBank(object):
    __slots__ = ['memory']

    def __init__(self, cpu, memory):
        cpu.register_io(self)
        self.memory = memory

    def __str__(self):
        return " RomBank 0x{:02X} selected".format(self.memory._activebank)

    def accept_output(self, address_high, address_low, data):
        # Active when A13 is low
        if (address_high & 0x20) != 0x00:
            if (address_high == 0xF8 and address_low == 0xFF):
                print " Soft reset"
                return True
            return False

        self.memory._activebank = data
        print self
        return True
