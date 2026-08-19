import socket
import cv2
import numpy as np
import onnxruntime
import struct
class ServerApp:
    def __init__(self, host="localhost", port=9999):
        self.host = host
        self.port = port
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print("Server is listening...")
            while True:
                client_socket, _ = server_socket.accept()
                with client_socket:
                    data = b""
                    payload_size = struct.calcsize("Q")
                    # 接收数据长度信息
                    while len(data) < payload_size:
                        packet = client_socket.recv(4096)
                        if not packet:
                            break
                        data += packet
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("Q", packed_msg_size)[0]
                    # 接收完整的数据
                    while len(data) < msg_size:
                        packet = client_socket.recv(4096)
                        if not packet:
                            break
                        data += packet