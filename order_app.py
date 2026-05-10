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
METHODS = ['電話', 'FAX', 'メール', '未設定']
# ================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
]

st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 18px; }
  h1 { font-size: 1.8em !important; }
  h2 { font-size: 1.4em !important; }
  .stButton > button {
    font-size: 1.1em !important;
    padding: 0.6em 1.2em !important;
    border-radius: 12px !important;
    width: 100%;
  }
  .success-box {
    background: #d4edda; color: #155724;
    padding: 20px; border-radius: 12px;
    font-size: 1.4em; font-weight: bold;
    text-align: center; margin: 16px 0;
  }
  .contact-box {
    background: #e8f4fd; padding: 16px;
    border-radius: 10px; margin: 10px 0;
  }
  .confirm-box {
    background: #fff8e1; padding: 20px;
    border-radius: 12px; border: 2px solid #f0ad4e;
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

@st.cache_data(ttl=60)
def load_products():
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_PRODUCTS)
    return sheet.get_all_records()

@st.cache_data(ttl=30)
def load_suppliers():
    try:
        client = get_client()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_SUPPLIERS)
        rows = sheet.get_all_records()
        return {r['業者名']: r for r in rows if r.get('業者名')}
    except Exception:
        return {}

def save_supplier(name, method, contact):
    client = get_client()
    book  = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = book.worksheet(SHEET_SUPPLIERS)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=SHEET_SUPPLIERS, rows=200, cols=5)
        sheet.append_row(['業者名', '発注方法', '連絡先'])

    all_vals = sheet.get_all_values()
    headers  = all_vals[0] if all_vals else []

    # 列インデックスを取得（なければ追加）
    def col_idx(header):
        if header in headers:
            return headers.index(header) + 1
        return None

    # 業者名の行を探す
    name_col = col_idx('業者名')
    target_row = None
    if name_col:
        for i, row in enumerate(all_vals[1:], start=2):
            if len(row) >= name_col and row[name_col - 1] == name:
                target_row = i
                break

    if target_row:
        method_col  = col_idx('発注方法')
        contact_col = col_idx('連絡先')
        if method_col:
            sheet.update_cell(target_row, method_col, method)
        if contact_col:
            sheet.update_cell(target_row, contact_col, contact)
    else:
        sheet.append_row([name, method, contact])

    st.cache_data.clear()

def write_order(rows):
    client = get_client()
    book = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = book.worksheet(SHEET_HISTORY)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=SHEET_HISTORY, rows=1000, cols=10)
        sheet.append_row(['発注日時', '発注者', '仕入れ先', '品物名', '頼む数', '入数', '発注方法'])
    sheet.append_rows(rows)

def show_contact_action(supplier_name, supplier_info, order_text):
    method  = supplier_info.get('発注方法', '').strip()
    contact = supplier_info.get('連絡先', '').strip()
    st.markdown('<div class="contact-box">', unsafe_allow_html=True)
    st.markdown(f'**{supplier_name} への連絡方法**')
    if method == 'メール' and contact:
        subject = urllib.parse.quote('【発注】フキヤファミリー')
        body    = urllib.parse.quote(f'お世話になっております。\n以下の通り発注いたします。\n\n{order_text}\n\nよろしくお願いいたします。\nフキヤファミリー')
        st.markdown(f'📧 メール：**{contact}**')
        st.markdown(f'[👆 タップしてメールを送る](mailto:{contact}?subject={subject}&body={body})')
    elif method == '電話' and contact:
        tel = contact.replace('-', '').replace(' ', '')
        st.markdown(f'📞 電話：**{contact}**')
        st.markdown(f'[👆 タップして電話をかける](tel:{tel})')
    elif method == 'FAX' and contact:
        st.markdown(f'📠 FAX番号：**{contact}**')
        st.markdown('以下の内容をFAXしてください：')
        st.code(order_text, language=None)
    else:
        st.info('連絡先が未登録です。「業者の連絡先管理」から登録できます。')
    st.markdown('</div>', unsafe_allow_html=True)

# ── セッション初期化 ──────────────────────────────────────────
for key, val in [('confirming', False), ('pending', []), ('done', False), ('done_info', [])]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── ページ切り替え ────────────────────────────────────────────
st.title('📦 フキヤファミリー 発注アプリ')
page = st.sidebar.radio('メニュー', ['📦 発注する', '📋 業者の連絡先管理'], label_visibility='collapsed')

# ════════════════════════════════════════════════════════════════
# ページ①：発注する
# ════════════════════════════════════════════════════════════════
if page == '📦 発注する':

    try:
        all_products = load_products()
        suppliers_map = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        st.stop()

    # 完了画面
    if st.session_state.done:
        st.markdown('<div class="success-box">✅ 注文を受け付けました！</div>', unsafe_allow_html=True)
        for info in st.session_state.done_info:
            show_contact_action(info['supplier'], suppliers_map.get(info['supplier'], {}), info['text'])
        st.divider()
        if st.button('🔄 続けて発注する'):
            st.session_state.done = False
            st.session_state.done_info = []
            st.rerun()
        st.stop()

    # 確認画面
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
            if st.button('✅ はい、注文します', type='primary'):
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                rows, lines = [], []
                for item in st.session_state.pending:
                    rows.append([now, item['user'], item['supplier'],
                                  item['name'], item['qty'], item['min_qty'], item['method']])
                    lines.append(f'・{item["name"]}　{item["qty"]}個')
                try:
                    write_order(rows)
                    supplier = st.session_state.pending[0]['supplier']
                    st.session_state.done_info = [{'supplier': supplier, 'text': '\n'.join(lines)}]
                    st.session_state.done = True
                    st.session_state.confirming = False
                    st.session_state.pending = []
                    st.rerun()
                except Exception as e:
                    st.error(f'記録に失敗しました：{e}')
        with col2:
            if st.button('❌ やめる・修正する'):
                st.session_state.confirming = False
                st.session_state.pending = []
                st.rerun()
        st.stop()

    # 発注入力
    st.sidebar.header('👤 発注者')
    user = st.sidebar.selectbox('だれが発注しますか？', USERS, label_visibility='collapsed')
    st.sidebar.header('🏭 業者を選ぶ')
    supplier_names = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))
    selected = st.sidebar.selectbox('業者名', supplier_names, label_visibility='collapsed')

    # 業者詳細（タップで開く）
    info = suppliers_map.get(selected, {})
    method  = info.get('発注方法', '未設定')
    contact = info.get('連絡先', '未登録')
    icons = {'電話': '📞', 'FAX': '📠', 'メール': '📧'}
    icon = icons.get(method, '📬')
    with st.expander(f'{icon} {selected} の連絡先を見る・変更する'):
        st.markdown(f'**発注方法：** {method}　／　**連絡先：** {contact}')
        st.markdown('---')
        new_method  = st.selectbox('発注方法を変更', METHODS,
                                    index=METHODS.index(method) if method in METHODS else 3,
                                    key=f'method_{selected}')
        new_contact = st.text_input('連絡先（電話番号・メール・FAX番号）',
                                     value=contact if contact != '未登録' else '',
                                     key=f'contact_{selected}')
        if st.button('💾 保存する', key=f'save_{selected}'):
            try:
                save_supplier(selected, new_method, new_contact)
                st.success('保存しました！')
            except Exception as e:
                st.error(f'保存に失敗しました：{e}')

    # 商品リスト
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
            qty = st.number_input('頼む数', min_value=0, value=0,
                                   step=max(min_qty, 1), key=name,
                                   label_visibility='collapsed')
        order_quantities[name] = (qty, min_qty)

    st.divider()
    if st.button(f'📨 {selected} に発注する', use_container_width=True, type='primary'):
        errors, to_order = [], []
        for p in products:
            name = p.get('商品名', '')
            qty, min_qty = order_quantities[name]
            if qty == 0:
                continue
            if min_qty > 0 and qty < min_qty:
                errors.append(f'❌ {name}：{qty}個は最低注文数（{min_qty}個）より少ないです')
                continue
            to_order.append({'name': name, 'qty': qty, 'min_qty': min_qty,
                              'supplier': selected, 'user': user,
                              'method': method})
        if errors:
            for e in errors:
                st.error(e)
        elif not to_order:
            st.warning('頼む数を入力してください。')
        else:
            st.session_state.pending = to_order
            st.session_state.confirming = True
            st.rerun()

# ════════════════════════════════════════════════════════════════
# ページ②：業者の連絡先管理
# ════════════════════════════════════════════════════════════════
else:
    st.subheader('📋 業者の連絡先管理')
    st.caption('各業者をタップすると連絡先を確認・変更できます')

    try:
        all_products  = load_products()
        suppliers_map = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        st.stop()

    supplier_names = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))
    icons = {'電話': '📞', 'FAX': '📠', 'メール': '📧'}

    for name in supplier_names:
        info    = suppliers_map.get(name, {})
        method  = info.get('発注方法', '未設定')
        contact = info.get('連絡先', '未登録')
        icon    = icons.get(method, '❓')

        with st.expander(f'{icon}　{name}　—　{method}　{contact}'):
            new_method  = st.selectbox('発注方法', METHODS,
                                        index=METHODS.index(method) if method in METHODS else 3,
                                        key=f'mgmt_method_{name}')
            new_contact = st.text_input('連絡先',
                                         value=contact if contact != '未登録' else '',
                                         key=f'mgmt_contact_{name}')
            if st.button('💾 保存する', key=f'mgmt_save_{name}'):
                try:
                    save_supplier(name, new_method, new_contact)
                    st.success(f'{name} の情報を保存しました！')
                    st.rerun()
                except Exception as e:
                    st.error(f'保存に失敗しました：{e}')
