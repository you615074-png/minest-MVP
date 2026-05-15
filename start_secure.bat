@echo off
echo 🛡️ 正在生成本地自签名 SSL 证书...
echo.

:: 检查是否安装了 openssl
where openssl >nul 2>nul
if %errorlevel% neq 0 (
    echo [警告] 未检测到 OpenSSL！
    echo 无法自动生成本地 SSL 证书。
    echo 请安装 OpenSSL 或在正式环境中使用 Nginx 配置 HTTPS。
    echo.
    echo 按任意键以普通模式启动（不带 HTTPS）...
    pause >nul
    .venv\Scripts\streamlit.exe run app.py
    exit /b
)

:: 生成证书
if not exist cert.pem (
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
    echo ✅ 证书生成成功 (cert.pem, key.pem)
) else (
    echo ✅ 已检测到现有证书
)

echo.
echo 🚀 正在启动安全的 HTTPS Streamlit 服务...
.venv\Scripts\streamlit.exe run app.py --server.sslCertFile=cert.pem --server.sslKeyFile=key.pem
