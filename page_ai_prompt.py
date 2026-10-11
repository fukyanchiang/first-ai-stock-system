import streamlit as st

def render_prompt_generator():
    st.markdown("<h1 style='color:#deff9a;'>🧠 旗艦指揮官：全局數據 AI 策略生成中心</h1>", unsafe_allow_html=True)
    st.markdown("本艙房能自動搜刮各個房間算好的數據，打包成結構化情報，供大模型（LLM）進行最高戰術策略判定。")

    st.markdown("---")

    # 1. 📡 實時讀取側邊欄全局基本參數
    current_market = st.session_state.get("global_market", "美股陣列")
    current_days = st.session_state.get("global_days", 20)
    current_symbol = st.session_state.get("symbol", "NVDA")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 策略大腦同步中")
    st.sidebar.caption(f"當前快照：{current_market} | {current_symbol}")

    # 2. 🗄️ 從中央大腦 (st.session_state) 安全搜刮所有前線艙房上繳的數據
    # 如果該分頁還沒被點擊運行，則自動顯示「未激活提示」
    all_pages_data = {
        "📊 艙房一：六維王者矩陣 (股票)": st.session_state.get("data_page1", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🔥 艙房二：期權多維雷達 (Options)": st.session_state.get("data_page2", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "📊 艙房 2a：全球市場市寬大面板": st.session_state.get("data_page_2a", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🛡️ 艙房 2b：環球市底大師指揮塔": st.session_state.get("data_page_2b", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🦅 艙房 2c：宏觀恐懼與美債雷達": st.session_state.get("data_page_2c", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "📡 艙房 2bb：個股版塊拔河熱力圖": st.session_state.get("data_page_2bb", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🌊 艙房三：全球宏觀資金流 (Liquidity)": st.session_state.get("data_page3", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🔴 艙房四：機構堡壘情報局 (Bloomberg)": st.session_state.get("data_page4", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。"),
        "🔴 艙房五：機構大鱷持倉 (13F/EPFR)": st.session_state.get("data_page5", "⚠️ 指揮官今日尚未激活此艙房運算，暫無實時數據。")
    }

    # 3. 🎛️ 戰術核心：給大指揮官「自由勾選組合」的多選掣
    st.subheader("🎛️ 第一步：請勾選您目前想發送給 LLM 的情報艙房")
    
    selected_pages = st.multiselect(
        "您可以自由多選、單選，或者全選：",
        options=list(all_pages_data.keys()),
        default=["📊 艙房 2a：全球市場市寬大面板", "📡 艙房 2bb：個股版塊拔河熱力圖"] # 預設幫您勾選這兩個
    )

    st.markdown("---")

    # 4. ⚡ 拼裝與生成總軍令字串
    if st.button("⚡ 一鍵拼裝生成：LLM 頂級量化決策 Prompt", type="primary"):
        if not selected_pages:
            st.warning("⚠️ 大指揮官，您最少要勾選一個艙房的數據，老奴才能幫您拼裝報告啊！")
            return
            
        st.subheader("📋 第二步：請點擊右上角 Copy，直接掟給您的 LLM（如 Claude / GPT）")

        # 基礎 AI 身份設定與限制條件
        final_prompt = f"""
你現在是華爾街頂級對沖基金的【首席量化投資大腦 (Chief Quant Strategist)】。
今天大指揮官為你收集了系統底層的實時量化情報。請你全面審視以下數據，並為我們制定下週的實戰資產配置策略。

=== 🌐 核心基礎參數 ===
- 當前研究資產：{current_symbol}
- 資產所屬市場：{current_market}
- 觀測時間窗口：{current_days} 天

=== 🛰️ 各大艙房實時量化情報匯總 ===
"""
        # 動態拼接大指揮官「有勾選」的房間數據
        for page_name in selected_pages:
            final_prompt += f"\n【{page_name}】\n{all_pages_data[page_name]}\n"
            final_prompt += "----------------------------------------\n"

        # 結尾：逼迫 LLM 做出高水準策略回答的軍令
        final_prompt += """
=== 🎯 首席量化大腦最高決策任務 ===
請根據以上提供的一切跨維度數據（若某些房間顯示未激活，則依據已有數據），進行深度矩陣交叉推演，並嚴格按照以下結構輸出報告：
1. **【市場當前環境定性】**：大盤市寬與資金流到底是健康、還是主力正在暗中撤退？
2. **【目標資產多空判定】**：結合該個股與其板塊的拔河熱力圖，判定該個股目前是強於大盤還是弱於大盤？短期勝率幾多？
3. **【防禦與進攻具體策略】**：給出下週最精確的建倉/加倉/減倉建議，並明確指出止損防線應該設在什麼位置。

請以最專業、冷酷、一針見血的量化總監口吻輸出。請開始你的推演：
"""

        # 顯示在 Streamlit 自帶一鍵複製的代碼框中
        st.code(final_prompt, language="markdown")
        st.success("🏆 跨艙房大戰報拼裝完畢！請點擊上方框框右上角的 『Copy』 即可出征！")

if __name__ == "__main__":
    render_prompt_generator()