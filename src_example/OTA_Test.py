import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))

import can 

import isotp

from uds import UdsMessage, IsoServices, Uds
import time

import multiprocessing as mp

def hybrid_delay_second(seconds):
    end_ns = time.perf_counter_ns() + int(seconds * 1e9)

    # 仅在非常早期让步一次
    remaining = end_ns - time.perf_counter_ns()
    if remaining > 5_000_000:  # >5ms
        time.sleep((remaining - 1_000_000) / 1e9)  # 睡到剩 1ms

    # 全忙等（关键）
    while time.perf_counter_ns() < end_ns:
        pass

isotpArgs={
                    "stmin": 0,
                    "override_receiver_stmin": 0.0001,
                    "blocksize": 8,
                    "wftmax": 0,
                    "tx_data_length": 8,
                    "tx_data_min_length": 8,
                    "tx_padding": 0,
                    "rx_flowcontrol_timeout": 5000,
                    "rx_consecutive_frame_timeout": 5000,
                    "max_frame_size": 8192,                 
                    "can_fd": True,                        
                    "bitrate_switch": True,                
                    "rate_limit_enable": False,             
                    "rate_limit_max_bitrate": 1000000,
                    "rate_limit_window_size": 0.2,     
                    "listen_mode": False,
                    "blocking_send": True,
                    "wait_func": hybrid_delay_second
                }

file_path = "data.appimage"

if __name__ == "__main__":
    canBus = can.interface.Bus(
                        interface="virtual", 
                        channel="0", 
                        bitrate=500000,
                        data_bitrate=2000000,
                        fd=True,
                        )

    try:
        canTp = isotp.CanStack(
                            bus=canBus,
                            address=isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x74c, rxid=0x7cc),
                            params=isotpArgs
                            )
        
        canTp.start()
        
        
        # example 直接通过CAN发送数据帧
        canUds = Uds(canTp)
        canMsg = can.Message(arbitration_id=0x190c8532, 
                          data=[0x02, 0x10, 0x60, 0x46, 0x4f, 0x52, 0x43, 0x45, 0x4a, 0x55, 0x4d, 0x50, 0xa5, 0xb6, 0xc7, 0xd8], 
                          is_extended_id=True,
                          bitrate_switch=True ,
                          is_fd=True,
                          )
        for _ in range(20):
            canBus.send(canMsg)
            time.sleep(0.1)
            
            
        
        # example 发送UDS请求并等待响应
        udsMsg = UdsMessage()
        udsMsg.create(0x10, [0x01, 0x02]) # 发送帧
        res,response = canUds.send(udsMsg,timeout=1, confirm=[0x50, 0x01]) # confirm 为确认帧
        print("Response:", res,response)
        
        
        
        
        # example 传输文件数据
        with open(file_path, "rb") as f:
            data = f.read()
            print("File content:", data)
        canUds.transferFile(fileData=data, # 传输文件数据
                            chunkSize=4096, # 每次传输的块大小
                            )
        

        canTp.stop()
    finally:
        canBus.shutdown()
