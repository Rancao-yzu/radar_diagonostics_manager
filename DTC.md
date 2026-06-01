# DTC 消息定义

所有雷达节点的 **相同 GROUP 消息结构是完全一样的**，只是字段名称后缀和 CAN ID 不同。

---

# 消息结构汇总

| 节点 | GROUP1 (带帧头) | GROUP2 (纯DTC) |
|------|----------------|----------------|
| **FL** (左前) | CAN ID: 0x400 | CAN ID: 0x401 |
| **FR** (右前) | CAN ID: 0x402 | CAN ID: 0x403 |
| **RL** (左后) | CAN ID: 0x404 | CAN ID: 0x405 |
| **RR** (右后) | CAN ID: 0x406 | CAN ID: 0x407 |

## DTC_GROUP1_FL

- **CAN ID**: 0x400
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: FL
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte54 ~ Byte57 | 4 | DTC_TimeStamp_FL | 无符号32位 | 4294967295 | 439 | 32 |
| Byte53 | 1 | DTC_Number_FL | 无符号8位 | 255 | 431 | 8 |
| Byte52 | 1 | DTC_MessageType_FL | 无符号8位 | 255 | 423 | 8 |
| Byte50 ~ Byte51 | 2 | DTC_Frame_Number_FL | 无符号16位 | 65535 | 407 | 16 |
| Byte49 | 1 | DTC_Entry5_status_mask_FL | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry5_dtc_type_FL | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry5_dtc_num_FL | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry5_change_ts_FL | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry4_status_mask_FL | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry4_dtc_type_FL | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry4_dtc_num_FL | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry4_change_ts_FL | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry3_status_mask_FL | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry3_dtc_type_FL | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry3_dtc_num_FL | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry3_change_ts_FL | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry2_status_mask_FL | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry2_dtc_type_FL | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry2_dtc_num_FL | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry2_change_ts_FL | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry1_status_mask_FL | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry1_dtc_type_FL | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry1_dtc_num_FL | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry1_change_ts_FL | 无符号32位 | 4294967295 | 7 | 32 |



## DTC_GROUP2_FL

- **CAN ID**: 0x401
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: FL
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte59 | 1 | DTC_Entry9_status_mask_FL | 无符号8位 | 255 | 479 | 8 |
| Byte58 | 1 | DTC_Entry9_dtc_type_FL | 无符号8位 | 255 | 471 | 8 |
| Byte54 ~ Byte57 | 4 | DTC_Entry9_dtc_num_FL | 无符号32位 | 4294967295 | 439 | 32 |
| Byte50 ~ Byte53 | 4 | DTC_Entry9_change_ts_FL | 无符号32位 | 4294967295 | 407 | 32 |
| Byte49 | 1 | DTC_Entry8_status_mask_FL | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry8_dtc_type_FL | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry8_dtc_num_FL | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry8_change_ts_FL | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry7_status_mask_FL | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry7_dtc_type_FL | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry7_dtc_num_FL | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry7_change_ts_FL | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry6_status_mask_FL | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry6_dtc_type_FL | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry6_dtc_num_FL | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry6_change_ts_FL | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry11_status_mask_FL | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry11_dtc_type_FL | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry11_dtc_num_FL | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry11_change_ts_FL | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry10_status_mask_FL | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry10_dtc_type_FL | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry10_dtc_num_FL | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry10_change_ts_FL | 无符号32位 | 4294967295 | 7 | 32 |

---


## DTC_GROUP1_FR

- **CAN ID**: 0x402
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: Vector__XXX
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte54 ~ Byte57 | 4 | DTC_TimeStamp_FR | 无符号32位 | 4294967295 | 439 | 32 |
| Byte53 | 1 | DTC_Number_FR | 无符号8位 | 255 | 431 | 8 |
| Byte52 | 1 | DTC_MessageType_FR | 无符号8位 | 255 | 423 | 8 |
| Byte50 ~ Byte51 | 2 | DTC_Frame_Number_FR | 无符号16位 | 65535 | 407 | 16 |
| Byte49 | 1 | DTC_Entry5_status_mask_FR | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry5_dtc_type_FR | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry5_dtc_num_FR | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry5_change_ts_FR | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry4_status_mask_FR | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry4_dtc_type_FR | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry4_dtc_num_FR | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry4_change_ts_FR | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry3_status_mask_FR | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry3_dtc_type_FR | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry3_dtc_num_FR | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry3_change_ts_FR | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry2_status_mask_FR | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry2_dtc_type_FR | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry2_dtc_num_FR | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry2_change_ts_FR | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry1_status_mask_FR | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry1_dtc_type_FR | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry1_dtc_num_FR | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry1_change_ts_FR | 无符号32位 | 4294967295 | 7 | 32 |

---

## DTC_GROUP2_FR

- **CAN ID**: 0x403
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: Vector__XXX
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte59 | 1 | DTC_Entry9_status_mask_FR | 无符号8位 | 255 | 479 | 8 |
| Byte58 | 1 | DTC_Entry9_dtc_type_FR | 无符号8位 | 255 | 471 | 8 |
| Byte54 ~ Byte57 | 4 | DTC_Entry9_dtc_num_FR | 无符号32位 | 4294967295 | 439 | 32 |
| Byte50 ~ Byte53 | 4 | DTC_Entry9_change_ts_FR | 无符号32位 | 4294967295 | 407 | 32 |
| Byte49 | 1 | DTC_Entry8_status_mask_FR | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry8_dtc_type_FR | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry8_dtc_num_FR | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry8_change_ts_FR | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry7_status_mask_FR | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry7_dtc_type_FR | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry7_dtc_num_FR | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry7_change_ts_FR | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry6_status_mask_FR | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry6_dtc_type_FR | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry6_dtc_num_FR | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry6_change_ts_FR | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry11_status_mask_FR | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry11_dtc_type_FR | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry11_dtc_num_FR | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry11_change_ts_FR | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry10_status_mask_FR | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry10_dtc_type_FR | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry10_dtc_num_FR | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry10_change_ts_FR | 无符号32位 | 4294967295 | 7 | 32 |

---





## DTC_GROUP1_RL

- **CAN ID**: 0x404
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: RL
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte54 ~ Byte57 | 4 | DTC_TimeStamp_RL | 无符号32位 | 4294967295 | 439 | 32 |
| Byte53 | 1 | DTC_Number_RL | 无符号8位 | 255 | 431 | 8 |
| Byte52 | 1 | DTC_MessageType_RL | 无符号8位 | 255 | 423 | 8 |
| Byte50 ~ Byte51 | 2 | DTC_Frame_Number_RL | 无符号16位 | 65535 | 407 | 16 |
| Byte49 | 1 | DTC_Entry5_status_mask_RL | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry5_dtc_type_RL | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry5_dtc_num_RL | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry5_change_ts_RL | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry4_status_mask_RL | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry4_dtc_type_RL | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry4_dtc_num_RL | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry4_change_ts_RL | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry3_status_mask_RL | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry3_dtc_type_RL | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry3_dtc_num_RL | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry3_change_ts_RL | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry2_status_mask_RL | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry2_dtc_type_RL | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry2_dtc_num_RL | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry2_change_ts_RL | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry1_status_mask_RL | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry1_dtc_type_RL | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry1_dtc_num_RL | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry1_change_ts_RL | 无符号32位 | 4294967295 | 7 | 32 |

---




## DTC_GROUP2_RL

- **CAN ID**: 0x405
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: RL
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte59 | 1 | DTC_Entry9_status_mask_RL | 无符号8位 | 255 | 479 | 8 |
| Byte58 | 1 | DTC_Entry9_dtc_type_RL | 无符号8位 | 255 | 471 | 8 |
| Byte54 ~ Byte57 | 4 | DTC_Entry9_dtc_num_RL | 无符号32位 | 4294967295 | 439 | 32 |
| Byte50 ~ Byte53 | 4 | DTC_Entry9_change_ts_RL | 无符号32位 | 4294967295 | 407 | 32 |
| Byte49 | 1 | DTC_Entry8_status_mask_RL | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry8_dtc_type_RL | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry8_dtc_num_RL | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry8_change_ts_RL | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry7_status_mask_RL | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry7_dtc_type_RL | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry7_dtc_num_RL | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry7_change_ts_RL | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry6_status_mask_RL | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry6_dtc_type_RL | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry6_dtc_num_RL | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry6_change_ts_RL | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry11_status_mask_RL | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry11_dtc_type_RL | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry11_dtc_num_RL | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry11_change_ts_RL | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry10_status_mask_RL | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry10_dtc_type_RL | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry10_dtc_num_RL | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry10_change_ts_RL | 无符号32位 | 4294967295 | 7 | 32 |

---


## DTC_GROUP1_RR

- **CAN ID**: 0x406
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: RR
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte54 ~ Byte57 | 4 | DTC_TimeStamp_RR | 无符号32位 | 4294967295 | 439 | 32 |
| Byte53 | 1 | DTC_Number_RR | 无符号8位 | 255 | 431 | 8 |
| Byte52 | 1 | DTC_MessageType_RR | 无符号8位 | 255 | 423 | 8 |
| Byte50 ~ Byte51 | 2 | DTC_Frame_Number_RR | 无符号16位 | 65535 | 407 | 16 |
| Byte49 | 1 | DTC_Entry5_status_mask_RR | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry5_dtc_type_RR | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry5_dtc_num_RR | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry5_change_ts_RR | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry4_status_mask_RR | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry4_dtc_type_RR | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry4_dtc_num_RR | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry4_change_ts_RR | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry3_status_mask_RR | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry3_dtc_type_RR | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry3_dtc_num_RR | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry3_change_ts_RR | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry2_status_mask_RR | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry2_dtc_type_RR | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry2_dtc_num_RR | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry2_change_ts_RR | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry1_status_mask_RR | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry1_dtc_type_RR | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry1_dtc_num_RR | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry1_change_ts_RR | 无符号32位 | 4294967295 | 7 | 32 |

---


## DTC_GROUP2_RR

- **CAN ID**: 0x407
- **帧类型**: CANFD扩展帧
- **总长度**: 64字节
- **DBC_TRANSMITTER**: RR
- **DBC_MESSAGE_COMMENT**: 

| 字节偏移位置 | 占用字节数 | 字段名称 | 数据类型 | 最大值 | 起始位 | 位长度 |
|------------|------------|----------|----------|--------|--------|--------|
| Byte59 | 1 | DTC_Entry9_status_mask_RR | 无符号8位 | 255 | 479 | 8 |
| Byte58 | 1 | DTC_Entry9_dtc_type_RR | 无符号8位 | 255 | 471 | 8 |
| Byte54 ~ Byte57 | 4 | DTC_Entry9_dtc_num_RR | 无符号32位 | 4294967295 | 439 | 32 |
| Byte50 ~ Byte53 | 4 | DTC_Entry9_change_ts_RR | 无符号32位 | 4294967295 | 407 | 32 |
| Byte49 | 1 | DTC_Entry8_status_mask_RR | 无符号8位 | 255 | 399 | 8 |
| Byte48 | 1 | DTC_Entry8_dtc_type_RR | 无符号8位 | 255 | 391 | 8 |
| Byte44 ~ Byte47 | 4 | DTC_Entry8_dtc_num_RR | 无符号32位 | 4294967295 | 359 | 32 |
| Byte40 ~ Byte43 | 4 | DTC_Entry8_change_ts_RR | 无符号32位 | 4294967295 | 327 | 32 |
| Byte39 | 1 | DTC_Entry7_status_mask_RR | 无符号8位 | 255 | 319 | 8 |
| Byte38 | 1 | DTC_Entry7_dtc_type_RR | 无符号8位 | 255 | 311 | 8 |
| Byte34 ~ Byte37 | 4 | DTC_Entry7_dtc_num_RR | 无符号32位 | 4294967295 | 279 | 32 |
| Byte30 ~ Byte33 | 4 | DTC_Entry7_change_ts_RR | 无符号32位 | 4294967295 | 247 | 32 |
| Byte29 | 1 | DTC_Entry6_status_mask_RR | 无符号8位 | 255 | 239 | 8 |
| Byte28 | 1 | DTC_Entry6_dtc_type_RR | 无符号8位 | 255 | 231 | 8 |
| Byte24 ~ Byte27 | 4 | DTC_Entry6_dtc_num_RR | 无符号32位 | 4294967295 | 199 | 32 |
| Byte20 ~ Byte23 | 4 | DTC_Entry6_change_ts_RR | 无符号32位 | 4294967295 | 167 | 32 |
| Byte19 | 1 | DTC_Entry11_status_mask_RR | 无符号8位 | 255 | 159 | 8 |
| Byte18 | 1 | DTC_Entry11_dtc_type_RR | 无符号8位 | 255 | 151 | 8 |
| Byte14 ~ Byte17 | 4 | DTC_Entry11_dtc_num_RR | 无符号32位 | 4294967295 | 119 | 32 |
| Byte10 ~ Byte13 | 4 | DTC_Entry11_change_ts_RR | 无符号32位 | 4294967295 | 87 | 32 |
| Byte9 | 1 | DTC_Entry10_status_mask_RR | 无符号8位 | 255 | 79 | 8 |
| Byte8 | 1 | DTC_Entry10_dtc_type_RR | 无符号8位 | 255 | 71 | 8 |
| Byte4 ~ Byte7 | 4 | DTC_Entry10_dtc_num_RR | 无符号32位 | 4294967295 | 39 | 32 |
| Byte0 ~ Byte3 | 4 | DTC_Entry10_change_ts_RR | 无符号32位 | 4294967295 | 7 | 32 |

---



解析方法：
struct.unpack('>', data[0:x])[0]