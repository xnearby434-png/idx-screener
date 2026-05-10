import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="TM XNearby – IDX Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0a0c10; }
    div[data-testid="metric-container"] {
        background: #111318;
        border: 1px solid #1e2330;
        border-radius: 8px;
        padding: 12px 16px;
    }
    h1, h2, h3 { color: #00e5a0 !important; }
    .tag-asing   { background:rgba(61,156,245,0.2);  color:#3d9cf5; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; }
    .tag-smart   { background:rgba(0,229,160,0.2);   color:#00e5a0; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; }
    .tag-retail  { background:rgba(255,107,53,0.2);  color:#ff6b35; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:bold; }
    .tag-buy     { background:rgba(0,229,160,0.2);   color:#00e5a0; padding:3px 10px; border-radius:4px; font-weight:bold; }
    .tag-exit    { background:rgba(255,165,0,0.2);   color:orange;  padding:3px 10px; border-radius:4px; font-weight:bold; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DAFTAR SAHAM IDX
# ─────────────────────────────────────────────
IDX_TICKERS = {
    "AALI":"AALI.JK","ADRO":"ADRO.JK","AKRA":"AKRA.JK","ANTM":"ANTM.JK",
    "ARTO":"ARTO.JK","ASII":"ASII.JK","BBCA":"BBCA.JK","BBNI":"BBNI.JK",
    "BBRI":"BBRI.JK","BBTN":"BBTN.JK","BMRI":"BMRI.JK","BRIS":"BRIS.JK",
    "BRPT":"BRPT.JK","CPIN":"CPIN.JK","EMTK":"EMTK.JK","ERAA":"ERAA.JK",
    "EXCL":"EXCL.JK","GGRM":"GGRM.JK","GOTO":"GOTO.JK","HMSP":"HMSP.JK",
    "HRUM":"HRUM.JK","ICBP":"ICBP.JK","INCO":"INCO.JK","INDF":"INDF.JK",
    "INKP":"INKP.JK","INTP":"INTP.JK","ISAT":"ISAT.JK","ITMG":"ITMG.JK",
    "JPFA":"JPFA.JK","JSMR":"JSMR.JK","KLBF":"KLBF.JK","MAPI":"MAPI.JK",
    "MBMA":"MBMA.JK","MDKA":"MDKA.JK","MEDC":"MEDC.JK","MIKA":"MIKA.JK",
    "MNCN":"MNCN.JK","PGAS":"PGAS.JK","PGEO":"PGEO.JK","PTBA":"PTBA.JK",
    "PTPP":"PTPP.JK","SMGR":"SMGR.JK","SMRA":"SMRA.JK","TINS":"TINS.JK",
    "TLKM":"TLKM.JK","TOWR":"TOWR.JK","TPIA":"TPIA.JK","UNTR":"UNTR.JK",
    "UNVR":"UNVR.JK","WSKT":"WSKT.JK","ACES":"ACES.JK","AGII":"AGII.JK",
    "AMRT":"AMRT.JK","BSDE":"BSDE.JK","CTRA":"CTRA.JK","DSNG":"DSNG.JK",
    "ELSA":"ELSA.JK","ESSA":"ESSA.JK","HEAL":"HEAL.JK","HRTA":"HRTA.JK",
    "INDY":"INDY.JK","LSIP":"LSIP.JK","MYOR":"MYOR.JK","NCKL":"NCKL.JK",
    "PALM":"PALM.JK","POWR":"POWR.JK","PWON":"PWON.JK","SIDO":"SIDO.JK",
    "SSMS":"SSMS.JK","TKIM":"TKIM.JK","TBIG":"TBIG.JK","ULTJ":"ULTJ.JK",
    "WIKA":"WIKA.JK","WIFI":"WIFI.JK",
}

# ─────────────────────────────────────────────
# INDICATOR FUNCTIONS
# ─────────────────────────────────────────────
def sma(s, n): return s.rolling(n).mean()
def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + g / l.replace(0, np.nan))

def bb(s, n=20, m=2.0):
    b = sma(s, n)
    d = s.rolling(n).std()
    return b, b + m*d, b - m*d

def roc(s, n=12): return s.pct_change(n) * 100

def atr(h, l, c, n=14):
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def calc_psar(h, l, af0=0.02, af_i=0.02, af_max=0.2):
    ps = l.copy(); bull = True; af = af0; ep = h.iloc[0]; ps.iloc[0] = l.iloc[0]
    for i in range(1, len(h)):
        if bull:
            ps.iloc[i] = ps.iloc[i-1] + af*(ep - ps.iloc[i-1])
            ps.iloc[i] = min(ps.iloc[i], l.iloc[i-1], l.iloc[i-2] if i>1 else l.iloc[i-1])
            if l.iloc[i] < ps.iloc[i]: bull=False; ps.iloc[i]=ep; ep=l.iloc[i]; af=af0
            elif h.iloc[i] > ep: ep=h.iloc[i]; af=min(af+af_i, af_max)
        else:
            ps.iloc[i] = ps.iloc[i-1] + af*(ep - ps.iloc[i-1])
            ps.iloc[i] = max(ps.iloc[i], h.iloc[i-1], h.iloc[i-2] if i>1 else h.iloc[i-1])
            if h.iloc[i] > ps.iloc[i]: bull=True; ps.iloc[i]=ep; ep=h.iloc[i]; af=af0
            elif l.iloc[i] < ep: ep=l.iloc[i]; af=min(af+af_i, af_max)
    return ps

# ─────────────────────────────────────────────
# FOREIGN FLOW DETECTOR
# Karena data asing IDX tidak tersedia gratis via API,
# kita estimasi dari pola volume & harga (proxy method)
# ─────────────────────────────────────────────
def detect_foreign_flow(c, h, l, v):
    """
    Proxy estimasi foreign flow berdasarkan:
    1. Volume besar + harga naik kuat = potensi akumulasi asing
    2. Volume besar + gap up = institutional buying
    3. Konsistensi akumulasi 5 hari = asing biasa akumulasi gradual
    4. Spread bar lebar + close di atas midpoint = buying pressure tinggi
    """
    vol_ma   = sma(v, 20)
    close_ma = sma(c, 20)

    results = []
    for i in range(len(c)):
        if i < 5:
            results.append(0)
            continue

        # Money Flow Index proxy
        typical = (h.iloc[i] + l.iloc[i] + c.iloc[i]) / 3
        spread  = h.iloc[i] - l.iloc[i]
        mid     = (h.iloc[i] + l.iloc[i]) / 2
        vol_i   = v.iloc[i]
        vol_avg = vol_ma.iloc[i] if not pd.isna(vol_ma.iloc[i]) else vol_i

        # Close di atas midpoint = buying pressure
        close_strength = (c.iloc[i] - mid) / spread if spread > 0 else 0

        # Volume relatif
        rvol_i = vol_i / vol_avg if vol_avg > 0 else 1

        # Konsistensi 5 hari (asing biasa akumulasi gradual)
        up_days = sum(1 for j in range(i-4, i+1) if j > 0 and c.iloc[j] > c.iloc[j-1])

        # Skor per bar
        flow_score = (close_strength * rvol_i * 0.5) + (up_days / 5 * 0.5)
        results.append(flow_score)

    return pd.Series(results, index=c.index)

def classify_player(c, h, l, v, vol_ma_series):
    """
    Klasifikasi siapa yang bermain berdasarkan karakteristik volume & price:

    ASING / INSTITUSI:
    - Volume sangat besar (>2x rata-rata) + harga naik konsisten
    - Bar spread lebar, close di atas 70% range
    - Akumulasi gradual beberapa hari berturut-turut

    SMART MONEY (Bandar lokal):
    - Volume besar tiba-tiba 1 hari + reversal cepat
    - Gap up/down dengan volume besar
    - Harga breakout dari range sebelumnya

    RETAIL:
    - Volume kecil dengan volatilitas tinggi
    - Banyak hari turun setelah naik (profit taking cepat)
    - Volume justru besar saat harga overbought
    """
    n = len(c)
    if n < 10:
        return "UNKNOWN", 0, 0, 0

    # Window 10 hari terakhir
    w = min(10, n)
    c_w = c.iloc[-w:]; h_w = h.iloc[-w:]; l_w = l.iloc[-w:]; v_w = v.iloc[-w:]
    vol_avg = vol_ma_series.iloc[-1] if not pd.isna(vol_ma_series.iloc[-1]) else v_w.mean()

    # ── Skor Asing ─────────────────────────────
    asing_score = 0
    # Akumulasi gradual: harga naik konsisten
    up_days = sum(1 for i in range(1, w) if c_w.iloc[i] > c_w.iloc[i-1])
    if up_days >= 6: asing_score += 30
    elif up_days >= 4: asing_score += 15

    # Volume konsisten di atas rata-rata
    high_vol_days = sum(1 for i in range(w) if v_w.iloc[i] > vol_avg * 1.2)
    if high_vol_days >= 5: asing_score += 25
    elif high_vol_days >= 3: asing_score += 10

    # Close strength (close dekat high) beberapa hari
    strong_close = 0
    for i in range(w):
        spread_i = h_w.iloc[i] - l_w.iloc[i]
        if spread_i > 0:
            cs = (c_w.iloc[i] - l_w.iloc[i]) / spread_i
            if cs > 0.65: strong_close += 1
    if strong_close >= 5: asing_score += 25
    elif strong_close >= 3: asing_score += 10

    # Trend konsisten (tidak volatile)
    price_range = (c_w.max() - c_w.min()) / c_w.mean() * 100
    if price_range < 8: asing_score += 20  # pergerakan smooth

    # ── Skor Smart Money ────────────────────────
    sm_score = 0
    # Volume spike tiba-tiba (1-2 hari volume sangat besar)
    max_rvol = (v_w / vol_avg).max() if vol_avg > 0 else 1
    if max_rvol >= 3.0: sm_score += 35
    elif max_rvol >= 2.0: sm_score += 20

    # Reversal cepat setelah volume besar
    for i in range(1, w):
        if v_w.iloc[i] > vol_avg * 2 and c_w.iloc[i] > c_w.iloc[i-1]:
            sm_score += 20
            break

    # Wide bar (spread besar) + close kuat
    for i in range(w):
        spread_i = h_w.iloc[i] - l_w.iloc[i]
        avg_spread = (h_w - l_w).mean()
        if spread_i > avg_spread * 1.5:
            cs = (c_w.iloc[i] - l_w.iloc[i]) / spread_i if spread_i > 0 else 0
            if cs > 0.6: sm_score += 15; break

    # Recent strong candle (3 hari terakhir)
    for i in range(-3, 0):
        if c_w.iloc[i] > c_w.iloc[i-1] and v_w.iloc[i] > vol_avg * 1.5:
            sm_score += 15; break

    # ── Skor Retail ─────────────────────────────
    retail_score = 0
    # Volume tinggi saat harga sudah naik jauh (tanda retail FOMO)
    if c_w.iloc[-1] > c_w.mean() * 1.05 and v_w.iloc[-1] > vol_avg * 1.5:
        retail_score += 30
    # Volatilitas tinggi (naik turun tidak konsisten)
    down_days = w - up_days
    if up_days > 0 and down_days > 0:
        choppiness = min(up_days, down_days) / max(up_days, down_days)
        if choppiness > 0.6: retail_score += 25
    # Volume kecil
    avg_rvol = (v_w / vol_avg).mean() if vol_avg > 0 else 1
    if avg_rvol < 0.8: retail_score += 20

    # Tentukan pemain dominan
    scores = {"ASING": asing_score, "SMART MONEY": sm_score, "RETAIL": retail_score}
    dominant = max(scores, key=scores.get)
    if scores[dominant] < 25:
        dominant = "MIXED"

    return dominant, asing_score, sm_score, retail_score

# ─────────────────────────────────────────────
# MAIN SCORING ENGINE
# ─────────────────────────────────────────────
def score_ticker(df, params):
    if df is None or len(df) < 30:
        return None

    c = df["Close"].squeeze()
    h = df["High"].squeeze()
    l = df["Low"].squeeze()
    o = df["Open"].squeeze()
    v = df["Volume"].squeeze()

    # Indikator dasar
    basis, upper, lower = bb(c, params["bb_len"], params["bb_mult"])
    ema_line  = ema(c, params["ema_len"])
    ema_fast  = ema(c, 10)
    ema_slow  = ema(c, 30)
    rsi_line  = rsi(c, params["rsi_len"])
    roc_line  = ema(roc(c, params["roc_len"]), params["roc_smooth"])
    atr_line  = atr(h, l, c, 14)
    vol_ma    = sma(v, 20)

    # Deteksi pemain
    dominant, asing_sc, sm_sc, retail_sc = classify_player(c, h, l, v, vol_ma)
    flow = detect_foreign_flow(c, h, l, v)

    # Latest values
    price    = float(c.iloc[-1])
    ema_f    = float(ema_fast.iloc[-1])
    ema_s    = float(ema_slow.iloc[-1])
    ema_f5   = float(ema_fast.iloc[-5]) if len(ema_fast) > 5 else ema_f
    rsi_now  = float(rsi_line.iloc[-1])
    rsi_prev = float(rsi_line.iloc[-3]) if len(rsi_line) > 3 else rsi_now
    roc_now  = float(roc_line.iloc[-1])
    roc_prev = float(roc_line.iloc[-2]) if len(roc_line) > 2 else roc_now
    atr_now  = float(atr_line.iloc[-1])
    vol_avg  = float(vol_ma.iloc[-1]) if not pd.isna(vol_ma.iloc[-1]) else float(v.iloc[-1])
    rvol     = float(v.iloc[-1]) / vol_avg if vol_avg > 0 else 0
    c3       = float(c.iloc[-4]) if len(c) > 4 else price
    c_prev   = float(c.iloc[-2]) if len(c) > 2 else price
    flow_5d  = float(flow.iloc[-5:].mean())

    rng      = float(h.iloc[-1]) - float(l.iloc[-1])
    low_wick = float(c.iloc[-1]) - float(l.iloc[-1])
    up_wick  = float(h.iloc[-1]) - float(c.iloc[-1])

    sl  = price - atr_now * params["sl_atr"]
    rsk = max(price - sl, 1)
    tp1 = price + rsk * params["rr1"]
    tp2 = price + rsk * params["rr2"]
    tp3 = price + rsk * params["rr3"]

    # ── SCORING ───────────────────────────────────
    score    = 0
    signals  = []

    # 1. Trend utama: EMA10 > EMA30 (WAJIB)
    ema_bull = ema_f > ema_s
    if ema_bull:
        score += 20
        signals.append("✅ EMA10 > EMA30 (Uptrend)")
    else:
        signals.append("❌ Downtrend (EMA10 < EMA30)")

    # 2. EMA slope naik
    if ema_f > ema_f5:
        score += 10
        signals.append("EMA slope ↑")

    # 3. Harga di atas EMA
    if price > float(ema_line.iloc[-1]):
        score += 10
        signals.append("Harga > EMA")

    # 4. RSI zona bullish (50-70)
    if 50 <= rsi_now <= 70:
        score += 15
        signals.append(f"RSI {rsi_now:.1f} zona bullish")
    elif rsi_now < 50 and rsi_now > rsi_prev:
        score += 8
        signals.append(f"RSI {rsi_now:.1f} mulai naik ↑")

    # 5. ROC positif dan naik
    if roc_now > 0 and roc_now > roc_prev:
        score += 12
        signals.append(f"ROC ↑ +{roc_now:.2f}%")
    elif roc_now > 0:
        score += 6
        signals.append(f"ROC +{roc_now:.2f}%")

    # 6. Harga naik 3 hari
    if price > c3:
        score += 8
        signals.append("Harga naik 3 hari")

    # 7. Volume + harga naik (konfirmasi)
    if rvol >= params["rvol_min"] and price > c_prev:
        score += 12
        signals.append(f"Vol↑ + Harga↑ (RVOL {rvol:.1f}x)")
    elif rvol >= params["rvol_min"]:
        score += 4
        signals.append(f"RVOL {rvol:.1f}x")

    # 8. Pullback ke EMA (zona entry optimal)
    if ema_bull and price >= float(ema_line.iloc[-1]) * 0.97 and price <= float(ema_line.iloc[-1]) * 1.05:
        score += 13
        signals.append("Pullback ke EMA (zona entry)")

    # ── BONUS dari deteksi pemain ──────────────────
    if dominant == "ASING":
        score += 25
        signals.append("🔵 ASING AKUMULASI")
    elif dominant == "SMART MONEY":
        score += 20
        signals.append("🟢 SMART MONEY masuk")
    elif dominant == "MIXED" and asing_sc > 20:
        score += 10
        signals.append("🔵 Potensi akumulasi asing")

    # Foreign flow positif 5 hari
    if flow_5d > 0.5:
        score += 10
        signals.append(f"Foreign flow positif ({flow_5d:.2f})")

    # Penalty jika retail dominan (hati-hati, bisa jebakan)
    if dominant == "RETAIL":
        score -= 10
        signals.append("⚠️ Retail dominan (hati-hati)")

    # ── PSAR ──────────────────────────────────────
    try:
        psar_val = float(calc_psar(h, l).iloc[-1])
        if psar_val < price:
            score += 10
            signals.append("PSAR bullish ✓")
    except:
        psar_val = np.nan

    # ── BIAS ──────────────────────────────────────
    bull_pts = sum([
        ema_bull, ema_f > ema_f5,
        price > float(ema_line.iloc[-1]),
        rsi_now > 50, roc_now > 0, price > c3,
        dominant in ["ASING", "SMART MONEY"],
    ])
    if bull_pts >= 6:   bias = "BULLISH KUAT 🔥"
    elif bull_pts >= 4: bias = "BULLISH ✅"
    elif bull_pts >= 2: bias = "MIXED ⚠️"
    else:               bias = "BEARISH ❌"

    # ── SINYAL FINAL ──────────────────────────────
    # BUY hanya jika trend bullish + ada konfirmasi pemain besar
    strong_player = dominant in ["ASING", "SMART MONEY"]
    buy_signal  = score >= 55 and ema_bull and (strong_player or score >= 70)
    exit_signal = (
        price > float(basis.iloc[-1]) and
        rsi_now > params["rsi_exit_min"] and
        rng > 0 and up_wick > (rng * 0.35)
    )

    # Lot sizing
    risk_rp  = params["modal"] * params["risk_pct"] / 100
    lembar   = int(risk_rp / rsk / 100) * 100
    lot      = lembar // 100

    return {
        "Kode":        "",
        "Harga":       int(price),
        "RSI":         round(rsi_now, 1),
        "ROC%":        round(roc_now, 2),
        "RVOL":        round(rvol, 2),
        "EMA":         int(ema_line.iloc[-1]),
        "ATR":         int(atr_now),
        "SL":          int(sl),
        "TP1":         int(tp1),
        "TP2":         int(tp2),
        "TP3":         int(tp3),
        "Lot":         lot,
        "Lembar":      lembar,
        "Risk Rp":     int(risk_rp),
        "Skor":        score,
        "Sinyal":      "⚡ BUY" if buy_signal else ("⚠ EXIT" if exit_signal else "–"),
        "Bias":        bias,
        "Pemain":      dominant,
        "Skor Asing":  asing_sc,
        "Skor SM":     sm_sc,
        "Skor Retail": retail_sc,
        "Flow 5D":     round(flow_5d, 2),
        "Konfirmasi":  " | ".join(signals),
    }

# ─────────────────────────────────────────────
# DATA FETCH
# ─────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_and_screen(tickers_dict, params, period="3mo"):
    results = []
    bar  = st.progress(0)
    info = st.empty()
    n    = len(tickers_dict)
    for i, (code, sym) in enumerate(tickers_dict.items()):
        info.text(f"Scanning {code}... ({i+1}/{n})")
        bar.progress((i+1)/n)
        try:
            df = yf.download(sym, period=period, interval="1d",
                             progress=False, auto_adjust=True)
            if df is not None and len(df) >= 25:
                r = score_ticker(df, params)
                if r:
                    r["Kode"] = code
                    results.append(r)
        except:
            pass
        time.sleep(0.08)
    bar.empty(); info.empty()
    return pd.DataFrame(results) if results else pd.DataFrame()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parameter")
    st.markdown("---")
    st.markdown("**💰 Risk Management**")
    modal    = st.number_input("Modal (Rp)", value=10_000_000, step=500_000, format="%d")
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.5, 0.5)

    st.markdown("---")
    st.markdown("**📊 Indikator**")
    bb_len   = st.slider("BB Length", 10, 50, 20)
    bb_mult  = st.slider("BB Mult", 1.0, 3.0, 2.0, 0.1)
    ema_len  = st.slider("EMA Length", 5, 50, 20)
    rsi_len  = st.slider("RSI Length", 5, 21, 14)
    rsi_buy  = st.slider("RSI Max BUY", 20, 70, 70)
    rsi_exit = st.slider("RSI Min EXIT", 55, 85, 65)
    roc_len  = st.slider("ROC Length", 5, 20, 12)
    roc_sm   = st.slider("ROC Smooth", 1, 5, 3)
    rvol_min = st.slider("Min RVOL", 1.0, 3.0, 1.3, 0.1)
    sl_atr   = st.slider("SL ATR Mult", 1.0, 3.0, 1.5, 0.1)
    rr1      = st.slider("TP1 R:R", 1.0, 3.0, 1.5, 0.1)
    rr2      = st.slider("TP2 R:R", 1.5, 5.0, 2.5, 0.1)
    rr3      = st.slider("TP3 R:R", 2.0, 8.0, 4.0, 0.1)

    st.markdown("---")
    st.markdown("**🔍 Filter**")
    min_score     = st.slider("Min Skor", 0, 120, 55)
    filter_pemain = st.multiselect("Filter Pemain",
        ["ASING","SMART MONEY","MIXED","RETAIL"], default=["ASING","SMART MONEY","MIXED"])
    only_buy  = st.checkbox("BUY signal saja", True)
    sort_col  = st.selectbox("Urutkan", ["Skor","Skor Asing","Skor SM","RSI","RVOL"])
    period    = st.selectbox("Periode data", ["1mo","3mo","6mo"], index=1)
    scan_btn  = st.button("🔍 SCAN SEKARANG", use_container_width=True, type="primary")

params = {
    "modal":modal,"risk_pct":risk_pct,
    "bb_len":bb_len,"bb_mult":bb_mult,"ema_len":ema_len,
    "rsi_len":rsi_len,"rsi_buy_max":rsi_buy,"rsi_exit_min":rsi_exit,
    "roc_len":roc_len,"roc_smooth":roc_sm,"rvol_min":rvol_min,
    "sl_atr":sl_atr,"rr1":rr1,"rr2":rr2,"rr3":rr3,
}

# ─────────────────────────────────────────────
# MAIN UI
# ─────────────────────────────────────────────
st.markdown("# 📈 TM XNearby – IDX Screener")
st.markdown(f"*Long Only | Trend Following | Deteksi: Asing · Smart Money · Retail | {datetime.now().strftime('%d %b %Y %H:%M')}*")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Screener","🔵 Flow Asing","📋 Watchlist","📖 Panduan"])

# ─────────────────────────────────────────────
# TAB 1: SCREENER
# ─────────────────────────────────────────────
with tab1:
    if scan_btn or "df_res" not in st.session_state:
        with st.spinner("Scanning & mendeteksi pemain... (~2 menit)"):
            st.session_state["df_res"] = fetch_and_screen(IDX_TICKERS, params, period)

    df = st.session_state.get("df_res", pd.DataFrame())

    if df.empty:
        st.warning("Tidak ada data. Pastikan koneksi internet dan coba scan ulang.")
    else:
        # Filter
        df_show = df.copy()
        if only_buy:
            df_show = df_show[df_show["Sinyal"] == "⚡ BUY"]
        if filter_pemain:
            df_show = df_show[df_show["Pemain"].isin(filter_pemain)]
        df_show = df_show[df_show["Skor"] >= min_score]
        df_show = df_show.sort_values(sort_col, ascending=False)

        # Metrics
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Total Scan",   len(df))
        c2.metric("⚡ BUY",       len(df[df["Sinyal"]=="⚡ BUY"]))
        c3.metric("🔵 Asing",     len(df[df["Pemain"]=="ASING"]))
        c4.metric("🟢 Smart $",   len(df[df["Pemain"]=="SMART MONEY"]))
        c5.metric("🟠 Retail",    len(df[df["Pemain"]=="RETAIL"]))

        st.markdown("---")

        if df_show.empty:
            st.info("Tidak ada saham yang memenuhi kriteria. Coba turunkan Min Skor atau ubah filter.")
        else:
            st.markdown(f"### Hasil: {len(df_show)} saham")

            # Color functions
            def c_sinyal(v):
                if v=="⚡ BUY":  return "background:rgba(0,229,160,0.2);color:#00e5a0;font-weight:bold"
                if v=="⚠ EXIT": return "background:rgba(255,165,0,0.2);color:orange;font-weight:bold"
                return ""
            def c_rsi(v):
                if isinstance(v,(int,float)):
                    if 50<=v<=70: return "color:#00e5a0"
                    if v>70:      return "color:orange"
                return ""
            def c_skor(v):
                if isinstance(v,(int,float)):
                    if v>=80: return "background:rgba(0,229,160,0.2);font-weight:bold"
                    if v>=55: return "background:rgba(0,229,160,0.1)"
                return ""
            def c_pemain(v):
                if v=="ASING":       return "background:rgba(61,156,245,0.2);color:#3d9cf5;font-weight:bold"
                if v=="SMART MONEY": return "background:rgba(0,229,160,0.2);color:#00e5a0;font-weight:bold"
                if v=="RETAIL":      return "background:rgba(255,107,53,0.2);color:#ff6b35"
                return ""
            def c_bias(v):
                if "BULLISH KUAT" in str(v): return "color:#00e5a0;font-weight:bold"
                if "BULLISH" in str(v):      return "color:#00e5a0"
                if "BEARISH" in str(v):      return "color:#ff4560"
                return "color:orange"

            cols = ["Kode","Harga","RSI","ROC%","RVOL","EMA","SL","TP1","TP2",
                    "Lot","Skor","Pemain","Skor Asing","Skor SM","Sinyal","Bias"]

            styled = (
                df_show[cols].style
                .map(c_sinyal,  subset=["Sinyal"])
                .map(c_rsi,     subset=["RSI"])
                .map(c_skor,    subset=["Skor"])
                .map(c_pemain,  subset=["Pemain"])
                .map(c_bias,    subset=["Bias"])
                .format({
                    "Harga":"{:,}","EMA":"{:,}","SL":"{:,}","TP1":"{:,}","TP2":"{:,}",
                    "ROC%":"{:.2f}","RVOL":"{:.2f}x","Skor":"{:.0f}",
                    "Skor Asing":"{:.0f}","Skor SM":"{:.0f}",
                })
            )
            st.dataframe(styled, use_container_width=True, height=480)

            # DETAIL
            st.markdown("---")
            st.markdown("### 🔎 Detail Saham")
            sel = st.selectbox("Pilih saham:", df_show["Kode"].tolist())
            if sel:
                row = df_show[df_show["Kode"]==sel].iloc[0]

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown("**📊 Trade Setup**")
                    st.markdown(f"""
| | Harga |
|--|--|
| Entry | Rp{row['Harga']:,} |
| SL | Rp{row['SL']:,} |
| TP1 (R:R {rr1}) | Rp{row['TP1']:,} |
| TP2 (R:R {rr2}) | Rp{row['TP2']:,} |
| TP3 (R:R {rr3}) | Rp{row['TP3']:,} |
                    """)
                with col_b:
                    st.markdown("**💰 Risk**")
                    st.markdown(f"""
| | |
|--|--|
| Modal | Rp{modal:,} |
| Risk % | {risk_pct}% |
| Risk Rp | Rp{row['Risk Rp']:,} |
| Lot | {row['Lot']} Lot |
| Lembar | {row['Lembar']:,} lbr |
                    """)
                with col_c:
                    st.markdown("**🎮 Pemain**")
                    pemain = row["Pemain"]
                    emoji = "🔵" if pemain=="ASING" else ("🟢" if pemain=="SMART MONEY" else "🟠")
                    st.markdown(f"**{emoji} {pemain}**")
                    st.progress(min(row["Skor Asing"]/100, 1.0), text=f"Asing: {row['Skor Asing']:.0f}/100")
                    st.progress(min(row["Skor SM"]/100, 1.0),    text=f"Smart Money: {row['Skor SM']:.0f}/100")
                    st.progress(min(row["Skor Retail"]/100, 1.0),text=f"Retail: {row['Skor Retail']:.0f}/100")

                st.markdown(f"**✅ Konfirmasi:** {row['Konfirmasi']}")

                # Mini chart
                try:
                    sym = IDX_TICKERS.get(sel)
                    if sym:
                        df_c = yf.download(sym, period="3mo", interval="1d",
                                           progress=False, auto_adjust=True)
                        if not df_c.empty:
                            cs = df_c["Close"].squeeze()
                            _, bb_u, bb_l = bb(cs, bb_len, bb_mult)
                            em = ema(cs, ema_len)
                            ef = ema(cs, 10)
                            es = ema(cs, 30)
                            st.line_chart(pd.DataFrame({
                                "Harga":cs,"BB Upper":bb_u,"BB Lower":bb_l,
                                "EMA":em,"EMA10":ef,"EMA30":es
                            }))
                except:
                    pass

            # Download
            csv = df_show[cols].to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV",
                csv, f"IDX_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv", use_container_width=True)

# ─────────────────────────────────────────────
# TAB 2: FOREIGN FLOW ANALYSIS
# ─────────────────────────────────────────────
with tab2:
    st.markdown("### 🔵 Analisis Akumulasi Asing & Smart Money")
    st.info("Deteksi berdasarkan pola volume, price action, dan konsistensi akumulasi. Bukan data real foreign flow dari IDX.")

    df = st.session_state.get("df_res", pd.DataFrame())
    if df.empty:
        st.warning("Scan dulu di tab Screener.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🔵 Top Akumulasi ASING")
            df_asing = df.nlargest(15, "Skor Asing")[
                ["Kode","Harga","Skor Asing","Skor SM","Bias","Sinyal","Flow 5D"]
            ]
            def c_asing(v):
                if isinstance(v,(int,float)) and v>=50: return "color:#3d9cf5;font-weight:bold"
                return ""
            st.dataframe(
                df_asing.style.map(c_asing, subset=["Skor Asing"])
                .map(c_sinyal, subset=["Sinyal"])
                .format({"Harga":"{:,}","Skor Asing":"{:.0f}","Skor SM":"{:.0f}","Flow 5D":"{:.2f}"}),
                use_container_width=True
            )

        with col2:
            st.markdown("#### 🟢 Top SMART MONEY")
            df_sm = df.nlargest(15, "Skor SM")[
                ["Kode","Harga","Skor SM","Skor Asing","Bias","Sinyal","RVOL"]
            ]
            def c_sm(v):
                if isinstance(v,(int,float)) and v>=50: return "color:#00e5a0;font-weight:bold"
                return ""
            st.dataframe(
                df_sm.style.map(c_sm, subset=["Skor SM"])
                .map(c_sinyal, subset=["Sinyal"])
                .format({"Harga":"{:,}","Skor SM":"{:.0f}","Skor Asing":"{:.0f}","RVOL":"{:.2f}x"}),
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("#### ⚠️ Waspada – Retail Dominan (Potensi Overbought / Jebakan)")
        df_retail = df[df["Pemain"]=="RETAIL"].nlargest(10, "Skor Retail")[
            ["Kode","Harga","RSI","RVOL","Skor Retail","Bias","Sinyal"]
        ]
        if df_retail.empty:
            st.success("Tidak ada saham retail dominan yang terdeteksi saat ini.")
        else:
            st.dataframe(
                df_retail.style
                .map(c_rsi, subset=["RSI"])
                .format({"Harga":"{:,}","Skor Retail":"{:.0f}","RVOL":"{:.2f}x"}),
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("#### 📊 Distribusi Pemain")
        dist = df["Pemain"].value_counts()
        st.bar_chart(dist)

# ─────────────────────────────────────────────
# TAB 3: WATCHLIST
# ─────────────────────────────────────────────
with tab3:
    st.markdown("### 📋 Scan Saham Pilihan")
    inp = st.text_input("Kode saham (pisah koma):", "BBCA, BBRI, TLKM, GOTO, ESSA, BRIS")
    if st.button("🔍 Scan Watchlist", type="primary"):
        codes = [x.strip().upper() for x in inp.split(",") if x.strip()]
        with st.spinner(f"Scanning {len(codes)} saham..."):
            df_w = fetch_and_screen({c: f"{c}.JK" for c in codes}, params, period)
        if not df_w.empty:
            cols_w = ["Kode","Harga","RSI","ROC%","RVOL","SL","TP1","TP2",
                      "Lot","Skor","Pemain","Skor Asing","Skor SM","Sinyal","Bias"]
            st.dataframe(
                df_w[cols_w].style
                .map(c_sinyal, subset=["Sinyal"])
                .map(c_pemain, subset=["Pemain"])
                .format({"Harga":"{:,}","SL":"{:,}","TP1":"{:,}","TP2":"{:,}",
                         "ROC%":"{:.2f}","RVOL":"{:.2f}x"}),
                use_container_width=True
            )
        else:
            st.warning("Data tidak ditemukan.")

# ─────────────────────────────────────────────
# TAB 4: PANDUAN
# ─────────────────────────────────────────────
with tab4:
    st.markdown("""
### 📖 Panduan Lengkap

#### 🎮 Klasifikasi Pemain
| Pemain | Karakteristik | Artinya |
|--------|--------------|---------|
| 🔵 **ASING** | Volume konsisten besar, harga naik gradual, spread bar lebar | Institusi asing akumulasi → ikuti! |
| 🟢 **SMART MONEY** | Volume spike tiba-tiba, reversal cepat, wide bar + close kuat | Bandar lokal masuk → ikuti! |
| 🟠 **RETAIL** | Volume tinggi saat harga sudah naik, volatilitas tinggi | Jangan ikuti — bisa jebakan |
| ⚪ **MIXED** | Tidak ada dominan jelas | Tunggu konfirmasi lebih |

#### 📊 Scoring System (Total maks ~145)
| Sinyal | Poin |
|--------|------|
| EMA10 > EMA30 (Uptrend) | 20 |
| EMA slope naik | 10 |
| Harga > EMA | 10 |
| RSI 50-70 zona bullish | 15 |
| ROC positif & naik | 12 |
| Harga naik 3 hari | 8 |
| Volume + harga naik | 12 |
| Pullback ke EMA | 13 |
| **Asing akumulasi (bonus)** | **25** |
| **Smart Money masuk (bonus)** | **20** |
| Foreign flow positif 5D | 10 |
| PSAR bullish | 10 |
| Retail dominan (penalty) | -10 |

#### 🎯 Cara Pakai
1. Scan setiap pagi **sebelum jam 09:30 WIB**
2. Prioritaskan skor ≥ 70 dengan pemain **ASING atau SMART MONEY**
3. Konfirmasi di chart TradingView (timeframe Daily + 1H)
4. Entry setelah candle **konfirmasi bullish** terbentuk
5. Pasang SL sesuai yang tertera — **jangan dimodifikasi**

#### ⚠️ Disclaimer
Screener ini adalah alat bantu analisis teknikal, **BUKAN rekomendasi investasi**.
Data foreign flow adalah **estimasi proxy** dari price & volume action,
bukan data real dari IDX. Selalu lakukan riset sendiri.
    """)

st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#64748b;font-size:11px'>"
    f"TM XNearby IDX Screener | Long Only | Trend Following | "
    f"Deteksi Pemain: Asing · Smart Money · Retail | "
    f"{datetime.now().strftime('%d %b %Y')}</div>",
    unsafe_allow_html=True
)