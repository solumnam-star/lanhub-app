import threading
import os
import sys

# Khai báo Kivy UI cho Mobile
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window

# Import các Module LANHUB đã chuyển đổi
from core import CoreSystem
from network_discovery import NetworkDiscovery
from web_server import LANHubWebServer

class LANHubMobileUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # Khởi tạo Core và Discovery
        self.core = CoreSystem()
        self.config = self.core.load_config()
        self.discovery = NetworkDiscovery(
            device_name=self.config.get("device_name"),
            port=self.config.get("server_port", 5000)
        )
        self.web_server = LANHubWebServer(self.core, self.discovery)

        # Tiêu đề UI
        self.add_widget(Label(
            text="LANHUB SERVER MOBILE",
            font_size='22sp',
            bold=True,
            color=(0.14, 0.38, 0.92, 1),
            size_hint_y=None,
            height=50
        ))

        # Khung trạng thái IP
        self.lbl_ip = Label(
            text=f"Địa chỉ IP: {self.core.get_local_ip()}",
            font_size='16sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(self.lbl_ip)

        self.lbl_status = Label(
            text="Trạng thái: Đang kết nối LAN...",
            font_size='14sp',
            color=(0.1, 0.8, 0.1, 1),
            size_hint_y=None,
            height=30
        )
        self.add_widget(self.lbl_status)

        # Nút hành động
        self.btn_action = Button(
            text="MỞ KHỞI CHẠY KHÔNG NỀN",
            background_color=(0.14, 0.38, 0.92, 1),
            size_hint_y=None,
            height=60
        )
        self.add_widget(self.btn_action)

        # Tự động Kích hoạt Flask & Discovery
        self.start_backend_services()

    def start_backend_services(self):
        # 1. Chạy Auto Discovery
        self.discovery.start_beacon(self.core.get_local_ip)

        # 2. Chạy Flask Web Server
        server_thread = threading.Thread(
            target=self.web_server.run,
            kwargs={"port": self.config.get("server_port", 5000)},
            daemon=True
        )
        server_thread.start()

class LANHubMobileApp(App):
    def build(self):
        self.title = "LANHUB Server Pro"
        return LANHubMobileUI()

if __name__ == '__main__':
    LANHubMobileApp().run()