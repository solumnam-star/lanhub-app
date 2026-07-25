import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from werkzeug.utils import secure_filename

class LANHubWebServer:
    def __init__(self, core_system, discovery_system):
        self.core = core_system
        self.discovery = discovery_system
        self.app = Flask(__name__, template_folder='templates')
        self.upload_folder = self.core.get_shared_folder()
        
        self.app.config['UPLOAD_FOLDER'] = self.upload_folder
        self.app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 * 1024  # Hỗ trợ file 15GB
        
        self._register_routes()

    def _register_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/api/info', methods=['GET'])
        def get_info():
            return jsonify({
                "device_name": self.core.load_config().get("device_name"),
                "ip": self.core.get_local_ip(),
                "hwid": self.core.get_hwid(),
                "active_devices": self.discovery.get_active_devices()
            })

        @self.app.route('/api/files', methods=['GET'])
        def list_files():
            files_data = []
            try:
                for filename in os.listdir(self.upload_folder):
                    file_path = os.path.join(self.upload_folder, filename)
                    if os.path.isfile(file_path):
                        size_bytes = os.path.getsize(file_path)
                        
                        if size_bytes < 1024 * 1024:
                            size_str = f"{round(size_bytes / 1024, 1)} KB"
                        elif size_bytes < 1024 * 1024 * 1024:
                            size_str = f"{round(size_bytes / (1024 * 1024), 1)} MB"
                        else:
                            size_str = f"{round(size_bytes / (1024 * 1024 * 1024), 2)} GB"

                        mtime = os.path.getmtime(file_path)
                        date_str = time.strftime('%H:%M %d/%m/%Y', time.localtime(mtime))

                        files_data.append({
                            'name': filename,
                            'size': size_str,
                            'date': date_str,
                            'bytes': size_bytes
                        })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

            return jsonify({'files': files_data})

        @self.app.route('/api/upload', methods=['POST'])
        def upload_file():
            if 'file' not in request.files:
                return jsonify({'error': 'Không tìm thấy file gửi lên'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Tên file rỗng'}), 400
            
            if file:
                filename = secure_filename(file.filename)
                if not filename:
                    filename = file.filename
                
                save_path = os.path.join(self.upload_folder, filename)
                file.save(save_path)
                return jsonify({'success': True, 'filename': filename})

        @self.app.route('/api/download/<path:filename>', methods=['GET'])
        def download_file(filename):
            return send_from_directory(self.upload_folder, filename, as_attachment=True)

        @self.app.route('/api/delete/<path:filename>', methods=['DELETE'])
        def delete_file(filename):
            file_path = os.path.join(self.upload_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return jsonify({'success': True})
            return jsonify({'error': 'File không tồn tại'}), 404

    def run(self, port=5000):
        self.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)