# -*- coding: utf-8 -*-
"""재고 분석 및 발주 권장 수량 계산"""

import pandas as pd
import io
from typing import Tuple, List, Dict, Any


# 재고 부족 기준: 현재재고 < 안전재고
# 발주 권장 수량: MAX(MOQ, 안전재고 - 현재재고)
def analyze_inventory(inventory_df: pd.DataFrame) -> pd.DataFrame:
    """재고 시트를 분석해 부족수량, 발주권장수량, 상태, 담당자알림메시지를 계산합니다."""
    df = inventory_df.copy()
    df["부족수량"] = (df["안전재고"] - df["현재재고"]).clip(lower=0).astype(int)
    df["발주권장수량"] = df.apply(
        lambda r: max(
            int(r["MOQ"]),
            int(r["부족수량"]),
        )
        if r["부족수량"] > 0
        else 0,
        axis=1,
    )
    df["상태"] = df.apply(
        lambda r: "발주 필요" if r["현재재고"] < r["안전재고"] else "정상",
        axis=1,
    )

    def alert_message(row):
        if row["상태"] != "발주 필요":
            return None
        return (
            f"{row['재료명']} 재고 부족 - 현재 {int(row['현재재고'])}{row['단위']}, "
            f"안전재고 {int(row['안전재고'])}{row['단위']}, 권장발주 {int(row['발주권장수량'])}{row['단위']}"
        )

    df["담당자알림메시지"] = df.apply(alert_message, axis=1)
    return df


def load_excel(file_content: bytes) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Excel 파일에서 Inventory, Suppliers, (선택) EmailTemplate 시트를 읽습니다."""
    xl = pd.ExcelFile(io.BytesIO(file_content))
    inventory = pd.read_excel(xl, sheet_name="Inventory")
    suppliers = pd.read_excel(xl, sheet_name="Suppliers")
    email_tpl = None
    if "EmailTemplate" in xl.sheet_names:
        email_tpl = pd.read_excel(xl, sheet_name="EmailTemplate")
    return inventory, suppliers, email_tpl


def get_order_summary(analyzed: pd.DataFrame) -> Dict[str, Any]:
    """분석된 재고에서 발주 요약 통계를 계산합니다."""
    need_order = analyzed[analyzed["상태"] == "발주 필요"]
    total_items = len(analyzed)
    need_count = len(need_order)
    total_qty = int(need_order["발주권장수량"].sum()) if need_count else 0
    return {
        "총_품목_수": total_items,
        "발주_필요_품목_수": need_count,
        "전체_권장_발주_수량": total_qty,
        "발주_필요_목록": need_order,
    }


def get_orders_by_supplier(analyzed: pd.DataFrame) -> List[Dict[str, Any]]:
    """거래처별로 발주 품목과 수량을 묶습니다."""
    need = analyzed[analyzed["상태"] == "발주 필요"]
    if need.empty:
        return []
    groups = need.groupby("거래처", sort=False)
    result = []
    for name, grp in groups:
        result.append({
            "거래처명": name,
            "발주_필요_품목_수": len(grp),
            "총_권장_발주_수량": int(grp["발주권장수량"].sum()),
            "담당자_이메일": grp["거래처이메일"].iloc[0] if "거래처이메일" in grp.columns else "",
            "리드타임_일": int(grp["리드타임(일)"].iloc[0]) if "리드타임(일)" in grp.columns else 0,
            "품목_목록": grp[
                ["재료명", "규격", "단위", "발주권장수량", "담당자알림메시지"]
            ].to_dict("records"),
        })
    return result
