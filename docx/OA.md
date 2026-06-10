# OA 标定

## 总纲
OA标定是通过解析DBC，传出以下Can id对应的变量。
```
_OA_CAN_IDS = {
    1502: "RR",   # FrameHeader_RR
    1470: "RL",   # FrameHeader_RL
    1454: "FR",   # FrameHeader_FR
    1486: "FL",   # FrameHeader_FL
}
```

## 传出变量（包含关键字即可）
- CALIB_RadarStatus
- CALIB_FinalCalibState
- YawMountAngle
- PitchMountAngle
- CALIB_EleOffset
- CALIB_AziOffset
- MountPosX
- MountPosZ
- MountPosY
