import socket
import json
import threading
import time

class NetworkDiscovery:
    def __init__(self, device_name, port=5000, broadcast_port=50001):
        self.device_name = device_name
        self.port = port
        self.broadcast_port = broadcast_port
        self.running = False
        self.discovered_devices = {}  # Format: {ip: {"name": name, "last_seen": timestamp}}

    def start_beacon(self, get_ip_func):
        """Phát tín hiệu UDP Broadcast để báo danh trong mạng LAN"""
        self.running = True
        
        # Thread phát sóng UDP
        broadcaster = threading.Thread(target=self._broadcast_presence, args=(get_ip_func,), daemon=True)
        broadcaster.start()

        # Thread lắng nghe các thiết bị khác trong mạng
        listener = threading.Thread(target=self._listen_for_devices, daemon=True)
        listener.start()

    def _broadcast_presence(self, get_ip_func):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2)

        while self.running:
            try:
                local_ip = get_ip_func()
                if local_ip != "127.0.0.1":
                    payload = json.dumps({
                        "type": "LANHUB_BEACON",
                        "device_name": self.device_name,
                        "ip": local_ip,
                        "port": self.port
                    }).encode('utf-8')
                    
                    sock.sendto(payload, ('<broadcast>', self.broadcast_port))
            except Exception as e:
                pass
            time.sleep(3)  # Phát tín hiệu mỗi 3 giây

    def _listen_for_devices(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('', self.broadcast_port))
        except Exception:
            return

        sock.settimeout(2)

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                
                if message.get("type") == "LANHUB_BEACON":
                    ip = message.get("ip")
                    name = message.get("device_name")
                    if ip and ip != addr[0]:  # Không ghi nhận chính mình
                        self.discovered_devices[ip] = {
                            "name": name,
                            "port": message.get("port", 5000),
                            "last_seen": time.time()
                        }
            except Exception:
                pass
            
            self._cleanup_old_devices()

    def _cleanup_old_devices(self):
        """Xóa thiết bị ngắt kết nối sau 10 giây"""
        now = time.time()
        to_delete = [ip for ip, info in self.discovered_devices.items() if now - info["last_seen"] > 10]
        for ip in to_delete:
            del self.discovered_devices[ip]

    def get_active_devices(self):
        return list(self.discovered_devices.values())

    def stop(self):
        self.running = False