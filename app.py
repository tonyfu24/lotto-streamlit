# -------------------------
# 匯入需要的套件
# -------------------------
import streamlit as st              # Streamlit：用來做網頁介面
import pandas as pd                 # pandas：讀取與處理 Excel 資料
import random                       # random：隨機選號、幸運值
from collections import Counter     # Counter：統計出現次數
from itertools import combinations  # combinations：計算號碼共現關係

# =====================================================
# 模型預設參數（整個 App 的基準設定）
# =====================================================

DEFAULT_FREQ_WEIGHT = 0.6     # 歷史出現頻率影響程度
DEFAULT_CO_WEIGHT = 0.2       # 號碼共現關係影響程度
DEFAULT_NOISE = 0.3           # 隨機擾動強度（玄學成分）

# 隨機擾動實際使用的範圍
DEFAULT_NOISE_RANGE = (1 - DEFAULT_NOISE, 1 + DEFAULT_NOISE)


# -------------------------
# 設定網頁基本資訊
# -------------------------
st.set_page_config(
    page_title="樂透智慧選號器",
    page_icon="🎯",
    layout="centered"
)

# =====================================================
# 初始化 Session State（只在第一次載入時執行）
# =====================================================

if "freq_w" not in st.session_state:
    st.session_state.freq_w = DEFAULT_FREQ_WEIGHT

if "co_w" not in st.session_state:
    st.session_state.co_w = DEFAULT_CO_WEIGHT

if "noise" not in st.session_state:
    st.session_state.noise = DEFAULT_NOISE

# -------------------------
# 網頁標題與說明
# -------------------------
st.title("🎯 樂透智慧選號器")
st.caption("統計理工 × 天選之人｜理性與命運的交會 🤞")

# =====================================================
# Step 1：選擇樂透種類
# =====================================================
game_type = st.radio(
    "🎮 選擇樂透玩法",
    ["大樂透", "威力彩"],
    horizontal=True
)

# =====================================================
# Step 2：選擇選號模式
# =====================================================
mode = st.radio(
    "🎛️ 選號模式",
    ["統計理工模式 🧠", "天選之人模式 🔮"]
)

# =====================================================
# Step 3：依玩法讀取對應資料
# =====================================================
if game_type == "大樂透":
    # 讀取大樂透歷史資料
    df = pd.read_excel("lotto_big.xlsx")

    # 六個主號欄位名稱
    number_cols = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5", "獎號6"]

    # 主號範圍 1~49
    number_range = range(1, 50)

    # 大樂透沒有第二區
    special_range = None

else:
    # 讀取威力彩歷史資料
    df = pd.read_excel("lotto_power.xlsx")

    # 六個第一區號碼欄位
    number_cols = ["獎號1", "獎號2", "獎號3", "獎號4", "獎號5", "獎號6"]

    # 第一區號碼範圍 1~38
    number_range = range(1, 39)

    # 第二區號碼範圍 1~8
    special_range = range(1, 9)

# 只留下六個主號，方便後續計算
numbers_df = df[number_cols]

# =====================================================
# Step 4：統計歷史出現頻率（只在理工模式使用）
# =====================================================
freq_counter = Counter(numbers_df.values.flatten())  # 每個號碼出現次數
max_freq = max(freq_counter.values())                # 最大出現次數（用來正規化）

# =====================================================
# Step 5：計算號碼共現關係（兩兩一起出現）
# =====================================================
pair_counter = Counter()

for row in numbers_df.values:
    # 每一期的 6 個號碼，取所有兩兩組合
    for a, b in combinations(sorted(row), 2):
        pair_counter[(a, b)] += 1

# 共現次數最大值（避免除以 0）
max_pair = max(pair_counter.values()) if pair_counter else 1

# =====================================================
# Step 6：統計理工模式 → 建立權重
# =====================================================
def build_weights(freq_w, co_w, noise_range):
    """
    建立每個號碼的權重（越大越容易被抽中）
    """
    weights = {}

    for num in number_range:
        # 歷史頻率權重（正規化到 0~1）
        freq_score = freq_counter.get(num, 0) / max_freq

        # 與其他號碼的共現程度
        co_score = sum(
            pair_counter.get((min(num, other), max(num, other)), 0)
            for other in number_range
        ) / max_pair

        # 隨機擾動（玄學來源）
        noise = random.uniform(*noise_range)

        # 最終權重
        raw_weight = (freq_w * freq_score + co_w * co_score)
        weights[num] = max(raw_weight * noise, 1e-6)


    return weights

# =====================================================
# Step 7：依權重產生 6 個不重複號碼
# =====================================================
def generate_weighted_numbers(weights):
    available = list(weights.keys())
    selected = []

    total_weight = sum(weights.values())
    if total_weight <= 0:
        # 極端情況退回純隨機
        return sorted(random.sample(available, 6))

    for _ in range(6):
        chosen = random.choices(
            available,
            weights=[weights[n] for n in available],
            k=1
        )[0]

        selected.append(chosen)
        available.remove(chosen)

    return sorted(selected)


# =====================================================
# Step 9：今日幸運值計算
# =====================================================
def luck_score(selected, weights=None):
    """
    幸運值不是中獎率，而是『模型偏好程度』
    """
    if weights is None:
        # 天選模式：完全隨機
        return random.randint(1, 99)

    # 將號碼依權重排序
    ranked = sorted(weights.items(), key=lambda x: x[1], reverse=True)

    # 取模型最喜歡的前 30%
    top_set = set(num for num, _ in ranked[:int(len(ranked) * 0.3)])

    # 計算選中號碼中，有幾個屬於模型偏好
    score = sum(1 for n in selected if n in top_set) / len(selected) * 100

    # 加一點隨機抖動
    score += random.uniform(-5, 5)

    return int(max(1, min(score, 99)))

# =====================================================
# Step 10：統計理工模式 → 參數滑桿（含小說明）
# =====================================================
if mode == "統計理工模式 🧠":
    st.markdown("### ⚙️ 模型參數設定")

    freq_w = st.slider(
        "📊 歷史頻率權重",
        0.0, 1.0,
        step=0.05,
        key="freq_w",
        help=(
            "📈 控制『歷史常出現號碼』的影響力。\n\n"
            "數值越高，越偏好過去出現次數多的號碼；\n"
            "數值越低，歷史資料影響越小。"
        )
    )

    co_w = st.slider(
        "🔗 共現關係權重",
        0.0, 1.0,
        step=0.05,
        key="co_w",
        help=(
            "🔗 控制『號碼彼此一起出現』的影響力。\n\n"
            "數值越高，越偏好歷史上常一起出現的號碼組合；\n"
            "數值越低，組合關係影響越小。"
        )
    )

    noise = st.slider(
        "🎲 隨機擾動強度",
        0.0, 1.0,
        step=0.05,
        key="noise",
        help=(
            "🎲 控制『隨機性／玄學成分』的強度。\n\n"
            "數值越高，每次結果變化越大；\n"
            "數值越低，選號結果越穩定。"
        )
    )

    # 根據隨機擾動強度，計算實際使用的 noise 範圍
    noise_range = (
        1 - st.session_state.noise,
        1 + st.session_state.noise
    )

    
# if st.button("🔁 恢復官方推薦參數"):
#     st.session_state.freq_w = DEFAULT_FREQ_WEIGHT
#     st.session_state.co_w = DEFAULT_CO_WEIGHT
#     st.session_state.noise = DEFAULT_NOISE

#     st.success("已恢復為官方推薦參數 ✨")

# is_default = (
#     st.session_state.freq_w == DEFAULT_FREQ_WEIGHT and
#     st.session_state.co_w == DEFAULT_CO_WEIGHT and
#     st.session_state.noise == DEFAULT_NOISE
# )

# if is_default:
#     st.info("📌 目前使用：**官方推薦參數**")
# else:
#     st.warning("⚙️ 目前使用：**自訂參數**")


# =====================================================
# Step 11：按鈕 → 產生建議號碼（修正版）
# =====================================================
if st.button("🎰 產生建議號碼"):

    if mode == "統計理工模式 🧠":
        weights = build_weights(
            st.session_state.freq_w,
            st.session_state.co_w,
            (
                1 - st.session_state.noise,
                1 + st.session_state.noise
            )
        )
        main_nums = generate_weighted_numbers(weights)
        luck = luck_score(main_nums, weights)

    else:
        main_nums = generate_random_numbers()
        luck = luck_score(main_nums)

    formatted = "、".join(f"{n:02d}" for n in main_nums)

    st.subheader("🎯 建議號碼")

    if game_type == "威力彩":
        st.success(f"第一區：{formatted}")
    else:
        st.success(formatted)

    if game_type == "威力彩":
        special = random.choice(list(special_range))
        st.info(f"第二區：{special}")

    st.markdown(f"### 🍀 今日幸運值：**{luck}%**")
    st.markdown("### 🎉 祝您中大獎!!")
