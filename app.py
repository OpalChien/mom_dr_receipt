from __future__ import annotations

import csv
import json
import os
from io import BytesIO
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:  # Lets the app show a helpful setup message instead of crashing.
    gspread = None
    Credentials = None


APP_DIR = Path(__file__).parent
LOCAL_LOG_FILENAME = "mom_dr_receipt_log.csv"
SHEET_NAME = "mom_dr收據_log"
SHEET_HEADERS = [
    "created_at",
    "receipt_no",
    "language",
    "receipt_date",
    "seller_name",
    "seller_tax_id",
    "seller_address",
    "seller_phone",
    "buyer_name",
    "item_name",
    "quantity",
    "unit_price",
    "amount",
    "notes",
    "total",
    "sheet_url",
]


TEXT = {
    "zh": {
        "language_name": "中文",
        "page_title": "mom_dr 收據紀錄",
        "receipt_tab": "建立收據",
        "history_tab": "紀錄",
        "settings_tab": "連線狀態",
        "language": "語言",
        "receipt_info": "收據資料",
        "seller_info": "店家 / 受領人",
        "buyer_info": "買受人",
        "items": "明細",
        "receipt_no": "收據編號",
        "receipt_date": "開立日期",
        "seller_name": "廠商或受領人姓名",
        "seller_tax_id": "統一編號 / 身分證字號",
        "seller_address": "地址",
        "seller_phone": "電話",
        "buyer_name": "買受人抬頭",
        "item_name": "品名",
        "quantity": "數量",
        "unit_price": "單價",
        "amount": "金額",
        "notes": "備註",
        "total": "合計",
        "save": "儲存到紀錄",
        "saved": "已儲存收據紀錄。",
        "print_hint": "可用瀏覽器列印功能把下方收據列印或另存 PDF。",
        "missing_google": "尚未設定 Google 連線，目前會寫入本機 CSV。",
        "connected_google": "已連線 Google Sheets。",
        "sheet_link": "開啟 mom_dr 收據 log 試算表",
        "no_records": "目前沒有紀錄。",
        "connection": "連線方式",
        "local_csv": "本機 CSV",
        "google_sheet": "Google Sheets",
        "download_html": "下載收據 HTML",
        "download_jpg": "下載收據 JPG",
        "google_ready": "Google 已連動：儲存後會寫入 Google 試算表。",
        "google_not_ready": "Google 尚未連動：目前只會寫入本機 CSV。",
        "local_log_folder": "本機紀錄資料夾路徑",
        "local_log_file": "目前本機紀錄檔",
        "local_folder_help": "本機執行時可讀寫這個資料夾；Streamlit Cloud 不能直接讀你的 Windows 電腦資料夾。",
        "record_source": "紀錄來源",
        "google_records": "Google 試算表",
        "local_records": "本機 CSV",
        "local_read_error": "讀取本機 CSV 失敗",
        "backup_restore": "備份 / 載入紀錄",
        "download_records": "下載目前紀錄 CSV",
        "upload_records": "載入紀錄 CSV",
        "uploaded_preview": "載入的紀錄預覽",
        "import_local": "匯入到本機 CSV",
        "import_google": "匯入到 Google 試算表",
        "imported": "已匯入 {count} 筆新紀錄。",
        "no_new_records": "沒有新紀錄需要匯入。",
        "invalid_csv": "CSV 格式不正確，請上傳由本工具下載的紀錄檔。",
        "receipt_title": "免用統一發票收據",
        "tax_id_label": "統一編號",
        "signature": "簽章",
        "grand_total": "合計新臺幣",
        "line_note": "備註",
    },
    "en": {
        "language_name": "English",
        "page_title": "mom_dr Receipt Log",
        "receipt_tab": "Create receipt",
        "history_tab": "Records",
        "settings_tab": "Connection",
        "language": "Language",
        "receipt_info": "Receipt details",
        "seller_info": "Vendor / payee",
        "buyer_info": "Buyer",
        "items": "Line item",
        "receipt_no": "Receipt no.",
        "receipt_date": "Issue date",
        "seller_name": "Vendor or payee name",
        "seller_tax_id": "Tax ID / personal ID",
        "seller_address": "Address",
        "seller_phone": "Phone",
        "buyer_name": "Buyer name",
        "item_name": "Item",
        "quantity": "Quantity",
        "unit_price": "Unit price",
        "amount": "Amount",
        "notes": "Notes",
        "total": "Total",
        "save": "Save to log",
        "saved": "Receipt record saved.",
        "print_hint": "Use your browser print command to print the receipt below or save it as PDF.",
        "missing_google": "Google connection is not configured. Records are saved to a local CSV for now.",
        "connected_google": "Connected to Google Sheets.",
        "sheet_link": "Open mom_dr receipt log spreadsheet",
        "no_records": "No records yet.",
        "connection": "Connection",
        "local_csv": "Local CSV",
        "google_sheet": "Google Sheets",
        "download_html": "Download receipt HTML",
        "download_jpg": "Download receipt JPG",
        "google_ready": "Google is connected. Saved receipts are written to Google Sheets.",
        "google_not_ready": "Google is not connected. Records are saved only to a local CSV.",
        "local_log_folder": "Local log folder path",
        "local_log_file": "Current local log file",
        "local_folder_help": "When running locally, the app can read and write this folder. Streamlit Cloud cannot directly read folders on your Windows computer.",
        "record_source": "Record source",
        "google_records": "Google Sheet",
        "local_records": "Local CSV",
        "local_read_error": "Failed to read local CSV",
        "backup_restore": "Backup / load records",
        "download_records": "Download current records CSV",
        "upload_records": "Load records CSV",
        "uploaded_preview": "Loaded records preview",
        "import_local": "Import to local CSV",
        "import_google": "Import to Google Sheet",
        "imported": "Imported {count} new records.",
        "no_new_records": "No new records to import.",
        "invalid_csv": "Invalid CSV. Please upload a record file downloaded from this tool.",
        "receipt_title": "Receipt",
        "tax_id_label": "Tax ID",
        "signature": "Signature",
        "grand_total": "Total NTD",
        "line_note": "Note",
    },
}


def t(key: str) -> str:
    return TEXT[st.session_state.language][key]


def money(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0")).quantize(Decimal("1"))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def get_secret_dict(name: str) -> dict[str, Any] | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        return None
    if not value:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def get_config_secret(key: str, service_account_info: dict[str, Any] | None = None) -> str | None:
    try:
        value = st.secrets.get(key)
    except Exception:
        value = None
    if value:
        return str(value)
    if service_account_info and service_account_info.get(key):
        return str(service_account_info[key])
    return None


def default_local_log_folder() -> str:
    try:
        secret_value = st.secrets.get("local_log_folder")
    except Exception:
        secret_value = None
    return str(secret_value or os.environ.get("MOM_DR_LOG_FOLDER") or APP_DIR)


def local_log_path() -> Path:
    folder = st.session_state.get("local_log_folder", default_local_log_folder())
    return Path(str(folder)).expanduser() / LOCAL_LOG_FILENAME


@st.cache_resource(show_spinner=False)
def get_google_sheet() -> tuple[Any | None, str | None, str | None]:
    if gspread is None or Credentials is None:
        return None, None, "Missing packages. Run `pip install -r requirements.txt`."

    service_account_info = get_secret_dict("gcp_service_account")
    if not service_account_info:
        return None, None, None

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        client = gspread.authorize(credentials)

        spreadsheet = None
        matches = client.openall(SHEET_NAME)
        if matches:
            spreadsheet = matches[0]
        else:
            folder_id = get_config_secret("google_drive_folder_id", service_account_info)
            spreadsheet = client.create(SHEET_NAME, folder_id=folder_id)
            share_with = get_config_secret("share_with_email", service_account_info)
            if share_with:
                spreadsheet.share(share_with, perm_type="user", role="writer")

        worksheet = spreadsheet.sheet1
        existing = worksheet.row_values(1)
        if existing != SHEET_HEADERS:
            worksheet.resize(rows=max(worksheet.row_count, 1000), cols=len(SHEET_HEADERS))
            worksheet.update("A1", [SHEET_HEADERS])
        return worksheet, spreadsheet.url, None
    except Exception as exc:
        return None, None, f"Google connection failed: {exc}"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/msjhbd.ttc" if bold else "C:/Windows/Fonts/msjh.ttc",
        "C:/Windows/Fonts/mingliub.ttc" if bold else "C:/Windows/Fonts/mingliu.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: Any, font: ImageFont.ImageFont, fill: str = "#1f1b18") -> None:
    draw.text(xy, str(text or ""), font=font, fill=fill)


def receipt_jpg_bytes(row: dict[str, Any]) -> bytes:
    labels = TEXT[st.session_state.language]
    width, height = 1400, 900
    margin = 70
    image = Image.new("RGB", (width, height), "#fffdf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    head_font = load_font(25, bold=True)
    body_font = load_font(24)
    small_font = load_font(21)

    border = "#2f2a25"
    fill_head = "#f4ead8"
    draw.rectangle((margin, 30, width - margin, height - 40), outline=border, width=2)

    y = 85
    draw_text(draw, (margin + 40, y), labels["receipt_title"], title_font)
    draw_text(draw, (width - 330, y + 10), f"{labels['tax_id_label']}: {row['seller_tax_id']}", small_font)
    y += 95
    draw.line((margin + 40, y, width - margin - 40, y), fill=border, width=3)
    y += 32
    draw_text(draw, (margin + 40, y), f"{labels['receipt_no']}: {row['receipt_no']}", body_font)
    draw_text(draw, (width - 430, y), f"{labels['receipt_date']}: {row['receipt_date']}", body_font)
    y += 52
    draw.line((margin + 40, y, width - margin - 40, y), fill=border, width=1)

    y += 32
    left_x = margin + 40
    right_x = margin + 650
    draw_text(draw, (left_x, y), labels["seller_name"], head_font)
    draw_text(draw, (left_x, y + 42), row["seller_name"], body_font)
    draw_text(draw, (right_x, y), labels["seller_address"], head_font)
    draw_text(draw, (right_x, y + 42), row["seller_address"], body_font)
    y += 92
    draw_text(draw, (left_x, y), labels["seller_phone"], head_font)
    draw_text(draw, (left_x, y + 42), row["seller_phone"], body_font)
    draw_text(draw, (right_x, y), labels["buyer_name"], head_font)
    draw_text(draw, (right_x, y + 42), row["buyer_name"], body_font)

    table_x = margin + 40
    table_y = y + 110
    table_w = width - (margin + 40) * 2
    row_h = 70
    col_widths = [280, 180, 210, 220, table_w - 890]
    headers = [labels["item_name"], labels["quantity"], labels["unit_price"], labels["amount"], labels["line_note"]]
    values = [row["item_name"], row["quantity"], row["unit_price"], row["amount"], row["notes"]]
    draw.rectangle((table_x, table_y, table_x + table_w, table_y + row_h), fill=fill_head, outline=border, width=2)
    current_x = table_x
    for index, col_w in enumerate(col_widths):
        draw.rectangle((current_x, table_y, current_x + col_w, table_y + row_h * 4), outline=border, width=2)
        draw_text(draw, (current_x + 18, table_y + 22), headers[index], head_font)
        draw_text(draw, (current_x + 18, table_y + row_h + 22), values[index], body_font)
        current_x += col_w
    for line in range(1, 4):
        draw.line((table_x, table_y + row_h * line, table_x + table_w, table_y + row_h * line), fill=border, width=2)

    y = table_y + row_h * 4 + 65
    total_text = f"{labels['grand_total']}: {row['total']}"
    total_box = draw.textbbox((0, 0), total_text, font=title_font)
    draw_text(draw, (width - margin - 40 - (total_box[2] - total_box[0]), y), total_text, title_font)
    y += 85
    sign_text = f"{labels['signature']}: ____________________"
    sign_box = draw.textbbox((0, 0), sign_text, font=small_font)
    draw_text(draw, (width - margin - 40 - (sign_box[2] - sign_box[0]), y), sign_text, small_font)

    output = BytesIO()
    image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def append_local(row: dict[str, Any]) -> None:
    path = local_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=SHEET_HEADERS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def normalize_records(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(columns=SHEET_HEADERS)
    normalized = records.copy()
    for header in SHEET_HEADERS:
        if header not in normalized.columns:
            normalized[header] = ""
    normalized = normalized[SHEET_HEADERS].fillna("")
    for header in SHEET_HEADERS:
        normalized[header] = normalized[header].astype(str)
    return normalized


def record_key(row: pd.Series) -> str:
    receipt_no = str(row.get("receipt_no", "")).strip()
    created_at = str(row.get("created_at", "")).strip()
    if receipt_no or created_at:
        return f"{created_at}|{receipt_no}"
    return "|".join(str(row.get(header, "")).strip() for header in SHEET_HEADERS)


def merge_new_records(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    existing = normalize_records(existing)
    incoming = normalize_records(incoming)
    existing_keys = set(existing.apply(record_key, axis=1)) if not existing.empty else set()
    new_rows = incoming[~incoming.apply(record_key, axis=1).isin(existing_keys)]
    if new_rows.empty:
        return pd.DataFrame(columns=SHEET_HEADERS)
    return new_rows


def records_csv_bytes(records: pd.DataFrame) -> bytes:
    normalized = normalize_records(records)
    return normalized.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def import_local_records(incoming: pd.DataFrame) -> int:
    existing, _ = read_local()
    new_rows = merge_new_records(existing, incoming)
    if new_rows.empty:
        return 0
    path = local_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = pd.concat([normalize_records(existing), new_rows], ignore_index=True)
    merged.to_csv(path, index=False, encoding="utf-8-sig")
    return len(new_rows)


def import_google_records(incoming: pd.DataFrame) -> int:
    worksheet, _, _ = get_google_sheet()
    if worksheet is None:
        return 0
    existing = pd.DataFrame(worksheet.get_all_records(), columns=SHEET_HEADERS)
    new_rows = merge_new_records(existing, incoming)
    if new_rows.empty:
        return 0
    worksheet.append_rows(new_rows[SHEET_HEADERS].values.tolist(), value_input_option="USER_ENTERED")
    return len(new_rows)


def read_local() -> tuple[pd.DataFrame, str | None]:
    path = local_log_path()
    if not path.exists():
        return pd.DataFrame(columns=SHEET_HEADERS), None
    try:
        return pd.read_csv(path), None
    except Exception as exc:
        return pd.DataFrame(columns=SHEET_HEADERS), str(exc)


def append_record(row: dict[str, Any]) -> tuple[str, str | None]:
    worksheet, sheet_url, error = get_google_sheet()
    row["sheet_url"] = sheet_url or ""
    if worksheet is not None:
        worksheet.append_row([row.get(key, "") for key in SHEET_HEADERS], value_input_option="USER_ENTERED")
        return "google", sheet_url
    append_local(row)
    return "local", error


def read_records() -> tuple[pd.DataFrame, str | None]:
    worksheet, sheet_url, _ = get_google_sheet()
    if worksheet is None:
        records, _ = read_local()
        return records, None
    values = worksheet.get_all_records()
    return pd.DataFrame(values, columns=SHEET_HEADERS), sheet_url


def receipt_html(row: dict[str, Any]) -> str:
    lang = st.session_state.language
    labels = TEXT[lang]
    return f"""
<section class="receipt-paper">
  <div class="receipt-top">
    <h2>{labels["receipt_title"]}</h2>
    <div>{labels["tax_id_label"]}: {row["seller_tax_id"]}</div>
  </div>
  <div class="receipt-meta">
    <span>{labels["receipt_no"]}: {row["receipt_no"]}</span>
    <span>{labels["receipt_date"]}: {row["receipt_date"]}</span>
  </div>
  <div class="receipt-grid">
    <div><strong>{labels["seller_name"]}</strong><br>{row["seller_name"]}</div>
    <div><strong>{labels["seller_address"]}</strong><br>{row["seller_address"]}</div>
    <div><strong>{labels["seller_phone"]}</strong><br>{row["seller_phone"]}</div>
    <div><strong>{labels["buyer_name"]}</strong><br>{row["buyer_name"]}</div>
  </div>
  <table class="receipt-table">
    <thead>
      <tr>
        <th>{labels["item_name"]}</th>
        <th>{labels["quantity"]}</th>
        <th>{labels["unit_price"]}</th>
        <th>{labels["amount"]}</th>
        <th>{labels["line_note"]}</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>{row["item_name"]}</td>
        <td>{row["quantity"]}</td>
        <td>{row["unit_price"]}</td>
        <td>{row["amount"]}</td>
        <td>{row["notes"]}</td>
      </tr>
      <tr><td>&nbsp;</td><td></td><td></td><td></td><td></td></tr>
      <tr><td>&nbsp;</td><td></td><td></td><td></td><td></td></tr>
    </tbody>
  </table>
  <div class="receipt-total">{labels["grand_total"]}: {row["total"]}</div>
  <div class="receipt-sign">{labels["signature"]}: ____________________</div>
</section>
"""


def styles() -> None:
    st.markdown(
        """
<style>
.block-container { max-width: 1080px; padding-top: 2rem; }
.receipt-paper {
  background: #fffdf7;
  border: 1px solid #2f2a25;
  color: #1f1b18;
  padding: 28px;
  margin-top: 16px;
  font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
}
.receipt-top {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: start;
  border-bottom: 2px solid #2f2a25;
  padding-bottom: 12px;
}
.receipt-top h2 { margin: 0; font-size: 28px; letter-spacing: 0; }
.receipt-meta {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 0;
  border-bottom: 1px solid #2f2a25;
}
.receipt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 14px 0;
}
.receipt-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}
.receipt-table th, .receipt-table td {
  border: 1px solid #2f2a25;
  padding: 10px;
  min-height: 42px;
  word-break: break-word;
}
.receipt-table th { background: #f4ead8; }
.receipt-total {
  text-align: right;
  font-size: 20px;
  font-weight: 700;
  padding-top: 18px;
}
.receipt-sign {
  padding-top: 30px;
  text-align: right;
}
@media (max-width: 720px) {
  .receipt-top, .receipt-meta { display: block; }
  .receipt-grid { grid-template-columns: 1fr; }
  .receipt-paper { padding: 16px; }
}
</style>
""",
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="mom_dr receipt log", layout="wide")
    if "language" not in st.session_state:
        st.session_state.language = "zh"
    if "local_log_folder" not in st.session_state:
        st.session_state.local_log_folder = default_local_log_folder()
    styles()

    st.session_state.language = st.sidebar.radio(
        "Language / 語言",
        ["zh", "en"],
        format_func=lambda code: TEXT[code]["language_name"],
        horizontal=True,
    )

    st.title(t("page_title"))
    worksheet, sheet_url, error = get_google_sheet()
    if worksheet is None:
        st.info(t("missing_google"))
        if error:
            st.caption(error)
    else:
        st.success(t("connected_google"))
        st.link_button(t("sheet_link"), sheet_url)

    receipt_tab, history_tab, settings_tab = st.tabs([t("receipt_tab"), t("history_tab"), t("settings_tab")])

    with receipt_tab:
        st.caption(t("print_hint"))
        with st.form("receipt_form", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader(t("receipt_info"))
                receipt_no = st.text_input(t("receipt_no"), value=datetime.now().strftime("R%Y%m%d%H%M"))
                receipt_date = st.date_input(t("receipt_date"), value=date.today())
                buyer_name = st.text_input(t("buyer_name"), value="mom_dr")
            with col_b:
                st.subheader(t("seller_info"))
                seller_name = st.text_input(t("seller_name"))
                seller_tax_id = st.text_input(t("seller_tax_id"))
                seller_address = st.text_input(t("seller_address"))
                seller_phone = st.text_input(t("seller_phone"))

            st.subheader(t("items"))
            col_1, col_2, col_3, col_4 = st.columns([3, 1, 1, 1])
            with col_1:
                item_name = st.text_input(t("item_name"))
            with col_2:
                quantity = st.number_input(t("quantity"), min_value=0.0, value=1.0, step=1.0)
            with col_3:
                unit_price = st.number_input(t("unit_price"), min_value=0.0, value=0.0, step=1.0)
            amount = money(quantity) * money(unit_price)
            with col_4:
                st.metric(t("amount"), f"{amount:,.0f}")
            notes = st.text_area(t("notes"), height=90)

            row = {
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "receipt_no": receipt_no,
                "language": st.session_state.language,
                "receipt_date": receipt_date.isoformat(),
                "seller_name": seller_name,
                "seller_tax_id": seller_tax_id,
                "seller_address": seller_address,
                "seller_phone": seller_phone,
                "buyer_name": buyer_name,
                "item_name": item_name,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": f"{amount:.0f}",
                "notes": notes,
                "total": f"{amount:.0f}",
                "sheet_url": sheet_url or "",
            }
            submitted = st.form_submit_button(t("save"), type="primary")

        if submitted:
            target, maybe_error = append_record(row)
            st.success(t("saved"))
            if target == "google" and maybe_error:
                st.link_button(t("sheet_link"), maybe_error)

        html = receipt_html(row)
        st.markdown(html, unsafe_allow_html=True)
        st.download_button(
            t("download_jpg"),
            data=receipt_jpg_bytes(row),
            file_name=f"{receipt_no or 'receipt'}.jpg",
            mime="image/jpeg",
        )

    with history_tab:
        source_options = ["google", "local"] if worksheet is not None else ["local"]
        record_source = st.radio(
            t("record_source"),
            source_options,
            format_func=lambda value: t("google_records") if value == "google" else t("local_records"),
            horizontal=True,
        )
        if record_source == "google":
            records, records_url = read_records()
            local_error = None
        else:
            records, local_error = read_local()
            records_url = None
            if local_error:
                st.error(f"{t('local_read_error')}: {local_error}")
        if records.empty:
            st.info(t("no_records"))
        else:
            st.dataframe(records.sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
            st.download_button(
                t("download_records"),
                data=records_csv_bytes(records),
                file_name=f"mom_dr_receipt_log_{date.today().isoformat()}.csv",
                mime="text/csv",
            )
        if records_url:
            st.link_button(t("sheet_link"), records_url)

        st.divider()
        st.subheader(t("backup_restore"))
        uploaded_records_file = st.file_uploader(t("upload_records"), type=["csv"])
        if uploaded_records_file is not None:
            try:
                uploaded_records = normalize_records(pd.read_csv(uploaded_records_file))
                st.dataframe(uploaded_records, use_container_width=True, hide_index=True)
                col_import_a, col_import_b = st.columns(2)
                with col_import_a:
                    if st.button(t("import_local"), type="primary"):
                        count = import_local_records(uploaded_records)
                        if count:
                            st.success(t("imported").format(count=count))
                        else:
                            st.info(t("no_new_records"))
                with col_import_b:
                    if worksheet is not None and st.button(t("import_google")):
                        count = import_google_records(uploaded_records)
                        if count:
                            st.success(t("imported").format(count=count))
                        else:
                            st.info(t("no_new_records"))
            except Exception as exc:
                st.error(f"{t('invalid_csv')} ({exc})")

    with settings_tab:
        connection = t("google_sheet") if worksheet is not None else t("local_csv")
        st.metric(t("connection"), connection)
        if sheet_url:
            st.success(t("google_ready"))
            st.write(sheet_url)
        else:
            st.warning(t("google_not_ready"))
            if error:
                st.caption(error)
        st.text_input(
            t("local_log_folder"),
            key="local_log_folder",
            help=t("local_folder_help"),
        )
        st.caption(f"{t('local_log_file')}: {local_log_path()}")
        st.code(
            """
share_with_email = "your-gmail@gmail.com"
google_drive_folder_id = "optional-shared-folder-id"
local_log_folder = "C:/Users/your-name/Documents/mom_dr_logs"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
""".strip(),
            language="toml",
        )


if __name__ == "__main__":
    main()
