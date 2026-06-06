# Calibration 标定

## 静态标定基本配置(大端)
### A
左前雷达
- 上位机发送 CAN ID=0x61, Data=02
- ECU 响应：ID=0x71, Data=02 01
  
右前雷达
- 发送 CAN ID=0x261, Data=02
- ECU 响应：ID=0x271, Data=02 01

左后雷达
- 上位机发送 CAN ID=0x461, Data=02
- ECU 响应：ID=0x471, Data=02 01
  
右后雷达
- 发送 CAN ID=0x661, Data=02
- ECU 响应：ID=0x671, Data=02 01

- if 没有合法响应   持续5s，等待ECU响应

### B
- ECU 发送响应：Data=04 xx xx xx xx xx xx xx xx xx
  
自04后开始，按顺序解析,大端字节序解析
#### 标定结果 占用2字节
    0x01：结果合格
    0x02：结果不合格
    0x03：标定进行中

#### 标定错误码 占用2字节
    0：标定进行中无错误码
    1：标定未成功触发
    2：flash存储失败
    3：车速超限
    4：角度过大
    5：角度过小
    6：目标数异常
    7：超时
    8：执行成功
    9:未找到标定板

以下角度为可选，debug用
#### 水平偏差角度 占用4字节
实际值=0.01x

#### 垂直偏差角度 占用4字节
实际值=0.01x 

## 标定外参配置(大端)
### A
左前雷达
下发参数
- 发送 CAN ID=0x60, Data=01 xx xx
- ECU 响应：ID=0x70, Data=01 01

清除参数（清除OA）
- 发送 CAN ID=0x60, Data=02
- ECU 响应：ID=0x70, Data=02 01
  
右前雷达
下发参数
- 发送 CAN ID=0x260, Data=01 xx xx xx xx xx xx xx xx
- ECU 响应：ID=0x270, Data=01 01

清除参数（清除OA）
- 发送 CAN ID=0x260, Data=02
- ECU 响应：ID=0x270, Data=02 01

左后雷达
下发参数
- 发送 CAN ID=0x460, Data=01 xx xx
- ECU 响应：ID=0x470, Data=01 01

清除参数（清除OA）
- 发送 CAN ID=0x460, Data=02
- ECU 响应：ID=0x470, Data=02 01
  
右后雷达
下发参数
- 发送 CAN ID=0x660, Data=01 xx xx xx xx xx xx xx xx
- ECU 响应：ID=0x670, Data=01 01

清除参数（清除OA）
- 发送 CAN ID=0x660, Data=02
- ECU 响应：ID=0x670, Data=02 01

- if 没有合法响应   持续3s，等待ECU响应

自01后开始，按顺序解析
### 标定参数表
| 占用字节数 | 字段名称 | 英文标识 | 数据类型 | 单位 | 说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 4 | 可通行高度(车辆高度) | vehicle_height | float | m | 可通行高度(车辆高度)，单位米 |
| 4 | 雷达纵向安装偏差 | radar_x_offset | float | m | 雷达相对车辆后轴中心的纵向偏差，向前为正 |
| 4 | 雷达横向安装偏差 | radar_y_offset | float | m | 雷达相对车辆后轴中心的横向偏差，左正右负 |
| 4 | 雷达对地安装高度 | radar_z_offset | float | m | 雷达对地安装高度，向上为正 |
| 4 | 雷达水平偏转角 | radar_yaw_angle | float | ° | 雷达相对主车坐标系的水平偏转角，水平向右为正 |
| 4 | 雷达俯仰角 | radar_pitch_angle | float | ° | 标定完成后雷达相对主车坐标系的俯仰角，竖直向上偏转为正 |
| 4 | 雷达横滚角 | radar_roll_angle | float | ° | 雷达相对主车坐标系的横滚角，绕x轴顺时针为正 |
| 35 | 保留 | reserve | - | - | - |

Data=01 + 标定参数表 =64字节

-----


静态标定，标定外参，如果有多余比特，不处理。
