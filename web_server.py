import os
import time
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

INDEX_HTML = '''<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LANHUB SERVER PRO</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: white; padding: 20px; }
        .card { background: #1e293b; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        h1 { color: #3b82f6; margin-top: 0; }
        .file-list { list-style: none; padding: 0; }
        .file-item { background: #334155; padding: 10px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; }
        a { color: #60a5fa; text-decoration: none; }
        button { background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🚀 LANHUB SERVER PRO (MOBILE)</h1>
        <p>Máy chủ lưu trữ và chia sẻ file trong mạng LAN</p>
    </div>

    <div class="card">
        <h3>Tải file lên</h3>
        <input type="file" id="fileInput">
        <button style="background:#2563eb;" onclick="uploadFile()">Upload</button>
    </div>

    <div class="card">
        <h3>Danh sách File</h3>
        <ul id="files" class="file-list"></ul>
    </div>

    <script>
        function loadFiles() {
            fetch('/api/files').then(r => r.json()).then(data => {
                let html = '';
                if(data.files) {
                    data.files.forEach(f => {
                        html += `<li class="file-item">
                            <span>${f.name} (${f.size})</span>
                            <div>
                                <a href="/api/download/${encodeURIComponent(f.name)}" target="_blank">Tải về</a>
                                <button onclick="deleteFile('${encodeURIComponent(f.name)}')">Xóa</button>
                            </div>
                        </li>`;
                    });
                }
                document.getElementById('files').innerHTML = html || 'Chưa có file nào';
            });
        }

        function uploadFile() {
            let input = document.getElementById('fileInput');
            if(!input.files.length) return alert('Chưa chọn file');
            let form = new FormData();
            form.append('file', input.files[0]);
            fetch('/api/upload', {method: 'POST', body: form})
            .then(r => r.json())
            .then(res => {
                if(res.success) { alert('Thành công!'); loadFiles(); }
                else { alert('Lỗi: ' + res.error); }
            });
        }

        function deleteFile(name) {
            if(!confirm('Xóa file này?')) return;
            fetch('/api/delete/' + name, {method: 'DELETE'})
            .then(r => r.json())
            .then(() => loadFiles());
        }

        loadFiles();
    </script>
</body>
</html>
'''

class LANHubWebServer:
    def __init__(self, core_system, discovery_system):
        self.core = core_system
        self.discovery = discovery_system
        self.app = Flask(__name__)
        self.upload_folder = self.core.get_shared_folder()
        
        self.app.config['UPLOAD_FOLDER'] = self.upload_folder
        self.app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024 * 1024
        
        self._register_routes()

    def _register_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(INDEX_HTML)

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
                return jsonify({'error': 'Không tìm thấy file'}), 400
            
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
                try:
                    os.remove(file_path)
                    return jsonify({'success': True})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            return jsonify({'error': 'File không tồn tại'}), 404

    def run(self, port=5000):
        self.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
