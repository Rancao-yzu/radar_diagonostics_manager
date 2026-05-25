import zlib

from intelhex import IntelHex

import bincopy

from ctypes import *

import os

from crc import Crc32,Calculator,Crc16, Crc8, Crc64, Register, TableBasedRegister, Configuration

from functools import lru_cache

CCITT = Configuration(
    width=16,
    polynomial=0x1021,
    init_value=0x0000,
    final_xor_value=0x0000,
    reverse_input=True,
    reverse_output=True,
)
CCITT_FALSE = Configuration(
    width=16,
    polynomial=0x1021,  # CRC16-CCITT polynomial
    init_value=0xFFFF,   # Initial value is 0xFFFF
    final_xor_value=0x0000,  # XOR with 0x0000
    reverse_input=False,     # No input reversal
    reverse_output=False,    # Output reversal (Big Endian) is not needed
)

COSTUME_CRC32_POLYNOMIAL = Configuration(
    width=32,
    polynomial=0x04C11DB7,
    init_value=0xFFFFFFFF,
    final_xor_value=0xFFFFFFFF,
    reverse_input=True,
    reverse_output=True,
)

# 0x77 0xa5 0x65
def crc_check(data: bytes, type='CRC32' , dll_path=None, warpper_path=None):
    type = type.upper()
    if type == 'CRC32':
        calculator = Calculator(Crc32.CRC32)
    if type == 'CRC32_DLL':
        raise NotImplementedError("CRC32_DLL is not implemented in this version.")
        calculator = Calculator(COSTUME_CRC32_POLYNOMIAL)
        # return crc32_dll(dll_path, data, warpper_path)
    elif type == 'CRC16_CCITT_FALSE':
        calculator = Calculator(CCITT_FALSE)
    elif type == 'CRC16_CCITT':
        calculator = Calculator(CCITT)
        

        
    return calculator.checksum(data)

@lru_cache(maxsize=10)
def _load_hex(filename):
    ih = IntelHex(filename)
    segments = ih.segments()

    start, end_exclusive = segments[0]
    data = bytes(ih.tobinarray(start=start, end=end_exclusive - 1))
    return start, data

def get_data_from_file(filename, segIdx):
    """
    Retrieves data from a file.
    Args:
        filename (str): The path to the file.
        segIdx (int): The index of the segment to retrieve data from.
    Returns:
        tuple: A tuple containing the starting address of the segment and the binary data.
        (startAddr, data)
    """
    # # ih = _load_hex(filename)
    # ih = IntelHex(filename)
    # segments = ih.segments()
    # return segments[segIdx][0],ih.tobinstr(segments[segIdx][0], segments[segIdx][1]-1) # -1 because the end is inclusive

    # ih = _load_hex(filename)
    # segments = ih.segments()

    # start, end_exclusive = segments[segIdx]
    # data = ih.tobinarray(start=start, end=end_exclusive - 1)

    return _load_hex(filename)

def get_srec_data_from_file(filename):
    """
    Retrieves data from a file.
    Args:
        filename (str): The path to the file.
    Returns:
        tuple: A tuple containing the starting address of the segment and the binary data.
        (startAddr, data)
    """
    with open(filename, 'r', encoding='utf-8') as file:
        s19_data = file.read()
    # 解析 S19 数据
    binary = bincopy.BinFile()
    binary.add_srec(s19_data)

    merged_data = binary.as_binary(minimum_address=None, padding=b'\x00')
    start_address = binary.minimum_address
    hex_data = merged_data
    return start_address, hex_data

def crc32_dll(dll_path: str, file_data: bytes, warpper_path: str = None, block_size: int = 128):
    # add dllpath to system path
    os.environ['PATH'] = os.path.dirname(dll_path) + ";" + os.environ['PATH']

    if warpper_path is not None:
        # 加载桥接 DLL
        wrapper = cdll.LoadLibrary(warpper_path)

        # 设置接口函数参数类型和返回值
        wrapper.LoadRealCrc32Dll.argtypes = [c_char_p]
        wrapper.LoadRealCrc32Dll.restype = c_bool

        wrapper.CRC32_create.restype = c_void_p
        wrapper.CRC32_destroy.argtypes = [c_void_p]
        wrapper.CRC32_calc.argtypes = [c_void_p, POINTER(c_ubyte), c_uint, c_uint, c_bool]
        wrapper.CRC32_calc.restype = c_uint

        dll_path_bytes = dll_path.encode('utf-8')
        # 第一步：加载原始 CRC32.dll（必须！）
        if not wrapper.LoadRealCrc32Dll(dll_path_bytes):
            raise RuntimeError("Failed to load CRC32.dll")

        # 第二步：创建 CRC32 实例
        obj = wrapper.CRC32_create()
        if not obj:
            raise RuntimeError("Failed to create CRC32 instance")
        
        crc_result = 0xFFFFFFFF 

        for i in range(0, len(file_data), block_size):
            # first block, calculate CRC
            block_data = file_data[i:i + block_size]
            accrual_size = len(block_data)
            buf = (c_ubyte * accrual_size)(*block_data)
            if i == 0:
                crc_result = wrapper.CRC32_calc(obj, buf, accrual_size, 0xFFFFFFFF, True)
            else:
                crc_result = wrapper.CRC32_calc(obj, buf, accrual_size, crc_result, False)
            # print(f"Processing block {i // block_size + 1}, size: {accrual_size} bytes, CRC: {crc_result:#010x}")


        # 第五步：清理（如果你实现了 destroy，否就跳过）
        wrapper.CRC32_destroy(obj)


    return crc_result



if __name__ == "__main__":
    # # 读取 S19 文件
    # filePath = r"E:\\code\\tempTest\\python_js_template\\src\\backEnd\\flashHexFile\\FlashDriver_TC277.s19"
    # with open(filePath, 'r', encoding='utf-8') as file:
    #     s19_data = file.read()
    # # 解析 S19 数据
    # binary = bincopy.BinFile()
    # binary.add_srec(s19_data)


    # merged_data = binary.as_binary(minimum_address=None, padding=b'\x00')
    # start_address = hex(binary.minimum_address)
    # total_length = len(merged_data)
    # hex_data = merged_data.hex()

    # print(f"start_address: {start_address} total_length: {total_length}")
    # print(f"hex_data: {hex_data}")


    # binAddr, binData = get_data_from_file('E:\\code\\tempTest\\python_js_template\\src\\backEnd\\flashHexFile\\FlashDriver_TC277.s19', 0)
    # ih = IntelHex()
    # ih.loadhex('')
    # print(hex(len(binData)))
    # print(hex(binAddr))
    # print(hex(crc_check(binData)))

    
    import time
    for i in range(10):
        start = time.time()
        filePath = r"E:\code\flash_test\flexFlowServerDev\project\20260121_BYD_PV4\productionsw.hex"
        startAddr, hexData = get_data_from_file(filePath, 0)
        print(f"startAddr: {hex(startAddr)}, time: {time.time() - start:.2f} seconds")