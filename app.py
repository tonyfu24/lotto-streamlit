import streamlit as st
import pandas as pd
import random
from itertools import combinations
from collections import Counter

# ===============================
# 基本設定
# ===============================
NUMBER_RANGE = range(1, 50)
SELECT_NUM = 6

st.set_page_config(page_title="大樂透號碼產生器", page_icon="🎯")

# ===============================
# 讀取資料
# ===============================
@st.cache_data
def load_data():
    return pd.read_excel("lotto_history.xlsx")

df = load_data()
numbers_df = df[[f"獎號{i}" for i in range(1, 7)]]

# ===============================
# 預先計算頻率與共現（只算一次）
# ===============================
@st.cache_data
def prepare_stats(numbers_df):
    freq = Counter(numbers_df.values.flatten())
    max_freq = max(freq.values())

    pair_count = Counter()
    for row in numbers_df.values:
        for a, b in combinations(sorted(row), 2):
            pair_count[(a, b)] += 1

    return freq, max_freq, pair_count

freq, max_freq, pair_count = prepare_stats(numbers_df)

# ===============================
# 產生號碼函式
# ===============================
def generate_numbers(freq_weight, co_weight, noise_range):
    weights = {}

    for num in NUMBER_RANGE:
        freq_w = freq.get(num, 0) / max_freq
        co_w = sum(
            pair_count.get(tuple(sorted((num, other))), 0)
            for other in NUMBER_RANGE if other != num
        )
        noise = random.uniform(*noise_range)
        weights[num] = (freq_weight * freq_w + co_weight * co_w) * noise

    total = sum(weights.values())
    probs = [weights[n] / total for n in NUMBER_RANGE]

    return sorted(
        random.choices(
            population=list(NUMBER_RANGE),
            weights=probs,
            k=SELECT_NUM
        )
    )

# ===============================
# UI 介面
# ===============================
st.title("🎯 大樂透建議號碼產生器")

st.markdown("📌 使用歷史資料的 **頻率 + 共現 + 隨機微擾** 模型（非預測）")

st.sidebar.header("⚙️ 參數設定")

freq_weight = st.sidebar.slider(
    "歷史頻率權重",
    0.0, 1.0, 0.6, 0.05
)

co_weight = st.sidebar.slider(
    "號碼共現權重",
    0.0, 1.0, 0.2, 0.05
)

noise_min, noise_max = st.sidebar.slider(
    "隨機擾動範圍",
    0.8, 1.2, (0.9, 1.1), 0.01
)

st.sidebar.markdown("---")
st.sidebar.caption("⚠️ 樂透為隨機機制，本工具僅供娛樂與統計實驗")

# ===============================
# 產生結果
# ===============================
if st.button("🎲 產生建議號碼"):
    nums = generate_numbers(
        freq_weight=freq_weight,
        co_weight=co_weight,
        noise_range=(noise_min, noise_max)
    )

    st.success("🎉 本次建議號碼：")
    st.markdown(
        f"<h2 style='text-align:center'>{'  '.join(map(str, nums))}</h2>",
        unsafe_allow_html=True
    )
