"""
An emulated Amstrad CPC 464
"""

from memory import Memory, RomChunk, UpperRomChunk
from instruction import Cpu
import cpcio
import screen

def _get_data_from_file(fname):
    with open(fname, 'rb') as fin:
        data = fin.read()
    return data

def _build_memory(screen):
    """ Initialize CPC464 memory map """
    memory = Memory(screen)
    memory.add_chunk(0x0000, RomChunk(_get_data_from_file('6128L.rom')))
    memory.add_chunk(0xC000, UpperRomChunk(0, _get_data_from_file('6128U-basic.rom')))
    memory.apply_ram_map(0)
    memory.dump_map()
    return memory

def _build_cpu(memory_map):
    return Cpu(memory_map)

class Cpc6128(object):
    def __init__(self):
        self.screen = scr = screen.Screen()
        self.memory = _build_memory(self.screen)
        self.cpu = _build_cpu(self.memory)
        self.gatearray = cpcio.GateArray(self.cpu, self.memory, scr)
        self.ppi8255 = cpcio.PPI8255(self.cpu)
        self.printer = cpcio.PrinterPort(self.cpu)
        self.crtc = cpcio.Crtc(self.cpu, scr)
        self.rombank = cpcio.RomBank(self.cpu, self.memory)
        self.floppy = cpcio.Floppy(self.cpu)

    def boot(self):
        try:
            self.cpu.execute(self.screen)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    CPC = Cpc6128()
    CPC.boot()
