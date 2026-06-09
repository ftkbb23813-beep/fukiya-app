import streamlit as st
import datetime
import urllib.parse
import pandas as pd
import plotly.express as px

# ===== 設定 =====
SPREADSHEET_ID       = '1_DHnh3SwVreDbWJm56fs6I8fWBwUvmhb2la24yoIHEI'
SALES_SPREADSHEET_ID = '1vs-kn-WsIduy1tPG4IDH4sBzsr_cI5NcSBx-bnmyJYQ'

# シートGID と 使用するスプレッドシートIDのマッピング
SHEET_GIDS = {
    '商品マスタ': '0',
    '業者マスタ': '993018520',
    '早見表':     '93293747',
    '売上データ': '0',
}
# '売上データ' だけ別ファイル。それ以外は SPREADSHEET_ID を使用
SHEET_SPREADSHEET = {
    '商品マスタ': SPREADSHEET_ID,
    '業者マスタ': SPREADSHEET_ID,
    '早見表':     SPREADSHEET_ID,
    '売上データ': SALES_SPREADSHEET_ID,
}

USERS   = ['由香', '由梨', '克治']
METHODS = ['電話', 'FAX', 'メール', '未設定']
STORE_COLORS = {
    '志摩の四季': '#1a7f37',
    'ゆめ畑':     '#1a73e8',
    '伊都国':     '#e8620a',
}
# ================

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

  /* ── 早見表 ── */
  .hayami-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 1.1em;
    margin-top: 8px;
  }
  .hayami-table th {
    background: #2c5f8a;
    color: white;
    padding: 14px 10px;
    text-align: left;
    font-size: 1.05em;
    position: sticky;
    top: 0;
  }
  .hayami-table td {
    padding: 16px 10px;
    vertical-align: top;
    line-height: 1.5;
    font-size: 1.05em;
    border-bottom: 1px solid #ddd;
    color: #111111 !important;
  }
  .hayami-row-even { background: #f0f5fb; color: #111111 !important; }
  .hayami-row-odd  { background: #ffffff; color: #111111 !important; }
  .hayami-name { font-weight: bold; font-size: 1.1em; color: #111111 !important; }
  .hayami-price { color: #c0392b !important; font-weight: bold; font-size: 1.1em; }

  /* ── 利益率計算 ── */
  .profit-card {
    border-radius: 18px;
    padding: 24px 14px 20px;
    margin: 10px 0;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.10);
  }
  .profit-card-blue {
    background: linear-gradient(160deg, #dbeeff, #c0ddff);
    border: 4px solid #1a73e8;
  }
  .profit-card-green {
    background: linear-gradient(160deg, #e0f8ea, #c0f0d0);
    border: 4px solid #1a7f37;
  }
  .profit-card-red {
    background: linear-gradient(160deg, #fde8e6, #ffc8c4);
    border: 4px solid #d32f2f;
  }
  .profit-card-danger {
    background: #f0f0f0;
    border: 3px solid #999;
  }
  .profit-rate-big-blue {
    color: #1055cc;
    font-size: 3.4em;
    font-weight: 900;
    display: block;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  .profit-rate-big-green {
    color: #166a2c;
    font-size: 3.4em;
    font-weight: 900;
    display: block;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  .profit-rate-big-red {
    color: #c0180e;
    font-size: 3.4em;
    font-weight: 900;
    display: block;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  .profit-rate-big-danger {
    color: #777;
    font-size: 3.4em;
    font-weight: 900;
    display: block;
    line-height: 1.1;
    letter-spacing: -0.02em;
  }
  .profit-emoji {
    font-size: 1.8em;
    display: block;
    margin-bottom: 4px;
  }
  .profit-fee-label {
    font-size: 1.05em;
    font-weight: bold;
    opacity: 0.75;
    display: block;
    margin-bottom: 2px;
  }
  .profit-amount {
    font-size: 1.5em;
    font-weight: bold;
    margin-top: 10px;
    display: block;
  }
  .profit-amount-sub {
    font-size: 1.0em;
    color: #555;
    margin-top: 4px;
    display: block;
  }
  .profit-warning {
    background: #fff3cd;
    border: 2px solid #f0ad4e;
    border-radius: 12px;
    padding: 14px;
    font-size: 1.05em;
    font-weight: bold;
    color: #856404;
    text-align: center;
    margin: 8px 0;
  }
  .profit-danger {
    background: #fdecea;
    border: 2px solid #d32f2f;
    border-radius: 12px;
    padding: 14px;
    font-size: 1.05em;
    font-weight: bold;
    color: #b71c1c;
    text-align: center;
    margin: 8px 0;
  }
  .profit-input-label {
    font-size: 1.25em;
    font-weight: bold;
    margin: 14px 0 4px;
    display: block;
  }
  .profit-product-badge {
    background: #e8f4fd;
    border: 1px solid #90caf9;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 1.0em;
    margin: 8px 0 14px;
    color: #1a5276;
  }
  .fee-header {
    font-size: 1.15em;
    font-weight: bold;
    text-align: center;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 8px;
    background: #f0f5fb;
  }
  .profit-detail-box {
    background: #fafafa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: 1.0em;
    margin-top: 8px;
  }
  .profit-detail-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #eee;
  }
  .profit-detail-row:last-child { border-bottom: none; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── CSV URL 生成 ──────────────────────────────────────────────
def _csv_url(sheet_key):
    sid = SHEET_SPREADSHEET[sheet_key]
    gid = SHEET_GIDS[sheet_key]
    return (
        f'https://docs.google.com/spreadsheets/d/{sid}'
        f'/export?format=csv&gid={gid}'
    )

# ── データ読み込み ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_products():
    df = pd.read_csv(_csv_url('商品マスタ')).fillna('')
    df.columns = [c.strip() for c in df.columns]
    return df.to_dict('records') if not df.empty else []

@st.cache_data(ttl=30)
def load_suppliers():
    try:
        df = pd.read_csv(_csv_url('業者マスタ')).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return {str(r['業者名']): r.to_dict() for _, r in df.iterrows() if r.get('業者名')}
    except Exception:
        return {}

@st.cache_data(ttl=120)
def load_hayami():
    try:
        df = pd.read_csv(_csv_url('早見表')).fillna('')
        df.columns = [c.strip() for c in df.columns]
        return df.to_dict('records') if not df.empty else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_sales() -> pd.DataFrame:
    df = pd.read_csv(_csv_url('売上データ'))
    if df.empty:
        return pd.DataFrame(columns=['日付', '店舗名', '金額', '処理日時'])
    df.columns = [c.strip() for c in df.columns]
    # 日付・金額列は数値変換するため fillna は変換後に行う
    df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
    df['金額'] = pd.to_numeric(
        df['金額'].astype(str).str.replace(',', '').str.replace('¥', '').str.replace('円', '').str.strip(),
        errors='coerce'
    ).fillna(0)
    # 文字列列の NaN を空文字に統一
    str_cols = df.select_dtypes(include='object').columns
    df[str_cols] = df[str_cols].fillna('')
    df = df.dropna(subset=['日付'])
    return df

# ── 書き込み（認証不要モードでは未対応） ───────────────────────
def save_supplier(name, method, tel='', email=''):
    raise NotImplementedError(
        'スプレッドシートへの書き込みには Google 認証の設定が必要です。'
        '現在は読み取り専用モードで動作しています。'
    )

def write_order(rows):
    raise NotImplementedError(
        'スプレッドシートへの書き込みには Google 認証の設定が必要です。'
        '現在は読み取り専用モードで動作しています。'
    )

def contact_buttons(supplier_name, info, order_text=''):
    """発注方法に応じて電話・メール・FAXボタンを表示"""
    method = info.get('発注方法', '').strip()
    tel    = info.get('電話番号', '').strip()
    email  = info.get('メールアドレス', '').strip()

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

def profit_card_html(fee_label, profit_amt, profit_rate, price, cost):
    """利益率に応じた色分けカードHTMLを返す"""
    if profit_rate >= 30:
        card_cls = 'profit-card profit-card-blue'
        rate_cls = 'profit-rate-big-blue'
        emoji    = '🎉'
        status   = '絶好調！'
    elif profit_rate >= 20:
        card_cls = 'profit-card profit-card-green'
        rate_cls = 'profit-rate-big-green'
        emoji    = '✅'
        status   = 'まずまず'
    elif profit_rate > 0:
        card_cls = 'profit-card profit-card-red'
        rate_cls = 'profit-rate-big-red'
        emoji    = '⚠️'
        status   = '要見直し'
    else:
        card_cls = 'profit-card profit-card-danger'
        rate_cls = 'profit-rate-big-danger'
        emoji    = '❌'
        status   = '赤字！'

    fee_amt  = price * (0.10 if '10' in fee_label else 0.20)
    amt_str  = f'¥{profit_amt:+,.0f}'
    rate_str = f'{profit_rate:.1f}%'

    return f"""
<div class="{card_cls}">
  <span class="profit-emoji">{emoji}</span>
  <span class="profit-fee-label">{fee_label}　{status}</span>
  <span class="{rate_cls}">{rate_str}</span>
  <span class="profit-amount">{amt_str}</span>
  <span class="profit-amount-sub">（手数料 ¥{fee_amt:,.0f}）</span>
</div>
"""

# ── セッション初期化 ─────────────────────────────────────────
for k, v in [('confirming', False), ('pending', []), ('done', False), ('done_info', [])]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── タイトル＋タブ ───────────────────────────────────────────
st.title('📦 フキヤファミリー 発注アプリ')
tab_order, tab_hayami, tab_profit, tab_sales, tab_mgmt = st.tabs([
    '📦　発注する',
    '📋　早見表',
    '💰　利益率計算',
    '📊　売上分析',
    '🏭　業者管理',
])

# ════════════════════════════════════════════════════════════════
# タブ①：発注する
# ════════════════════════════════════════════════════════════════
with tab_order:
    _load_err = False
    try:
        all_products  = load_products()
        suppliers_map = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        all_products  = []
        suppliers_map = {}
        _load_err = True

    if _load_err:
        pass  # エラーは上で表示済み

    # ── 完了画面 ──────────────────────────────────────────────
    elif st.session_state.done:
        st.markdown('<div class="success-box">✅ 注文を受け付けました！</div>', unsafe_allow_html=True)
        for d in st.session_state.done_info:
            st.markdown(f'**{d["supplier"]}** への連絡：')
            contact_buttons(d['supplier'], suppliers_map.get(d['supplier'], {}), d['text'])
        st.divider()
        if st.button('🔄 続けて発注する', type='primary'):
            st.session_state.done = False
            st.session_state.done_info = []
            st.rerun()

    # ── 確認画面 ──────────────────────────────────────────────
    elif st.session_state.confirming:
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

    # ── 発注入力 ──────────────────────────────────────────────
    else:
        user = st.selectbox('👤 発注者（だれが発注しますか？）', USERS)

        supplier_names = sorted(set(p.get('仕入れ先', '') for p in all_products if p.get('仕入れ先', '')))
        selected = st.selectbox('🏭 業者を選んでください', supplier_names)

        info    = suppliers_map.get(selected, {})
        method  = info.get('発注方法', '未設定')
        tel     = info.get('電話番号', '')
        email   = info.get('メールアドレス', '')
        icons   = {'電話': '📞', 'FAX': '📠', 'メール': '📧'}
        icon    = icons.get(method, '❓')
        summary = '　'.join(filter(None, [tel, email])) or '未登録'

        with st.expander(f'{icon}　{selected} の連絡先を確認する　({summary})'):
            contact_buttons(selected, info)

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
# タブ②：早見表
# ════════════════════════════════════════════════════════════════
with tab_hayami:
    st.markdown('### 📋 早見表')

    hayami_data = load_hayami()

    if not hayami_data:
        st.warning('早見表のデータがありません。スプレッドシートの「早見表」シートを確認してください。')
    else:
        # 列名を取得
        all_keys = list(hayami_data[0].keys()) if hayami_data else []

        # 検索窓
        search_query = st.text_input(
            '🔍 商品名・カテゴリで検索',
            placeholder='例：りんご、野菜、冷凍...',
            key='hayami_search'
        )

        # フィルタリング
        if search_query.strip():
            q = search_query.strip().lower()
            filtered = [
                row for row in hayami_data
                if any(q in str(v).lower() for v in row.values())
            ]
        else:
            filtered = hayami_data

        st.caption(f'全 {len(hayami_data)} 件中 {len(filtered)} 件表示')

        if not filtered:
            st.info('該当する商品が見つかりませんでした。')
        else:
            # 表示する優先列を決定（商品名・店舗・価格 を先頭に）
            priority = ['商品名', '店舗', 'カテゴリ', '価格', '単価', '備考']
            display_keys = [k for k in priority if k in all_keys]
            display_keys += [k for k in all_keys if k not in display_keys]

            # HTMLテーブル生成
            th_cells = ''.join(f'<th>{k}</th>' for k in display_keys)
            rows_html = ''
            for i, row in enumerate(filtered):
                row_cls = 'hayami-row-even' if i % 2 == 0 else 'hayami-row-odd'
                cells = ''
                for j, k in enumerate(display_keys):
                    val = str(row.get(k, ''))
                    if j == 0:
                        cells += f'<td class="hayami-name">{val}</td>'
                    elif k in ('価格', '単価'):
                        cells += f'<td class="hayami-price">{val}</td>'
                    else:
                        cells += f'<td>{val}</td>'
                rows_html += f'<tr class="{row_cls}">{cells}</tr>'

            html = f"""
<div style="overflow-x:auto; -webkit-overflow-scrolling:touch;">
  <table class="hayami-table">
    <thead><tr>{th_cells}</tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
"""
            st.markdown(html, unsafe_allow_html=True)

        if st.button('🔄 最新データを読み込む', key='reload_hayami'):
            st.cache_data.clear()
            st.rerun()

# ════════════════════════════════════════════════════════════════
# タブ③：利益率計算
# ════════════════════════════════════════════════════════════════
with tab_profit:
    st.markdown('### 💰 利益率計算機')
    st.caption('商品を選ぶと原価が自動入力。売価を入れたら即座に計算します。')

    # ── 商品マスタ読み込み ────────────────────────────────────
    try:
        profit_products = load_products()
    except Exception:
        profit_products = []

    # ── 商品検索 → プルダウン絞り込み ────────────────────────
    p_search = st.text_input(
        '🔍 商品を検索（キーワードで絞り込み）',
        placeholder='例：豆腐、冷凍、お菓子...',
        key='profit_product_search'
    )

    NONE_LABEL = '　（商品を選んでください）'
    if p_search.strip():
        q = p_search.strip().lower()
        matched_pp = [p for p in profit_products if q in str(p.get('商品名', '')).lower()]
    else:
        matched_pp = profit_products

    p_options = [NONE_LABEL] + [p['商品名'] for p in matched_pp if p.get('商品名', '')]

    selected_p = st.selectbox(
        '📦 商品を選択（選ぶと原価が自動入力されます）',
        p_options,
        key='profit_selectbox'
    )

    current_p = selected_p if selected_p != NONE_LABEL else ''

    # ── 選択商品の原価を取得（列名ゆらぎに対応） ─────────────
    def extract_cost(product_row: dict) -> int:
        """商品マスタのレコードから原価（E列相当）を取り出す。
        列名が異なる場合も '原価' '仕入' を含む列を自動探索。"""
        # 完全一致優先
        for key in ['原価', '原価（仕入れ値）', '仕入値', '仕入れ値', '仕入原価', 'cost']:
            val = product_row.get(key)
            if val not in (None, '', 0):
                try:
                    n = int(float(str(val).replace(',', '').replace('¥', '').replace('円', '').strip()))
                    if n > 0:
                        return n
                except (ValueError, TypeError):
                    pass
        # 部分一致フォールバック：'原価' または '仕入' を含む列
        for key, val in product_row.items():
            if ('原価' in str(key) or '仕入' in str(key)) and val not in (None, '', 0):
                try:
                    n = int(float(str(val).replace(',', '').replace('¥', '').replace('円', '').strip()))
                    if n > 0:
                        return n
                except (ValueError, TypeError):
                    pass
        return 0

    auto_cost = 0
    if current_p:
        pm = next((p for p in profit_products if p.get('商品名') == current_p), None)
        if pm:
            auto_cost = extract_cost(pm)
        badge_cost_str = f'¥{auto_cost:,}' if auto_cost > 0 else '（原価データなし）'
        st.markdown(
            f'<div class="profit-product-badge">'
            f'✅ 選択中：<strong>{current_p}</strong>　原価 → {badge_cost_str}'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # ── 原価入力
    # key を商品名に連動させることで、商品が変わると widget が再初期化され
    # value=auto_cost が確実に反映される。同一商品内では手動編集値を維持。
    cost_widget_key = f'pcost__{current_p}' if current_p else 'pcost____none'

    st.markdown('<span class="profit-input-label">💴 原価（仕入れ値）― 変更もできます</span>', unsafe_allow_html=True)
    cost = st.number_input(
        '原価',
        min_value=0,
        value=auto_cost,
        step=10,
        key=cost_widget_key,
        label_visibility='collapsed',
    )

    st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

    # ── 売価入力（特大）────────────────────────────────────────
    st.markdown('<span class="profit-input-label">🏷️ 売価（販売価格）― 自由に入力</span>', unsafe_allow_html=True)
    price = st.number_input(
        '売価',
        min_value=0,
        value=0,
        step=10,
        key='profit_price_num',
        label_visibility='collapsed',
    )

    st.divider()

    # ── 結果表示 ──────────────────────────────────────────────
    if cost == 0 and price == 0:
        st.markdown(
            '<div style="text-align:center; color:#aaa; font-size:1.1em; padding:28px 0;">'
            '⬆️ 商品を選ぶか、原価・売価を入力してください<br>'
            '<span style="font-size:0.85em;">入力すると自動で計算されます</span>'
            '</div>',
            unsafe_allow_html=True
        )
    elif price == 0:
        st.markdown(
            '<div class="profit-warning">⚠️ 売価が 0 円です。販売価格を入力してください。</div>',
            unsafe_allow_html=True
        )
    else:
        fee_rates = [('委託手数料 10%', 0.10), ('委託手数料 20%', 0.20)]

        col1, col2 = st.columns(2)

        for col, (label, rate) in zip([col1, col2], fee_rates):
            fee_amt     = price * rate
            profit_amt  = price - cost - fee_amt
            profit_rate = (profit_amt / price * 100) if price > 0 else 0

            with col:
                st.markdown(
                    profit_card_html(label, profit_amt, profit_rate, price, cost),
                    unsafe_allow_html=True
                )
                if profit_rate < 0:
                    st.markdown(
                        '<div class="profit-danger">❌ 赤字！売価を上げましょう</div>',
                        unsafe_allow_html=True
                    )
                elif profit_rate < 20:
                    st.markdown(
                        '<div class="profit-warning">⚠️ 利益率20%未満。要見直し</div>',
                        unsafe_allow_html=True
                    )

        # 明細ボックス
        st.divider()
        st.markdown('##### 📊 計算の内訳')
        dc1, dc2 = st.columns(2)
        for col, (label, rate) in zip([dc1, dc2], fee_rates):
            fee_amt    = price * rate
            profit_amt = price - cost - fee_amt
            profit_rate = (profit_amt / price * 100) if price > 0 else 0
            with col:
                st.markdown(
                    f'<div class="profit-detail-box">'
                    f'<div style="font-weight:bold;margin-bottom:8px;">{label}</div>'
                    f'<div class="profit-detail-row"><span>売価</span><span>¥{price:,}</span></div>'
                    f'<div class="profit-detail-row"><span>原価</span><span>¥{cost:,}</span></div>'
                    f'<div class="profit-detail-row"><span>手数料</span><span>¥{fee_amt:,.0f}</span></div>'
                    f'<div class="profit-detail-row"><span>利益</span><span>¥{profit_amt:,.0f}（{profit_rate:.1f}%）</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ════════════════════════════════════════════════════════════════
# タブ④：売上分析ダッシュボード
# ════════════════════════════════════════════════════════════════
with tab_sales:
    st.write("デバッグ：売上分析タブの読み込みテスト")
    st.markdown('### 📊 売上分析ダッシュボード')

    # ── データ読み込み ────────────────────────────────────────
    try:
        df_sales = load_sales()
    except Exception as e:
        st.error(f'売上データの読み込みに失敗しました：{e}')
        df_sales = pd.DataFrame(columns=['日付', '店舗名', '金額', '処理日時'])

    # ── 期間切り替え（常に表示） ──────────────────────────────
    period = st.radio(
        '集計期間',
        ['日毎', '週毎', '月毎'],
        horizontal=True,
        key='sales_period'
    )

    # ── 店舗フィルター（常に表示） ────────────────────────────
    all_stores = sorted(df_sales['店舗名'].dropna().unique().tolist()) if not df_sales.empty else []
    default_stores = [s for s in ['志摩の四季', 'ゆめ畑', '伊都国'] if s in all_stores] or all_stores
    selected_stores = st.multiselect(
        '店舗を選択',
        options=all_stores,
        default=default_stores,
        key='sales_stores'
    )

    if df_sales.empty:
        st.warning('売上データがありません。スプレッドシートにデータを入力してください。')
    else:
        try:
            df_f = df_sales[df_sales['店舗名'].isin(selected_stores)].copy() if selected_stores else df_sales.copy()

            # ── 集計 ─────────────────────────────────────────
            if period == '日毎':
                df_f['period'] = df_f['日付'].dt.date
                period_label = '日付'
            elif period == '週毎':
                df_f['period'] = df_f['日付'].dt.to_period('W').apply(lambda p: p.start_time.date())
                period_label = '週（開始日）'
            else:
                df_f['period'] = df_f['日付'].dt.to_period('M').apply(lambda p: p.start_time.date())
                period_label = '月'

            df_agg = df_f.groupby(['period', '店舗名'], as_index=False)['金額'].sum()
            df_agg['period'] = pd.to_datetime(df_agg['period'])

            color_map = {s: STORE_COLORS.get(s, '#888888') for s in all_stores}

            # ── グラフ描画 ────────────────────────────────────
            if df_agg.empty:
                st.info('該当するデータがありません。')
            elif len(df_agg['period'].unique()) < 2 and period == '日毎':
                st.info('表示できる十分なデータがありません（日別グラフには2件以上の日付が必要です）。')
                st.dataframe(df_agg[['period', '店舗名', '金額']].rename(columns={'period': '日付'}), use_container_width=True)
            elif period == '日毎':
                fig = px.line(
                    df_agg,
                    x='period', y='金額', color='店舗名',
                    color_discrete_map=color_map,
                    markers=True,
                    labels={'period': period_label, '金額': '売上金額（円）', '店舗名': '店舗'},
                    title='日別 売上推移',
                )
                fig.update_layout(
                    xaxis_title=period_label,
                    yaxis_tickformat=',.0f',
                    legend_title='店舗',
                    margin=dict(t=48, b=8),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                fig = px.bar(
                    df_agg,
                    x='period', y='金額', color='店舗名',
                    color_discrete_map=color_map,
                    barmode='group',
                    labels={'period': period_label, '金額': '売上金額（円）', '店舗名': '店舗'},
                    title=f'{"週" if period == "週毎" else "月"}別 売上比較',
                )
                fig.update_layout(
                    xaxis_title=period_label,
                    yaxis_tickformat=',.0f',
                    legend_title='店舗',
                    margin=dict(t=48, b=8),
                )
                st.plotly_chart(fig, use_container_width=True)

            # ── メトリクス ────────────────────────────────────
            st.divider()
            total = int(df_f['金額'].sum())
            store_totals = df_f.groupby('店舗名')['金額'].sum().sort_values(ascending=False)

            st.markdown('#### 集計サマリー')
            st.metric('総売上金額', f'¥{total:,}')

            if len(store_totals) > 0:
                cols_m = st.columns(min(len(store_totals), 3))
                for i, (store, amt) in enumerate(store_totals.items()):
                    share = amt / total * 100 if total > 0 else 0
                    with cols_m[i % len(cols_m)]:
                        st.metric(store, f'¥{int(amt):,}', f'{share:.1f}%')

            # ── 店舗別シェア円グラフ ──────────────────────────
            if len(store_totals) > 1:
                st.markdown('#### 店舗別 売上シェア')
                df_pie = store_totals.reset_index()
                df_pie.columns = ['店舗名', '金額']
                fig_pie = px.pie(
                    df_pie,
                    names='店舗名',
                    values='金額',
                    color='店舗名',
                    color_discrete_map=color_map,
                    hole=0.38,
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(
                    showlegend=True,
                    legend_title='店舗',
                    margin=dict(t=24, b=8),
                )
                st.plotly_chart(fig_pie, use_container_width=True)

        except Exception as e:
            st.error(f'データの集計・描画中にエラーが発生しました：{e}')

    if st.button('🔄 最新データを読み込む', key='reload_sales'):
        st.cache_data.clear()
        st.rerun()


# ════════════════════════════════════════════════════════════════
# タブ⑤：業者管理
# ════════════════════════════════════════════════════════════════
with tab_mgmt:
    st.markdown('#### 業者の連絡先一覧')
    st.caption('業者名をタップすると連絡先を確認・変更できます')

    try:
        all_products2  = load_products()
        suppliers_map2 = load_suppliers()
    except Exception as e:
        st.error(f'データの読み込みに失敗しました：{e}')
        all_products2  = []
        suppliers_map2 = {}

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
