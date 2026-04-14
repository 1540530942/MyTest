# 个人域名网页在线可视化控制台

这是一个面向个人域名部署的远程设备控制网页工程。前端默认通过 HTTP `POST` 向你填写的远端服务地址发送 JSON 指令，适合后续接入 Arduino、ESP32、树莓派或任意自建后端服务。

## 快速开始

```powershell
npm install
npm run dev
```

浏览器打开终端里显示的本地地址后，填写你的远端接口，例如：

```text
https://api.your-domain.com/device
```

点击页面按钮时会发送类似下面的数据：

```json
{
  "command": "led:on",
  "source": "personal-domain-dashboard",
  "timestamp": "2026-04-15T00:00:00.000Z"
}
```

## 部署

```powershell
npm run build
```

构建结果会输出到 `dist` 目录，可部署到 Nginx、静态网站托管服务、GitHub Pages 或你的个人域名服务器。

## Git 远端

本工程计划连接到：

```text
https://github.com/1540530942/MyTest.git
```

如果本机网络可以访问 GitHub，可执行：

```powershell
git push -u origin feature/personal-domain-visual-control
```
