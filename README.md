# 🗾 大阪・関西万博 来場者数ダッシュボード

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black.svg)](https://your-streamlit-cloud-url)

公式サイトから最新の来場者数データを取得し、曜日別・日別の入場傾向を可視化するアプリです。

---

## 🔧 機能

- 公式サイトの該当記事を自動収集
- 来場者数とAD証入場者数の推移を折れ線グラフで表示
- 曜日ごとの来場者数を棒グラフ＋曜日平均付きで表示
- ボタン1つでデータの再取得とグラフ更新が可能

---

## 💻 実行方法（ローカル）

### 1. 必要なライブラリをインストール

```bash
pip install -r requirements.txt