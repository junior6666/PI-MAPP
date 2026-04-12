import asyncio
import websockets
import socket
import time


class WebSocketServer:
    def __init__(self, port=8765):
        self.port = port
        self.clients = set()

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except:
            return '127.0.0.1'
        finally:
            s.close()

    async def handler(self, websocket, path):
        self.clients.add(websocket)
        client_ip = websocket.remote_address[0]
        print(f"[+] 手机已连接: {client_ip}")

        try:
            # 发送欢迎消息
            await websocket.send("已连接! 等待消息...")

            # 保持连接
            async for message in websocket:
                print(f"[←] 收到手机消息: {message}")
                await websocket.send("已收到!")

        except websockets.exceptions.ConnectionClosed:
            print(f"[-] 手机断开: {client_ip}")
        finally:
            self.clients.discard(websocket)

    async def send_to_phones(self, message: str):
        """发送多行字符串到所有手机"""
        if not self.clients:
            print("[!] 没有已连接的设备")
            return

        data = message
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(data)
                print(f"[→] 已发送消息")
            except:
                disconnected.add(client)

        for client in disconnected:
            self.clients.discard(client)

    async def start(self):
        local_ip = self.get_local_ip()
        print(f"=" * 50)
        print(f"WebSocket 服务器已启动!")
        print(f"本机IP: {local_ip}")
        print(f"手机访问: ws://{local_ip}:{self.port}")
        print(f"=" * 50)

        async with websockets.serve(self.handler, "0.0.0.0", self.port):
            await asyncio.Future()  # 永久运行


# 使用示例
async def main():
    server = WebSocketServer(port=8765)

    # 在后台启动服务器
    server_task = asyncio.create_task(server.start())

    # 模拟发送消息
    messages = [
        """📢 系统通知
这是第一行
这是第二行
时间: {time}""".format(time=time.strftime("%H:%M:%S"))
    ]

    await asyncio.sleep(2)  # 等待服务器启动

    idx = 0
    while True:
        try:
            cmd = input("\n按 Enter 发送消息，q 退出: ")
            if cmd.lower() == 'q':
                break
            await server.send_to_phones(messages[idx % len(messages)])
            idx += 1
        except KeyboardInterrupt:
            break

    server_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())