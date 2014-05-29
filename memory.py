
class _MemoryChunk(object):
    """ A 16 kB block of memory """
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return "MEM"

class RomChunk(_MemoryChunk):
    def __init__(self, data):
        _MemoryChunk.__init__(self, bytearray(data))

    def __str__(self):
        return 'ROM@'+hex(id(self))

class UpperRomChunk(RomChunk):
    def __init__(self, bank, data):
        RomChunk.__init__(self, bytearray(data))
        self.bank = bank

    def __str__(self):
        return 'Upper ROM{:02X}@'.format(self.bank)+hex(id(self))


def address_to_chunk(address):
    if address < 0x4000:
        return 0
    elif address < 0x8000:
        return 1
    elif address < 0xC000:
        return 2
    else:
        return 3

A2CHUNK = [address_to_chunk(x) for x in range(0, 0x10000)]

MAPPING = {
    0 : [0,1,2,3],
    1 : [0,1,2,7],
    2 : [4,5,6,7],
    3 : [0,3,2,7],
    4 : [0,4,2,3],
    5 : [0,5,2,3],
    6 : [0,6,2,3],
    7 : [0,7,2,3]
    }

class Memory(object):
    """ Memory map. """

    def __init__(self, screen):
        """ Initialise memory map """
        self._screen = screen
        self._rammap = [None, None, None, None]
        self._rambanks = [bytearray(16384), bytearray(16384),
                          bytearray(16384), bytearray(16384),
                          bytearray(16384), bytearray(16384),
                          bytearray(16384), bytearray(16384)]
        self.apply_ram_map(0)
        self._rommap = [None, None, None, dict()]
        self._upperrom = False
        self._activebank = 0
        self._lowerrom = True

    def add_chunk(self, address, chunk):
        """ Add a chunk of memory to the map at the given address.

        The memory map can handle 1 RAM chunk and 1 ROM chunk at any
        particular address, which must be on a 16kB boundary.

        """
        if isinstance(chunk, UpperRomChunk):
            self._rommap[address_to_chunk(address)][chunk.bank] = chunk
        elif isinstance(chunk, RomChunk):
            self._rommap[address_to_chunk(address)] = chunk

    def apply_ram_map(self, num):
        mapping = MAPPING[num]
        self._rammap[0] = self._rambanks[mapping[0]]
        self._rammap[1] = self._rambanks[mapping[1]]
        self._rammap[2] = self._rambanks[mapping[2]]
        self._rammap[3] = self._rambanks[mapping[3]]

    def dump_map(self):
        """ Print the current memory map """
        print "      ROM"
        print "C000  {:16s}{:s}".format(
                self._rommap[address_to_chunk(0xC000)][self._activebank],
                '*' if self._upperrom else '')
        print "0000  {:16s}{:s}".format(
                self._rommap[address_to_chunk(0x0000)],
                '*' if self._lowerrom else '')

    def __setitem__(self, address, value):
        chunk = A2CHUNK[address]
        chunkaddress = address & 0x3FFF
        if chunk == 3:
            self._screen[address] = value
        self._rammap[chunk][chunkaddress] = value

    def __getitem__(self, address):
        chunk = A2CHUNK[address]
        chunkaddress = address & 0x3FFF
        if chunk == 0 and self._lowerrom:
            return self._rommap[chunk].data[chunkaddress]
        elif chunk == 3 and self._upperrom:
            if self._activebank not in self._rommap[chunk]:
                return self._rommap[chunk][0].data[chunkaddress]
            else:
                return self._rommap[chunk][self._activebank].data[chunkaddress]
        else:
            return self._rammap[chunk][chunkaddress]
