"""
邮件发送工具 — 通过 SMTP 发送开发信。
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_email(to_email: str, subject: str, body: str, ps_line: str,
               smtp_host: str, smtp_port: int, smtp_user: str,
               smtp_pass: str, sender_name: str) -> tuple[bool, str]:
    if not all([smtp_host, smtp_user, smtp_pass]):
        return False, "SMTP 配置不完整，请在侧边栏完成邮件配置"

    full_body = f"{body}\n\n{ps_line}" if ps_line else body

    msg = MIMEText(full_body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = to_email

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()

        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        return True, f"邮件已发送至 {to_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP 认证失败，请检查邮箱账号和授权码是否正确"
    except smtplib.SMTPConnectError:
        return False, f"无法连接 SMTP 服务器 {smtp_host}:{smtp_port}，请检查地址和端口"
    except smtplib.SMTPRecipientsRefused:
        return False, f"收件人邮箱 {to_email} 被拒绝，请检查地址是否正确"
    except smtplib.SMTPServerDisconnected:
        return False, "SMTP 服务器意外断开，请重试"
    except OSError as e:
        return False, f"网络错误：{str(e)[:60]}"
    except Exception as e:
        return False, f"发送失败：{str(e)[:100]}"
