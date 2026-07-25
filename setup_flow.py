from flask import redirect, render_template_string, request

from .core import complete_first_run_setup, is_setup_required


SETUP_HTML = """<!doctype html><html><head><meta charset="utf-8"><title>LANHUB SERVER PRO - Setup</title><style>
body{margin:0;background:#1e293b;font-family:Arial,sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;color:white}.box{width:380px;background:#0f172a;padding:30px;border-radius:12px;box-shadow:0 10px 25px rgba(0,0,0,0.5);border:1px solid #334155}h2{margin-top:0;color:#f8fafc}input{width:100%;padding:11px;margin-top:12px;border:1px solid #334155;background:#1e293b;color:white;border-radius:6px;box-sizing:border-box;font-size:14px}button{width:100%;padding:12px;margin-top:20px;border:none;border-radius:6px;background:#2563eb;color:white;font-weight:bold;cursor:pointer;font-size:14px}.err{color:#ef4444;font-size:13px;margin-top:8px}.hint{color:#94a3b8;font-size:13px;line-height:1.4}
</style></head><body><div class="box"><h2>First Run Setup</h2><p class="hint">Tạo tài khoản Quản trị viên cho LANHUB SERVER PRO.</p>{% if error %}<p class="err">{{error}}</p>{% endif %}<form method="POST"><input type="hidden" name="csrf_token" value="{{csrf_token}}"><input name="server_name" placeholder="Tên Server" value="LANHUB SERVER PRO"><input name="username" placeholder="Tên đăng nhập Admin" value="admin"><input type="password" name="password" placeholder="Mật khẩu mới"><input type="password" name="confirm" placeholder="Xác nhận mật khẩu"><button type="submit">LƯU VÀ BẮT ĐẦU</button></form></div></body></html>"""


def register_setup_routes(app, get_csrf_token, verify_csrf):
    @app.route("/setup", methods=["GET", "POST"])
    def setup():
        if not is_setup_required():
            return redirect("/")
        error = None
        if request.method == "POST":
            if not verify_csrf():
                error = "Security token không hợp lệ"
            else:
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "")
                confirm = request.form.get("confirm", "")
                server_name = request.form.get("server_name", "").strip()
                if not username:
                    error = "Vui lòng nhập tên đăng nhập"
                elif len(password.strip()) < 6:
                    error = "Mật khẩu phải từ 6 ký tự trở lên"
                elif password == "1234":
                    error = "Vui lòng chọn mật khẩu mạnh hơn"
                elif password != confirm:
                    error = "Mật khẩu xác nhận không khớp"
                else:
                    complete_first_run_setup(username, password, server_name)
                    return redirect("/")
        return render_template_string(SETUP_HTML, error=error, csrf_token=get_csrf_token())