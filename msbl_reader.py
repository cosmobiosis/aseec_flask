from __future__ import print_function
from copy import deepcopy
from ctypes import *
import base64
import struct

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
        ret_num_pages_bytes = struct.pack('>h', self.msbl.header.numPages)
        ret_page_size_bytes = struct.pack('>h', self.msbl.header.pageSize)

        numPage_prefix = bytes.fromhex("01030004")
        pageSize_prefix = bytes.fromhex("01040004")
        nonce_prefix = bytes.fromhex("0105000B")
        auth_prefix = bytes.fromhex("0106000F")
        return  {
            "nonce": self.get_base64_string(nonce_prefix + self.msbl.header.nonce),
            "auth" : self.get_base64_string(auth_prefix + self.msbl.header.auth),
            "numPages": self.get_base64_string(numPage_prefix + ret_num_pages_bytes),
            "pageSize": self.get_base64_string(pageSize_prefix + ret_page_size_bytes),
            "pages" : self.msbl.pages_base64,
            "cmds": self.msbl.cmds_base64,
        }

    def get_base64_string(self, data):
        return base64.b64encode(data).decode('ascii')

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
                print('pageSize', header.pageSize)
            else:
                print("FILE ERROR")
                return False

            self.msbl.header = header
            i = 0
            self.msbl.cmds_base64 = []
            self.msbl.pages_base64 = []
            tmp_page = Page()
            last_pos = self.f.tell()
            total_size = total_size + sizeof(header)
            # print('last_pos: ' + str(last_pos))
            while self.f.readinto(tmp_page) == sizeof(tmp_page):
                buf_copy = deepcopy(tmp_page.data)
                # self.msbl.pages_data.append(buf_copy)
                page_base64 = []
                TRUNK_SIZE = 64
                TRUNK_CNT = 128
                for trunk_ind in range(TRUNK_CNT):
                    prefix_bytes = bytes.fromhex("01070102")
                    offset_bytes = struct.pack('>h', 2 + trunk_ind * TRUNK_SIZE)
                    page_base64.append(self.get_base64_string(prefix_bytes 
                    + offset_bytes + bytearray(buf_copy[trunk_ind * TRUNK_SIZE: (trunk_ind + 1) * TRUNK_SIZE])))
                offset_bytes = struct.pack('>h', 2 + TRUNK_CNT * TRUNK_SIZE)
                self.msbl.cmds_base64.append(self.get_base64_string(bytes.fromhex("01080012") 
                + offset_bytes + bytearray(buf_copy[8192:])))
                self.msbl.pages_base64.append(page_base64)
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