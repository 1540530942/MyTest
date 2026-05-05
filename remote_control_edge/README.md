# Remote Control Edge

本模块是远程遥控系统的边缘侧实现，负责连接 PC、Arduino/ESP32、串口、MQTT 和本地控制页面。它不作为公网 Web 服务独立部署，但属于平台远程遥控链路的一部分，必须按模块合入规范维护。

## 作用

- `pc_controller/`：本地 PC 控制服务和静态控制页，用于串口控制、测试公网指令和本地调试。
- `mqtt_serial_bridge/`：MQTT 到串口的桥接进程，用于把云端指令转发给边缘设备。
- `remote_connect_led/`：PlatformIO 固件工程，用于 Arduino/ESP32 侧 LED 或 GPIO 控制。

## 本地运行

PC 控制服务：

```powershell
cd remote_control_edge\pc_controller
python -m pip install -r requirements.txt
.\run_server.ps1
```

MQTT 串口桥：

```powershell
cd remote_control_edge\mqtt_serial_bridge
python -m pip install -r requirements.txt
.\run_bridge.ps1
```

固件工程：

```powershell
cd remote_control_edge\remote_connect_led
pio run
```

## 健康检查

该模块主要运行在边缘设备或开发 PC 上，不在平台 Compose 中提供统一容器健康检查。合入时必须至少完成以下验证之一：

- PC 控制服务能启动并打开本地页面。
- MQTT 串口桥能连接 MQTT Broker 和目标串口。
- PlatformIO 固件能编译通过。

## 数据与配置

- 串口号、设备 ID、MQTT 地址和 Token 应放在本地配置或环境变量中。
- 不得把真实 Token、设备密钥或公网控制口令提交到仓库。
- 日志文件属于运行产物，不应作为模块合入内容提交。

## 平台关系

平台注册项是 `remote-control`，云端目录是 `remote_control_cloud/`，边缘侧目录是 `remote_control_edge/`。两者共同构成远程遥控系统。

## 合入准则满足情况

- README 已建立。
- 模块边界已明确。
- 本地运行方式已记录。
- 健康检查替代验证方式已记录。
- 数据和密钥约束已记录。
