import can
import time
import struct
from threading import Thread, Event

class RadarECUSimulator:
    def __init__(self, bus):
        self.bus = bus
        self.running = Event()
        self.running.set()
        
        # 静态标定结果配置
        self.calibration_results = {
            'left': {
                'cal_result': 0x01,       # 0x01：结果合格
                'error_code': 0x08        # 0x08：执行成功
            },
            'right': {
                'cal_result': 0x01,       # 0x01：结果合格
                'error_code': 0x08        # 0x08：执行成功
            }
        }
        
    def build_calibration_response(self, radar_side='left'):
        """
        构建静态标定响应数据
        格式：04 + 标定结果(2字节) + 标定错误码(2字节) = 5字节
        """
        result = self.calibration_results[radar_side]
        
        # 构建数据：04 + 标定结果(2字节大端) + 错误码(2字节大端)
        cal_result_bytes = result['cal_result'].to_bytes(2, byteorder='big')
        error_code_bytes = result['error_code'].to_bytes(2, byteorder='big')
        
        full_data = bytes([0x04]) + cal_result_bytes + error_code_bytes
        
        return full_data
    
    def parse_and_print_extrinsic_params(self, radar_side, data):
        """
        解析并打印接收到的外参数据
        data: 63字节的参数表（不包含0x01）
        """
        print(f"\n  ========== 接收到的{radar_side}雷达外参解析 ==========")
        
        if len(data) < 28:  # 至少需要前28字节（7个float）
            print(f"  [错误] 外参数据长度不足: {len(data)}字节, 需要至少28字节")
            return
        
        offset = 0
        vehicle_height = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_x_offset = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_y_offset = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_z_offset = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_yaw_angle = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_pitch_angle = struct.unpack_from('>f', data, offset)[0]
        offset += 4
        radar_roll_angle = struct.unpack_from('>f', data, offset)[0]
        
        print(f"  可通行高度(车辆高度): {vehicle_height:.3f} m")
        print(f"  雷达纵向安装偏差:     {radar_x_offset:.3f} m (向前为正)")
        print(f"  雷达横向安装偏差:     {radar_y_offset:.3f} m (左正右负)")
        print(f"  雷达对地安装高度:     {radar_z_offset:.3f} m (向上为正)")
        print(f"  雷达水平偏转角:       {radar_yaw_angle:.3f} ° (水平向右为正)")
        print(f"  雷达俯仰角:           {radar_pitch_angle:.3f} ° (竖直向上偏转为正)")
        print(f"  雷达横滚角:           {radar_roll_angle:.3f} ° (绕x轴顺时针为正)")
        
        print(f"  ====================================================\n")
        
    def send_safe(self, arbitration_id, data):
        """安全发送函数，补齐到12字节（Kvaser要求）"""
        if len(data) < 12:
            padded_data = data + bytes([0x00] * (12 - len(data)))
        else:
            padded_data = data[:12]
        
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=padded_data,
            is_extended_id=False,
            is_fd=True,
        )
        self.bus.send(msg)
        print(f"  [SEND] ID=0x{arbitration_id:X}, 原始({len(data)}字节)={data.hex()}")
        print(f"         补齐后({len(padded_data)}字节)={padded_data.hex()}")
        return padded_data
    
    def handle_static_calibration(self, msg):
        """处理静态标定命令"""
        if msg.arbitration_id == 0x61 and msg.data[0] == 0x02:
            print(f"\n收到左雷达静态标定启动命令")
            
            # 1. 发送确认响应 02 01
            self.send_safe(0x71, bytes([0x02, 0x01]))
            
            # 2. 延时模拟标定过程
            time.sleep(0.1)
            
            # 3. 发送标定结果
            result_data = self.build_calibration_response('left')
            self.send_safe(0x71, result_data)
            
            result = self.calibration_results['left']
            print(f"  [预期] 标定结果=0x{result['cal_result']:04X}(结果合格), 错误码=0x{result['error_code']:04X}(执行成功)")
            
        elif msg.arbitration_id == 0x261 and msg.data[0] == 0x02:
            print(f"\n收到右雷达静态标定启动命令")
            
            # 1. 发送确认响应 02 01
            self.send_safe(0x271, bytes([0x02, 0x01]))
            
            # 2. 延时模拟标定过程
            time.sleep(0.1)
            
            # 3. 发送标定结果
            result_data = self.build_calibration_response('right')
            self.send_safe(0x271, result_data)
            
            result = self.calibration_results['right']
            print(f"  [预期] 标定结果=0x{result['cal_result']:04X}(结果合格), 错误码=0x{result['error_code']:04X}(执行成功)")
    
    def handle_extrinsic_calibration(self, msg):
        """处理外参标定命令"""
        # 左雷达
        if msg.arbitration_id == 0x60:
            if msg.data[0] == 0x01:
                print(f"\n收到左雷达外参下发命令")
                
                # 总数据应该是64字节：0x01 + 63字节参数表
                if len(msg.data) >= 64:
                    # 跳过0x01，取后面的63字节参数表
                    received_params = msg.data[1:64]
                    print(f"  [接收] 外参原始数据({len(received_params)}字节)={received_params.hex()}")
                    
                    # 解析并打印外参
                    self.parse_and_print_extrinsic_params('左', received_params)
                else:
                    print(f"  [警告] 外参数据长度不足: {len(msg.data)}字节, 需要64字节")
                    print(f"  [调试] 接收到的完整数据: {msg.data.hex()}")
                
                # 响应
                self.send_safe(0x70, bytes([0x01, 0x01]))
                print(f"  [响应] 外参下发成功")
                
            elif msg.data[0] == 0x02:
                print(f"\n收到左雷达清除参数命令")
                self.send_safe(0x70, bytes([0x02, 0x01]))
                print(f"  [响应] 参数清除成功")
        
        # 右雷达
        elif msg.arbitration_id == 0x260:
            if msg.data[0] == 0x01:
                print(f"\n收到右雷达外参下发命令")
                
                # 总数据应该是64字节：0x01 + 63字节参数表
                if len(msg.data) >= 64:
                    # 跳过0x01，取后面的63字节参数表
                    received_params = msg.data[1:64]
                    print(f"  [接收] 外参原始数据({len(received_params)}字节)={received_params.hex()}")
                    
                    # 解析并打印外参
                    self.parse_and_print_extrinsic_params('右', received_params)
                else:
                    print(f"  [警告] 外参数据长度不足: {len(msg.data)}字节, 需要64字节")
                    print(f"  [调试] 接收到的完整数据: {msg.data.hex()}")
                
                # 响应
                self.send_safe(0x270, bytes([0x01, 0x01]))
                print(f"  [响应] 外参下发成功")
                
            elif msg.data[0] == 0x02:
                print(f"\n收到右雷达清除参数命令")
                self.send_safe(0x270, bytes([0x02, 0x01]))
                print(f"  [响应] 参数清除成功")
    
    def run(self):
        """主循环，监听CAN消息"""
        print("=" * 60)
        print("ECU模拟器已启动")
        print("等待CAN命令...")
        print("=" * 60)
        
        while self.running.is_set():
            try:
                msg = self.bus.recv(timeout=1.0)
                if msg:
                    print(f"\n[RECV] ID=0x{msg.arbitration_id:X}, Data({len(msg.data)}字节)={msg.data.hex()}")
                    
                    if msg.arbitration_id in [0x61, 0x261]:
                        self.handle_static_calibration(msg)
                    elif msg.arbitration_id in [0x60, 0x260]:
                        self.handle_extrinsic_calibration(msg)
                        
            except Exception as e:
                print(f"接收消息时出错: {e}")
                continue
    
    def stop(self):
        self.running.clear()
        print("\nECU模拟器已停止")

def main():
    try:
        # 配置CAN FD总线
        bus = can.Bus(
            interface="kvaser",
            channel=1,
            bitrate=500000,
            fd=True,
            data_bitrate=2000000
        )
        
        print("CAN FD总线连接成功 (channel=1, 500k/2M)")
        
        # 创建并运行模拟器
        simulator = RadarECUSimulator(bus)
        
        try:
            simulator.run()
        except KeyboardInterrupt:
            print("\n\n用户中断")
        finally:
            simulator.stop()
            bus.shutdown()
            
    except Exception as e:
        print(f"初始化CAN总线失败: {e}")

if __name__ == "__main__":
    main()
