import streamlit as st
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import os
import altair as alt

st.set_page_config(layout="wide")
st.title("大阪・関西万博 来場者数分析")

# 1) フォントフォルダを探す
font_dir = os.path.join(os.getcwd(), ".streamlit", "fonts")
if not os.path.isdir(font_dir):
    st.error(f"フォントフォルダが見つかりません: {font_dir}")

# 2) フォントファイルをすべて登録
for fname in os.listdir(font_dir):
    if fname.lower().endswith(".ttf"):
        font_path = os.path.join(font_dir, fname)
        font_manager.fontManager.addfont(font_path)

# 3) 登録されたフォント一覧からIPAex系を探す
ipa_fonts = [f.name for f in font_manager.fontManager.ttflist if "IPAex" in f.name]
if not ipa_fonts:
    st.error("IPAexフォントが登録されていません。フォント名候補: " +
             ",".join(f.name for f in font_manager.fontManager.ttflist[:5]))
else:
    # 一番目を採用
    selected_font = ipa_fonts[0]
    mpl.rcParams["font.family"] = selected_font
    mpl.rcParams["font.sans-serif"] = selected_font
    st.write(f"→ Matplotlib フォントに設定: {selected_font}")

# ===== データ取得関数 =====
@st.cache_data(show_spinner=False)
def get_visitor_data():
    keyword = "来場者数と入場チケット販売数について"
    search_url = f"https://www.expo2025.or.jp/?s={requests.utils.quote(keyword)}"
    res = requests.get(search_url)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    base_url = "https://www.expo2025.or.jp"
    article_links = []
    for a in soup.find_all("a", href=True):
        if keyword in a.get_text():
            href = a["href"]
            url = href if href.startswith("http") else base_url + href
            article_links.append(url)

    article_links = list(set(article_links))
    data = []

    for url in article_links:
        try:
            res = requests.get(url)
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text, "html.parser")
            table = soup.find("table", class_="has-fixed-layout")
            if not table:
                continue
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue
                date_raw = cols[0].text.strip()
                if "合計" in date_raw:
                    continue
                visitors = int(cols[1].text.strip().replace(",", ""))
                ad = int(cols[3].text.strip().replace(",", ""))
                m = re.search(r"(\d{1,2})月(\d{1,2})日", date_raw)
                if not m:
                    continue
                month, day = m.groups()
                date = f"2025-{int(month):02}-{int(day):02}"
                data.append([date, visitors, ad])
        except Exception as e:
            st.error(f"{url} 読込失敗: {e}")
    df = pd.DataFrame(data, columns=["日付", "来場者数", "AD証入場者数"])
    df = pd.DataFrame(data, columns=["日付", "来場者数", "AD証入場者数"])
    df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
    df = df.dropna(subset=["日付"])  # ← この行を追加
    df.sort_values("日付", inplace=True)
    return df

# ===== ボタン付きUI =====
if st.button("🔄 データを更新して再表示"):
    with st.spinner("公式サイトから最新データ取得中..."):
        df = get_visitor_data()
        st.success("✅ データ更新完了")
else:
    df = get_visitor_data()

# ===== 前処理 =====
df["曜日番号"] = df["日付"].dt.weekday
weekday_map = {0:"月",1:"火",2:"水",3:"木",4:"金",5:"土",6:"日"}
df["曜日"] = df["曜日番号"].map(weekday_map)
df["週"] = df["日付"].dt.to_period("W-SUN").apply(lambda r: r.start_time)

# ===== ピボット =====
pivot_df = df.pivot(index="曜日", columns="週", values="来場者数")

# ===== グラフ表示 =====
fig, axs = plt.subplots(1, 2, figsize=(16, 6))

# --- 折れ線（左） ---
axs[0].plot(df["日付"], df["来場者数"], marker='o', label="来場者数")
axs[0].plot(df["日付"], df["AD証入場者数"], marker='s', label="AD証入場者数")
sundays = pd.date_range(start=df["日付"].min(), end=df["日付"].max(), freq='W-SUN')
for date in sundays:
    axs[0].axvline(x=date, color='gray', linestyle='--', alpha=0.5)
axs[0].set_xticks(sundays)
axs[0].set_xticklabels([d.strftime('%m/%d') for d in sundays], rotation=45)
axs[0].set_title("日別の来場者数推移（週区切り：日曜日）")
axs[0].set_xlabel("日付（日曜日のみ表示）")
axs[0].set_ylabel("人数")
axs[0].legend()
axs[0].grid(False)

# --- 棒グラフ（右） ---
pivot_df.plot(kind="bar", ax=axs[1])
axs[1].set_title("曜日ごとの来場者数（週別）＋曜日平均")
axs[1].set_xlabel("曜日")
axs[1].set_ylabel("人数")
axs[1].legend(title="週の開始日", fontsize=8)

# 曜日平均の線
for i, day in enumerate(pivot_df.index):
    values = pivot_df.iloc[i].dropna()
    if len(values) == 0:
        continue
    avg = values.mean()
    axs[1].hlines(y=avg, xmin=i - 0.4, xmax=i + 0.4, colors='red', linestyles='dashed', alpha=0.8)
    axs[1].text(i + 0.45, avg, f"{avg/10000:.1f}万", color='red', fontsize=9, va='center')

st.pyplot(fig)