import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(page_title="TM QTS – IDX", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
div[data-testid="metric-container"] { background:#111318; border:1px solid #1e2330; border-radius:8px; padding:12px 16px; }
h1,h2,h3 { color:#00e5a0 !important; }
.badge { padding:3px 10px; border-radius:4px; font-size:11px; font-weight:bold; display:inline-block; }
.prime   { background:rgba(255,215,0,0.2);   color:#ffd700; }
.strong  { background:rgba(0,229,160,0.2);   color:#00e5a0; }
.spec    { background:rgba(255,165,0,0.2);   color:#ffa500; }
.hold    { background:rgba(61,156,245,0.2);  color:#3d9cf5; }
.bear    { background:rgba(255,69,96,0.2);   color:#ff4560; }
.takeoff { background:rgba(255,215,0,0.25);  color:#ffd700; font-size:13px; }
.early   { background:rgba(0,229,160,0.25);  color:#00e5a0; font-size:13px; }
</style>
""", unsafe_allow_html=True)

# ─── SAHAM IDX LENGKAP (330+ saham) ─────────
_RAW = [
    # PERBANKAN
    "BBCA","BBRI","BMRI","BBNI","BBTN","BRIS","NISP","MEGA","BNGA","BNLI",
    "PNBN","BDMN","BTPS","BJTM","BJBR","BSIM","BCIC","AGRO","ARTO","BBYB",
    "DNAR","INPC","BBMD","NOBU","BACA","MCOR","BGTG","BANK","AMAR","BABP",
    # KONSUMER MAKANAN & MINUMAN
    "ICBP","INDF","MYOR","CPIN","JPFA","ULTJ","SIDO","DLTA","MLBI","SKBM",
    "SKLT","ROTI","GOOD","HOKI","CEKA","BUDI","CAMP","DMND","KEJU","PANI",
    # RETAIL & CONSUMER
    "MAPI","ACES","RALS","LPPF","MPMX","AMRT","MIDI","HERO","CSAP","RANC",
    "ERAA","KINO","MBTO","TCID","UNVR","GGRM","HMSP","WIIM","RMBA",
    # PROPERTI
    "BSDE","CTRA","SMRA","PWON","DMAS","LPKR","ASRI","JRPT","MKPI","PPRO",
    "MTLA","BKSL","KIJA","PLIN","EMDE","DART","DUTI","GPRA","NIRO","OMRE",
    "TARA","MDLN","APLN","BEST","DILD","KOTA","FORZ","URBN",
    # TELEKOMUNIKASI & TEKNOLOGI
    "TLKM","EXCL","ISAT","FREN","TBIG","TOWR","LINK","MNCN","EMTK","MDIA",
    "DNET","WIFI","GOTO","BUKA","MCAS","NTBK","KETR","DOOH",
    # ENERGI BATUBARA
    "ADRO","PTBA","HRUM","ITMG","INDY","BYAN","ARII","DOID","GEMS",
    "MBAP","MYOH","PKPK","SMMT","BSSR","TOBA","DEWA","COAL",
    # MINYAK & GAS
    "ELSA","MEDC","PGAS","RAJA","RUIS","BIPI","ESSA","ARTI","ENRG",
    # TAMBANG MINERAL & NIKEL
    "INCO","ANTM","TINS","MBMA","NCKL","MDKA","PSAB","DKFT","NICL","AGMR",
    "PGEO","SMCB","IFSH",
    # INFRASTRUKTUR
    "JSMR","WIKA","PTPP","ADHI","WSKT","WTON","ACST","NRCA","TOTL","DGIK",
    "IDPR","WEGE","PBSA","PPRE",
    # HEALTHCARE & FARMASI
    "KLBF","MIKA","HEAL","SILO","SAME","PRDA","BMHS","TSPC","KAEF","PYFA",
    "SQBI","INAF","DVLA","PRIM","RSGK","DAYA",
    # PERTANIAN & PERKEBUNAN
    "AALI","LSIP","SSMS","PALM","DSNG","SIMP","TBLA","SMAR","BWPT",
    "JAWA","SGRO","TAPG","CSRA","ANJT",
    # KIMIA & INDUSTRI DASAR
    "TPIA","BRPT","DPNS","EKAD","INCI","SRSN","UNIC","AKPI","APLI",
    "BRNA","FPNI","IGAR","IMPC","IPOL","TRST","YPAS",
    # SEMEN & KONSTRUKSI MATERIAL
    "SMGR","INTP","SMBR","WSBP","MARK","KDSI","ISSP","LION","LMSH","PICO",
    # OTOMOTIF
    "ASII","AUTO","BOLT","GJTL","GDYR","IMAS","INDS","MASA","NIPS","SMSM","TURI",
    # KEUANGAN NON BANK
    "PNLF","ADMF","BFIN","CSUL","MFIN","TIFA","WOMF","BCAP","BPFI",
    "SMMA","AMOR","KREN","RELI","DEFI",
    # MEDIA & ENTERTAINMENT
    "MNCN","SCMA","KBLV","MSKY","ABBA","FORU","LPLI",
    # TEKSTIL
    "TRIS","ARGO","ERTX","ESTI","INDR","SRIL","RICY","TFCO","POLU",
    # TRANSPORTASI & LOGISTIK
    "GIAA","CMPP","SMDR","SHIP","NELY","TMAS","WINS","BLTA","ASSA","BIRD",
    # CONSUMER LAIN
    "INKP","TKIM","AKRA","UNTR","BRPT","HRTA","POWR","PWON","SIDO",
    "TBIG","WIKA","WIFI","MAPA","SSMS","TBLA",
    # SPEKULATIF & SMALL CAP AKTIF
    "SMIL","CBMF","RAAM","FORE","MUTU","SONA","MAYA","LUCK","PURE",
    "LABA","PANS","CUAN","NASI","PADI","KOPI","BUMI","BKDP","CPRI",
    "BBMD","ANDI","APEX","MEJA","GOLD","BHAT","GAMA","RBMS","SAFE",
]
# Hapus duplikat, buat dict
_UNIQUE = list(dict.fromkeys(_RAW))
IDX_TICKERS = {code: f"{code}.JK" for code in _UNIQUE}

# ─── HELPERS ─────────────────────────────────
def sma(s,n): return s.rolling(n).mean()
def ema(s,n): return s.ewm(span=n,adjust=False).mean()
def rsi(s,n=14):
    d=s.diff(); g=d.clip(lower=0).rolling(n).mean(); l=(-d.clip(upper=0)).rolling(n).mean()
    return 100-100/(1+g/l.replace(0,np.nan))
def atr(h,l,c,n=14):
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()
def calc_psar(h,l,af0=0.02,afi=0.02,afm=0.2):
    ps=l.copy(); bull=True; af=af0; ep=h.iloc[0]; ps.iloc[0]=l.iloc[0]
    for i in range(1,len(h)):
        if bull:
            ps.iloc[i]=ps.iloc[i-1]+af*(ep-ps.iloc[i-1])
            ps.iloc[i]=min(ps.iloc[i],l.iloc[i-1],l.iloc[i-2] if i>1 else l.iloc[i-1])
            if l.iloc[i]<ps.iloc[i]: bull=False;ps.iloc[i]=ep;ep=l.iloc[i];af=af0
            elif h.iloc[i]>ep: ep=h.iloc[i];af=min(af+afi,afm)
        else:
            ps.iloc[i]=ps.iloc[i-1]+af*(ep-ps.iloc[i-1])
            ps.iloc[i]=max(ps.iloc[i],h.iloc[i-1],h.iloc[i-2] if i>1 else h.iloc[i-1])
            if h.iloc[i]>ps.iloc[i]: bull=True;ps.iloc[i]=ep;ep=h.iloc[i];af=af0
            elif l.iloc[i]<ep: ep=l.iloc[i];af=min(af+afi,afm)
    return ps

# ─── CORE SCORING (MAX 100) ──────────────────
def analyze(df, params):
    if df is None or len(df) < 40: return None
    c=df["Close"].squeeze(); h=df["High"].squeeze()
    l=df["Low"].squeeze(); o=df["Open"].squeeze(); v=df["Volume"].squeeze()

    vol_ma20  = sma(v, 20)
    vol_ma5   = sma(v, 5)
    ema10     = ema(c, 10)
    ema20     = ema(c, 20)
    ema30     = ema(c, 30)
    ema50     = ema(c, 50)
    rsi_line  = rsi(c, 14)
    atr_line  = atr(h, l, c, 14)

    # Latest values
    price     = float(c.iloc[-1])
    vol_now   = float(v.iloc[-1])
    vol_avg   = float(vol_ma20.iloc[-1]) if not pd.isna(vol_ma20.iloc[-1]) else vol_now
    vol_avg5  = float(vol_ma5.iloc[-3])  if len(vol_ma5)>3 else vol_avg
    rvol      = vol_now / vol_avg if vol_avg > 0 else 1
    rsi_now   = float(rsi_line.iloc[-1])
    rsi_prev  = float(rsi_line.iloc[-5]) if len(rsi_line)>5 else rsi_now
    atr_now   = float(atr_line.iloc[-1])
    e10       = float(ema10.iloc[-1]); e20=float(ema20.iloc[-1])
    e30       = float(ema30.iloc[-1]); e50=float(ema50.iloc[-1])
    e10_5d    = float(ema10.iloc[-5]) if len(ema10)>5 else e10
    e30_5d    = float(ema30.iloc[-5]) if len(ema30)>5 else e30
    c_prev    = float(c.iloc[-2]) if len(c)>2 else price
    c_5d      = float(c.iloc[-6]) if len(c)>6 else price
    c_20d     = float(c.iloc[-21]) if len(c)>21 else price
    c_low_20  = float(c.iloc[-20:].min())
    c_high_20 = float(c.iloc[-20:].max())
    rng_20    = c_high_20 - c_low_20
    open_now  = float(o.iloc[-1])

    # ── VOLUME PATTERN ANALYSIS ──────────────
    # Cek apakah volume sepi sebelumnya (10-30 hari lalu)
    vol_quiet_period = float(v.iloc[-30:-5].mean()) if len(v)>30 else vol_avg
    vol_quiet_ratio  = vol_quiet_period / vol_avg if vol_avg > 0 else 1
    was_quiet        = vol_quiet_ratio < 0.7   # volume sepi sebelumnya

    # Volume explosion: volume hari ini vs rata-rata quiet period
    vol_explosion_ratio = vol_now / vol_quiet_period if vol_quiet_period > 0 else 1
    vol_exploding = vol_explosion_ratio >= 3.0

    # Volume spike 5 hari terakhir
    vol_spike_5d = float(v.iloc[-5:].max()) / vol_avg if vol_avg > 0 else 1
    recent_spike = vol_spike_5d >= 2.5

    # ── RANGE / CONSOLIDATION ────────────────
    # Konsolidasi sempit: range 20 hari < 15% dari harga
    range_pct     = rng_20 / c_low_20 * 100 if c_low_20 > 0 else 99
    tight_range   = range_pct < 15
    very_tight    = range_pct < 8

    # ── BREAKOUT DETECTION ───────────────────
    # Harga breakout dari range konsolidasi
    breakout_now   = price > c_high_20 * 0.98  # breakout atau hampir
    strong_breakout= price > c_high_20 * 1.02  # breakout kuat
    close_strength = (price - float(l.iloc[-1])) / (float(h.iloc[-1]) - float(l.iloc[-1])) if (float(h.iloc[-1])-float(l.iloc[-1]))>0 else 0.5

    # ── EMA ANALYSIS ─────────────────────────
    ema_bull      = e10 > e30
    ema_fan       = e10 > e20 > e30   # EMA fan bullish
    ema_crossover = e10 > e30 and e10_5d <= e30_5d  # golden cross baru
    ema_slope_up  = e10 > e10_5d
    price_above_emas = price > e10 and price > e20

    # ── NAIK DULUAN CHECK (penalty) ──────────
    already_up_20d = (price - c_20d) / c_20d * 100 if c_20d > 0 else 0

    # ── PEMAIN DETECTION ─────────────────────
    strong_close_days = sum(1 for i in range(-10,0)
        if len(h)>abs(i) and (h.iloc[i]-l.iloc[i])>0
        and (c.iloc[i]-l.iloc[i])/(h.iloc[i]-l.iloc[i]) > 0.6)
    up_days_10 = sum(1 for i in range(-10,0) if len(c)>abs(i) and c.iloc[i]>c.iloc[i-1])
    high_vol_days = sum(1 for i in range(-10,0) if len(v)>abs(i) and v.iloc[i]>vol_avg*1.3)

    asing_score = min(100, (up_days_10/10*40) + (strong_close_days/10*35) + (min(high_vol_days/10,1)*25))
    sm_score    = min(100, (min(vol_explosion_ratio/5,1)*50) + (close_strength*30) + (20 if recent_spike else 0))

    if asing_score >= 60:   pemain = "ASING"
    elif sm_score >= 55:    pemain = "SMART MONEY"
    elif asing_score >= 40: pemain = "MIXED"
    else:                   pemain = "RETAIL"

    # ═══════════════════════════════════════
    # SCORING SYSTEM — TOTAL MAX 100
    # ═══════════════════════════════════════
    score = 0
    factors = []

    # 1. VOLUME EXPLOSION (maks 30 poin) — faktor terpenting
    if vol_exploding and was_quiet:
        score += 30
        factors.append(f"Volume meledak {vol_explosion_ratio:.1f}x setelah sepi")
    elif vol_exploding:
        score += 20
        factors.append(f"Volume meledak {vol_explosion_ratio:.1f}x")
    elif recent_spike:
        score += 12
        factors.append(f"Volume spike {vol_spike_5d:.1f}x (5 hari)")
    elif rvol >= 1.5:
        score += 6
        factors.append(f"RVOL {rvol:.1f}x")

    # 2. KONSOLIDASI SEBELUMNYA (maks 15 poin)
    if very_tight and was_quiet:
        score += 15
        factors.append(f"Konsolidasi sangat ketat ({range_pct:.1f}%)")
    elif tight_range:
        score += 8
        factors.append(f"Konsolidasi sempit ({range_pct:.1f}%)")

    # 3. BREAKOUT (maks 20 poin)
    if strong_breakout and close_strength > 0.7:
        score += 20
        factors.append("Breakout kuat + close tinggi")
    elif breakout_now and close_strength > 0.6:
        score += 13
        factors.append("Breakout dari range + close kuat")
    elif breakout_now:
        score += 7
        factors.append("Breakout dari range")

    # 4. EMA (maks 15 poin)
    if ema_crossover:
        score += 15
        factors.append("Golden Cross EMA10/30 (baru!)")
    elif ema_fan:
        score += 12
        factors.append("EMA fan bullish (10>20>30)")
    elif ema_bull and ema_slope_up:
        score += 7
        factors.append("EMA10 > EMA30 + slope naik")
    elif ema_bull:
        score += 4
        factors.append("EMA10 > EMA30")

    # 5. RSI (maks 10 poin)
    if 40 <= rsi_now <= 65 and rsi_now > rsi_prev:
        score += 10
        factors.append(f"RSI {rsi_now:.1f} naik dari {rsi_prev:.1f}")
    elif rsi_now < 40 and rsi_now > rsi_prev:
        score += 8
        factors.append(f"RSI {rsi_now:.1f} keluar oversold")
    elif 40 <= rsi_now <= 65:
        score += 5
        factors.append(f"RSI {rsi_now:.1f} zona sehat")

    # 6. PEMAIN (maks 10 poin)
    if pemain == "ASING":
        score += 10
        factors.append("Asing akumulasi")
    elif pemain == "SMART MONEY":
        score += 8
        factors.append("Smart money masuk")
    elif pemain == "MIXED":
        score += 4
        factors.append("Mixed (asing/SM potensi)")

    # PENALTY: sudah naik duluan
    if already_up_20d > 40:
        score -= 25
        factors.append(f"⚠ Sudah naik {already_up_20d:.0f}% (20 hari)")
    elif already_up_20d > 25:
        score -= 15
        factors.append(f"⚠ Sudah naik {already_up_20d:.0f}% (20 hari)")
    elif already_up_20d > 15:
        score -= 5
        factors.append(f"Naik {already_up_20d:.0f}% (20 hari)")

    score = max(0, min(100, score))

    # ═══════════════════════════════════════
    # FASE DETEKSI (Wyckoff)
    # ═══════════════════════════════════════
    if was_quiet and tight_range and not recent_spike:
        fase = "AKUMULASI"
    elif (vol_exploding or recent_spike) and (breakout_now or ema_crossover) and was_quiet:
        fase = "TAKE OFF"
    elif ema_fan and price_above_emas and already_up_20d > 10:
        fase = "MARKUP"
    elif already_up_20d > 30 and rsi_now > 65:
        fase = "DISTRIBUSI"
    elif not ema_bull and rsi_now < 45:
        fase = "DOWNTREND"
    else:
        fase = "TRANSISI"

    # ═══════════════════════════════════════
    # SINYAL
    # ═══════════════════════════════════════
    if score >= 80:
        sinyal = "PRIME BUY 🔥"
        kategori_trade = "Trading Kilat"
    elif score >= 65:
        sinyal = "STRONG BUY"
        kategori_trade = "Trading Santai"
    elif score >= 50:
        sinyal = "Speculative BUY"
        kategori_trade = "Speculative"
    elif score >= 35 and fase == "AKUMULASI":
        sinyal = "Early BUY Signal"
        kategori_trade = "Trading Santai"
    elif already_up_20d > 30 or (not ema_bull and rsi_now < 40):
        sinyal = "BEAR / EXIT"
        kategori_trade = "-"
    else:
        sinyal = "WAIT"
        kategori_trade = "-"

    # ═══════════════════════════════════════
    # SIAP TAKE OFF?
    # ═══════════════════════════════════════
    siap_takeoff = (
        fase in ["AKUMULASI", "TRANSISI"] and
        was_quiet and tight_range and
        recent_spike and score >= 40
    )
    early_buy = (
        fase == "AKUMULASI" and
        was_quiet and tight_range and
        not recent_spike and
        rvol >= 1.2 and score >= 30
    )

    # ── TRADE SETUP ──────────────────────────
    sl   = price - atr_now * params["sl_atr"]
    rsk  = max(price - sl, 1)
    tp1  = price + rsk * params["rr1"]
    tp2  = price + rsk * params["rr2"]
    tp3  = price + rsk * params["rr3"]
    risk_rp  = params["modal"] * params["risk_pct"] / 100
    lembar   = int(risk_rp / rsk / 100) * 100
    lot      = lembar // 100

    return {
        "Kode":         "",
        "Harga":        int(price),
        "Skor":         int(score),
        "Fase":         fase,
        "Sinyal":       sinyal,
        "Kategori":     kategori_trade,
        "Siap Take Off":siap_takeoff,
        "Early BUY":    early_buy,
        "Pemain":       pemain,
        "RSI":          round(rsi_now, 1),
        "RVOL":         round(rvol, 2),
        "Vol Exp":      round(vol_explosion_ratio, 1),
        "Range%":       round(range_pct, 1),
        "Naik 20d%":    round(already_up_20d, 1),
        "EMA Status":   "Fan ↑" if ema_fan else ("Cross!" if ema_crossover else ("Bull" if ema_bull else "Bear")),
        "SL":           int(sl),
        "TP1":          int(tp1),
        "TP2":          int(tp2),
        "TP3":          int(tp3),
        "Lot":          lot,
        "Lembar":       lembar,
        "Risk Rp":      int(risk_rp),
        "ATR":          int(atr_now),
        "Faktor":       " | ".join(factors) if factors else "-",
        "Skor Asing":   round(asing_score, 0),
        "Skor SM":      round(sm_score, 0),
    }

# ─── FETCH ───────────────────────────────────
@st.cache_data(ttl=3600)
def run_scan(tickers, params, period):
    results = []
    bar = st.progress(0); info = st.empty(); n = len(tickers)
    for i, (code, sym) in enumerate(tickers.items()):
        info.text(f"Scanning {code}... ({i+1}/{n})")
        bar.progress((i+1)/n)
        try:
            df = yf.download(sym, period=period, interval="1d", progress=False, auto_adjust=True)
            if df is not None and len(df) >= 35:
                r = analyze(df, params)
                if r:
                    r["Kode"] = code
                    results.append(r)
        except: pass
        time.sleep(0.08)
    bar.empty(); info.empty()
    return pd.DataFrame(results) if results else pd.DataFrame()

# ─── SIDEBAR ─────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Parameter")
    st.markdown("---")
    st.markdown("**💰 Risk Management**")
    modal    = st.number_input("Modal (Rp)", value=10_000_000, step=500_000, format="%d")
    risk_pct = st.slider("Risk per Trade (%)", 0.5, 5.0, 1.5, 0.5)

    st.markdown("---")
    st.markdown("**📊 Trade Setup**")
    sl_atr = st.slider("SL ATR Mult", 1.0, 3.0, 1.5, 0.1)
    rr1    = st.slider("TP1 R:R", 1.0, 3.0, 1.5, 0.1)
    rr2    = st.slider("TP2 R:R", 1.5, 5.0, 2.5, 0.1)
    rr3    = st.slider("TP3 R:R", 2.0, 8.0, 4.0, 0.1)

    st.markdown("---")
    st.markdown("**🔍 Filter Scan**")
    min_score  = st.slider("Min Skor", 0, 100, 35)
    period     = st.selectbox("Periode data", ["2mo","3mo","6mo"], index=1)
    scan_btn   = st.button("🔍 SCAN SEKARANG", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("**Keterangan Fase**")
    st.markdown("""
- 🟡 **AKUMULASI** — range sempit, volume sepi
- 🚀 **TAKE OFF** — volume meledak + breakout
- 📈 **MARKUP** — trend naik kuat
- 🔴 **DISTRIBUSI** — waspada, siap turun
- ⬇️ **DOWNTREND** — hindari
    """)

params = {"modal":modal,"risk_pct":risk_pct,"sl_atr":sl_atr,"rr1":rr1,"rr2":rr2,"rr3":rr3}

# ─── MAIN ────────────────────────────────────
st.markdown("# 🚀 TM Quantitative Trading System — IDX")
st.markdown(f"*Long Only | Deteksi: Akumulasi → Take Off → Markup | Skor Max 100 | Scan {len(IDX_TICKERS)} saham | {datetime.now().strftime('%d %b %Y %H:%M')}*")
st.markdown("---")

# Tambah saham custom
with st.expander("➕ Tambah Saham Custom ke Scan"):
    custom_input = st.text_input("Kode saham tambahan (pisah koma):", placeholder="contoh: BREN, CUAN, PANI")
    if custom_input:
        extras = [x.strip().upper() for x in custom_input.split(",") if x.strip()]
        for e in extras:
            if e not in IDX_TICKERS:
                IDX_TICKERS[e] = f"{e}.JK"
        st.success(f"✅ {len(extras)} saham ditambahkan. Total scan: {len(IDX_TICKERS)} saham")

if scan_btn or "df_qts" not in st.session_state:
    with st.spinner("Scanning & menganalisa fase saham..."):
        st.session_state["df_qts"] = run_scan(IDX_TICKERS, params, period)

df = st.session_state.get("df_qts", pd.DataFrame())

if df.empty:
    st.warning("Tidak ada data. Cek koneksi internet dan scan ulang.")
    st.stop()

# ─── TABS ────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Siap Take Off",
    "🌱 Early BUY Signal",
    "📊 Semua Saham",
    "🎮 Per Kategori Trading",
    "📖 Panduan"
])

# ── COLOR FUNCTIONS ──────────────────────────
def c_sinyal(v):
    m = {"PRIME BUY 🔥":"background:rgba(255,215,0,0.2);color:#ffd700;font-weight:bold",
         "STRONG BUY":"background:rgba(0,229,160,0.2);color:#00e5a0;font-weight:bold",
         "Speculative BUY":"background:rgba(255,165,0,0.2);color:#ffa500;font-weight:bold",
         "Early BUY Signal":"background:rgba(61,156,245,0.2);color:#3d9cf5;font-weight:bold",
         "BEAR / EXIT":"background:rgba(255,69,96,0.2);color:#ff4560;font-weight:bold"}
    return m.get(v,"")

def c_fase(v):
    m = {"TAKE OFF":"background:rgba(255,215,0,0.2);color:#ffd700;font-weight:bold",
         "MARKUP":"background:rgba(0,229,160,0.2);color:#00e5a0",
         "AKUMULASI":"background:rgba(61,156,245,0.2);color:#3d9cf5",
         "DISTRIBUSI":"background:rgba(255,69,96,0.2);color:#ff4560",
         "DOWNTREND":"background:rgba(255,69,96,0.3);color:#ff4560"}
    return m.get(v,"")

def c_skor(v):
    if isinstance(v,(int,float)):
        if v>=80: return "background:rgba(255,215,0,0.2);font-weight:bold;color:#ffd700"
        if v>=65: return "background:rgba(0,229,160,0.15);color:#00e5a0"
        if v>=50: return "background:rgba(255,165,0,0.15);color:#ffa500"
    return ""

def c_pemain(v):
    m = {"ASING":"background:rgba(61,156,245,0.2);color:#3d9cf5;font-weight:bold",
         "SMART MONEY":"background:rgba(0,229,160,0.2);color:#00e5a0;font-weight:bold",
         "RETAIL":"background:rgba(255,107,53,0.2);color:#ff6b35"}
    return m.get(v,"")

def render_table(df_in, cols):
    subset_cols = [c for c in ["Sinyal","Fase","Skor","Pemain"] if c in cols]
    s = df_in[cols].style
    if "Sinyal"  in cols: s = s.map(c_sinyal,  subset=["Sinyal"])
    if "Fase"    in cols: s = s.map(c_fase,    subset=["Fase"])
    if "Skor"    in cols: s = s.map(c_skor,    subset=["Skor"])
    if "Pemain"  in cols: s = s.map(c_pemain,  subset=["Pemain"])
    fmt = {}
    for col in cols:
        if col in ["Harga","SL","TP1","TP2","TP3","ATR"]: fmt[col]="{:,}"
        elif col in ["RSI","Range%","Naik 20d%"]:         fmt[col]="{:.1f}"
        elif col in ["RVOL","Vol Exp"]:                   fmt[col]="{:.1f}x"
    return s.format(fmt)

# ─── TAB 1: SIAP TAKE OFF ────────────────────
with tab1:
    st.markdown("### 🚀 Saham Siap Take Off")
    st.markdown("*Volume mulai meledak setelah sepi panjang + range konsolidasi sempit. Ini momen paling bagus!*")

    df_to = df[df["Siap Take Off"]==True].sort_values("Skor", ascending=False)
    df_prime = df[(df["Sinyal"]=="PRIME BUY 🔥") | (df["Sinyal"]=="STRONG BUY")].sort_values("Skor", ascending=False)

    c1,c2,c3 = st.columns(3)
    c1.metric("🚀 Siap Take Off",  len(df_to))
    c2.metric("🔥 PRIME BUY",     len(df[df["Sinyal"]=="PRIME BUY 🔥"]))
    c3.metric("✅ STRONG BUY",    len(df[df["Sinyal"]=="STRONG BUY"]))

    st.markdown("---")

    if df_to.empty:
        st.info("Belum ada saham yang terdeteksi siap take off saat ini. Coba scan ulang esok hari.")
    else:
        st.markdown(f"**{len(df_to)} saham terdeteksi siap take off:**")
        cols_to = ["Kode","Harga","Skor","Fase","Sinyal","Pemain","RSI","RVOL","Vol Exp","Range%","EMA Status","SL","TP1","TP2","Lot","Faktor"]
        st.dataframe(render_table(df_to, cols_to), use_container_width=True, height=400)

    st.markdown("---")
    st.markdown("### 🔥 PRIME BUY & STRONG BUY")
    if df_prime.empty:
        st.info("Tidak ada saat ini.")
    else:
        cols_p = ["Kode","Harga","Skor","Fase","Sinyal","Kategori","Pemain","RSI","RVOL","SL","TP1","TP2","TP3","Lot","Faktor"]
        st.dataframe(render_table(df_prime, cols_p), use_container_width=True, height=350)

# ─── TAB 2: EARLY BUY SIGNAL ─────────────────
with tab2:
    st.markdown("### 🌱 Early BUY Signal — Akumulasi Belum Selesai")
    st.markdown("""
    *Saham yang masih dalam fase akumulasi (range sempit, volume sepi) tapi mulai ada tanda-tanda volume 
    sedikit naik. Ini untuk yang sabar menunggu — entry lebih awal, risk lebih rendah.*
    """)

    df_early = df[df["Early BUY"]==True].sort_values("Skor", ascending=False)
    df_accum = df[df["Fase"]=="AKUMULASI"].sort_values("Skor", ascending=False)

    c1,c2,c3 = st.columns(3)
    c1.metric("🌱 Early BUY",    len(df_early))
    c2.metric("📦 Fase Akumulasi",len(df_accum))
    c3.metric("⏳ Perlu Sabar",   len(df_accum) - len(df_early))

    st.markdown("---")
    st.markdown("#### 🌱 Early BUY — Mulai Pantau")
    if df_early.empty:
        st.info("Tidak ada early signal saat ini. Semua saham akumulasi masih belum ada tanda-tanda.")
    else:
        cols_e = ["Kode","Harga","Skor","Fase","Sinyal","Pemain","RSI","RVOL","Range%","Naik 20d%","EMA Status","SL","TP1","TP2","Lot","Faktor"]
        st.dataframe(render_table(df_early, cols_e), use_container_width=True, height=350)

    st.markdown("---")
    st.markdown("#### 📦 Semua Saham Fase Akumulasi (Watchlist)")
    st.markdown("*Belum ada sinyal, tapi pantau terus. Bisa take off kapan saja.*")
    if df_accum.empty:
        st.info("Tidak ada saham di fase akumulasi saat ini.")
    else:
        cols_a = ["Kode","Harga","Skor","Fase","Pemain","RSI","RVOL","Range%","EMA Status","Faktor"]
        st.dataframe(render_table(df_accum, cols_a), use_container_width=True, height=350)

# ─── TAB 3: SEMUA SAHAM ──────────────────────
with tab3:
    st.markdown("### 📊 Semua Saham")

    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        filter_fase = st.multiselect("Filter Fase",
            ["TAKE OFF","MARKUP","AKUMULASI","TRANSISI","DISTRIBUSI","DOWNTREND"],
            default=["TAKE OFF","MARKUP","AKUMULASI","TRANSISI"])
    with col_filter2:
        filter_pemain = st.multiselect("Filter Pemain",
            ["ASING","SMART MONEY","MIXED","RETAIL"],
            default=["ASING","SMART MONEY","MIXED","RETAIL"])
    with col_filter3:
        min_s = st.slider("Min Skor", 0, 100, min_score, key="s3")

    df_all = df[
        df["Fase"].isin(filter_fase) &
        df["Pemain"].isin(filter_pemain) &
        (df["Skor"] >= min_s)
    ].sort_values("Skor", ascending=False)

    st.markdown(f"**{len(df_all)} saham** | Total scan: {len(df)}")

    cols_all = ["Kode","Harga","Skor","Fase","Sinyal","Kategori","Pemain",
                "RSI","RVOL","Vol Exp","Range%","Naik 20d%","EMA Status","SL","TP1","TP2","Lot"]
    st.dataframe(render_table(df_all, cols_all), use_container_width=True, height=500)

    # Download
    csv = df_all[cols_all].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv,
        f"IDX_QTS_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# ─── TAB 4: KATEGORI TRADING ─────────────────
with tab4:
    st.markdown("### 🎮 Pilih Gaya Trading")

    gaya = st.radio("Kategori:", ["Trading Kilat ⚡","Trading Santai 😎","Swing / Positional 📈"], horizontal=True)

    st.markdown("---")

    if "Kilat" in gaya:
        st.markdown("#### ⚡ Trading Kilat — Target 1–5 Hari")
        st.markdown("*Volume explosion baru terjadi, momentum tinggi, masuk cepat keluar cepat*")
        df_k = df[
            (df["Kategori"]=="Trading Kilat") |
            ((df["Fase"]=="TAKE OFF") & (df["Skor"]>=60))
        ].sort_values("Skor",ascending=False)
        if df_k.empty:
            st.info("Tidak ada setup Trading Kilat saat ini.")
        else:
            cols_k = ["Kode","Harga","Skor","Fase","Sinyal","Pemain","RSI","RVOL","Vol Exp","SL","TP1","TP2","Lot","Faktor"]
            st.dataframe(render_table(df_k, cols_k), use_container_width=True, height=400)
            st.markdown(f"**{len(df_k)} saham** | Strategi: Entry saat breakout, TP1 dulu, geser SL ke BEP")

    elif "Santai" in gaya:
        st.markdown("#### 😎 Trading Santai — Target 1–4 Minggu")
        st.markdown("*Akumulasi selesai, markup baru dimulai. Entry awal setelah konfirmasi, hold santai*")
        df_s = df[
            (df["Kategori"].isin(["Trading Santai","Speculative"])) |
            (df["Siap Take Off"]==True) |
            (df["Early BUY"]==True)
        ].sort_values("Skor",ascending=False)
        if df_s.empty:
            st.info("Tidak ada setup Trading Santai saat ini.")
        else:
            cols_s = ["Kode","Harga","Skor","Fase","Sinyal","Pemain","RSI","RVOL","Range%","EMA Status","SL","TP1","TP2","TP3","Lot","Faktor"]
            st.dataframe(render_table(df_s, cols_s), use_container_width=True, height=400)
            st.markdown(f"**{len(df_s)} saham** | Strategi: Entry di pullback EMA, TP bertahap, hold sampai distribusi")

    else:
        st.markdown("#### 📈 Swing / Positional — Target 1–3 Bulan")
        st.markdown("*Trend utama kuat, EMA fan sempurna, pemain besar konsisten akumulasi*")
        df_sw = df[
            (df["Fase"]=="MARKUP") &
            (df["EMA Status"].isin(["Fan ↑"])) &
            (df["Pemain"].isin(["ASING","SMART MONEY"])) &
            (df["Skor"]>=55)
        ].sort_values("Skor",ascending=False)
        if df_sw.empty:
            st.info("Tidak ada setup Swing saat ini.")
        else:
            cols_sw = ["Kode","Harga","Skor","Fase","Sinyal","Pemain","RSI","RVOL","Naik 20d%","EMA Status","SL","TP1","TP2","TP3","Lot","Faktor"]
            st.dataframe(render_table(df_sw, cols_sw), use_container_width=True, height=400)
            st.markdown(f"**{len(df_sw)} saham** | Strategi: Average up di setiap pullback, SL trailing, target TP3")

    # Detail saham
    st.markdown("---")
    st.markdown("### 🔎 Detail Saham")
    all_codes = df.sort_values("Skor",ascending=False)["Kode"].tolist()
    sel = st.selectbox("Pilih saham:", all_codes)
    if sel:
        row = df[df["Kode"]==sel].iloc[0]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Harga",  f"Rp{row['Harga']:,}")
        c2.metric("Skor",   f"{row['Skor']}/100")
        c3.metric("Fase",   row['Fase'])
        c4.metric("Sinyal", row['Sinyal'])

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.markdown("**Trade Setup**")
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
            st.markdown("**Risk**")
            st.markdown(f"""
| | |
|--|--|
| Risk % | {risk_pct}% |
| Risk Rp | Rp{row['Risk Rp']:,} |
| Lot | {row['Lot']} Lot |
| Lembar | {row['Lembar']:,} lbr |
            """)
        with col_c:
            st.markdown("**Analisa**")
            st.markdown(f"""
| | |
|--|--|
| Pemain | {row['Pemain']} |
| RSI | {row['RSI']} |
| RVOL | {row['RVOL']:.1f}x |
| Vol Exp | {row['Vol Exp']:.1f}x |
| Range Konsol | {row['Range%']:.1f}% |
| Naik 20h | {row['Naik 20d%']:.1f}% |
| EMA | {row['EMA Status']} |
            """)

        st.markdown(f"**Faktor:** {row['Faktor']}")

        # Mini chart
        try:
            sym = IDX_TICKERS.get(sel, f"{sel}.JK")
            df_c = yf.download(sym, period="3mo", interval="1d", progress=False, auto_adjust=True)
            if not df_c.empty:
                cs = df_c["Close"].squeeze()
                st.line_chart(pd.DataFrame({
                    "Harga": cs,
                    "EMA10": ema(cs,10),
                    "EMA20": ema(cs,20),
                    "EMA30": ema(cs,30),
                }))
        except: pass

# ─── TAB 5: PANDUAN ──────────────────────────
with tab5:
    st.markdown("""
### 📖 Panduan Sistem

#### Skor 0–100
| Range | Sinyal | Aksi |
|-------|--------|------|
| 80–100 | PRIME BUY 🔥 | Entry agresif, volume besar + breakout kuat |
| 65–79 | STRONG BUY | Entry normal, konfirmasi kuat |
| 50–64 | Speculative BUY | Entry kecil dulu, pantau terus |
| 35–49 | Early BUY Signal | Watchlist, belum entry |
| < 35 | WAIT / BEAR | Skip |

#### Komponen Skor
| Faktor | Maks Poin | Keterangan |
|--------|-----------|------------|
| Volume Explosion | 30 | Terpenting — volume meledak setelah sepi |
| Breakout | 20 | Harga keluar dari range sempit |
| EMA | 15 | Golden cross / fan bullish |
| Konsolidasi Sempit | 15 | Range < 15% selama 20 hari |
| RSI | 10 | Zona sehat 40–65, arah naik |
| Pemain | 10 | Asing/Smart Money bonus |
| Penalty naik duluan | -25 | Kalau sudah naik > 40% dalam 20 hari |

#### Fase Wyckoff
- **AKUMULASI** — range sempit, volume sepi, bandar masih kumpul
- **TAKE OFF** — volume meledak + breakout = momen paling bagus!
- **MARKUP** — trend naik, EMA fan, momentum kuat
- **DISTRIBUSI** — harga stagnan di atas, volume besar, siap turun
- **DOWNTREND** — hindari

#### Tips
1. Prioritas utama: Tab "Siap Take Off" setiap pagi sebelum 09:30
2. Saham akumulasi lama tapi belum breakout → pantau di "Early BUY"
3. Jangan entry saham yang sudah naik > 30% dalam 20 hari
4. Konfirmasi dulu di chart TradingView sebelum execute
    """)

# ─── FOOTER ──────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:#64748b;font-size:11px'>"
    f"TM Quantitative Trading System | IDX Long Only | Skor Max 100 | "
    f"Deteksi: Akumulasi → Take Off → Markup | {datetime.now().strftime('%d %b %Y')}"
    f"</div>", unsafe_allow_html=True
)