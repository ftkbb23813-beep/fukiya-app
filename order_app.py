import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ===== 設定 =====
SPREADSHEET_ID   = '1_DHnh3SwVreDbWJm56fs6I8fWBwUvmhb2la24yoIHEI'
SHEET_PRODUCTS   = '商品マスタ'
SHEET_HISTORY    = '発注履歴'
CREDENTIALS_FILE = 'credentials.json'
# ================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
]

def get_client():
    import os, json
    if 'gcp_service_account' in st.secrets:
        # Streamlit Cloud
        secret = st.secrets['gcp_service_account']
        # 文字列（JSON）の場合とTOMLセクション（辞書）の場合の両方に対応
        if isinstance(secret, str):
            info = json.loads(secret)
        else:
            info = dict(secret)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        # ローカル開発環境（credentials.json）
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_products():
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_PRODUCTS)
    return sheet.get_all_records()

def write_order(rows):
    client = get_client()
    book = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = book.worksheet(SHEET_HISTORY)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=SHEET_HISTORY, rows=1000, cols=10)
        sheet.append_row(['発注日時', '仕入れ先', '商品名', '発注数', '入数'])
    sheet.append_rows(rows)

# ── UI ──────────────────────────────────────────
st.set_page_config(page_title='フキヤファミリー 発注アプリ', layout='centered')
st.title('📦 フキヤファミリー 発注アプリ')

try:
    all_products = load_products()
except Exception as e:
    st.error(f'データ読み込みエラー：{e}')
    st.stop()

# 仕入れ先一覧
suppliers = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))

st.sidebar.header('🏭 仕入れ先を選択')
selected_supplier = st.sidebar.selectbox('業者名', suppliers)

# 選択業者の商品を絞り込み
products = [p for p in all_products if p.get('仕入れ先', '') == selected_supplier]

st.subheader(f'{selected_supplier}　({len(products)}品)')

# 発注数入力
order_quantities = {}
for p in products:
    name    = p.get('商品名', '')
    min_qty = int(p.get('入数', 0) or 0)

    col1, col2 = st.columns([3, 1])
    with col1:
        label = f"{name}"
        if min_qty > 0:
            label += f"　（最小 {min_qty}）"
        st.markdown(label)
    with col2:
        qty = st.number_input(
            '発注数',
            min_value=0,
            value=0,
            step=max(min_qty, 1),
            key=name,
            label_visibility='collapsed'
        )
    order_quantities[name] = (qty, min_qty)

# 発注ボタン
st.divider()
if st.button('✅ 発注する', use_container_width=True, type='primary'):
    errors = []
    to_order = []
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    for p in products:
        name    = p.get('商品名', '')
        qty, min_qty = order_quantities[name]

        if qty == 0:
            continue
        if min_qty > 0 and qty < min_qty:
            errors.append(f'❌ {name}：{qty}は最小発注数（{min_qty}）未満です')
            continue
        to_order.append([now, selected_supplier, name, qty, min_qty])

    if errors:
        for e in errors:
            st.error(e)
    elif not to_order:
        st.warning('発注数を入力してください')
    else:
        try:
            write_order(to_order)
            st.success(f'✅ {len(to_order)}品を発注しました！')
            st.cache_data.clear()
        except Exception as e:
            st.error(f'書き込みエラー：{e}')
