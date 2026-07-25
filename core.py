import os
import sys
import json
import socket
import platform
import uuid

# Fix encoding stdout cho Android/Linux/Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

class CoreSystem:
    def __init__(self):
        self.os_type = platform.system()
        self.app_dir = self._get_app_storage_dir()
        self.config_file = os.path.join(self.app_dir, "lanhub_config.json")
        self._ensure_storage()

    def _get_app_storage_dir(self):
        """Xác định đường dẫn lưu trữ tương thích cả Android và PC"""
        if "ANDROID_ARGUMENT" in os.environ or self.os_type == "Linux":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
            except ImportError:
                pass
            
            base_path = os.environ.get("ANDROID_PRIVATE", os.path.expanduser("~"))
            storage_path = os.path.join(base_path, "LANHUB_Data")
        else:
            appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            storage_path = os.path.join(appdata, "LANHUB_Server")

        return storage_path

    def _ensure_storage(self):
        if not os.path.exists(self.app_dir):
            os.makedirs(self.app_dir, exist_ok=True)
            
        shared_dir = self.get_shared_folder()
        if not os.path.exists(shared_dir):
            os.makedirs(shared_dir, exist_ok=True)

    def get_shared_folder(self):
        """Lấy đường dẫn kho lưu trữ file shared"""
        return os.path.join(self.app_dir, "Shared_Files")

    def get_hwid(self):
        """Lấy HWID định danh thiết bị"""
        try:
            if self.os_type == "Linux" or "ANDROID_ARGUMENT" in os.environ:
                try:
                    from jnius import autoclass
                    Secure = autoclass('android.provider.Settings$Secure')
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    content_resolver = PythonActivity.mActivity.getContentResolver()
                    android_id = Secure.getString(content_resolver, Secure.ANDROID_ID)
                    if android_id:
                        return f"ANDROID-{android_id.upper()}"
                except Exception:
                    pass
            
            mac_num = uuid.getnode()
            return f"HWID-{hex(mac_num)[2:].upper()}"
        except Exception:
            return "HWID-GENERIC-MOBILE-001"

    def get_local_ip(self):
        """Lấy IP mạng LAN hiện tại của thiết bị"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def save_config(self, data):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Lỗi lưu cấu hình: {e}")
            return False

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "server_port": 5000,
            "device_name": f"LANHUB-Mobile-{self.get_hwid()[:6]}",
            "auto_start": True
        }
