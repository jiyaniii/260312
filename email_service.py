# -*- coding: utf-8 -*-
"""발주서 이메일 발송 (수신: songjy0727@gmail.com)"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple


# 발송 대상 이메일 (담당기업 직원)
ORDER_RECIPIENT_EMAIL = "songjy0727@gmail.com"


def _get_smtp_settings():
    raw_password = os.environ.get("SMTP_PASSWORD", "")
    # Gmail 앱 비밀번호: 공백 제거, 앞뒤 따옴표 제거
    password = (raw_password or "").strip().strip('"\'')
    password = password.replace(" ", "")
    return {
        "host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": os.environ.get("SMTP_USER", "").strip(),
        "password": password,
        "use_tls": os.environ.get("SMTP_USE_TLS", "true").lower().strip() == "true",
    }


def build_order_email_content(
    store_name: str,
    orders_by_supplier: List[Dict[str, Any]],
    order_date: Optional[str] = None,
) -> Tuple[str, str]:
    """이메일 제목과 본문(HTML)을 만듭니다."""
    order_date = order_date or datetime.now().strftime("%Y-%m-%d")
    subject = f"[발주요청] {store_name} / 재고자동화시스템 / {order_date}"

    rows = []
    for sup in orders_by_supplier:
        rows.append(f"<strong>{sup['거래처명']}</strong> (리드타임 {sup['리드타임_일']}일)")
        rows.append("<ul>")
        for item in sup["품목_목록"]:
            qty = item.get("발주권장수량", 0)
            unit = item.get("단위", "")
            name = item.get("재료명", "")
            spec = item.get("규격", "")
            rows.append(f"<li>{name} ({spec}) — {qty}{unit}</li>")
        rows.append("</ul>")

    body = f"""
<html>
<body style="font-family: sans-serif;">
<p>안녕하세요.</p>
<p>도미노피자 <strong>{store_name}</strong> 재고·발주 자동화 시스템입니다.<br/>
아래 품목에 대해 발주 요청드립니다.</p>
<h3>거래처별 발주 내역</h3>
{"".join(rows)}
<p>확인 부탁드립니다. 감사합니다.</p>
<p>— 재고·발주 자동화 시스템</p>
</body>
</html>
"""
    return subject, body


def send_order_email(
    store_name: str,
    orders_by_supplier: List[Dict[str, Any]],
    recipient: str = ORDER_RECIPIENT_EMAIL,
) -> Tuple[bool, str]:
    """
    발주 요약 이메일을 발송합니다.
    성공 여부와 메시지를 반환합니다.
    """
    if not orders_by_supplier:
        return False, "발주할 품목이 없습니다."

    subject, body_html = build_order_email_content(store_name, orders_by_supplier)
    smtp = _get_smtp_settings()

    if not smtp["user"] or not smtp["password"]:
        return False, "SMTP 설정이 없습니다. .env에 SMTP_USER, SMTP_PASSWORD를 설정하세요."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp["user"]
    msg["To"] = recipient
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        if smtp["use_tls"]:
            with smtplib.SMTP(smtp["host"], smtp["port"], timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp["user"], smtp["password"])
                server.sendmail(smtp["user"], recipient, msg.as_string())
        else:
            with smtplib.SMTP_SSL(smtp["host"], smtp["port"], timeout=15) as server:
                server.login(smtp["user"], smtp["password"])
                server.sendmail(smtp["user"], recipient, msg.as_string())
        return True, f"발주 이메일이 {recipient} 로 발송되었습니다."
    except smtplib.SMTPAuthenticationError as e:
        return False, "이메일 로그인 실패: Gmail 주소와 앱 비밀번호를 확인하세요. (2단계 인증 후 '앱 비밀번호' 사용)"
    except smtplib.SMTPException as e:
        return False, f"SMTP 오류: {str(e)}"
    except Exception as e:
        return False, f"이메일 발송 실패: {str(e)}"
