"""
安全启动脚本 - 修复 .env 和敏感文件暴露问题
通过反向代理方式阻止访问敏感文件
"""
import subprocess
import threading
import http.server
import socketserver
import urllib.request
import urllib.error
import os
import signal
import sys

PORT = 8501
UPSTREAM = "http://127.0.0.1:8502"

# 禁止访问的路径模式
BLOCKED_PATHS = [
    ".env",
    ".git",
    ".gitignore",
    ".env.example",
    "__pycache__",
]

class SecurityProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 检查是否禁止访问
        path = self.path.split("?")[0]
        for blocked in BLOCKED_PATHS:
            if path.startswith(f"/{blocked}") or path.startswith(f"/static/{blocked}"):
                self.send_response(403)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Forbidden")
                return
        
        # 允许的请求转发到上游 Streamlit
        try:
            req = urllib.request.Request(f"{UPSTREAM}{self.path}")
            # 转发请求头
            for header in ["Cookie", "User-Agent", "Accept", "Accept-Language"]:
                if header in self.headers:
                    req.add_header(header, self.headers[header])
            
            # 添加 X-Forwarded headers
            req.add_header("X-Forwarded-For", self.client_address[0])
            req.add_header("X-Forwarded-Proto", "http")
            
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for header, value in response.getheaders():
                    if header.lower() not in ("transfer-encoding", "connection"):
                        self.send_header(header, value)
                self.end_headers()
                self.wfile.write(response.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Upstream error: {str(e)}".encode())
    
    def do_POST(self):
        # POST 请求同样转发
        self.do_GET()

def start_upstream():
    """启动上游 Streamlit 服务"""
    # 切换到项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__)) if __file__ else "."
    if os.path.isfile(os.path.join(project_dir, "app.py")):
        project_dir = os.path.dirname(os.path.abspath(__file__))
    else:
        project_dir = r"C:\Users\28451\Desktop\minest MVP"
    
    os.chdir(project_dir)
    
    # 启动 Streamlit 在 8502 端口
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port=8502",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=true",
        "--server.runOnSave=false",
        "--server.staticFolder=static",
    ]
    
    print(f"启动 Streamlit: {' '.join(cmd)}")
    subprocess.call(cmd)

def main():
    print(f"""
=============================================
  安全启动脚本 - B2B AI SDR
=============================================
  本地端口: {PORT}
  上游端口: 8502
  已阻止: {', '.join(BLOCKED_PATHS)}
=============================================
    """)
    
    # 启动上游 Streamlit
    upstream_thread = threading.Thread(target=start_upstream, daemon=True)
    upstream_thread.start()
    
    # 等待上游启动
    import time
    time.sleep(3)
    
    # 启动代理服务器
    with socketserver.TCPServer(("", PORT), SecurityProxyHandler) as httpd:
        print(f"安全代理运行在 http://localhost:{PORT}")
        print("按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止服务...")
            httpd.server_close()

if __name__ == "__main__":
    main()