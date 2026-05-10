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
USERS   = ['由香', '由梨', '克治']
METHODS = ['電話', 'FAX', 'メール', '未設定']
# ================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
]

# ── スマホ最適化CSS ──────────────────────────────────────────
st.markdown("""
<style>
  /* ベースフォント・余白 */
  html, body, [class*="css"] { font-size: 20px !important; }
  .main .block-container { padding: 0.8rem 0.6rem 3rem; max-width: 100% !important; }

  /* 見出し */
  h1 { font-size: 1.5em !important; margin-bottom: 0.3em !important; }
  h2, h3 { font-size: 1.2em !important; }

  /* ボタン：大きく・押しやすく */
  .stButton > button {
    font-size: 1.15em !important;
    min-height: 3.2em !important;
    border-radius: 14px !important;
    width: 100% !important;
    margin-bottom: 0.4em !important;
    white-space: normal !important;
    line-height: 1.3 !important;
  }

  /* セレクトボックス・入力欄 */
  .stSelectbox > div, .stNumberInput > div {
    font-size: 1.1em !important;
  }
  input[type=number] { font-size: 1.3em !important; min-height: 2.5em !important; }

  /* 商品カード */
  .product-card {
    background: #f4f6f8;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 10px;
  }
  .product-name { font-size: 1.1em; font-weight: bold; margin-bottom: 4px; }
  .product-sub  { font-size: 0.85em; color: #666; }

  /* 連絡先アクションボタン（HTML） */
  .action-btn {
    display: block;
    width: 100%;
    text-align: center;
    padding: 22px 12px;
    border-radius: 18px;
    font-size: 1.35em;
    font-weight: bold;
    text-decoration: none !important;
    color: white !important;
    margin: 12px 0;
    box-shadow: 0 5px 12px rgba(0,0,0,0.25);
    letter-spacing: 0.02em;
    line-height: 1.6;
    -webkit-tap-highlight-color: transparent;
  }
  .action-btn:active { opacity: 0.85; transform: scale(0.98); }
  .btn-call { background: linear-gradient(135deg, #1a7f37, #28a745); }
  .btn-mail { background: linear-gradient(135deg, #0057b8, #1a73e8); }
  .btn-fax  { background: linear-gradient(135deg, #7b3f00, #a0522d); }

  /* 完了・確認ボックス */
  .success-box {
    background: #d4edda; color: #155724;
    padding: 22px; border-radius: 14px;
    font-size: 1.4em; font-weight: bold;
    text-align: center; margin: 12px 0;
  }
  .confirm-box {
    background: #fff8e1; padding: 18px;
    border-radius: 14px; border: 2px solid #f0ad4e;
    font-size: 1.05em; margin-bottom: 12px;
  }
  .info-badge {
    display: inline-block;
    background: #e8f4fd; border-radius: 8px;
    padding: 4px 10px; font-size: 0.9em; margin: 2px;
  }

  /* タブ */
  .stTabs [data-baseweb="tab"] { font-size: 1em !important; padding: 10px 14px !important; }
</style>
""", unsafe_allow_html=True)

# ── Google 接続 ──────────────────────────────────────────────
def get_client():
    if 'gcp_service_account' in st.secrets:
        secret = st.secrets['gcp_service_account']
        info = json.loads(secret) if isinstance(secret, str) else dict(secret)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    return gspread.authorize(creds)

@st.cache_data(ttl=120)
def load_products():
    client = get_client()
    return client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_PRODUCTS).get_all_records()

@st.cache_data(ttl=30)
def load_suppliers():
    try:
        client = get_client()
        rows = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_SUPPLIERS).get_all_records()
        return {r['業者名']: r for r in rows if r.get('業者名')}
    except Exception:
        return {}

def save_supplier(name, method, tel='', email=''):
    client = get_client()
    book  = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = book.worksheet(SHEET_SUPPLIERS)
    except gspread.WorksheetNotFound:
        sheet = book.add_worksheet(title=SHEET_SUPPLIERS, rows=200, cols=6)
        sheet.append_row(['業者名', '発注方法', '電話番号', 'メールアドレス'])

    all_vals = sheet.get_all_values()
    headers  = all_vals[0] if all_vals else []

    def col_idx(h):
        return (headers.index(h) + 1) if h in headers else None

    name_col = col_idx('業者名')
    target_row = None
    if name_col:
        for i, row in enumerate(all_vals[1:], start=2):
            if len(row) >= name_col and row[name_col - 1] == name:
                target_row = i
                break
    if target_row:
        updates = {'発注方法': method, '電話番号': tel, 'メールアドレス': email}
        for col_name, val in updates.items():
            c = col_idx(col_name)
            if c:
                sheet.update_cell(target_row, c, val)
    else:
        sheet.append_row([name, method, tel, email])
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

def contact_buttons(supplier_name, info, order_text=''):
    """発注方法に応じて電話・メール・FAXボタンを表示"""
    method = info.get('発注方法', '').strip()
    tel    = info.get('電話番号', '').strip()
    email  = info.get('メールアドレス', '').strip()

    # 本文（メール用）
    if order_text:
        body_text = (
            f'いつもお世話になっております。\n'
            f'フキヤファミリーです。\n'
            f'以下の通り発注をお願いします。\n\n'
            f'{order_text}\n\n'
            f'よろしくお願いいたします。\n'
            f'フキヤファミリー'
        )
    else:
        body_text = 'フキヤファミリーよりご連絡いたします。'

    subject  = urllib.parse.quote('【発注】フキヤファミリーより', safe='')
    body_enc = urllib.parse.quote(body_text, safe='')

    if method == '電話' and tel:
        tel_clean = tel.replace('-', '').replace(' ', '').replace('　', '')
        st.markdown(
            f'<a href="tel:{tel_clean}" class="action-btn btn-call">'
            f'📞　電話をかける<br>'
            f'<span style="font-size:0.78em;font-weight:normal;opacity:0.9;">{tel}</span>'
            f'</a>',
            unsafe_allow_html=True
        )

    elif method == 'メール' and email:
        href = f'mailto:{email}?subject={subject}&body={body_enc}'
        st.markdown(
            f'<a href="{href}" class="action-btn btn-mail">'
            f'✉️　メールで注文する<br>'
            f'<span style="font-size:0.78em;font-weight:normal;opacity:0.9;">{email}</span>'
            f'</a>',
            unsafe_allow_html=True
        )

    elif method == 'FAX' and tel:
        st.markdown(
            f'<div class="action-btn btn-fax">'
            f'📠　FAX：{tel}'
            f'</div>',
            unsafe_allow_html=True
        )
        if order_text:
            st.markdown('**📋 以下の内容をFAXしてください：**')
            st.code(order_text, language=None)

    else:
        # 発注方法未設定でも電話番号があれば表示
        if tel:
            tel_clean = tel.replace('-', '').replace(' ', '')
            st.markdown(
                f'<a href="tel:{tel_clean}" class="action-btn btn-call">'
                f'📞　電話をかける　{tel}'
                f'</a>',
                unsafe_allow_html=True
            )
        elif email:
            href = f'mailto:{email}?subject={subject}&body={body_enc}'
            st.markdown(
                f'<a href="{href}" class="action-btn btn-mail">'
                f'✉️　メールで注文する　{email}'
                f'</a>',
                unsafe_allow_html=True
            )
        else:
            st.info('💡 連絡先が未登録です。「業者管理」タブから登録できます。')

# ── セッション初期化 ─────────────────────────────────────────
for k, v in [('confirming', False), ('pending', []), ('done', False), ('done_info', [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── タイトル＋タブ ───────────────────────────────────────────
st.title('📦 フキヤファミリー 発注アプリ')
tab_order, tab_mgmt = st.tabs(['📦　発注する', '📋　業者管理'])

# ════════════════════════════════════════════════════════════════
# タブ①：発注する
# ════════════════════════════════════════════════════════════════
with tab_order:
    try:
        all_products  = load_products()
        suppliers_map = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        st.stop()

    # ── 完了画面 ──────────────────────────────────────────────
    if st.session_state.done:
        st.markdown('<div class="success-box">✅ 注文を受け付けました！</div>', unsafe_allow_html=True)
        for d in st.session_state.done_info:
            st.markdown(f'**{d["supplier"]}** への連絡：')
            contact_buttons(d['supplier'], suppliers_map.get(d['supplier'], {}), d['text'])
        st.divider()
        if st.button('🔄 続けて発注する', type='primary'):
            st.session_state.done = False
            st.session_state.done_info = []
            st.rerun()
        st.stop()

    # ── 確認画面 ──────────────────────────────────────────────
    if st.session_state.confirming:
        st.markdown('<div class="confirm-box">', unsafe_allow_html=True)
        st.subheader('⚠️ この内容で注文しますか？')
        for item in st.session_state.pending:
            st.markdown(f'・**{item["name"]}**　{item["qty"]} 個')
        st.markdown(f'発注先：**{st.session_state.pending[0]["supplier"]}**')
        st.markdown(f'発注者：**{st.session_state.pending[0]["user"]}**')
        st.markdown('</div>', unsafe_allow_html=True)

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

        if st.button('❌ やめる・修正する'):
            st.session_state.confirming = False
            st.session_state.pending = []
            st.rerun()
        st.stop()

    # ── 発注入力 ──────────────────────────────────────────────
    user = st.selectbox('👤 発注者（だれが発注しますか？）', USERS)

    supplier_names = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))
    selected = st.selectbox('🏭 業者を選んでください', supplier_names)

    # 業者の連絡先をワンタップで確認
    info    = suppliers_map.get(selected, {})
    method  = info.get('発注方法', '未設定')
    tel     = info.get('電話番号', '')
    email   = info.get('メールアドレス', '')
    icons   = {'電話': '📞', 'FAX': '📠', 'メール': '📧'}
    icon    = icons.get(method, '❓')
    summary = '　'.join(filter(None, [tel, email])) or '未登録'

    with st.expander(f'{icon}　{selected} の連絡先を確認する　({summary})'):
        contact_buttons(selected, info)

    # 商品リスト（縦長・スマホ向け）
    st.markdown(f'#### {selected} の品物一覧')
    products = [p for p in all_products if p.get('仕入れ先', '') == selected]
    order_quantities = {}

    for p in products:
        name    = p.get('商品名', '')
        min_qty = int(p.get('入数', 0) or 0)
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        sub = f'最低 {min_qty} 個から' if min_qty > 0 else ''
        st.markdown(f'<div class="product-name">{name}</div>'
                    f'<div class="product-sub">{sub}</div>', unsafe_allow_html=True)
        qty = st.number_input(
            '頼む数', min_value=0, value=0,
            step=max(min_qty, 1), key=name,
            label_visibility='visible'
        )
        order_quantities[name] = (qty, min_qty)
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    if st.button(f'📨　{selected} に発注する', use_container_width=True, type='primary'):
        errors, to_order = [], []
        for p in products:
            name = p.get('商品名', '')
            qty, min_qty = order_quantities[name]
            if qty == 0:
                continue
            if min_qty > 0 and qty < min_qty:
                errors.append(f'❌ {name}：{qty}個は最低 {min_qty} 個より少ないです')
                continue
            to_order.append({'name': name, 'qty': qty, 'min_qty': min_qty,
                              'supplier': selected, 'user': user, 'method': method})
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
# タブ②：業者管理
# ════════════════════════════════════════════════════════════════
with tab_mgmt:
    st.markdown('#### 業者の連絡先一覧')
    st.caption('業者名をタップすると連絡先を確認・変更できます')

    try:
        all_products2  = load_products()
        suppliers_map2 = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        st.stop()

    supplier_names2 = sorted(set(p.get('仕入れ先', '') for p in all_products2 if p.get('仕入れ先', '')))
    icons = {'電話': '📞', 'FAX': '📠', 'メール': '📧'}

    for name in supplier_names2:
        info2   = suppliers_map2.get(name, {})
        method2 = info2.get('発注方法', '未設定')
        tel2    = info2.get('電話番号', '')
        email2  = info2.get('メールアドレス', '')
        icon2   = icons.get(method2, '❓')

        with st.expander(f'{icon2}　{name}　／　{tel2}　{email2}'):
            new_method = st.selectbox(
                '発注方法', METHODS,
                index=METHODS.index(method2) if method2 in METHODS else 3,
                key=f'm_{name}'
            )
            new_tel = st.text_input(
                '📞 電話番号', value=tel2, key=f't_{name}',
                placeholder='例）092-123-4567'
            )
            new_email = st.text_input(
                '✉️ メールアドレス', value=email2, key=f'e_{name}',
                placeholder='例）info@example.com'
            )
            if st.button('💾 保存する', key=f's_{name}', type='primary'):
                try:
                    save_supplier(name, new_method, new_tel, new_email)
                    st.success(f'✅ {name} の情報を保存しました！')
                    st.rerun()
                except Exception as e:
                    st.error(f'保存に失敗しました：{e}')
