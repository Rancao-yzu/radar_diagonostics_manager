# OTA 升级
- 提供Hex文件
- OTA 升级方案基于 PFBoot 实现客户App的升级
- 芯片上电后依次执行两级 Boot，每一级 Boot 完成自身职责后跳转到下一级，最终进入客户应用 CUAP。
- OTA 升级流程中，BM 检测到上位机发来的 FORCEJUMP 安全帧后，会停留在PFboot不再跳转到 APP，接收上位机的UDS刷写命令。


## A   进入 PFBoot OTA 模式
#### A1：扩展会话切换
- 请求 [A1] 02 10 03
- 响应 50 03 ...

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
12.5811,tx,74C,8,02 10 03 00 00 00 00 00,OK
12.5831,rx,7CC,8,06 50 03 00 32 01 F4 00,OK
```
02 = 数据长度 2 字节(有效数据长度)

#### A2：ECU复位
- 请求 [A2] 02 11 01
- 响应 51 01
  
ECU 复位中 100-200ms

#### A3：发送安全帧
- 上位机在 ECU 复位后 40ms 内开始以 1ms 周期发送安全帧, 持续 3s(建议)。
- 安全帧：专用 CAN-FD 扩展帧 ID (0x190C8532)：与日常诊断报文 ID 完全隔离, 避免误触发。  
- FORCEJUMP + 0xA5B6C7D8：重复发送，直到PFBoot识别，PFBoot 识别FORCEJUMP后, 会停留在 PFboot 状态, 等待上位机的 UDS 刷写命令。

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
6.9722,tx,190C8532,16,02 10 60 46 4F 52 43 45 4A 55 4D 50 A5 B6 C7 D8,OK
```

## B  维持扩展会话
- 请求 [B1] 02 10 03
- 响应 50 03
  
- 每1000ms（1秒）发送一次3E 80，可以持续维持扩展会话，确保整个固件下载过程中会话不会中断。
- 服务器不发送任何响应。

## C  擦除目标区域
- 请求 [C] 31 01 FF 00 +0x 90 00 00 + 长度
- 响应 71 01 FF 00 00

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
12.6708,tx,74C,16,00 0C 31 01 FF 00 00 09 00 00 00 20 00 00 00 00,OK
12.6731,rx,7CC,8,03 7F 31 78 00 00 00 00,OK
17.6631,rx,7CC,8,03 7F 31 78 00 00 00 00,OK
19.6561,rx,7CC,8,05 71 01 FF 00 10 00 00,OK
```

- NRC 0x78 是 UDS 中常见的延迟响应机制，防止请求方超时。
- 标准规定 ECU 可以在收到复杂请求时回复 0x78，表示不要放弃，继续等待。
- 最终正响应，此时距离请求已经过去 约 7 秒

## D  下载与传输
#### D1：下载固件
- 请求 [D1] 34 00 44 + 0x90000 + 长度
- 响应 74 20 0F FA (MaxBlock = 4090)

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
19.6594,tx,74C,16,00 0B 34 00 44 00 09 00 00 00 20 00 00 00 00 00,OK
19.6612,rx,7CC,8,04 74 20 0F FF 00 00 00,OK

```

#### D2：传输数据
- 请求 [D2] 36 SN [data...]
- 响应 76 SN

```example 例如SN = 0x01
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
19.6753,tx,74C,64,1F FF 36 01 [data...]
19.6761,rx,7CC,8,30 00 00 00 00 00 00 00,OK #流控制帧

[data...][data...][data...][data...][data...]...
19.7851,rx,7CC,8,02 76 01 00 00 00 00 00,OK
```

#### D3：传输结束
- 请求 [D3] 01 37 (TransferExit)
- 响应 77

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
77.5856,tx,74C,8,01 37 00 00 00 00 00 00,OK
77.5891,rx,7CC,8,01 77 00 00 00 00 00 00,OK
```

## E 完整性校验与激活

#### E1：CRC32 校验
- 请求 [E1] 31 01 02 12 + CRC32
- 响应 71 01 02 12 00

```example
Timestamp,Tx/Rx,ID,DLC,MSG,STATUS
77.5924,tx,74C,12,00 08 31 01 02 12 23 E1 6E BA 00 00,OK
77.6081,rx,7CC,8,03 7F 31 78 00 00 00 00,OK
82.0111,rx,7CC,8,06 71 01 02 12 10 00 00,OK
```

#### E2：Dependency Check
- 请求 [E2] 31 01 02 05
- 响应 71 01 02 05 00

#### E3：Reset
- 请求 [E3] 02 11 01
- 响应 51 01
  
上位机在发送 11 01 后，停止之前周期性发送的 3E 80（在线保持）命令

