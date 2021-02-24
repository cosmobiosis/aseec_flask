from __future__ import print_function
from copy import deepcopy
from ctypes import *
import base64

VERSION = "0.32"
platform_types = { 1: 'MAX32660' }

class MsblHeader(Structure):
    _fields_ = [('magic', 4 * c_char),
                ('formatVersion', c_uint),
                ('target', 16 * c_char),
                ('enc_type', 16 * c_char),
                ('nonce', 11 * c_ubyte),
                ('resv0', c_ubyte),
                ('auth', 16 * c_ubyte),
                ('numPages', c_ushort),
                ('pageSize', c_ushort),
                ('crcSize', c_ubyte),
                ('resv1', 3 * c_ubyte)]

class AppHeader(Structure):
    _fields_ = [('crc32', c_uint),
                ('length', c_uint),
                ('validMark', c_uint),
                ('boot_mode', c_uint)]

class Page(Structure):
    _fields_ = [('data', (8192 + 16) * c_ubyte)]

class CRC32(Structure):
    _fields_ = [('val', c_uint)]

class Object(object):
    pass

class MaximBootloader(object):
    def __init__(self, msbl_file):
        # print('msbl file name: ' + self.file_name)
        self.msbl = Object()
        self.file_name = msbl_file
        success = self.read_msbl_file()
        if not success:
            print("TERMINATING PROGRAM")
            exit(0)

    def get_response_data(self):
        return  {
            "nonce": self.get_base64_string(self.msbl.header.nonce),
            "auth" : self.get_base64_string(self.msbl.header.auth),
            "numPages": self.msbl.header.numPages,
            "pages" : self.msbl.pages_base64
        }

    def get_base64_string(self, data):
        return base64.b64encode(data).decode('utf-8')

    def print_as_hex(self, label, arr):
        print(label + ' : ' + ' '.join(format(i, '02x') for i in arr))

    def read_msbl_file(self):
        total_size = 0
        with open(self.file_name, 'rb') as self.f:
            header = MsblHeader()
            if self.f.readinto(header) == sizeof(header):
                self.print_as_hex('nonce', header.nonce)
                self.print_as_hex('auth', header.auth)
                self.print_as_hex('resv1', header.resv1)
            else:
                print("FILE ERROR")
                return False

            self.msbl.header = header
            i = 0
            self.msbl.pages_data = []
            self.msbl.pages_base64 = []
            tmp_page = Page()
            last_pos = self.f.tell()
            total_size = total_size + sizeof(header)
            # print('last_pos: ' + str(last_pos))
            while self.f.readinto(tmp_page) == sizeof(tmp_page):
                buf_copy = deepcopy(tmp_page.data)
                self.msbl.pages_data.append(buf_copy)
                self.msbl.pages_base64.append(self.get_base64_string(buf_copy))
                total_size = total_size + sizeof(tmp_page)
                # print(self.msbl.pages_data[i])
                #print('read page ' + str(i));
                i = i + 1
                last_pos = self.f.tell()
                #print('last_pos: ' + str(last_pos))

            # self.msbl.crc32 = CRC32()
            # self.f.seek(-4, 2)
            #
            # self.f.readinto(self.msbl.crc32)
            # boot_mem_page = i - 1
            # total_size = total_size + sizeof(self.msbl.crc32)

            # print('Total file size: ' + str(total_size) + ' CRC32: ' + hex(self.msbl.crc32.val))
            # print('Reading msbl file succeed.')
        self.f.close()
        return True