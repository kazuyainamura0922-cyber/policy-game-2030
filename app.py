import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.dates as mdates

# --- フォント設定 ---
import platform
if platform.system() == 'Windows':
    # あなたのPC（Windows）用
    plt.rcParams['font.family'] = 'MS Gothic'
else:
    # クラウド（Linux）用
    import japanize_matplotlib
    # importするだけで自動的に日本語化されます

# --- ページ設定 ---
st.set_page_config(page_title="2030年 観光政策シミュレーター", layout="wide")

# --- タイトル ---
st.title("🇯🇵 2030年 観光政策シミュレーション・ゲーム")
st.markdown("""
**【現在の時刻：2025年12月】**
あなたは日本の政策決定者です。
現在、観光客の急増により**2030年に労働崩壊**が予測されています。
「今すぐ」決断すれば間に合うのか？それとも手遅れか？
スライダーを動かして、**「総量規制＆高付加価値化」**の実行タイミングを決めてください！
""")

# --- サイドバー ---
st.sidebar.header("🎮 政策実行パネル")

dates = pd.date_range(start='2025-01-01', end='2030-12-31', freq='M')
date_labels = [d.strftime('%Y年%m月') for d in dates]

# デフォルト値を「現在（2025年12月）」に設定
default_index = 11

trigger_idx = st.sidebar.select_slider(
    "いつ、改革を実行しますか？",
    options=range(len(dates)),
    value=default_index, 
    format_func=lambda x: date_labels[x]
)

trigger_date = dates[trigger_idx]
st.sidebar.markdown(f"### 決断日: **{trigger_date.strftime('%Y年%m月')}**")

st.sidebar.divider()

# ★減税オプション★
st.sidebar.markdown("### 💰 追加政策オプション")
use_tax_cut = st.sidebar.checkbox("賃上げ・DX投資減税を行う", value=False)

if use_tax_cut:
    st.sidebar.info("🔥 **減税効果発動！**\n企業の設備投資が加速し、生産性がさらに向上します。")

# --- シミュレーション・パラメータ ---
base_visitors = 4300 / 12
base_spend = 21.0
base_gdp = base_visitors * base_spend
base_workers = 100

# シナリオA：放置 (崩壊ルート)
r_vis_a = (1 + 0.10) ** (1/12) - 1 
r_spd_a = (1 + 0.01) ** (1/12) - 1 
r_prod_a = (1 + 0.005) ** (1/12) - 1 

# シナリオB：改革 (生存ルート)
prod_growth_base = 0.12 
if use_tax_cut:
    prod_growth_base = 0.15 

r_vis_b = (1 - 0.05) ** (1/12) - 1 
r_spd_b = (1 + 0.13) ** (1/12) - 1 
r_prod_b = (1 + prod_growth_base) ** (1/12) - 1 

# 労働供給限界 (-1.1%/年)
labor_supply_rate = (1 - 0.011) ** (1/12) - 1
labor_supply = [100 * (1 + labor_supply_rate) ** m for m in range(len(dates))]

# 計算ループ
vis_list, rev_list, lab_list = [], [], []
curr_vis = base_visitors
curr_spd = base_spend
curr_prod = 1.0

for i in range(len(dates)):
    if i < trigger_idx: # 実行前
        curr_vis *= (1 + r_vis_a)
        curr_spd *= (1 + r_spd_a)
        curr_prod *= (1 + r_prod_a)
    else: # 実行後
        curr_vis *= (1 + r_vis_b)
        curr_spd *= (1 + r_spd_b)
        curr_prod *= (1 + r_prod_b)
    
    vis_list.append(curr_vis)
    rev_list.append(curr_vis * curr_spd)
    lab_list.append(((curr_vis * curr_spd) / base_gdp) / curr_prod * 100)

# 判定
final_labor_demand = lab_list[-1]
final_labor_supply = labor_supply[-1]
gap = final_labor_demand - final_labor_supply

# --- 表示 ---
if trigger_idx == len(dates)-1:
    st.sidebar.error("⚠️ 政策未実行（現状維持）")
elif gap > 0:
    st.sidebar.error("🚨 手遅れです...")
else:
    st.sidebar.success("✅ 改革成功！")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("2030年の訪日客数", f"{int(vis_list[-1]*12):,} 万人")
with col2:
    st.metric("2030年の観光消費", f"{int(rev_list[-1]*12/10000):,} 兆円")
with col3:
    if gap > 0:
        st.error(f"💀 労働崩壊 (不足: {gap:.1f}pt)")
    else:
        st.success(f"🎉 持続可能 (余裕: {abs(gap):.1f}pt)")

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
plt.subplots_adjust(wspace=0.3)

for ax in [ax1, ax2, ax3]:
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%y年'))
    ax.grid(True, linestyle='--', alpha=0.5)
    if trigger_idx < len(dates)-1:
        ax.axvline(trigger_date, color='orange', linestyle='--', linewidth=2, label='政策実行')

ax1.plot(dates, vis_list, color='#0077b6', linewidth=3)
ax1.set_title('① 月間訪日客数 (万人)', fontsize=14, fontweight='bold')
ax1.set_ylabel('万人')

ax2.plot(dates, rev_list, color='#e85d04', linewidth=3)
ax2.set_title('② 月間観光消費 (億円)', fontsize=14, fontweight='bold')
ax2.set_ylabel('億円')

# ★ここが修正箇所です！カッコを閉じました★
ax3.plot(dates, lab_list, label='必要労働力', color='red' if gap > 0 else 'green', linewidth=4)
ax3.plot(dates, labor_supply, label='供給限界', color='black', linestyle='-.', linewidth=2)
ax3.fill_between(
    dates, 
    labor_supply, 
    lab_list, 
    where=(np.array(lab_list) > np.array(labor_supply)), 
    color='red', 
    alpha=0.3
)
ax3.set_title('③ 労働需給バランス (2025=100)', fontsize=14, fontweight='bold')
ax3.legend()

st.pyplot(fig)

st.divider()
if gap > 0:
    st.markdown("### 🚨 Bad End: 手遅れでした...")
    st.write(f"残念ながら、**{trigger_date.strftime('%Y年%m月')}** の決断では間に合いませんでした。人手不足が深刻化し、現場は限界を超えてしまいました。")
else:
    st.markdown("### 🏆 Good End: 未来を変えました！")
    if use_tax_cut:
        st.write(f"素晴らしい！早期の決断に加え、**「投資減税」**を行ったことで、生産性が劇的に向上しました。労働力に十分な余裕（{abs(gap):.1f}pt）が生まれ、理想的な「高付加価値観光」が実現しています！")
    else:
        st.write(f"お見事です！ **{trigger_date.strftime('%Y年%m月')}** に決断したことで、ギリギリ破綻を回避しました。ただ、余裕はあまりありません。さらに盤石にするには「減税」も検討すべきかもしれません。")
    
    if 'balloons_shown' not in st.session_state:
        st.session_state['balloons_shown'] = -1
    if st.session_state['balloons_shown'] != trigger_idx:
        st.balloons()
        st.session_state['balloons_shown'] = trigger_idx