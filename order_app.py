import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import urllib.parse
import json

# ===== 設定 =====
SPREADSHEET_ID  = '1_DHnh3SwVreDbWJm56fs6I8fWBwUvmhb2la24yoIHEI'
SHEET_PRODUCTS  = '商品マスタ'
SHEET_HISTORY   = '発注履歴'
SHEET_SUPPLIERS = '業者マスタ'
CREDENTIALS_FILE = 'credentials.json'
USERS = ['長尾', 'お母さん', '淳一']
# ================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
]

# ── 大きくて読みやすいスタイル ────────────────────────────────
st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 18px; }
  h1 { font-size: 1.8em !important; }
  h2 { font-size: 1.4em !important; }
  .stButton > button {
    font-size: 1.2em !important;
    padding: 0.6em 1.2em !important;
    border-radius: 12px !important;
    width: 100%;
  }
  .order-btn > button { background-color: #1a7f37 !important; color: white !important; font-size: 1.4em !important; }
  .cancel-btn > button { background-color: #b00020 !important; color: white !important; }
  .success-box {
    background: #d4edda; color: #155724;
    padding: 20px; border-radius: 12px;
    font-size: 1.4em; font-weight: bold;
    text-align: center; margin: 16px 0;
  }
  .contact-box {
    background: #e8f4fd; padding: 16px;
    border-radius: 10px; margin: 10px 0;
    font-size: 1.1em;
  }
  .confirm-box {
    background: #fff8e1; padding: 20px;
    border-radius: 12px; border: 2px solid #f0ad4e;
    font-size: 1.1em;
  }
</style>
""", unsafe_allow_html=True)

# ── Google 接続 ────────────────────────────────────────────────
def get_client():
    if 'gcp_service_account' in st.secrets:
        secret = st.secrets['gcp_service_account']
        info = json.loads(secret) if isinstance(secret, str) else dict(secret)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_products():
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_PRODUCTS)
    return sheet.get_all_records()

@st.cache_data(ttl=300)
def load_suppliers():
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_SUPPLIERS)
        rows = sheet.get_all_records()
        return {r['業者名']: r for r in rows if r.get('業者名')}
    except Exception:
        return {}

def write_order(rows):
    client = get_client()
    book = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = book.worksheet(SHEET_HISTORY)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=SHEET_HISTORY, rows=1000, cols=10)
        sheet.append_row(['発注日時', '発注者', '仕入れ先', '品物名', '頼む数', '入数', '発注方法'])
    sheet.append_rows(rows)

# ── 連絡先UI ──────────────────────────────────────────────────
def show_contact(supplier_name, supplier_info, order_text):
    method  = supplier_info.get('発注方法', '').strip()
    contact = supplier_info.get('連絡先', '').strip()

    st.markdown('<div class="contact-box">', unsafe_allow_html=True)
    st.markdown(f'**📋 {supplier_name} への連絡方法**')

    if method == 'メール' and contact:
        subject = urllib.parse.quote(f'【発注】フキヤファミリー')
        body    = urllib.parse.quote(f'お世話になっております。\n以下の通り発注いたします。\n\n{order_text}\n\nよろしくお願いいたします。\nフキヤファミリー')
        mailto  = f'mailto:{contact}?subject={subject}&body={body}'
        st.markdown(f'📧 メール送信先：**{contact}**')
        st.markdown(f'[👆 ここをタップしてメールを開く]({mailto})', unsafe_allow_html=False)

    elif method == '電話' and contact:
        tel = f'tel:{contact.replace("-", "").replace(" ", "")}'
        st.markdown(f'📞 電話番号：**{contact}**')
        st.markdown(f'[👆 ここをタップして電話をかける]({tel})', unsafe_allow_html=False)

    elif method == 'FAX' and contact:
        st.markdown(f'📠 FAX番号：**{contact}**')
        st.markdown('**以下の内容をFAXしてください：**')
        st.code(order_text, language=None)

    elif contact:
        st.markdown(f'📬 連絡先：**{contact}**')

    else:
        st.info('業者マスタに連絡先が登録されていません。')

    st.markdown('</div>', unsafe_allow_html=True)

# ── セッション初期化 ──────────────────────────────────────────
for key, val in [('confirming', False), ('pending', []), ('done', False), ('done_info', [])]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── 画面タイトル ─────────────────────────────────────────────
st.title('📦 フキヤファミリー 発注アプリ')

# ── データ読み込み ────────────────────────────────────────────
try:
    all_products = load_products()
    suppliers_map = load_suppliers()
except Exception as e:
    st.error(f'データの読み込みに失敗しました：{e}')
    st.stop()

# ── 発注完了画面 ─────────────────────────────────────────────
if st.session_state.done:
    st.markdown('<div class="success-box">✅ 注文を受け付けました！</div>', unsafe_allow_html=True)

    for info in st.session_state.done_info:
        show_contact(info['supplier'], suppliers_map.get(info['supplier'], {}), info['text'])

    st.divider()
    if st.button('🔄 続けて発注する'):
        st.session_state.done = False
        st.session_state.done_info = []
        st.cache_data.clear()
        st.rerun()
    st.stop()

# ── 確認画面 ─────────────────────────────────────────────────
if st.session_state.confirming:
    st.markdown('<div class="confirm-box">', unsafe_allow_html=True)
    st.subheader('⚠️ 本当に注文しますか？')
    for item in st.session_state.pending:
        st.markdown(f'・**{item["name"]}** を **{item["qty"]} 個**')
    st.markdown(f'発注先：**{st.session_state.pending[0]["supplier"]}**')
    st.markdown(f'発注者：**{st.session_state.pending[0]["user"]}**')
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.markdown('<div class="order-btn">', unsafe_allow_html=True)
            if st.button('✅ はい、注文します'):
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                rows = []
                order_lines = []
                for item in st.session_state.pending:
                    rows.append([now, item['user'], item['supplier'],
                                  item['name'], item['qty'], item['min_qty'], item['method']])
                    order_lines.append(f'・{item["name"]}　{item["qty"]}個')

                try:
                    write_order(rows)
                    supplier = st.session_state.pending[0]['supplier']
                    order_text = '\n'.join(order_lines)
                    st.session_state.done_info = [{'supplier': supplier, 'text': order_text}]
                    st.session_state.done = True
                    st.session_state.confirming = False
                    st.session_state.pending = []
                    st.rerun()
                except Exception as e:
                    st.error(f'記録に失敗しました：{e}')
            st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if st.button('❌ やめる・修正する'):
            st.session_state.confirming = False
            st.session_state.pending = []
            st.rerun()
    st.stop()

# ── 発注入力画面 ─────────────────────────────────────────────
st.sidebar.header('👤 発注者')
user = st.sidebar.selectbox('だれが発注しますか？', USERS, label_visibility='collapsed')

st.sidebar.header('🏭 業者を選ぶ')
suppliers = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))
selected = st.sidebar.selectbox('業者名', suppliers, label_visibility='collapsed')

# 選択業者の連絡先情報を表示
if selected in suppliers_map:
    info = suppliers_map[selected]
    method  = info.get('発注方法', '')
    contact = info.get('連絡先', '')
    if contact:
        icons = {'メール': '📧', '電話': '📞', 'FAX': '📠'}
        icon = icons.get(method, '📬')
        st.sidebar.info(f'{icon} {method}：{contact}')

products = [p for p in all_products if p.get('仕入れ先', '') == selected]
st.subheader(f'{selected}　({len(products)} 品)')

order_quantities = {}
for p in products:
    name    = p.get('商品名', '')
    min_qty = int(p.get('入数', 0) or 0)

    col1, col2 = st.columns([3, 1])
    with col1:
        label = f'**{name}**'
        if min_qty > 0:
            label += f'　（最低 {min_qty} 個から）'
        st.markdown(label)
    with col2:
        qty = st.number_input(
            '頼む数',
            min_value=0, value=0,
            step=max(min_qty, 1),
            key=name,
            label_visibility='collapsed'
        )
    order_quantities[name] = (qty, min_qty)

# ── 発注ボタン ────────────────────────────────────────────────
st.divider()
method_display = suppliers_map.get(selected, {}).get('発注方法', '？')
st.markdown(f'<div class="order-btn">', unsafe_allow_html=True)
if st.button(f'📨 {selected} に発注する（{method_display}）', use_container_width=True):
    errors = []
    to_order = []

    for p in products:
        name = p.get('商品名', '')
        qty, min_qty = order_quantities[name]
        if qty == 0:
            continue
        if min_qty > 0 and qty < min_qty:
            errors.append(f'❌ {name}：{qty}個は最低注文数（{min_qty}個）より少ないです')
            continue
        to_order.append({
            'name': name, 'qty': qty, 'min_qty': min_qty,
            'supplier': selected, 'user': user,
            'method': suppliers_map.get(selected, {}).get('発注方法', '未設定')
        })

    if errors:
        for e in errors:
            st.error(e)
    elif not to_order:
        st.warning('頼む数を入力してください。')
    else:
        st.session_state.pending = to_order
        st.session_state.confirming = True
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
