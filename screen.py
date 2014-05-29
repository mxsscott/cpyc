import pygame
import thread
import sys

pygame.init()

COLORS = [
    (0x80, 0x80, 0x80),
    (0x80, 0x80, 0x80),
    (0x00, 0xFF, 0x80),
    (0xFF, 0xFF, 0x80),
    (0x00, 0x00, 0x80),
    (0xFF, 0x00, 0x80),
    (0x00, 0x80, 0x80),
    (0xFF, 0x80, 0x80),
    (0xFF, 0x00, 0x80),
    (0xFF, 0xFF, 0x80),
    (0xFF, 0xFF, 0x00),
    (0xFF, 0xFF, 0xFF),
    (0xFF, 0x00, 0x00),
    (0xFF, 0x00, 0xFF),
    (0xFF, 0x80, 0x00),
    (0xFF, 0x80, 0xFF),
    (0x00, 0x00, 0x80),
    (0x00, 0xFF, 0x80),
    (0x00, 0xFF, 0x00),
    (0x00, 0xFF, 0xFF),
    (0x00, 0x00, 0x00),
    (0x00, 0x00, 0xFF),
    (0x00, 0x80, 0x00),
    (0x00, 0x80, 0xFF),
    (0x80, 0x00, 0x80),
    (0x80, 0xFF, 0x80),
    (0x80, 0xFF, 0x00),
    (0x80, 0xFF, 0xFF),
    (0x80, 0x00, 0x00),
    (0x80, 0x00, 0xFF),
    (0x80, 0x80, 0x00),
    (0x80, 0x80, 0xFF)]

MODE1 = [0 for i in range(0,256)]

for i in range(0, 256):
    j = i & 0x1F
    if (j & 0x11) == 0x00:
        MODE1[i] = 0
    elif (j & 0x11) == 0x10:
        MODE1[i] = 1
    elif (j & 0x11) == 0x01:
        MODE1[i] = 2
    else:
        MODE1[i] = 3

def _get_coord(address):
    row = ((address & 0x3800) >> 11) + (((address & 0x07FF) / 0x50) << 3)
    col = ((address & 0x07FF) % 0x50) << 2
    return col, row

MODE1XY = [_get_coord(address) for address in range(0x0000, 0x4000)]

class Screen(object):
    __slots__ = ['mem',
        'wholesize',
        'origin',
        'size',
        'screen',
        'palette',
        'buffer',
        'pix',
        'dirty']

    def __init__(self):
        fpsClock = pygame.time.Clock()
        
        pygame.display.set_caption('Amstrad CPC')
        self.screen = pygame.display.set_mode((640, 400), 0, 8)
        self.buffer = pygame.Surface((640,400), 0, 8)
        self.pix = pygame.PixelArray(self.buffer)
        self.dirty = False
        pygame.display.update()
        fpsClock.tick(30) 

    def init(self, crtc):
        print crtc
        self.reconfigure(crtc)

    def reconfigure(self, crtc):
        self.set_size(crtc.registers[0:8])
        del self.pix
        self.pix = pygame.PixelArray(self.buffer)
        pygame.display.update()

    def set_size(self, registers):
        self.compute_wholesize(registers)
        self.compute_origin(registers)
        self.compute_size(registers)
        self.screen = pygame.display.set_mode(self.wholesize, 0, 8)

    def compute_wholesize(self, registers):
        width = (registers[0] - (registers[3] & 0x0F)) * 16
        height = (registers[4] - ((registers[3] & 0xF0) >> 4)) * 16
        if width <= 0 or height <= 0:
            self.wholesize = 300, 40
        else:
            self.wholesize = width, height

    def compute_origin(self, registers):
        left = self.wholesize[0] - (registers[1] * 16)
        top = self.wholesize[1] - (registers[6] * 16)
        self.origin = left, top

    def compute_size(self, registers):
        self.size = (registers[1] * 16), (registers[6] * 16)

    def update_palette(self, palette):
        self.palette = [COLORS[x] for x in palette]
        pygame.display.set_palette(self.palette)

    def __setitem__(self, address, data):
        col,row = MODE1XY[address & 0x3FFF]
        self.pix[col,   row] = MODE1[data >> 3]
        self.pix[col+1, row] = MODE1[data >> 2]
        self.pix[col+2, row] = MODE1[data >> 1]
        self.pix[col+3, row] = MODE1[data >> 0]

    def blit(self):
        del self.pix
        self.screen.blit(self.buffer, (50,50))
        pygame.display.update()
        self.pix = pygame.PixelArray(self.buffer)
