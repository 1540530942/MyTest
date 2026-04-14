param(
  [string]$MqttHost = "127.0.0.1",
  [int]$MqttPort = 1883,
  [string]$DeviceId = "desk-led",
  [string]$ArduinoPort = "COM3",
  [int]$ArduinoBaudrate = 115200
)

$env:MQTT_HOST = $MqttHost
$env:MQTT_PORT = "$MqttPort"
$env:DEVICE_ID = $DeviceId
$env:ARDUINO_PORT = $ArduinoPort
$env:ARDUINO_BAUDRATE = "$ArduinoBaudrate"

python .\bridge.py
