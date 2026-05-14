import socket
import json
import threading
import traceback
import json
from enum import Enum

def to_json_dict(obj):
    if obj is None: return obj
    if isinstance(obj, str): return obj
    if isinstance(obj, int): return obj
    if isinstance(obj, bool): return obj
    if isinstance(obj, float): return obj
    if isinstance(obj, Enum): return obj.value
    if isinstance(obj, tuple):
        return to_json_dict(list(obj))
    if isinstance(obj, set):
        return to_json_dict(list(obj))

    if isinstance(obj, list):
        result = []
        for e in obj:
            result.append(to_json_dict(e))
        return result
    
    if isinstance(obj, dict):
        result = {}
        for key in obj:
            if isinstance(key, str) or isinstance(key, int) or isinstance(key, bool):
                result[key] = to_json_dict(obj[key])
            else:
                result[str(key)] = to_json_dict(obj[key])
        return result
    
    if hasattr(obj, "__dict__"):    
        d = {}
        for k, v in obj.__dict__.items():
            if not k.startswith("_"):
                d[k] = v
        return to_json_dict(d)

    return str(obj)

class JSON:
    @classmethod
    def stringify(self, obj):
        return json.dumps(to_json_dict(obj))
    
class Connection:
    def __init__(self, port=5432) -> None:
        self.port = port
        self.host = "127.0.0.1"
        self.socket = None
        self.connection_callbacks = []
        self.msg_callbacks = []
        self.start()
    
    def on_client_connected(self, callback):
        self.connection_callbacks.append(callback)

    def on_message_received(self, callback):
        self.msg_callbacks.append(callback)

    def is_connected(self):
        return self.socket != None

    def start(self):
        self.thread = threading.Thread(target=self.accept_connections, args=(), daemon=True)
        self.thread.start()

    def accept_connections(self):
        print("Waiting for connections...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            conn, addr = s.accept()
            self.socket = conn
            print(f"Connected by {addr}")

            for callback in self.connection_callbacks:
                callback()

        while True:
            buffer = self.socket.recv(1024)
            if not buffer:
                print("Error de conexión!")
                self.socket.close()
                self.socket = None
                self.start()
                break

            type = buffer[0]
            data = buffer[1:]
        
            for callback in self.msg_callbacks:
                callback(type, data)

    def send_binary(self, data):
        if self.socket == None: return
        try:
            self.socket.sendall(data)
        except Exception:
            print("Connection lost!")
            print(traceback.format_exc())
            self.socket.close()
            self.socket = None
            self.start()

    def send_json(self, obj):
        data = JSON.stringify(obj).encode("utf8")
        self.send_binary(data)