from __future__ import annotations

import csv
import html as html_lib
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
LOCAL_RECEIPT_FOLDER_NAME = "receipts"
SHEET_NAME = "mom_dr收據_log"
DEFAULT_CURRENCY = "TWD"
CURRENCY_OPTIONS = {
    "TWD": "TWD - New Taiwan Dollar",
    "USD": "USD - US Dollar",
    "JPY": "JPY - Japanese Yen",
    "EUR": "EUR - Euro",
    "CNY": "CNY - Chinese Yuan",
}
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
    "patient_dob",
    "passport_no",
    "item_name",
    "quantity",
    "unit_price",
    "amount",
    "notes",
    "total",
    "sheet_url",
    "items_json",
    "currency",
]
DEFAULT_VENDOR = {
    "zh": {
        "seller_name": "誠品診所",
        "seller_tax_id": "97974582",
        "seller_address": "106臺北市大安區敦安里敦化南路1段317號",
        "seller_phone": "",
    },
    "en": {
        "seller_name": "Chen Pin Clinic",
        "seller_tax_id": "97974582",
        "seller_address": "No. 317, Sec. 1, Dunhua S. Rd., Da'an Dist., Taipei City 106, Taiwan",
        "seller_phone": "",
    },
}


TEXT = {
    "zh": {
        "language_name": "中文",
        "page_title": "mom_dr 收據紀錄",
        "receipt_tab": "建立收據",
        "history_tab": "紀錄",
        "settings_tab": "連線狀態",
        "language": "語言",
        "receipt_info": "收據資料",
        "seller_info": "診所資訊",
        "buyer_info": "病患資訊",
        "items": "明細",
        "receipt_no": "收據編號",
        "receipt_date": "開立日期",
        "currency": "幣別",
        "seller_name": "診所名稱",
        "seller_tax_id": "統一編號 / 身分證字號",
        "seller_address": "地址",
        "seller_phone": "電話",
        "buyer_name": "病患姓名",
        "patient_dob": "出生日期",
        "passport_no": "護照號碼",
        "item_name": "品名",
        "quantity": "數量",
        "unit_price": "單價",
        "amount": "金額",
        "notes": "備註",
        "total": "合計",
        "add_item": "新增明細",
        "clear_items": "清空明細",
        "current_amount": "本筆金額",
        "current_items": "目前明細",
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
        "local_receipt_folder": "本機收據 JPG 資料夾路徑",
        "local_receipt_file": "已儲存收據 JPG",
        "local_receipt_browse": "瀏覽本機已存 JPG",
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
        "select_record_print": "選一筆紀錄預覽 / 列印",
        "selected_receipt": "選取的收據",
        "saved_local_jpg": "已儲存 JPG 到本機資料夾。",
        "no_local_jpg": "目前沒有本機 JPG 檔。",
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
        "seller_info": "Clinic information",
        "buyer_info": "Patient information",
        "items": "Line item",
        "receipt_no": "Receipt no.",
        "receipt_date": "Issue date",
        "currency": "Currency",
        "seller_name": "Clinic's name",
        "seller_tax_id": "Tax ID / personal ID",
        "seller_address": "Address",
        "seller_phone": "Phone",
        "buyer_name": "Patient's name",
        "patient_dob": "Date of birth",
        "passport_no": "Passport no.",
        "item_name": "Item",
        "quantity": "Quantity",
        "unit_price": "Unit price",
        "amount": "Amount",
        "notes": "Notes",
        "total": "Total",
        "add_item": "Add item",
        "clear_items": "Clear items",
        "current_amount": "Current amount",
        "current_items": "Current items",
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
        "local_receipt_folder": "Local receipt JPG folder path",
        "local_receipt_file": "Saved receipt JPG",
        "local_receipt_browse": "Browse saved local JPGs",
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
        "select_record_print": "Select a record to preview / print",
        "selected_receipt": "Selected receipt",
        "saved_local_jpg": "Saved JPG to the local folder.",
        "no_local_jpg": "No local JPG files yet.",
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


def money_text(value: Any) -> str:
    return f"{money(value):.0f}"


def row_currency(row: dict[str, Any]) -> str:
    currency = str(row.get("currency", "") or DEFAULT_CURRENCY).strip().upper()
    return currency if currency else DEFAULT_CURRENCY


def money_display(value: Any, currency: str | None = None) -> str:
    return f"{currency or DEFAULT_CURRENCY} {money(value):,.0f}"


def money_header(label: str, currency: str | None = None) -> str:
    return f"{label} ({currency or DEFAULT_CURRENCY})"


def default_line_items() -> pd.DataFrame:
    return pd.DataFrame(columns=["item_name", "quantity", "unit_price", "amount", "notes"])


def calculate_line_items(items: pd.DataFrame) -> pd.DataFrame:
    if items is None or items.empty:
        items = default_line_items()
    calculated = items.copy()
    for column in ["item_name", "quantity", "unit_price", "amount", "notes"]:
        if column not in calculated.columns:
            calculated[column] = "" if column in ["item_name", "notes"] else 0.0
    calculated["quantity"] = pd.to_numeric(calculated["quantity"], errors="coerce").fillna(0)
    calculated["unit_price"] = pd.to_numeric(calculated["unit_price"], errors="coerce").fillna(0)
    calculated["amount"] = calculated["quantity"] * calculated["unit_price"]
    calculated["item_name"] = calculated["item_name"].fillna("").astype(str)
    calculated["notes"] = calculated["notes"].fillna("").astype(str)
    keep = (calculated["item_name"].str.strip() != "") | (calculated["quantity"] != 0) | (calculated["unit_price"] != 0) | (calculated["notes"].str.strip() != "")
    calculated = calculated[keep]
    if calculated.empty:
        return pd.DataFrame(columns=["item_name", "quantity", "unit_price", "amount", "notes"])
    return calculated[["item_name", "quantity", "unit_price", "amount", "notes"]].reset_index(drop=True)


def line_items_total(items: pd.DataFrame) -> Decimal:
    calculated = calculate_line_items(items)
    total = Decimal("0")
    for value in calculated["amount"]:
        total += money(value)
    return total


def items_to_json(items: pd.DataFrame) -> str:
    calculated = calculate_line_items(items)
    payload = []
    for item in calculated.to_dict("records"):
        payload.append(
            {
                "item_name": item.get("item_name", ""),
                "quantity": float(item.get("quantity") or 0),
                "unit_price": float(item.get("unit_price") or 0),
                "amount": float(item.get("amount") or 0),
                "notes": item.get("notes", ""),
            }
        )
    return json.dumps(payload, ensure_ascii=False)


def items_from_row(row: dict[str, Any]) -> pd.DataFrame:
    raw_items = str(row.get("items_json", "") or "").strip()
    if raw_items:
        try:
            parsed = json.loads(raw_items)
            if isinstance(parsed, list):
                return calculate_line_items(pd.DataFrame(parsed))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return calculate_line_items(
        pd.DataFrame(
            [
                {
                    "item_name": row.get("item_name", ""),
                    "quantity": row.get("quantity", 0),
                    "unit_price": row.get("unit_price", 0),
                    "amount": row.get("amount", 0),
                    "notes": row.get("notes", ""),
                }
            ]
        )
    )


def row_item_summary(items: pd.DataFrame, column: str) -> str:
    calculated = calculate_line_items(items)
    if column == "amount":
        return "\n".join(money_text(value) for value in calculated[column])
    return "\n".join(str(value) for value in calculated[column])


def current_input_line_items() -> pd.DataFrame:
    item_name = str(st.session_state.get("new_item_name", "") or "")
    quantity = st.session_state.get("new_quantity", 0.0)
    unit_price = st.session_state.get("new_unit_price", 0.0)
    notes = str(st.session_state.get("new_notes", "") or "")
    has_content = item_name.strip() or notes.strip() or money(quantity) != 0 or money(unit_price) != 0
    if not has_content:
        return default_line_items()
    return calculate_line_items(
        pd.DataFrame(
            [
                {
                    "item_name": item_name,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "notes": notes,
                }
            ]
        )
    )


def all_visible_line_items() -> pd.DataFrame:
    return calculate_line_items(pd.concat([st.session_state.line_items, current_input_line_items()], ignore_index=True))


def add_current_item_to_list() -> None:
    draft = current_input_line_items()
    if not draft.empty:
        st.session_state.line_items = calculate_line_items(pd.concat([st.session_state.line_items, draft], ignore_index=True))
    st.session_state.new_item_name = ""
    st.session_state.new_quantity = 1.0
    st.session_state.new_unit_price = 0.0
    st.session_state.new_notes = ""


def clear_line_items() -> None:
    st.session_state.line_items = default_line_items()
    st.session_state.new_item_name = ""
    st.session_state.new_quantity = 1.0
    st.session_state.new_unit_price = 0.0
    st.session_state.new_notes = ""


def display_line_items(items: pd.DataFrame) -> pd.DataFrame:
    labels = TEXT[st.session_state.language]
    currency = st.session_state.get("currency", DEFAULT_CURRENCY)
    displayed = calculate_line_items(items).copy()
    if displayed.empty:
        return displayed
    displayed["unit_price"] = displayed["unit_price"].map(lambda value: money_display(value, currency))
    displayed["amount"] = displayed["amount"].map(lambda value: money_display(value, currency))
    return displayed.rename(
        columns={
            "item_name": labels["item_name"],
            "quantity": labels["quantity"],
            "unit_price": labels["unit_price"],
            "amount": labels["amount"],
            "notes": labels["notes"],
        }
    )


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


def default_local_receipt_folder() -> str:
    try:
        secret_value = st.secrets.get("local_receipt_folder")
    except Exception:
        secret_value = None
    return str(secret_value or os.environ.get("MOM_DR_RECEIPT_FOLDER") or (APP_DIR / LOCAL_RECEIPT_FOLDER_NAME))


def local_log_path() -> Path:
    folder = st.session_state.get("local_log_folder", default_local_log_folder())
    return Path(str(folder)).expanduser() / LOCAL_LOG_FILENAME


def local_receipt_folder() -> Path:
    folder = st.session_state.get("local_receipt_folder", default_local_receipt_folder())
    return Path(str(folder)).expanduser()


def safe_receipt_filename(row: dict[str, Any]) -> str:
    raw = str(row.get("receipt_no") or datetime.now().strftime("R%Y%m%d%H%M%S"))
    safe = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in raw)
    return f"{safe}.jpg"


def save_local_receipt_jpg(row: dict[str, Any]) -> Path:
    folder = local_receipt_folder()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / safe_receipt_filename(row)
    path.write_bytes(receipt_jpg_bytes(row))
    return path


def local_receipt_files() -> list[Path]:
    folder = local_receipt_folder()
    if not folder.exists():
        return []
    return sorted(folder.glob("*.jpg"), key=lambda path: path.stat().st_mtime, reverse=True)


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


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, text: Any, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    value = str(text or "")
    if not value:
        return [""]
    lines: list[str] = []
    for paragraph in value.splitlines() or [""]:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if text_width(draw, candidate, font) <= max_width:
                current = candidate
                continue
            if current:
                lines.append(current)
            if text_width(draw, word, font) <= max_width:
                current = word
                continue
            chunk = ""
            for char in word:
                candidate_chunk = f"{chunk}{char}"
                if text_width(draw, candidate_chunk, font) <= max_width:
                    chunk = candidate_chunk
                else:
                    if chunk:
                        lines.append(chunk)
                    chunk = char
            current = chunk
        lines.append(current)
    return lines


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: Any,
    font: ImageFont.ImageFont,
    max_width: int,
    fill: str = "#1f1b18",
    line_gap: int = 6,
    max_lines: int | None = None,
) -> int:
    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    x, y = xy
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + line_gap
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def receipt_jpg_bytes(row: dict[str, Any]) -> bytes:
    labels = TEXT[st.session_state.language]
    items = items_from_row(row)
    currency = row_currency(row)
    width, height = 1600, 1200
    margin = 70
    image = Image.new("RGB", (width, height), "#fffdf7")
    draw = ImageDraw.Draw(image)
    title_font = load_font(42, bold=True)
    head_font = load_font(25, bold=True)
    body_font = load_font(24)
    small_font = load_font(21)

    border = "#2f2a25"
    fill_head = "#f4ead8"
    content_right = width - margin - 40
    draw.rectangle((margin, 30, width - margin, height - 40), outline=border, width=2)

    y = 85
    draw_text(draw, (margin + 40, y), labels["receipt_title"], title_font)
    draw_text(draw, (width - 330, y + 10), f"{labels['tax_id_label']}: {row['seller_tax_id']}", small_font)
    y += 95
    draw.line((margin + 40, y, content_right, y), fill=border, width=3)
    y += 32
    draw_text(draw, (margin + 40, y), f"{labels['receipt_no']}: {row['receipt_no']}", body_font)
    draw_text(draw, (width - 520, y), f"{labels['receipt_date']}: {row['receipt_date']}", body_font)
    y += 52
    draw.line((margin + 40, y, content_right, y), fill=border, width=1)

    y += 32
    left_x = margin + 40
    right_x = margin + 720
    left_w = 540
    right_w = content_right - right_x
    draw_text(draw, (left_x, y), labels["seller_name"], head_font)
    left_bottom = draw_wrapped_text(draw, (left_x, y + 42), row["seller_name"], body_font, left_w, max_lines=2)
    draw_text(draw, (right_x, y), labels["seller_address"], head_font)
    right_bottom = draw_wrapped_text(draw, (right_x, y + 42), row["seller_address"], body_font, right_w, max_lines=3)
    y = max(left_bottom, right_bottom) + 24
    draw_text(draw, (left_x, y), labels["seller_phone"], head_font)
    left_bottom = draw_wrapped_text(draw, (left_x, y + 42), row["seller_phone"], body_font, left_w, max_lines=1)
    draw_text(draw, (right_x, y), labels["buyer_name"], head_font)
    right_bottom = draw_wrapped_text(draw, (right_x, y + 42), row["buyer_name"], body_font, right_w, max_lines=2)
    y = max(left_bottom, right_bottom) + 24
    draw_text(draw, (left_x, y), labels["patient_dob"], head_font)
    left_bottom = draw_wrapped_text(draw, (left_x, y + 42), row.get("patient_dob", ""), body_font, left_w, max_lines=1)
    draw_text(draw, (right_x, y), labels["passport_no"], head_font)
    right_bottom = draw_wrapped_text(draw, (right_x, y + 42), row.get("passport_no", ""), body_font, right_w, max_lines=1)
    y = max(left_bottom, right_bottom)

    table_x = margin + 40
    table_y = y + 70
    table_w = width - (margin + 40) * 2
    row_h = 72
    col_widths = [320, 160, 260, 260, table_w - 1000]
    headers = [
        labels["item_name"],
        labels["quantity"],
        money_header(labels["unit_price"], currency),
        money_header(labels["amount"], currency),
        labels["line_note"],
    ]
    draw.rectangle((table_x, table_y, table_x + table_w, table_y + row_h), fill=fill_head, outline=border, width=2)
    current_x = table_x
    visible_rows = max(4, len(items))
    table_rows = visible_rows + 1
    for index, col_w in enumerate(col_widths):
        draw.rectangle((current_x, table_y, current_x + col_w, table_y + row_h * table_rows), outline=border, width=2)
        draw_wrapped_text(draw, (current_x + 18, table_y + 14), headers[index], head_font, col_w - 28, max_lines=2, line_gap=3)
        current_x += col_w
    for row_index, item in items.iterrows():
        values = [
            item["item_name"],
            item["quantity"],
            money_display(item["unit_price"], currency),
            money_display(item["amount"], currency),
            item["notes"],
        ]
        current_x = table_x
        for index, col_w in enumerate(col_widths):
            draw_wrapped_text(
                draw,
                (current_x + 18, table_y + row_h * (row_index + 1) + 16),
                values[index],
                small_font,
                col_w - 28,
                max_lines=2,
                line_gap=3,
            )
            current_x += col_w
    for line in range(1, table_rows):
        draw.line((table_x, table_y + row_h * line, table_x + table_w, table_y + row_h * line), fill=border, width=2)

    y = min(table_y + row_h * table_rows + 65, height - 190)
    total_text = f"{labels['grand_total']}: {money_display(row['total'], currency)}"
    total_box = draw.textbbox((0, 0), total_text, font=title_font)
    draw_text(draw, (content_right - (total_box[2] - total_box[0]), y), total_text, title_font)
    y += 85
    sign_text = f"{labels['signature']}: ____________________"
    sign_box = draw.textbbox((0, 0), sign_text, font=small_font)
    draw_text(draw, (content_right - (sign_box[2] - sign_box[0]), y), sign_text, small_font)

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
    if "currency" in normalized.columns:
        normalized["currency"] = normalized["currency"].replace("", DEFAULT_CURRENCY).fillna(DEFAULT_CURRENCY)
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


def row_to_dict(row: pd.Series) -> dict[str, Any]:
    normalized = {header: row.get(header, "") for header in SHEET_HEADERS}
    return normalized


def record_option_label(index: int, row: pd.Series) -> str:
    receipt_no = str(row.get("receipt_no", "")).strip() or f"#{index + 1}"
    receipt_date = str(row.get("receipt_date", "")).strip()
    item_name = str(row.get("item_name", "")).strip()
    total = str(row.get("total", "")).strip()
    currency = str(row.get("currency", "") or DEFAULT_CURRENCY).strip()
    parts = [receipt_no]
    if receipt_date:
        parts.append(receipt_date)
    if item_name:
        parts.append(item_name)
    if total:
        parts.append(money_display(total, currency))
    return " | ".join(parts)


def selected_record_tools(records: pd.DataFrame, key_prefix: str) -> None:
    normalized = normalize_records(records)
    if normalized.empty:
        return
    options = list(range(len(normalized)))
    selected_index = st.selectbox(
        t("select_record_print"),
        options,
        format_func=lambda index: record_option_label(index, normalized.iloc[index]),
        key=f"{key_prefix}_selected_record",
    )
    selected_row = row_to_dict(normalized.iloc[selected_index])
    st.subheader(t("selected_receipt"))
    st.markdown(receipt_html(selected_row), unsafe_allow_html=True)
    st.download_button(
        t("download_jpg"),
        data=receipt_jpg_bytes(selected_row),
        file_name=safe_receipt_filename(selected_row),
        mime="image/jpeg",
        key=f"{key_prefix}_download_jpg",
    )


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
    items = items_from_row(row)
    currency = row_currency(row)
    item_rows = "".join(
        "<tr>"
        f"<td>{html_lib.escape(str(item['item_name']))}</td>"
        f"<td>{html_lib.escape(str(item['quantity']))}</td>"
        f"<td>{money_display(item['unit_price'], currency)}</td>"
        f"<td>{money_display(item['amount'], currency)}</td>"
        f"<td>{html_lib.escape(str(item['notes']))}</td>"
        "</tr>"
        for _, item in items.iterrows()
    )
    empty_rows = "".join("<tr><td>&nbsp;</td><td></td><td></td><td></td><td></td></tr>" for _ in range(max(0, 3 - len(items))))
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
    <div><strong>{labels["patient_dob"]}</strong><br>{row.get("patient_dob", "")}</div>
    <div><strong>{labels["passport_no"]}</strong><br>{row.get("passport_no", "")}</div>
  </div>
  <table class="receipt-table">
    <thead>
      <tr>
        <th>{labels["item_name"]}</th>
        <th>{labels["quantity"]}</th>
        <th>{money_header(labels["unit_price"], currency)}</th>
        <th>{money_header(labels["amount"], currency)}</th>
        <th>{labels["line_note"]}</th>
      </tr>
    </thead>
    <tbody>
{item_rows}
{empty_rows}
    </tbody>
  </table>
  <div class="receipt-total">{labels["grand_total"]}: {money_display(row["total"], currency)}</div>
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
    if "local_receipt_folder" not in st.session_state:
        st.session_state.local_receipt_folder = default_local_receipt_folder()
    if "line_items" not in st.session_state:
        st.session_state.line_items = default_line_items()
    if "currency" not in st.session_state:
        st.session_state.currency = DEFAULT_CURRENCY
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
        default_vendor = DEFAULT_VENDOR[st.session_state.language]
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader(t("receipt_info"))
            receipt_no = st.text_input(t("receipt_no"), value=datetime.now().strftime("CPC%Y%m%d"))
            receipt_date = st.date_input(t("receipt_date"), value=date.today())
            currency = st.radio(
                t("currency"),
                list(CURRENCY_OPTIONS.keys()),
                key="currency",
                horizontal=True,
            )
            st.subheader(t("buyer_info"))
            buyer_name = st.text_input(t("buyer_name"), value="")
            patient_dob = st.date_input(t("patient_dob"), value=None, min_value=date(1900, 1, 1), max_value=date.today())
            passport_no = st.text_input(t("passport_no"), value="")
        with col_b:
            st.subheader(t("seller_info"))
            seller_name = st.text_input(t("seller_name"), value=default_vendor["seller_name"])
            seller_tax_id = st.text_input(t("seller_tax_id"), value=default_vendor["seller_tax_id"])
            seller_address = st.text_input(t("seller_address"), value=default_vendor["seller_address"])
            seller_phone = st.text_input(t("seller_phone"), value=default_vendor["seller_phone"])

        st.subheader(t("items"))
        item_col, qty_col, price_col, amount_col = st.columns([3, 1, 1, 1])
        with item_col:
            new_item_name = st.text_input(t("item_name"), key="new_item_name")
        with qty_col:
            new_quantity = st.number_input(t("quantity"), min_value=0.0, value=1.0, step=1.0, key="new_quantity")
        with price_col:
            new_unit_price = st.number_input(t("unit_price"), min_value=0.0, value=0.0, step=1.0, key="new_unit_price")
        new_amount = money(new_quantity) * money(new_unit_price)
        with amount_col:
            st.metric(t("current_amount"), money_display(new_amount, currency))
        new_notes = st.text_input(t("notes"), key="new_notes")

        add_col, clear_col = st.columns([1, 4])
        with add_col:
            st.button(t("add_item"), type="secondary", on_click=add_current_item_to_list)
        with clear_col:
            st.button(t("clear_items"), on_click=clear_line_items)

        line_items = all_visible_line_items()
        total = line_items_total(line_items)
        if not line_items.empty:
            st.caption(t("current_items"))
            st.dataframe(display_line_items(line_items), width="stretch", hide_index=True)
        st.metric(t("total"), money_display(total, currency))

        row = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "receipt_no": receipt_no,
            "language": st.session_state.language,
            "receipt_date": receipt_date.isoformat(),
            "currency": currency,
            "seller_name": seller_name,
            "seller_tax_id": seller_tax_id,
            "seller_address": seller_address,
            "seller_phone": seller_phone,
            "buyer_name": buyer_name,
            "patient_dob": patient_dob.isoformat() if patient_dob else "",
            "passport_no": passport_no,
            "item_name": row_item_summary(line_items, "item_name"),
            "quantity": row_item_summary(line_items, "quantity"),
            "unit_price": row_item_summary(line_items, "unit_price"),
            "amount": row_item_summary(line_items, "amount"),
            "notes": row_item_summary(line_items, "notes"),
            "items_json": items_to_json(line_items),
            "total": f"{total:.0f}",
            "sheet_url": sheet_url or "",
        }
        submitted = st.button(t("save"), type="primary")

        if submitted:
            target, maybe_error = append_record(row)
            saved_jpg_path = save_local_receipt_jpg(row)
            st.success(t("saved"))
            st.caption(f"{t('local_receipt_file')}: {saved_jpg_path}")
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
            st.dataframe(records.sort_values("created_at", ascending=False), width="stretch", hide_index=True)
            selected_record_tools(records, "history")
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
                st.dataframe(uploaded_records, width="stretch", hide_index=True)
                selected_record_tools(uploaded_records, "uploaded")
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
        st.text_input(
            t("local_receipt_folder"),
            key="local_receipt_folder",
            help=t("local_folder_help"),
        )
        st.caption(f"{t('local_receipt_folder')}: {local_receipt_folder()}")
        st.subheader(t("local_receipt_browse"))
        jpg_files = local_receipt_files()
        if not jpg_files:
            st.info(t("no_local_jpg"))
        else:
            selected_file = st.selectbox(
                t("local_receipt_browse"),
                jpg_files,
                format_func=lambda path: path.name,
            )
            st.caption(str(selected_file))
            st.image(str(selected_file), width="stretch")
            st.download_button(
                t("download_jpg"),
                data=selected_file.read_bytes(),
                file_name=selected_file.name,
                mime="image/jpeg",
                key="saved_local_jpg_download",
            )
        st.code(
            """
share_with_email = "your-gmail@gmail.com"
google_drive_folder_id = "optional-shared-folder-id"
local_log_folder = "C:/Users/your-name/Documents/mom_dr_logs"
local_receipt_folder = "C:/Users/your-name/Documents/mom_dr_receipts"

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
