# 时间同步帧结构（流程说明）

**CANID:** 0x0400  
**帧类型:** CANFD 扩展帧  
**总长度:** 64 字节(大端)

---
DBC 消息定义（Motorola 大端序）：
- TSYNC_FL (0x040): 前左轮时间同步
- TSYNC_FR (0x041): 前右轮时间同步
- TSYNC_RL (0x042): 后左轮时间同步
- TSYNC_RR (0x043): 后右轮时间同步


## 数据组装 / 解析流程（按字节顺序）

| 信号 | start_bit\|length | 位范围 | 字节范围 |
|------|-------------------|--------|---------|
| **TSYNC_CRC_RR** | **7\|16** | **7..0 + 15..8** | **Byte 0–1**  |
| TSYNC_GT_Nanoseconds_RR | 23\|32 | 23..0 + ... | Byte 2–5 |
| TSYNC_GT_Seconds_RR | 55\|32 | 55..24 | Byte 6–9 |
| TSYNC_message_type_RR | 87\|8 | 87..80 | Byte 10 |
| TSYNC_SequenceCounter_RR | 95\|8 | 95..88 | Byte 11 |
| TSYNC_Reserved_RR | 103\|24 | 103..80 | Byte 12–14 |
| TSYNC_Status_RR | 127\|8 | 127..120 | Byte 15 |

其余 Byte 16–63 未使用。

---