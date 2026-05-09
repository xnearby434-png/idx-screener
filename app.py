import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TM XNearby – IDX Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0a0c10; }
    .stMetric { background: #111318; border: 1px solid #1e2330; border-radius: 8px; padding: 12px; }
    .stDataFrame { font-size: 12px; }
    div[data-testid="metric-container"] {
        background: #111318;
        border: 1px solid #1e2330;
        border-radius: 8px;
        padding: 12px 16px;
    }
    .buy-signal  { background-color: rgba(0,229,160,0.15); color: #00e5a0; font-weight: bold; padding: 3px 8px; border-radius: 4px; }
    .exit-signal { background-color: rgba(255,165,0,0.15); color: orange; font-weight: bold; padding: 3px 8px; border-radius: 4px; }
    .neutral     { background-color: rgba(100,116,139,0.15); color: #64748b; padding: 3px 8px; border-radius: 4px; }
    h1, h2, h3  { color: #00e5a0 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DAFTAR SAHAM IDX (LQ45 + IDXSMC + pilihan)
# ─────────────────────────────────────────────
IDX_TICKERS = {
    # LQ45 Blue Chips
    "AALI": "AALI.JK",  "ADRO": "ADRO.JK",  "AKRA": "AKRA.JK",
    "ANTM": "ANTM.JK",  "ARTO": "ARTO.JK",  "ASII": "ASII.JK",
    "BBCA": "BBCA.JK",  "BBNI": "BBNI.JK",  "BBRI": "BBRI.JK",
    "BBTN": "BBTN.JK",  "BMRI": "BMRI.JK",  "BRIS": "BRIS.JK",
    "BRPT": "BRPT.JK",  "CPIN": "CPIN.JK",  "EMTK": "EMTK.JK",
    "ERAA": "ERAA.JK",  "EXCL": "EXCL.JK",  "GGRM": "GGRM.JK",
    "GOTO": "GOTO.JK",  "HMSP": "HMSP.JK",  "HRUM": "HRUM.JK",
    "ICBP": "ICBP.JK",  "INCO": "INCO.JK",  "INDF": "INDF.JK",
    "INKP": "INKP.JK",  "INTP": "INTP.JK",  "ISAT": "ISAT.JK",
    "ITMG": "ITMG.JK",  "JPFA": "JPFA.JK",  "JSMR": "JSMR.JK",
    "KLBF": "KLBF.JK",  "MAPI": "MAPI.JK",  "MBMA": "MBMA.JK",
    "MDKA": "MDKA.JK",  "MEDC": "MEDC.JK",  "MIKA": "MIKA.JK",
    "MNCN": "MNCN.JK",  "PGAS": "PGAS.JK",  "PGEO": "PGEO.JK",
    "PTBA": "PTBA.JK",  "PTPP": "PTPP.JK",  "SMGR": "SMGR.JK",
    "SMRA": "SMRA.JK",  "TINS": "TINS.JK",  "TLKM": "TLKM.JK",
    "TOWR": "TOWR.JK",  "TPIA": "TPIA.JK",  "UNTR": "UNTR.JK",
    "UNVR": "UNVR.JK",  "WSKT": "WSKT.JK",
    # IDX80 Tambahan
    "ACES": "ACES.JK",  "AGII": "AGII.JK",  "AMRT": "AMRT.JK",
    "APEX": "APEX.JK",  "BFIN": "BFIN.JK",  "BMRI": "BMRI.JK",
    "BSDE": "BSDE.JK",  "CTRA": "CTRA.JK",  "DNET": "DNET.JK",
    "DSNG": "DSNG.JK",  "ELSA": "ELSA.JK",  "ESSA": "ESSA.JK",
    "HEAL": "HEAL.JK",  "HOKI": "HOKI.JK",  "HRTA": "HRTA.JK",
    "INDY": "INDY.JK",  "IPCC": "IPCC.JK",  "ITMG": "ITMG.JK",
    "LSIP": "LSIP.JK",  "MAPA": "MAPA.JK",  "MYOR": "MYOR.JK",
    "NCKL": "NCKL.JK",  "PALM": "PALM.JK",  "PNLF": "PNLF.JK",
    "POWR": "POWR.JK",  "PWON": "PWON.JK",  "SIDO": "SIDO.JK",
    "SMCB": "SMCB.JK",  "SRTG": "SRTG.JK",  "SSMS": "SSMS.JK",
    "TKIM": "TKIM.JK",  "TBIG": "TBIG.JK",  "ULTJ": "ULTJ.JK",
    "WIFI": "WIFI.JK",  "WIKA": "WIKA.JK",
}

# ─────────────────────────────────────────────
# INDICATOR FUNCTIONS
# ─────────────────────────────────────────────
def calc_sma(series, period):
    return series.rolling(window=period).mean()

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_bb(series, period=20, mult=2.0):
    basis = calc_sma(series, period)
    std   = series.rolling(period).std()
    upper = basis + mult * std
    lower = basis - mult * std
    return basis, upper, lower

def calc_roc(series, period=12):
    return series.pct_change(periods=period) * 100

def calc_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calc_psar(high, low, af_start=0.02, af_inc=0.02, af_max=0.2):
    """Simplified PSAR"""
    psar   = low.copy()
    bull   = True
    af     = af_start
    ep     = high.iloc[0]
    psar.iloc[0] = low.iloc[0]
    for i in range(1, len(high)):
        if bull:
            psar.iloc[i] = psar.iloc[i-1] + af * (ep - psar.iloc[i-1])
            psar.iloc[i] = min(psar.iloc[i], low.iloc[i-1], low.iloc[i-2] if i > 1 else low.iloc[i-1])
            if low.iloc[i] < psar.iloc[i]:
                bull = False
                psar.iloc[i] = ep
                ep = low.iloc[i]
                af = af_start
            else:
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + af_inc, af_max)
        else:
            psar.iloc[i] = psar.iloc[i-1] + af * (ep - psar.iloc[i-1])
            psar.iloc[i] = max(psar.iloc[i], high.iloc[i-1], high.iloc[i-2] if i > 1 else high.iloc[i-1])
            if high.iloc[i] > psar.iloc[i]:
                bull = True
                psar.iloc[i] = ep
                ep = high.iloc[i]
                af = af_start
            else:
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + af_inc, af_max)
    return psar

# ─────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────
def score_ticker(df, params):
    if df is None or len(df) < 30:
        return None

    c = df["Close"].squeeze()
    h = df["High"].squeeze()
    l = df["Low"].squeeze()
    o = df["Open"].squeeze()
    v = df["Volume"].squeeze()

    basis, upper, lower = calc_bb(c, params["bb_len"], params["bb_mult"])
    ema    = calc_ema(c, params["ema_len"])
    rsi    = calc_rsi(c, params["rsi_len"])
    roc    = calc_ema(calc_roc(c, params["roc_len"]), params["roc_smooth"])
    atr    = calc_atr(h, l, c, 14)
    vol_ma = calc_sma(v, 20)

    # Latest values
    latest = {
        "close":  c.iloc[-1],
        "open":   o.iloc[-1],
        "high":   h.iloc[-1],
        "low":    l.iloc[-1],
        "volume": v.iloc[-1],
        "basis":  basis.iloc[-1],
        "upper":  upper.iloc[-1],
        "lower":  lower.iloc[-1],
        "ema":    ema.iloc[-1],
        "rsi":    rsi.iloc[-1],
        "roc":    roc.iloc[-1],
        "atr":    atr.iloc[-1],
        "vol_ma": vol_ma.iloc[-1],
        "rvol":   v.iloc[-1] / vol_ma.iloc[-1] if vol_ma.iloc[-1] > 0 else 0,
    }

    price = latest["close"]
    sl    = price - latest["atr"] * params["sl_atr"]
    rsk   = price - sl
    tp1   = price + rsk * params["rr1"]
    tp2   = price + rsk * params["rr2"]
    tp3   = price + rsk * params["rr3"]

    # ── SCORING ──────────────────────────────────
    score = 0
    signals = []

    # 1. RSI oversold
    if latest["rsi"] < params["rsi_buy_max"]:
        score += 20
        signals.append(f"RSI {latest['rsi']:.1f} < {params['rsi_buy_max']}")

    # 2. Harga dekat / di bawah BB lower
    touch_pct = params["touch_pct"]
    if latest["close"] <= latest["lower"] * touch_pct:
        score += 25
        signals.append("Sentuh BB Lower")
    elif latest["close"] < latest["basis"]:
        score += 10
        signals.append("Di bawah BB Basis")

    # 3. ROC positif (momentum bullish)
    if latest["roc"] > 0:
        score += 15
        signals.append(f"ROC +{latest['roc']:.2f}%")

    # 4. Harga di bawah EMA (zona diskon)
    if latest["close"] < latest["ema"]:
        score += 10
        signals.append("Di bawah EMA")

    # 5. Volume spike
    if latest["rvol"] >= params["rvol_min"]:
        score += 15
        signals.append(f"RVOL {latest['rvol']:.1f}x")

    # 6. Lower wick (rejection dari bawah)
    body  = abs(latest["close"] - latest["open"])
    rng   = latest["high"] - latest["low"]
    lower_wick = latest["close"] - latest["low"]
    if rng > 0 and lower_wick > (rng * 0.4):
        score += 15
        signals.append("Lower wick kuat")

    # 7. PSAR di atas harga (potensi reversal)
    try:
        psar_val = calc_psar(h, l).iloc[-1]
        if psar_val > latest["close"]:
            score += 10
            signals.append("PSAR ↑ (reversal)")
        latest["psar"] = psar_val
    except:
        latest["psar"] = np.nan

    # ── BIAS ──────────────────────────────────────
    bias = "BULLISH" if latest["close"] >= latest["ema"] else "BEARISH"

    # ── EXIT SIGNAL ───────────────────────────────
    upper_wick  = latest["high"] - latest["close"]
    exit_signal = (
        latest["close"] > latest["basis"] and
        latest["rsi"]   > params["rsi_exit_min"] and
        upper_wick > (rng * 0.4)
    )

    # Lot sizing
    risk_rp   = params["modal"] * params["risk_pct"] / 100
    risk_per  = max(price - sl, 1)
    lembar    = int(risk_rp / risk_per / 100) * 100
    lot       = lembar // 100

    return {
        "Kode":       "",  # filled later
        "Harga":      int(price),
        "RSI":        round(latest["rsi"], 1),
        "ROC%":       round(latest["roc"], 2),
        "RVOL":       round(latest["rvol"], 2),
        "BB Lower":   int(latest["lower"]),
        "EMA":        int(latest["ema"]),
        "ATR":        int(latest["atr"]),
        "SL":         int(sl),
        "TP1":        int(tp1),
        "TP2":        int(tp2),
        "TP3":        int(tp3),
        "Lot":        lot,
        "Lembar":     lembar,
        "Risk Rp":    int(risk_rp),
        "Skor":       score,
        "Sinyal":     "⚡ BUY" if score >= 50 else ("⚠ EXIT" if exit_signal else "–"),
        "Bias":       bias,
        "Konfirmasi": " | ".join(signals) if signals else "–",
    }

# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)  # cache 1 jam
def fetch_and_screen(tickers_dict, params, period="3mo"):
    results = []
    progress = st.progress(0)
    status   = st.empty()
    total    = len(tickers_dict)

    for i, (code, ticker) in enumerate(tickers_dict.items()):
        status.text(f"Scanning {code}... ({i+1}/{total})")
        progress.progress((i+1) / total)
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
            if df is not None and len(df) >= 20:
                result = score_ticker(df, params)
                if result:
                    result["Kode"] = code
                    results.append(result)
        except Exception:
            pass
        time.sleep(0.1)  # hindari rate limit

    progress.empty()
    status.empty()
    return pd.DataFrame(results) if results else pd.DataFrame()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parameter")
    st.markdown("---")

    st.markdown("**Risk Management**")
    modal    = st.number_input("Modal (Rp)", value=10_000_000, step=500_000, format="%d")
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.5, 0.5)

    st.markdown("---")
    st.markdown("**Indikator**")
    bb_len      = st.slider("BB Length", 10, 50, 20)
    bb_mult     = st.slider("BB Mult", 1.0, 3.0, 2.0, 0.1)
    ema_len     = st.slider("EMA Length", 5, 50, 20)
    rsi_len     = st.slider("RSI Length", 5, 21, 14)
    rsi_buy_max = st.slider("RSI Max BUY", 20, 60, 45)
    rsi_exit    = st.slider("RSI Min EXIT", 55, 85, 65)
    roc_len     = st.slider("ROC Length", 5, 20, 12)
    roc_smooth  = st.slider("ROC Smooth", 1, 5, 3)
    touch_pct   = st.slider("Touch Tolerance", 1.00, 1.05, 1.01, 0.001)
    rvol_min    = st.slider("Min RVOL", 1.0, 3.0, 1.5, 0.1)
    sl_atr      = st.slider("SL ATR Mult", 1.0, 3.0, 1.5, 0.1)
    rr1         = st.slider("TP1 R:R", 1.0, 3.0, 1.5, 0.1)
    rr2         = st.slider("TP2 R:R", 1.5, 5.0, 2.5, 0.1)
    rr3         = st.slider("TP3 R:R", 2.0, 8.0, 4.0, 0.1)

    st.markdown("---")
    st.markdown("**Filter Tampilan**")
    min_score = st.slider("Min Skor BUY", 0, 100, 50)
    show_only_buy = st.checkbox("Tampilkan BUY signal saja", value=True)
    sort_by   = st.selectbox("Urutkan berdasarkan", ["Skor", "RSI", "RVOL", "Harga"])

    period = st.selectbox("Periode data", ["1mo", "3mo", "6mo"], index=1)

    scan_btn = st.button("🔍 SCAN SEKARANG", use_container_width=True, type="primary")

params = {
    "modal": modal, "risk_pct": risk_pct,
    "bb_len": bb_len, "bb_mult": bb_mult,
    "ema_len": ema_len, "rsi_len": rsi_len,
    "rsi_buy_max": rsi_buy_max, "rsi_exit_min": rsi_exit,
    "roc_len": roc_len, "roc_smooth": roc_smooth,
    "touch_pct": touch_pct, "rvol_min": rvol_min,
    "sl_atr": sl_atr, "rr1": rr1, "rr2": rr2, "rr3": rr3,
}

# ─────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────
st.markdown("# 📈 TM XNearby – IDX Screener")
st.markdown(f"*Long Only | Scan otomatis {len(IDX_TICKERS)} saham IDX | Update: {datetime.now().strftime('%d %b %Y %H:%M')}*")
st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Screener", "📋 Watchlist Manual", "📖 Panduan"])

# ─────────────────────────────────────────────
# TAB 1: SCREENER
# ─────────────────────────────────────────────
with tab1:
    if scan_btn or "df_results" not in st.session_state:
        with st.spinner("Scanning saham IDX... harap tunggu 1-2 menit"):
            st.session_state["df_results"] = fetch_and_screen(IDX_TICKERS, params, period)

    df = st.session_state.get("df_results", pd.DataFrame())

    if df.empty:
        st.warning("Tidak ada data. Pastikan koneksi internet aktif dan coba scan ulang.")
    else:
        # Filter
        if show_only_buy:
            df_show = df[df["Sinyal"] == "⚡ BUY"].copy()
        else:
            df_show = df.copy()

        df_show = df_show[df_show["Skor"] >= min_score]
        df_show = df_show.sort_values(sort_by, ascending=(sort_by == "RSI"))

        # Metrics
        total_buy  = len(df[df["Sinyal"] == "⚡ BUY"])
        total_exit = len(df[df["Sinyal"] == "⚠ EXIT"])
        avg_rsi    = df[df["Sinyal"] == "⚡ BUY"]["RSI"].mean() if total_buy > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Saham Scan",  len(df))
        col2.metric("⚡ BUY Signal",     total_buy,  delta=None)
        col3.metric("⚠ EXIT Signal",    total_exit, delta=None)
        col4.metric("Avg RSI (BUY)",     f"{avg_rsi:.1f}" if total_buy > 0 else "–")

        st.markdown("---")

        if df_show.empty:
            st.info("Tidak ada saham yang memenuhi kriteria saat ini. Coba turunkan Min Skor atau ubah filter.")
        else:
            st.markdown(f"### Hasil Scan: {len(df_show)} saham")

            # Color coding
            def color_signal(val):
                if val == "⚡ BUY":  return "background-color: rgba(0,229,160,0.2); color: #00e5a0; font-weight: bold"
                if val == "⚠ EXIT": return "background-color: rgba(255,165,0,0.2); color: orange; font-weight: bold"
                return ""

            def color_rsi(val):
                if isinstance(val, float):
                    if val < 30: return "color: #00e5a0; font-weight: bold"
                    if val > 65: return "color: orange"
                return ""

            def color_score(val):
                if isinstance(val, (int, float)):
                    if val >= 70: return "background-color: rgba(0,229,160,0.2); font-weight: bold"
                    if val >= 50: return "background-color: rgba(0,229,160,0.1)"
                return ""

            def color_bias(val):
                if val == "BULLISH": return "color: #00e5a0"
                if val == "BEARISH": return "color: #ff4560"
                return ""

            display_cols = ["Kode", "Harga", "RSI", "ROC%", "RVOL", "BB Lower",
                            "EMA", "SL", "TP1", "TP2", "Lot", "Skor", "Sinyal", "Bias", "Konfirmasi"]

            styled = (
                df_show[display_cols]
                .style
                .map(color_signal, subset=["Sinyal"])
                .map(color_rsi,    subset=["RSI"])
                .map(color_score,  subset=["Skor"])
                .map(color_bias,   subset=["Bias"])
                .format({
                    "Harga": "{:,}", "BB Lower": "{:,}", "EMA": "{:,}",
                    "SL": "{:,}", "TP1": "{:,}", "TP2": "{:,}",
                    "ROC%": "{:.2f}", "RVOL": "{:.2f}x", "Skor": "{:.0f}"
                })
            )
            st.dataframe(styled, use_container_width=True, height=500)

            # Detail saham terpilih
            st.markdown("---")
            st.markdown("### 🔎 Detail Saham")
            selected = st.selectbox("Pilih saham untuk detail:", df_show["Kode"].tolist())

            if selected:
                row = df_show[df_show["Kode"] == selected].iloc[0]
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Harga",    f"Rp{row['Harga']:,}")
                c2.metric("RSI",      f"{row['RSI']:.1f}")
                c3.metric("RVOL",     f"{row['RVOL']:.2f}x")
                c4.metric("Skor",     f"{row['Skor']:.0f}/110")
                c5.metric("Bias",     row["Bias"])

                st.markdown("#### Trade Setup")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"""
| Level | Harga |
|-------|-------|
| **Entry** | Rp{row['Harga']:,} |
| **SL** | Rp{row['SL']:,} |
| **TP1** (R:R {rr1}) | Rp{row['TP1']:,} |
| **TP2** (R:R {rr2}) | Rp{row['TP2']:,} |
| **TP3** (R:R {rr3}) | Rp{row['TP3']:,} |
                    """)
                with col_b:
                    st.markdown(f"""
| Risk | Nilai |
|------|-------|
| **Modal** | Rp{modal:,} |
| **Risk %** | {risk_pct}% |
| **Risk Rp** | Rp{row['Risk Rp']:,} |
| **Lot** | {row['Lot']} Lot ({row['Lembar']:,} lbr) |
| **ATR** | Rp{row['ATR']:,} |
                    """)

                st.markdown(f"**Konfirmasi:** {row['Konfirmasi']}")

                # Chart mini
                try:
                    ticker_sym = IDX_TICKERS.get(selected)
                    if ticker_sym:
                        df_chart = yf.download(ticker_sym, period="3mo", interval="1d",
                                               progress=False, auto_adjust=True)
                        if not df_chart.empty:
                            close_s = df_chart["Close"].squeeze()
                            _, bb_u, bb_l = calc_bb(close_s, bb_len, bb_mult)
                            ema_s = calc_ema(close_s, ema_len)
                            chart_df = pd.DataFrame({
                                "Harga": close_s,
                                "BB Upper": bb_u,
                                "BB Lower": bb_l,
                                "EMA": ema_s
                            })
                            st.line_chart(chart_df)
                except:
                    pass

            # Download
            st.markdown("---")
            csv = df_show[display_cols].to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Hasil Screener (CSV)",
                csv,
                f"IDX_Screener_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )

# ─────────────────────────────────────────────
# TAB 2: WATCHLIST MANUAL
# ─────────────────────────────────────────────
with tab2:
    st.markdown("### Scan Saham Pilihan Sendiri")
    st.markdown("Masukkan kode saham IDX (pisah koma, tanpa .JK):")

    custom_input = st.text_input("Contoh: BBCA, TLKM, GOTO, ESSA", "BBCA, BBRI, TLKM, GOTO, BRIS")
    custom_btn   = st.button("🔍 Scan Watchlist", type="primary")

    if custom_btn and custom_input:
        codes = [c.strip().upper() for c in custom_input.split(",") if c.strip()]
        custom_tickers = {c: f"{c}.JK" for c in codes}

        with st.spinner(f"Scanning {len(codes)} saham..."):
            df_custom = fetch_and_screen(custom_tickers, params, period)

        if not df_custom.empty:
            st.dataframe(df_custom[[
                "Kode","Harga","RSI","ROC%","RVOL","SL","TP1","TP2","Lot","Skor","Sinyal","Bias","Konfirmasi"
            ]], use_container_width=True)
        else:
            st.warning("Data tidak ditemukan. Pastikan kode saham benar.")

# ─────────────────────────────────────────────
# TAB 3: PANDUAN
# ─────────────────────────────────────────────
with tab3:
    st.markdown("""
### 📖 Cara Pakai IDX Screener

#### Sistem Scoring (Total maks ~110)
| Konfirmasi | Poin |
|-----------|------|
| RSI < batas BUY | 20 |
| Sentuh BB Lower | 25 |
| Di bawah BB Basis saja | 10 |
| ROC positif (momentum ↑) | 15 |
| Harga di bawah EMA | 10 |
| Volume spike (RVOL tinggi) | 15 |
| Lower wick kuat | 15 |
| PSAR di atas harga | 10 |

#### Interpretasi Skor
| Skor | Arti |
|------|------|
| ≥ 80 | 🔥 Setup sangat kuat — prioritas utama |
| 60–79 | ✅ Setup baik — layak dipertimbangkan |
| 50–59 | ⚠️ Setup lemah — tunggu konfirmasi lebih |
| < 50 | ❌ Belum masuk kriteria |

#### Kolom Penting
- **SL**: Stop Loss berdasarkan ATR × multiplier
- **TP1/TP2**: Target profit berdasarkan R:R ratio
- **Lot**: Jumlah lot berdasarkan risk % dari modal
- **RVOL**: Relative Volume (1.5x = volume 50% lebih tinggi dari rata-rata)
- **ROC%**: Rate of Change — positif artinya momentum naik

#### Tips
1. Gunakan timeframe **Daily** sebagai filter utama
2. Konfirmasi di **1H atau 4H** sebelum entry
3. Prioritaskan saham dengan skor ≥ 70 dan RVOL ≥ 1.5x
4. Jangan entry jika market sedang crash besar (cek IHSG dulu)
5. Scan ulang setiap hari sebelum jam 09:30 WIB

#### Cara Deploy ke Internet (Streamlit Cloud)
```
1. Upload folder ini ke GitHub (gratis)
2. Buka share.streamlit.io
3. Connect repo GitHub kamu
4. Klik Deploy — selesai! Website langsung online
```
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:11px'>"
    "TM XNearby IDX Screener | Long Only | Bukan rekomendasi investasi | "
    f"Data via Yahoo Finance | {datetime.now().strftime('%d %b %Y')}"
    "</div>",
    unsafe_allow_html=True
)