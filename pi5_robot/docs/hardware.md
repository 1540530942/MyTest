# 硬件接入

## 推荐 MVP 硬件

| 模块 | 推荐 |
| --- | --- |
| 主控 | Raspberry Pi 5 |
| 辅助控制器 | Arduino / Pico / ESP32 |
| 摄像头 | Pi Camera Module 3 或 USB 摄像头 |
| 底盘 | 两轮差速底盘 |
| 电机 | 带编码器直流减速电机 |
| 电机驱动 | TB6612FNG / BTS7960，按电机电流选择 |
| 距离传感器 | ToF / 超声波 / 红外 |
| 云台 | 二自由度舵机云台 |
| 急停 | 实体急停按钮 |

## 接线原则

```text
Camera
  |
  v
Raspberry Pi 5 -- USB Serial -- Arduino / Pico / ESP32
                                   |-- Motor driver
                                   |-- Servo pan/tilt
                                   |-- Encoder
                                   |-- E-stop input
```

## 电源原则

- 树莓派使用独立稳定供电。
- 电机使用独立电池或大电流电源。
- 树莓派与电机控制器必须共地。
- 舵机不要直接从树莓派 5V 引脚大量取电。
- 电机电源线路建议加保险丝。
- 低电量时禁止自动任务。

## 串口协议建议

固件占位见 [firmware/motor_controller/motor_controller.ino](../firmware/motor_controller/motor_controller.ino)。

建议命令保持短小、可校验、可拒绝：

```text
MOVE <direction> <distance_cm> <speed_mps>
ROTATE <angle_deg>
SERVO <pan_deg> <tilt_deg>
STOP
STATE
```
