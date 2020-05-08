"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            
            logins = [client.login for client in self.server.clients]

            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                if self.login in logins:
                    self.transport.write(
                        "Занято".encode()
                    )
                    self.login = None


                else:

                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
                

                        
            else:
                self.transport.write(
                    "Неправильный логин!".encode()
                )
        else:
            self.send_message(decoded)

    def save_history(self, message):
        self.server.history.append(message)
        if len(self.server.history) > 10:
            del self.server.history[0]

    def send_history(self):  
        for message in self.server.history:
            self.transport.write(
                f"\n{message.decode()}".encode()
                )


    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.save_history(encoded)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list


    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")