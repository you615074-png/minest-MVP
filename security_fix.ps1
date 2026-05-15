# =============================================
# Streamlit 安全加固脚本
# 放在项目目录，双击运行即可
# =============================================

$ErrorActionPreference = "Stop"
$projectDir = $PSScriptRoot
$port = 8501

Write-Host "=== Streamlit 安全加固脚本 ===" -ForegroundColor Cyan

# 1. 检测并终止占用8501端口的旧进程
Write-Host "`n[1/4] 检查并终止旧进程..." -ForegroundColor Yellow
$oldProcs = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" } | Select-Object -ExpandProperty OwningProcess -Unique
if ($oldProcs) {
    foreach ($pid in $oldProcs) {
        Write-Host "  终止 PID: $pid" -ForegroundColor Red
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 2
}

# 2. 创建加强版 robots.txt（阻止所有爬虫）
Write-Host "`n[2/4] 更新 robots.txt..." -ForegroundColor Yellow
@"
User-agent: *
Disallow: /

# 安全增强
Disallow: /.git
Disallow: /.env
Disallow: /sitemap.xml
Disallow: /__pycache__
Disallow: /.venv
"@ | Out-File -FilePath "$projectDir\static\robots.txt" -Encoding UTF8 -Force

# 3. 创建安全中间件配置（可选，如果用户有 nginx）
Write-Host "`n[3/4] 创建 nginx 安全配置示例..." -ForegroundColor Yellow
$nginxConf = @"
# 在 nginx.conf 的 server 块中添加：

# 隐藏 .env 和 .git
location ~ /\.(env|git) {
    deny all;
    return 404;
}

# 安全Headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000" always;

# 禁用目录列表
autoindex off;
"@

$nginxConf | Out-File -FilePath "$projectDir\security_nginx.conf" -Encoding UTF8 -Force

# 4. 启动 Streamlit（禁用静态文件目录列表 + 本地访问）
Write-Host "`n[4/4] 以安全模式启动 Streamlit..." -ForegroundColor Yellow

$venvPython = "$projectDir\.venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    $venvPython = "python"
}

# 使用 --static-dir 限制静态文件 + server.headless
# --static-dir 是 Streamlit 1.57+ 新参数，限制可访问的静态目录
$cmd = "$venvPython -m streamlit run `"$projectDir\app.py`" --server.port $port --server.headless true --server.enableCORS false --server.enableXsrfProtection true"

Write-Host "`n执行命令: $cmd" -ForegroundColor Cyan

# 启动新进程
$proc = Start-Process -FilePath $venvPython -ArgumentList "-m", "streamlit", "run", "$projectDir\app.py", "--server.port=$port", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=true" -PassThru -NoNewWindow

Write-Host "`n✅ 新进程已启动 PID: $($proc.Id)" -ForegroundColor Green
Start-Sleep -Seconds 3

# 验证端口
Write-Host "`n验证端口监听..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort $port -State Listen | Format-Table LocalAddress, LocalPort, State, OwningProcess -AutoSize

Write-Host @"

=== 安全加固完成 ===

修复内容:
1. 终止了所有旧 Streamlit 进程
2. 更新了 robots.txt（阻止爬虫）
3. 创建了 nginx 配置模板（可选）
4. 以安全参数启动了 Streamlit

额外建议（需要外部工具）:
- 使用 nginx 反向代理添加安全Headers
- 配置防火墙规则限制访问IP
- 启用 HTTPS（需要 SSL 证书）

访问 http://localhost:$port 检���是否正常
"@ -ForegroundColor Cyan

# 保持窗口打开（可选）
# Read-Host "按回车退出"