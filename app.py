# -*- coding: utf-8 -*-
"""
재고·발주 웹 시스템
- Excel 업로드 또는 데이터 입력 → 재고 분석 → 발주서 생성 및 이메일 발송 (songjy0727@gmail.com)
"""

import os
import json
import uuid
try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    load_dotenv(_env_path)
except ImportError:
    pass
import time
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
import pandas as pd

from inventory import (
    load_excel,
    analyze_inventory,
    get_order_summary,
    get_orders_by_supplier,
)
from email_service import send_order_email, ORDER_RECIPIENT_EMAIL

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")

# 기본 샘플 Excel 경로
SAMPLE_EXCEL = Path(__file__).parent / "domino_inventory_training.xlsx"

# 분석 결과 임시 저장 (토큰 -> 데이터), 쿠키 크기 제한 회피
RESULT_STORE = {}
STORE_TTL_SEC = 3600  # 1시간


def _get_result_data():
    token = request.session.get("result_token")
    if not token:
        return None
    data = RESULT_STORE.get(token)
    if not data:
        return None
    if time.time() - data.get("created_at", 0) > STORE_TTL_SEC:
        RESULT_STORE.pop(token, None)
        return None
    return data


@app.route("/")
def index():
    return render_template("index.html", recipient_email=ORDER_RECIPIENT_EMAIL)


@app.route("/standalone")
def standalone():
    """standalone.html 제공 — 이 주소로 열면 이메일 자동 발송(API) 사용 가능."""
    return send_from_directory(Path(__file__).resolve().parent, "standalone.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "excel_file" not in request.files:
        flash("Excel 파일을 선택해 주세요.", "error")
        return redirect(url_for("index"))

    f = request.files["excel_file"]
    if f.filename == "":
        flash("파일을 선택해 주세요.", "error")
        return redirect(url_for("index"))

    if not (f.filename.endswith(".xlsx") or f.filename.endswith(".xls")):
        flash("엑셀 파일(.xlsx, .xls)만 업로드 가능합니다.", "error")
        return redirect(url_for("index"))

    try:
        content = f.read()
        inventory_df, suppliers_df, _ = load_excel(content)
        analyzed = analyze_inventory(inventory_df)
        summary = get_order_summary(analyzed)
        by_supplier = get_orders_by_supplier(analyzed)

        token = str(uuid.uuid4())
        RESULT_STORE[token] = {
            "analyzed_inventory": analyzed.to_dict(orient="records"),
            "order_summary": {
                "총_품목_수": summary["총_품목_수"],
                "발주_필요_품목_수": summary["발주_필요_품목_수"],
                "전체_권장_발주_수량": summary["전체_권장_발주_수량"],
            },
            "orders_by_supplier": by_supplier,
            "store_name": request.form.get("store_name", "점포1"),
            "created_at": time.time(),
        }
        request.session["result_token"] = token

        return redirect(url_for("result"))
    except Exception as e:
        flash(f"파일 처리 중 오류: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/use_sample")
def use_sample():
    """기본 제공 Excel(domino_inventory_training.xlsx)로 분석합니다."""
    if not SAMPLE_EXCEL.exists():
        flash("샘플 파일(domino_inventory_training.xlsx)이 없습니다.", "error")
        return redirect(url_for("index"))
    try:
        content = SAMPLE_EXCEL.read_bytes()
        inventory_df, _, _ = load_excel(content)
        analyzed = analyze_inventory(inventory_df)
        summary = get_order_summary(analyzed)
        by_supplier = get_orders_by_supplier(analyzed)

        token = str(uuid.uuid4())
        RESULT_STORE[token] = {
            "analyzed_inventory": analyzed.to_dict(orient="records"),
            "order_summary": {
                "총_품목_수": summary["총_품목_수"],
                "발주_필요_품목_수": summary["발주_필요_품목_수"],
                "전체_권장_발주_수량": summary["전체_권장_발주_수량"],
            },
            "orders_by_supplier": by_supplier,
            "store_name": "도미노피자 점포(샘플)",
            "created_at": time.time(),
        }
        request.session["result_token"] = token

        return redirect(url_for("result"))
    except Exception as e:
        flash(f"샘플 분석 오류: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/analyze_manual", methods=["POST"])
def analyze_manual():
    """화면에서 입력한 재고 데이터(JSON)로 분석합니다."""
    raw = request.form.get("inventory_json")
    store_name = request.form.get("store_name", "").strip() or "점포"
    if not raw:
        flash("입력된 데이터가 없습니다.", "error")
        return redirect(url_for("index"))
    try:
        rows = json.loads(raw)
        if not rows:
            flash("최소 1개 품목을 입력해 주세요.", "error")
            return redirect(url_for("index"))
        inventory_df = pd.DataFrame(rows)
        analyzed = analyze_inventory(inventory_df)
        summary = get_order_summary(analyzed)
        by_supplier = get_orders_by_supplier(analyzed)

        token = str(uuid.uuid4())
        RESULT_STORE[token] = {
            "analyzed_inventory": analyzed.to_dict(orient="records"),
            "order_summary": {
                "총_품목_수": summary["총_품목_수"],
                "발주_필요_품목_수": summary["발주_필요_품목_수"],
                "전체_권장_발주_수량": summary["전체_권장_발주_수량"],
            },
            "orders_by_supplier": by_supplier,
            "store_name": store_name,
            "created_at": time.time(),
        }
        request.session["result_token"] = token
        return redirect(url_for("result"))
    except json.JSONDecodeError as e:
        flash(f"데이터 형식 오류: {str(e)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"분석 중 오류: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/result")
def result():
    data = _get_result_data()
    if not data:
        flash("먼저 Excel을 업로드하거나 샘플 데이터를 사용해 주세요.", "error")
        return redirect(url_for("index"))

    return render_template(
        "result.html",
        summary=data["order_summary"],
        orders_by_supplier=data["orders_by_supplier"],
        store_name=data["store_name"],
        analyzed_list=data["analyzed_inventory"],
        recipient_email=ORDER_RECIPIENT_EMAIL,
    )


@app.route("/send_email", methods=["POST"])
def send_email():
    data = _get_result_data()
    if not data:
        flash("세션이 만료되었습니다. 다시 분석해 주세요.", "error")
        return redirect(url_for("index"))
    store_name = data["store_name"]
    orders_by_supplier = data["orders_by_supplier"]

    if not orders_by_supplier:
        flash("발주할 품목이 없습니다.", "info")
        return redirect(url_for("result"))

    success, message = send_order_email(
        store_name=store_name,
        orders_by_supplier=orders_by_supplier,
        recipient=ORDER_RECIPIENT_EMAIL,
    )
    if success:
        flash(message, "success")
    else:
        flash(message, "error")
    return redirect(url_for("result"))


@app.route("/api/send_order_email", methods=["POST"])
def api_send_order_email():
    """자동 이메일 발송 API (JSON body: store_name, orders_by_supplier). CORS 허용."""
    if request.method == "OPTIONS":
        return "", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }
    try:
        data = request.get_json() or {}
        store_name = data.get("store_name", "점포")
        orders_by_supplier = data.get("orders_by_supplier", [])
        if not orders_by_supplier:
            return jsonify({"ok": False, "message": "발주할 품목이 없습니다."}), 400
        success, message = send_order_email(
            store_name=store_name,
            orders_by_supplier=orders_by_supplier,
            recipient=ORDER_RECIPIENT_EMAIL,
        )
        if success:
            return jsonify({"ok": True, "message": message}), 200, {"Access-Control-Allow-Origin": "*"}
        return jsonify({"ok": False, "message": message}), 400, {"Access-Control-Allow-Origin": "*"}
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500, {"Access-Control-Allow-Origin": "*"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(debug=True, port=port)
