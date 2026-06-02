
## Flash 分区表

| Block Name | Block ID | Size in KB (code + rodata) | Mode | encrypted | signed | Flash Block # | Address | Comment |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| Boot Manager | BTMG | 128 | exe | YES | TI | block 0-1 | 0x00'0000-0x01'FFFF | Boot Manager |
| Platform Boot | PFBT | 192 | exe | YES | BOSCH | block 2-4 | 0x02'0000-0x04'FFFF | PF Boot在工厂端使用，可以用来刷写Customer Boot, Customer App |
| Customer Boot | CUBT | 256 | exe | YES | BOSCH | block 5-8 | 0x05'0000-0x08'FFFF | FBL for customer |
| Customer APP | CUAP | 2048 | exe | YES | BOSCH | block 9-40 | 0x09'0000-0x28'FFFF | Application image, include MSS, DSS, RSS |
| Production App | PDAP | 0 | exe | NO | NO | block 9-40 | 0x09'0000-0x28'FFFF | 用于在售工厂端做无线数据标定，硬件测试等 |
| Reserve | | 256 | | | | block 41-44 | 0x29'0000-0x2C'FFFF | Reserve for APP |
| HSM | HSM_ | 256 | exe | YES | TI | block 45-48 | 0x2D'0000-0x30'FFFF | |
| Weifu Data | WFDA | 64 | data | NO | NO | block 49 | 0x31'0000-0x31'FFFF | Hardware SN, PCB SN |
| Customer Data | CUDA | 64 | data | YES | BOSCH | block 50 | 0x32'0000-0x32'FFFF | Application parameters such as VKL |
| Calibration Data | CLDA | 64 | data | NO | BOSCH | block 51 | 0x33'0000-0x33'FFFF | Antenna calibration data |
| Reserve | | 64 | | | | block52 | 0x34'0000-0x34'FFFF | |
| NvM | | 512 | data | NO | NO | block 53-60 | 0x35'0000-0x3C'FFFF |  |
| Reserve | | 64 | | | | block 61 | 0x3D'0000-0x3D'FFFF | |
| SecureData | | 12K | data | NO | NO | block 62 | 0x3E'0000-0x3E'FFFF | 第一个4K用来存放 lifecycle |
| | | | | | | 0x3E'1000-0x3E'1FFF | 第二个4K用来存放密钥，该密钥给客户项目预留 |
| | | | | | | 0x3E'2000-0x3E'2FFF | 第三个4K用来存放工厂初始数据，实际大小为128bytes |
| Reserve | | 52K | | | | block 62 | 0x3E'3000-0x3E'FFFF | 未使用 |
| Reserve | | 64 | | | | block 63 | 0x3F'0000-0x3F'FFFF | Reserve for future blocks |

---

## 关键地址速查表

| 用途 | 起始地址 | 结束地址 | 大小 |
|:---|:---|:---|:---|
| Boot Manager | 0x00'0000 | 0x01'FFFF | 128 KB |
| Platform Boot (PFBoot) | 0x02'0000 | 0x04'FFFF | 192 KB |
| Customer Boot | 0x05'0000 | 0x08'FFFF | 256 KB |
| **Customer APP** | **0x09'0000** | **0x28'FFFF** | **2048 KB (2 MB)** |
| Reserve for APP | 0x29'0000 | 0x2C'FFFF | 256 KB |
| HSM | 0x2D'0000 | 0x30'FFFF | 256 KB |
| Weifu Data (SN) | 0x31'0000 | 0x31'FFFF | 64 KB |
| Customer Data (参数) | 0x32'0000 | 0x32'FFFF | 64 KB |
| Calibration Data | 0x33'0000 | 0x33'FFFF | 64 KB |
| NvM | 0x35'0000 | 0x3C'FFFF | 512 KB |
| SecureData | 0x3E'0000 | 0x3E'FFFF | 64 KB (实际使用12KB) |

---
