import can
import time
import struct
from threading import Thread, Event

# 参数数据格式（大端序，与主程序calibration.py保持一致）
PARAM_STRUCT = struct.Struct('>iiiiiii')

class RadarECUSimulator:
    def __init__(self, bus):
        self.bus = bus
        self.running = Event()
        self.running.set()
        
        # 雷达CAN ID配置（与config_c.ini及version_query.py保持一致）
        self.radar_configs = {
            'FL': {
                'name': '左前',
                'static_send': 0x61, 'static_recv': 0x71,
                'param_send': 0x60, 'param_recv': 0x70,
                'ver_req': 0x74F, 'ver_resp': 0x74E,
            },
            'FR': {
                'name': '右前',
                'static_send': 0x261, 'static_recv': 0x271,
                'param_send': 0x260, 'param_recv': 0x270,
                'ver_req': 0x78F, 'ver_resp': 0x78E,
            },
            'RL': {
                'name': '左后',
                'static_send': 0x461, 'static_recv': 0x471,
                'param_send': 0x460, 'param_recv': 0x470,
                'ver_req': 0x72F, 'ver_resp': 0x72E,
            },
            'RR': {
                'name': '右后',
                'static_send': 0x661, 'static_recv': 0x671,
                'param_send': 0x660, 'param_recv': 0x670,
                'ver_req': 0x76F, 'ver_resp': 0x76E,
            },
        }

        # 静态标定结果配置
        self.calibration_results = {
            key: {
                'cal_result': 0x01,       # 0x01：结果合格
                'error_code': 0x08        # 0x08：执行成功
            } for key in self.radar_configs
        }

        # 版本号配置（模拟值，ASCII字符串）
        self.version_strings = {
            key: {'software': '001000505DSW1.11', 'hardware': '001000505DHW1.11'}
            for key in self.radar_configs
        }
        
    def build_calibration_response(self, radar_side='FL'):
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
        
        if len(data) < 28:  # 至少需要前28字节（7个int32）
            print(f"  [错误] 外参数据长度不足: {len(data)}字节, 需要至少28字节")
            return
        
        # 解析7个int32（大端），与主程序PARAM_STRUCT一致
        vh, x, y, z, yaw, pitch, roll = PARAM_STRUCT.unpack_from(data, 0)
        
        # 还原实际值：高度/偏移放大1000倍，角度放大10000倍
        vehicle_height = vh / 1000.0
        radar_x_offset = x / 1000.0
        radar_y_offset = y / 1000.0
        radar_z_offset = z / 1000.0
        radar_yaw_angle = yaw / 10000.0
        radar_pitch_angle = pitch / 10000.0
        radar_roll_angle = roll / 10000.0
        
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
        for key, cfg in self.radar_configs.items():
            if msg.arbitration_id == cfg['static_send'] and msg.data[0] == 0x02:
                print(f"\n收到{cfg['name']}雷达静态标定启动命令")
                
                # 1. 发送确认响应 02 01
                self.send_safe(cfg['static_recv'], bytes([0x02, 0x01]))
                
                # 2. 延时模拟标定过程
                time.sleep(0.1)
                
                # 3. 发送标定结果
                result_data = self.build_calibration_response(key)
                self.send_safe(cfg['static_recv'], result_data)
                
                result = self.calibration_results[key]
                print(f"  [预期] 标定结果=0x{result['cal_result']:04X}(结果合格), 错误码=0x{result['error_code']:04X}(执行成功)")
                break
    
    def handle_extrinsic_calibration(self, msg):
        """处理外参标定命令"""
        for cfg in self.radar_configs.values():
            if msg.arbitration_id != cfg['param_send']:
                continue
            
            if msg.data[0] == 0x01:
                print(f"\n收到{cfg['name']}雷达外参下发命令")
                
                # 总数据应该是64字节：0x01 + 63字节参数表
                if len(msg.data) >= 64:
                    # 跳过0x01，取后面的63字节参数表
                    received_params = msg.data[1:64]
                    print(f"  [接收] 外参原始数据({len(received_params)}字节)={received_params.hex()}")
                    
                    # 解析并打印外参
                    self.parse_and_print_extrinsic_params(cfg['name'], received_params)
                else:
                    print(f"  [警告] 外参数据长度不足: {len(msg.data)}字节, 需要64字节")
                    print(f"  [调试] 接收到的完整数据: {msg.data.hex()}")
                
                # 响应
                self.send_safe(cfg['param_recv'], bytes([0x01, 0x01]))
                print(f"  [响应] 外参下发成功")
                
            elif msg.data[0] == 0x02:
                print(f"\n收到{cfg['name']}雷达清除参数命令")
                self.send_safe(cfg['param_recv'], bytes([0x02, 0x01]))
                print(f"  [响应] 参数清除成功")
            break

    def handle_version_query(self, msg):
        """处理版本查询命令（与version_query.py协议一致）
        请求: 0x22 + DID(2字节大端) + 0x00*5
        响应: 0x62 + DID(2字节) + 有效长度 + ASCII版本字符串
        """
        DID_SOFTWARE = 0xFF00  # 软件版本
        DID_HARDWARE = 0xFF01  # 硬件版本

        for key, cfg in self.radar_configs.items():
            if msg.arbitration_id != cfg['ver_req']:
                continue

            if len(msg.data) < 3 or msg.data[0] != 0x22:
                print(f"  [警告] {cfg['name']}版本查询请求格式异常: {msg.data.hex()}")
                break

            did = (msg.data[1] << 8) | msg.data[2]
            if did == DID_SOFTWARE:
                ver_str = self.version_strings[key]['software']
            elif did == DID_HARDWARE:
                ver_str = self.version_strings[key]['hardware']
            else:
                print(f"  [警告] {cfg['name']}版本查询未知DID=0x{did:04X}")
                break

            ascii_bytes = ver_str.encode('ascii')
            valid_len = len(ascii_bytes)
            # 响应: 0x62 + DID(2字节) + 有效长度 + ASCII数据
            resp = bytes([0x62, (did >> 8) & 0xFF, did & 0xFF, valid_len]) + ascii_bytes
            self.send_safe(cfg['ver_resp'], resp)
            print(f"  [响应] {cfg['name']}版本查询 DID=0x{did:04X} 版本={ver_str}")
            break

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
                    
                    # 按配置的CAN ID分发：静态标定 / 参数标定 / 版本查询
                    static_send_ids = [cfg['static_send'] for cfg in self.radar_configs.values()]
                    param_send_ids = [cfg['param_send'] for cfg in self.radar_configs.values()]
                    ver_req_ids = [cfg['ver_req'] for cfg in self.radar_configs.values()]
                    if msg.arbitration_id in static_send_ids:
                        self.handle_static_calibration(msg)
                    elif msg.arbitration_id in param_send_ids:
                        self.handle_extrinsic_calibration(msg)
                    elif msg.arbitration_id in ver_req_ids:
                        self.handle_version_query(msg)
                        
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
