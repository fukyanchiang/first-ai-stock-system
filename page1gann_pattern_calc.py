"""
Filename: page1gann_pattern_calc.py
Description: 📐 經典形態與諧波幾何智能預測雷達
升級亮點：
  1. 引入 Scott Carney 體系「🚫 PRZ 結構失效止損紅線 (Invalidation Line)」
  2. 實時盈虧比 (R:R Ratio) 量化評級 (⭐⭐⭐優 / ⭐⭐良 / ⚠️偏低降級)
  3. 主力擊穿失效紅字警報 (⚠️ 形態已被主力擊穿無效，嚴禁左側交易！)
  4. 主圖紅色細虛線繪製結構失效線，右側雙欄智能階梯避讓
  5. 戰術看板 HUD 左上角等寬純淨 span 排版，根除代碼洩漏
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _calc_rr_and_invalidation(entry, target, invalidation, direction="看漲", is_invalidated=False):
    """計算實時盈虧比 (R:R) 與狀態評級"""
    risk = abs(entry - invalidation)
    reward = abs(target - entry)
    rr = reward / risk if risk > 0 else 0

    if is_invalidated:
        return {
            'invalidation': invalidation,
            'is_invalidated': True,
            'rr': rr,
            'rr_str': '無效',
            'rr_badge': "<span style='color:#ef4444; background:#450a0a; border:1px solid #ef4444; padding:1px 4px; border-radius:3px;'><b>⚠️ 已擊穿無效</b></span>"
        }

    if rr >= 3.0:
        badge = f"<span style='color:#facc15;'><b>1:{rr:.1f}</b></span> <span style='color:#fef08a; font-size:9px;'>(⭐⭐⭐優)</span>"
    elif rr >= 2.0:
        badge = f"<span style='color:#4ade80;'><b>1:{rr:.1f}</b></span> <span style='color:#86efac; font-size:9px;'>(⭐⭐良)</span>"
    else:
        badge = f"<span style='color:#94a3b8;'><b>1:{rr:.1f}</b></span> <span style='color:#cbd5e1; font-size:9px;'>⚠️偏低(<1:2)</span>"

    return {
        'invalidation': invalidation,
        'is_invalidated': False,
        'rr': rr,
        'rr_str': f"1:{rr:.1f}",
        'rr_badge': badge
    }


def detect_chart_patterns(df: pd.DataFrame):
    """
    掃描 K 線數據中的技術形態與諧波預測形態，包含結構失效止損線與實時盈虧比量化
    """
    if df is None or len(df) < 15:
        return None

    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    dates = df.index
    n = len(df)
    last_close = float(closes[-1])
    last_date_str = pd.to_datetime(dates[-1]).strftime("%m-%d")

    # 1. 局部高低轉折點 (Swing Pivots)
    window = 3
    raw_pivots = []
    for i in range(window, n - window):
        if highs[i] == max(highs[i - window:i + window + 1]):
            raw_pivots.append(('H', i, dates[i], float(highs[i])))
        if lows[i] == min(lows[i - window:i + window + 1]):
            raw_pivots.append(('L', i, dates[i], float(lows[i])))

    # Zigzag 交替波折過濾
    pivots = []
    for p in raw_pivots:
        if not pivots:
            pivots.append(p)
        else:
            if p[0] == pivots[-1][0]:
                if p[0] == 'H' and p[3] > pivots[-1][3]:
                    pivots[-1] = p
                elif p[0] == 'L' and p[3] < pivots[-1][3]:
                    pivots[-1] = p
            else:
                pivots.append(p)

    h_pivots = [p for p in pivots if p[0] == 'H']
    l_pivots = [p for p in pivots if p[0] == 'L']

    pattern_data = {
        'last_date_str': last_date_str,
        'last_close': last_close,
        'pivots': pivots,
        'double_top': None,
        'double_bottom': None,
        'head_shoulders': None,
        'triangle': None,
        'butterfly': None,
        'abcd': None,
        'vcp': None,
        'right_badges': [],
        'invalidation_lines': []
    }

    # ==========================================
    # A. 雙頂 (Double Top)
    # ==========================================
    if len(h_pivots) >= 2:
        for idx in range(len(h_pivots) - 1, 0, -1):
            p2 = h_pivots[idx]
            p1 = h_pivots[idx - 1]
            inter_l = [l for l in l_pivots if p1[1] < l[1] < p2[1]]
            if inter_l:
                trough = min(inter_l, key=lambda x: x[3])
                diff_ratio = abs(p1[3] - p2[3]) / max(p1[3], p2[3])
                depth = (min(p1[3], p2[3]) - trough[3]) / min(p1[3], p2[3])
                if diff_ratio <= 0.08 and depth >= 0.04:
                    nl = trough[3]
                    avg_p = (p1[3] + p2[3]) / 2.0
                    target = nl - (avg_p - nl)
                    h1_amp = p1[3] - nl
                    h2_amp = p2[3] - nl
                    sym = (min(h1_amp, h2_amp) / max(h1_amp, h2_amp)) * 100.0 if max(h1_amp, h2_amp) > 0 else 100.0

                    # 🎯 結構失效線：頂部峰值 + 緩衝 (收盤突破此線則空頭形態完全失效)
                    inval_price = max(p1[3], p2[3]) * 1.008
                    is_inval = last_close > inval_price
                    entry_p = last_close if last_close < nl else nl
                    rr_info = _calc_rr_and_invalidation(entry_p, target, inval_price, direction="看跌", is_invalidated=is_inval)

                    status = "已確認跌破" if last_close < nl else "形成中"
                    pattern_data['double_top'] = {
                        'name': '雙頂',
                        'status': status,
                        'top_str': f"{p1[3]:.2f}/{p2[3]:.2f}",
                        'p1': p1, 'p2': p2, 'trough': trough,
                        'nl': nl,
                        'target': target,
                        'symmetry': sym,
                        'invalidation': inval_price,
                        'is_invalidated': is_inval,
                        'rr_info': rr_info
                    }
                    if target > 0:
                        pattern_data['right_badges'].append({'label': f"目標 {target:.2f}", 'price': target, 'bg': '#00b0ff', 'text_col': '#ffffff'})
                    pattern_data['right_badges'].append({'label': f"頸線 {nl:.2f}", 'price': nl, 'bg': '#ffd700', 'text_col': '#000000'})
                    break

    # ==========================================
    # B. 雙底 (Double Bottom)
    # ==========================================
    if len(l_pivots) >= 2:
        for idx in range(len(l_pivots) - 1, 0, -1):
            l2 = l_pivots[idx]
            l1 = l_pivots[idx - 1]
            inter_h = [h for h in h_pivots if l1[1] < h[1] < l2[1]]
            if inter_h:
                peak = max(inter_h, key=lambda x: x[3])
                diff_ratio = abs(l1[3] - l2[3]) / min(l1[3], l2[3])
                height = (peak[3] - max(l1[3], l2[3])) / max(l1[3], l2[3])
                if diff_ratio <= 0.08 and height >= 0.04:
                    nl = peak[3]
                    avg_l = (l1[3] + l2[3]) / 2.0
                    target = nl + (nl - avg_l)
                    l1_amp = nl - l1[3]
                    l2_amp = nl - l2[3]
                    sym = (min(l1_amp, l2_amp) / max(l1_amp, l2_amp)) * 100.0 if max(l1_amp, l2_amp) > 0 else 100.0

                    # 🎯 結構失效線：底部谷值 - 緩衝 (收盤跌破此線則多頭形態完全失效)
                    inval_price = min(l1[3], l2[3]) * 0.992
                    is_inval = last_close < inval_price
                    entry_p = last_close if last_close > nl else nl
                    rr_info = _calc_rr_and_invalidation(entry_p, target, inval_price, direction="看漲", is_invalidated=is_inval)

                    status = "已確認突破" if last_close > nl else "形成中"
                    pattern_data['double_bottom'] = {
                        'name': '雙底',
                        'status': status,
                        'bot_str': f"{l1[3]:.2f}/{l2[3]:.2f}",
                        'l1': l1, 'l2': l2, 'peak': peak,
                        'nl': nl,
                        'target': target,
                        'symmetry': sym,
                        'invalidation': inval_price,
                        'is_invalidated': is_inval,
                        'rr_info': rr_info
                    }
                    pattern_data['right_badges'].append({'label': f"目標 {target:.2f}", 'price': target, 'bg': '#00b0ff', 'text_col': '#ffffff'})
                    pattern_data['right_badges'].append({'label': f"頸線 {nl:.2f}", 'price': nl, 'bg': '#ffd700', 'text_col': '#000000'})
                    break

    # ==========================================
    # C. 下降三角形 (Descending Triangle)
    # ==========================================
    if len(h_pivots) >= 2 and len(l_pivots) >= 2:
        for i in range(len(h_pivots) - 1, 0, -1):
            h2 = h_pivots[i]
            h1 = h_pivots[i - 1]
            if h1[3] > h2[3]:
                rel_lows = [l for l in l_pivots if h1[1] <= l[1] <= min(n - 1, h2[1] + 25)]
                if len(rel_lows) >= 2:
                    l1, l2 = rel_lows[0], rel_lows[1]
                    if abs(l1[3] - l2[3]) / min(l1[3], l2[3]) <= 0.045:
                        nl = min(l1[3], l2[3])
                        slope = (h2[3] - h1[3]) / max(1, (h2[1] - h1[1]))

                        breakout_found = False
                        bo_bar, bo_date, bo_price = None, None, None
                        for b_idx in range(h2[1], n):
                            line_val = h1[3] + slope * (b_idx - h1[1])
                            if closes[b_idx] > line_val and not breakout_found:
                                breakout_found = True
                                bo_bar = b_idx
                                bo_date = dates[b_idx]
                                bo_price = float(line_val)
                                break

                        tri_height = h1[3] - nl
                        bo_display = bo_price if breakout_found else float(h1[3] + slope * (n - 1 - h1[1]))
                        target = (bo_price if breakout_found else h2[3]) + tri_height
                        status = "已確認突破" if breakout_found else "形成中"
                        direction = "向上" if breakout_found or last_close >= nl else "向下"

                        # 🎯 結構失效線：若已向上突破，收盤重新跌破頸線 NL 則判定假突破失效
                        inval_price = nl * 0.992
                        is_inval = breakout_found and (last_close < nl)
                        entry_p = bo_display if breakout_found else h2[3]
                        rr_info = _calc_rr_and_invalidation(entry_p, target, inval_price, direction="看漲", is_invalidated=is_inval)

                        pattern_data['triangle'] = {
                            'type': '下降三角形',
                            'status': status,
                            'direction': direction,
                            'h1': h1, 'h2': h2, 'l1': l1, 'l2': l2,
                            'nl': nl,
                            'slope': slope,
                            'breakout_found': breakout_found,
                            'bo_bar': bo_bar,
                            'bo_date': bo_date,
                            'bo_price': bo_display,
                            'target': target,
                            'invalidation': inval_price,
                            'is_invalidated': is_inval,
                            'rr_info': rr_info
                        }
                        pattern_data['right_badges'].append({'label': f"目標 {target:.2f}", 'price': target, 'bg': '#00e5ff', 'text_col': '#000000'})
                        pattern_data['right_badges'].append({'label': f"突破位 {bo_display:.2f}", 'price': bo_display, 'bg': '#ff9800', 'text_col': '#000000'})
                        pattern_data['right_badges'].append({'label': f"頸線 {nl:.2f}", 'price': nl, 'bg': '#ffd700', 'text_col': '#000000'})
                        break

    # ==========================================
    # D. 蝴蝶形態 (Butterfly Pattern - 諧波預測)
    # ==========================================
    if len(pivots) >= 4:
        for i in range(len(pivots) - 4, -1, -1):
            px, pa, pb, pc = pivots[i:i + 4]

            # 看漲蝴蝶 (Bullish)
            if px[0] == 'L' and pa[0] == 'H' and pb[0] == 'L' and pc[0] == 'H':
                xa = pa[3] - px[3]
                if xa > 0:
                    b_retr = (pa[3] - pb[3]) / xa
                    if 0.65 <= b_retr <= 0.88:
                        ab = pa[3] - pb[3]
                        c_retr = (pc[3] - pb[3]) / ab if ab > 0 else 0
                        if 0.30 <= c_retr <= 1.0 and pc[3] < pa[3]:
                            d_price = pa[3] - 1.272 * xa
                            prz_min = pa[3] - 1.414 * xa
                            prz_max = pa[3] - 1.272 * xa
                            fwd_bars = max(3, pb[1] - pa[1])
                            pred_d_date = pd.to_datetime(pc[2]) + pd.to_timedelta(fwd_bars * 1.5, unit='D')

                            # 🎯 Scott Carney 蝴蝶結構失效點：1.618 XA 延伸極限
                            inval_price = pa[3] - 1.618 * xa
                            is_inval = last_close < inval_price
                            target_p = pb[3]  # 經典目標：回抽 Point B
                            entry_p = last_close if (prz_min * 0.98 <= last_close <= prz_max * 1.02) else d_price
                            rr_info = _calc_rr_and_invalidation(entry_p, target_p, inval_price, direction="看漲", is_invalidated=is_inval)

                            status = "已抵達 PRZ 反轉" if (last_close <= prz_max * 1.02 and last_close >= prz_min * 0.98) else ("⚠️ 已擊穿失效" if is_inval else "預測 D 形成中")

                            pattern_data['butterfly'] = {
                                'type': '看漲蝴蝶',
                                'direction': '看漲',
                                'status': status,
                                'x': px, 'a': pa, 'b': pb, 'c': pc,
                                'd_price': d_price,
                                'd_date': pred_d_date,
                                'prz_str': f"{prz_min:.2f}–{prz_max:.2f}",
                                'invalidation': inval_price,
                                'target': target_p,
                                'is_invalidated': is_inval,
                                'rr_info': rr_info
                            }
                            pattern_data['right_badges'].append({'label': f"蝴蝶 D {d_price:.2f}", 'price': d_price, 'bg': '#e040fb', 'text_col': '#ffffff'})
                            pattern_data['right_badges'].append({'label': f"🚫失效 {inval_price:.2f}", 'price': inval_price, 'bg': '#7f1d1d', 'text_col': '#fca5a5'})
                            pattern_data['invalidation_lines'].append({'name': '蝴蝶結構失效線', 'price': inval_price, 'date_start': pc[2], 'date_end': pred_d_date})
                            break

            # 看跌蝴蝶 (Bearish)
            elif px[0] == 'H' and pa[0] == 'L' and pb[0] == 'H' and pc[0] == 'L':
                xa = px[3] - pa[3]
                if xa > 0:
                    b_retr = (pb[3] - pa[3]) / xa
                    if 0.65 <= b_retr <= 0.88:
                        ab = pb[3] - pa[3]
                        c_retr = (pb[3] - pc[3]) / ab if ab > 0 else 0
                        if 0.30 <= c_retr <= 1.0 and pc[3] > pa[3]:
                            d_price = pa[3] + 1.272 * xa
                            prz_min = pa[3] + 1.272 * xa
                            prz_max = pa[3] + 1.414 * xa
                            fwd_bars = max(3, pb[1] - pa[1])
                            pred_d_date = pd.to_datetime(pc[2]) + pd.to_timedelta(fwd_bars * 1.5, unit='D')

                            # 🎯 Scott Carney 蝴蝶結構失效點：1.618 XA 延伸極限
                            inval_price = pa[3] + 1.618 * xa
                            is_inval = last_close > inval_price
                            target_p = pb[3]  # 經典目標：回抽 Point B
                            entry_p = last_close if (prz_min * 0.98 <= last_close <= prz_max * 1.02) else d_price
                            rr_info = _calc_rr_and_invalidation(entry_p, target_p, inval_price, direction="看跌", is_invalidated=is_inval)

                            status = "已抵達 PRZ 反轉" if (last_close >= prz_min * 0.98 and last_close <= prz_max * 1.02) else ("⚠️ 已擊穿失效" if is_inval else "預測 D 形成中")

                            pattern_data['butterfly'] = {
                                'type': '看跌蝴蝶',
                                'direction': '看跌',
                                'status': status,
                                'x': px, 'a': pa, 'b': pb, 'c': pc,
                                'd_price': d_price,
                                'd_date': pred_d_date,
                                'prz_str': f"{prz_min:.2f}–{prz_max:.2f}",
                                'invalidation': inval_price,
                                'target': target_p,
                                'is_invalidated': is_inval,
                                'rr_info': rr_info
                            }
                            pattern_data['right_badges'].append({'label': f"蝴蝶 D {d_price:.2f}", 'price': d_price, 'bg': '#e040fb', 'text_col': '#ffffff'})
                            pattern_data['right_badges'].append({'label': f"🚫失效 {inval_price:.2f}", 'price': inval_price, 'bg': '#7f1d1d', 'text_col': '#fca5a5'})
                            pattern_data['invalidation_lines'].append({'name': '蝴蝶結構失效線', 'price': inval_price, 'date_start': pc[2], 'date_end': pred_d_date})
                            break

    # ==========================================
    # E. AB=CD 形態 (等長預測)
    # ==========================================
    if len(pivots) >= 3:
        for i in range(len(pivots) - 3, -1, -1):
            pa, pb, pc = pivots[i:i + 3]

            if pa[0] == 'H' and pb[0] == 'L' and pc[0] == 'H':
                ab_len = pa[3] - pb[3]
                bc_len = pc[3] - pb[3]
                if ab_len > 0 and 0.35 <= (bc_len / ab_len) <= 0.88 and pc[3] < pa[3]:
                    d_price = pc[3] - ab_len
                    fwd_bars = max(3, pb[1] - pa[1])
                    pred_d_date = pd.to_datetime(pc[2]) + pd.to_timedelta(fwd_bars * 1.5, unit='D')

                    # 🎯 結構失效線：1.382 AB 延伸
                    inval_price = d_price - 0.382 * ab_len
                    is_inval = last_close < inval_price
                    target_p = pc[3]
                    entry_p = last_close if abs(last_close - d_price) / d_price <= 0.02 else d_price
                    rr_info = _calc_rr_and_invalidation(entry_p, target_p, inval_price, direction="看漲", is_invalidated=is_inval)

                    status = "已抵達 D 點" if abs(last_close - d_price) / d_price <= 0.02 else ("⚠️ 已擊穿失效" if is_inval else "預測 D 形成中")

                    pattern_data['abcd'] = {
                        'type': '看漲 AB=CD',
                        'direction': '看漲',
                        'status': status,
                        'a': pa, 'b': pb, 'c': pc,
                        'd_price': d_price,
                        'd_date': pred_d_date,
                        'prz_str': f"等長 {d_price:.2f}",
                        'invalidation': inval_price,
                        'target': target_p,
                        'is_invalidated': is_inval,
                        'rr_info': rr_info
                    }
                    pattern_data['right_badges'].append({'label': f"ABCD D {d_price:.2f}", 'price': d_price, 'bg': '#00e5ff', 'text_col': '#000000'})
                    pattern_data['right_badges'].append({'label': f"🚫失效 {inval_price:.2f}", 'price': inval_price, 'bg': '#7f1d1d', 'text_col': '#fca5a5'})
                    pattern_data['invalidation_lines'].append({'name': 'ABCD結構失效線', 'price': inval_price, 'date_start': pc[2], 'date_end': pred_d_date})
                    break

            elif pa[0] == 'L' and pb[0] == 'H' and pc[0] == 'L':
                ab_len = pb[3] - pa[3]
                bc_len = pb[3] - pc[3]
                if ab_len > 0 and 0.35 <= (bc_len / ab_len) <= 0.88 and pc[3] > pa[3]:
                    d_price = pc[3] + ab_len
                    fwd_bars = max(3, pb[1] - pa[1])
                    pred_d_date = pd.to_datetime(pc[2]) + pd.to_timedelta(fwd_bars * 1.5, unit='D')

                    # 🎯 結構失效線：1.382 AB 延伸
                    inval_price = d_price + 0.382 * ab_len
                    is_inval = last_close > inval_price
                    target_p = pc[3]
                    entry_p = last_close if abs(last_close - d_price) / d_price <= 0.02 else d_price
                    rr_info = _calc_rr_and_invalidation(entry_p, target_p, inval_price, direction="看跌", is_invalidated=is_inval)

                    status = "已抵達 D 點" if abs(last_close - d_price) / d_price <= 0.02 else ("⚠️ 已擊穿失效" if is_inval else "預測 D 形成中")

                    pattern_data['abcd'] = {
                        'type': '看跌 AB=CD',
                        'direction': '看跌',
                        'status': status,
                        'a': pa, 'b': pb, 'c': pc,
                        'd_price': d_price,
                        'd_date': pred_d_date,
                        'prz_str': f"等長 {d_price:.2f}",
                        'invalidation': inval_price,
                        'target': target_p,
                        'is_invalidated': is_inval,
                        'rr_info': rr_info
                    }
                    pattern_data['right_badges'].append({'label': f"ABCD D {d_price:.2f}", 'price': d_price, 'bg': '#00e5ff', 'text_col': '#000000'})
                    pattern_data['right_badges'].append({'label': f"🚫失效 {inval_price:.2f}", 'price': inval_price, 'bg': '#7f1d1d', 'text_col': '#fca5a5'})
                    pattern_data['invalidation_lines'].append({'name': 'ABCD結構失效線', 'price': inval_price, 'date_start': pc[2], 'date_end': pred_d_date})
                    break

    # ==========================================
    # F. 頭肩頂 / 底
    # ==========================================
    if len(h_pivots) >= 3:
        p3, p2, p1 = h_pivots[-1], h_pivots[-2], h_pivots[-3]
        if p2[3] > p1[3] and p2[3] > p3[3] and abs(p1[3] - p3[3]) / p1[3] <= 0.08:
            inter_l = [l for l in l_pivots if p1[1] < l[1] < p3[1]]
            if len(inter_l) >= 2:
                nl = (inter_l[0][3] + inter_l[1][3]) / 2.0
                target = nl - (p2[3] - nl)
                inval_price = p2[3] * 1.008
                is_inval = last_close > inval_price
                pattern_data['head_shoulders'] = {
                    'type': '頭肩頂',
                    'status': '已確認跌破' if last_close < nl else '形成中',
                    'nl': nl,
                    'target': target,
                    'invalidation': inval_price,
                    'is_invalidated': is_inval
                }

    return pattern_data


def render_pattern_traces_and_hud(fig: go.Figure, pattern_data: dict):
    """
    在主圖渲染紫線、紅線、蝴蝶7線、ABCD 3線、結構失效線、智能避讓氣泡與純淨左置 HUD 看板
    """
    if not pattern_data:
        return

    # 1. 紅線 (Zigzag 轉折軌跡路徑)
    pivots = pattern_data.get('pivots', [])
    if len(pivots) >= 3:
        sub_pivots = pivots[-8:]
        red_x = [p[2] for p in sub_pivots]
        red_y = [p[3] for p in sub_pivots]
        fig.add_trace(go.Scatter(
            x=red_x,
            y=red_y,
            mode='lines',
            line=dict(color='#ff3366', width=2.0),
            name='波折軌跡 (紅線)',
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

    # 2. 下降三角形：紫線與主圖徽章
    tri = pattern_data.get('triangle')
    if tri:
        h1 = tri['h1']
        h2 = tri['h2']
        nl = tri['nl']
        slope = tri['slope']

        ext_len = 18
        x1_date = h1[2]
        x2_date = pd.to_datetime(h2[2]) + pd.to_timedelta(ext_len * 1.5, unit='D')
        y2_val = h1[3] + slope * (h2[1] - h1[1] + ext_len)

        fig.add_trace(go.Scatter(
            x=[x1_date, x2_date],
            y=[h1[3], y2_val],
            mode='lines',
            line=dict(color='#ab47bc', width=2.0),
            name='下降壓制線 (紫線)',
            hoverinfo='skip',
            showlegend=False
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=[h1[2], x2_date],
            y=[nl, nl],
            mode='lines',
            line=dict(color='#ab47bc', width=2.0),
            name='水平頸線 (紫線)',
            hoverinfo='skip',
            showlegend=False
        ), row=1, col=1)

        fig.add_annotation(
            x=h1[2], y=h1[3],
            text=f"<b>下降三角形<br>{h1[3]:.2f}</b>",
            bgcolor="#1e1035",
            bordercolor="#ab47bc",
            borderwidth=1.5,
            borderpad=4,
            font=dict(color="#ffffff", size=10, family="monospace"),
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ab47bc",
            ay=-36,
            row=1, col=1
        )

        fig.add_annotation(
            x=tri['l1'][2], y=nl,
            text=f"<b>NL<br>{nl:.2f}</b>",
            bgcolor="#2a1d00",
            bordercolor="#ffd700",
            borderwidth=1.5,
            borderpad=4,
            font=dict(color="#ffd700", size=10, family="monospace"),
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ffd700",
            ay=36,
            row=1, col=1
        )

        if tri['breakout_found'] and tri['bo_date']:
            fig.add_annotation(
                x=tri['bo_date'], y=tri['bo_price'],
                text="<b>確認突破</b>",
                bgcolor="#0a2e1d",
                bordercolor="#00e676",
                borderwidth=1.5,
                borderpad=4,
                font=dict(color="#00e676", size=10, family="Arial Black"),
                showarrow=False,
                row=1, col=1
            )

    # 3. 蝴蝶形態（Butterfly Pattern）7 條線幾何
    bf = pattern_data.get('butterfly')
    if bf:
        x_pt, a_pt, b_pt, c_pt = bf['x'], bf['a'], bf['b'], bf['c']
        d_p = bf['d_price']
        d_d = bf['d_date']

        wing_color = '#00e676' if '看漲' in bf['type'] else '#ff5252'
        fill_color = 'rgba(0, 230, 118, 0.14)' if '看漲' in bf['type'] else 'rgba(255, 82, 82, 0.14)'

        fig.add_trace(go.Scatter(
            x=[x_pt[2], a_pt[2], b_pt[2], x_pt[2]],
            y=[x_pt[3], a_pt[3], b_pt[3], x_pt[3]],
            fill='toself',
            fillcolor=fill_color,
            mode='lines+text',
            line=dict(color=wing_color, width=2.0),
            text=["X", "A", "B", ""],
            textposition="top center",
            textfont=dict(color="#ffffff", size=11, family="Arial Black"),
            showlegend=False
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=[b_pt[2], c_pt[2], d_d, b_pt[2]],
            y=[b_pt[3], c_pt[3], d_p, b_pt[3]],
            fill='toself',
            fillcolor=fill_color,
            mode='lines+text',
            line=dict(color=wing_color, width=2.0, dash='dash'),
            text=["", "C", "D 預測", ""],
            textposition="bottom center",
            textfont=dict(color="#ffd700", size=11, family="Arial Black"),
            showlegend=False
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=[x_pt[2], d_d],
            y=[x_pt[3], d_p],
            mode='lines',
            line=dict(color='rgba(255, 255, 255, 0.65)', width=1.5, dash='dot'),
            showlegend=False
        ), row=1, col=1)

    # 4. AB=CD 形態 3 條線幾何
    abcd = pattern_data.get('abcd')
    if abcd:
        a_pt, b_pt, c_pt = abcd['a'], abcd['b'], abcd['c']
        d_p = abcd['d_price']
        d_d = abcd['d_date']

        fig.add_trace(go.Scatter(
            x=[a_pt[2], b_pt[2], c_pt[2], d_d],
            y=[a_pt[3], b_pt[3], c_pt[3], d_p],
            mode='lines+markers+text',
            line=dict(color='#00e5ff', width=2.2, dash='solid'),
            marker=dict(size=6, color=['#00e5ff', '#00e5ff', '#00e5ff', '#ffd700']),
            text=[" A", " B", " C", " D (預測)"],
            textposition="top right",
            textfont=dict(color="#00e5ff", size=11, family="Arial Black"),
            showlegend=False
        ), row=1, col=1)

    # 🎯 渲染結構失效止損細紅虛線 (Invalidation Lines)
    inval_lines = pattern_data.get('invalidation_lines', [])
    for inv in inval_lines:
        fig.add_trace(go.Scatter(
            x=[inv['date_start'], inv['date_end']],
            y=[inv['price'], inv['price']],
            mode='lines',
            line=dict(color='rgba(239, 68, 68, 0.85)', width=1.5, dash='dash'),
            name=inv['name'],
            hoverinfo='name',
            showlegend=False
        ), row=1, col=1)

    # 5. 主圖氣泡「扇形左右智能避讓」
    has_bf = bf is not None
    has_abcd = abcd is not None
    is_close = False

    if has_bf and has_abcd:
        price_diff = abs(bf['d_price'] - abcd['d_price']) / max(bf['d_price'], abcd['d_price'])
        if price_diff <= 0.06:
            is_close = True

    if has_bf:
        d_p = bf['d_price']
        d_d = bf['d_date']
        is_bull = '看漲' in bf['type']
        ax_offset = -55 if is_close else 0
        ay_offset = (42 if is_bull else -42)

        fig.add_annotation(
            x=d_d, y=d_p,
            ax=ax_offset, ay=ay_offset,
            text=f"<b>蝴蝶 D點預測<br>${d_p:.2f} (PRZ)</b>",
            bgcolor="#311b92",
            bordercolor="#e040fb",
            borderwidth=1.5,
            borderpad=4,
            font=dict(color="#e040fb", size=10, family="monospace"),
            showarrow=True,
            arrowhead=2,
            arrowcolor="#e040fb",
            row=1, col=1
        )

    if has_abcd:
        d_p = abcd['d_price']
        d_d = abcd['d_date']
        is_bear = '看跌' in abcd['type']
        ax_offset = 55 if is_close else 0
        ay_offset = (-42 if is_bear else 42)

        fig.add_annotation(
            x=d_d, y=d_p,
            ax=ax_offset, ay=ay_offset,
            text=f"<b>AB=CD 預測<br>${d_p:.2f}</b>",
            bgcolor="#00334e",
            bordercolor="#00e5ff",
            borderwidth=1.5,
            borderpad=4,
            font=dict(color="#00e5ff", size=10, family="monospace"),
            showarrow=True,
            arrowhead=2,
            arrowcolor="#00e5ff",
            row=1, col=1
        )

    # 6. 右側膠囊「雙欄階梯錯位與垂直避讓」
    raw_badges = pattern_data.get('right_badges', [])
    if raw_badges:
        all_prices = [b['price'] for b in raw_badges]
        y_span = max(all_prices) - min(all_prices) if max(all_prices) > min(all_prices) else 20.0
        min_gap = max(2.5, y_span * 0.07)

        sorted_badges = sorted(raw_badges, key=lambda b: b['price'])
        adjusted_badges = []
        for b in sorted_badges:
            item = b.copy()
            item['plot_y'] = b['price']
            item['xshift'] = 0
            adjusted_badges.append(item)

        for i in range(len(adjusted_badges)):
            for j in range(i + 1, len(adjusted_badges)):
                diff_y = adjusted_badges[j]['plot_y'] - adjusted_badges[i]['plot_y']
                if diff_y < min_gap:
                    if adjusted_badges[i]['xshift'] == 0:
                        adjusted_badges[j]['xshift'] = -105
                    else:
                        adjusted_badges[j]['xshift'] = 0
                    nudge = (min_gap - diff_y) * 0.45
                    adjusted_badges[j]['plot_y'] += nudge
                    adjusted_badges[i]['plot_y'] -= nudge

        for b in adjusted_badges:
            fig.add_annotation(
                xref="x domain",
                yref="y",
                x=0.998,
                y=b['plot_y'],
                xshift=b['xshift'],
                text=f"<b>{b['label']}</b>",
                bgcolor=b['bg'],
                bordercolor=b['bg'],
                borderwidth=1.5,
                borderpad=4,
                font=dict(color=b.get('text_col', '#ffffff'), size=10, family="monospace, Arial"),
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                row=1, col=1
            )

    # 7. 懸浮戰術看板 HUD：左上角定位
    hud_clean_text = _build_clean_hud_text(pattern_data)
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0.015,
        y=0.985,
        text=hud_clean_text,
        bgcolor="rgba(15, 23, 42, 0.92)",
        bordercolor="#4f46e5",
        borderwidth=1.5,
        borderpad=8,
        font=dict(color="#ffffff", size=10, family="Courier New, monospace, Consolas"),
        showarrow=False,
        xanchor="left",
        yanchor="top",
        align="left"
    )


def _build_clean_hud_text(pattern_data: dict) -> str:
    """
    純淨格式化戰術看板 (升級：展示 🚫結構失效線 與 盈虧比量化評級)
    """
    d_top = pattern_data.get('double_top')
    d_bottom = pattern_data.get('double_bottom')
    tri = pattern_data.get('triangle')
    bf = pattern_data.get('butterfly')
    abcd = pattern_data.get('abcd')
    hs = pattern_data.get('head_shoulders')
    last_date = pattern_data.get('last_date_str', '10-16')

    if hs:
        hs_str = f"<span style='color:#f43f5e;'><b>{hs['type']} · {hs['status']} (頸線 ${hs['nl']:.2f})</b></span>"
    else:
        hs_str = "<span style='color:#94a3b8;'>頭肩頂 / 頭肩底 · 未見形態</span>"

    # 表 1: 反轉形態
    t1_header = "<span style='color:#a5b4fc;'><b>【反轉形態】  狀態      頂/底          頸線    目標    🚫失效線  盈虧比</b></span>"
    if d_top:
        st_c = "#ffffff" if d_top['status'] == '形成中' else "#f87171"
        rr_b = d_top['rr_info']['rr_badge']
        row_dt = f"<span style='color:#f87171;'><b>雙頂</b></span>        <span style='color:{st_c};'>{d_top['status']}</span>    {d_top['top_str']}  <span style='color:#fbbf24;'><b>{d_top['nl']:.2f}</b></span>  <span style='color:#38bdf8;'><b>{d_top['target']:.2f}</b></span>  <span style='color:#f87171;'><b>{d_top['invalidation']:.2f}</b></span>  {rr_b}"
    else:
        row_dt = "<span style='color:#64748b;'>雙頂        未見形態       -           -       -       -       - </span>"

    if d_bottom:
        st_c = "#ffffff" if d_bottom['status'] == '形成中' else "#00e676"
        rr_b = d_bottom['rr_info']['rr_badge']
        row_db = f"<span style='color:#4ade80;'><b>雙底</b></span>        <span style='color:{st_c};'>{d_bottom['status']}</span>    {d_bottom['bot_str']}  <span style='color:#fbbf24;'><b>{d_bottom['nl']:.2f}</b></span>  <span style='color:#38bdf8;'><b>{d_bottom['target']:.2f}</b></span>  <span style='color:#f87171;'><b>{d_bottom['invalidation']:.2f}</b></span>  {rr_b}"
    else:
        row_db = "<span style='color:#64748b;'>雙底        未見形態       -           -       -       -       - </span>"

    # 表 2: 突破形態
    t2_header = "<span style='color:#a5b4fc;'><b>【突破形態】  狀態      方向    突破位    目標    🚫失效線  盈虧比</b></span>"
    if tri:
        st_c = "#00e676" if tri['status'] == '已確認突破' else "#fbbf24"
        rr_b = tri['rr_info']['rr_badge']
        row_tri = f"<span style='color:#c084fc;'><b>{tri['type']}</b></span>  <span style='color:{st_c};'><b>{tri['status']}</b></span>  <span style='color:#38bdf8;'>{tri['direction']}</span>    <span style='color:#fbbf24;'><b>{tri['bo_price']:.2f}</b></span>  <span style='color:#38bdf8;'><b>{tri['target']:.2f}</b></span>  <span style='color:#f87171;'><b>{tri['invalidation']:.2f}</b></span>  {rr_b}"
    else:
        row_tri = "<span style='color:#64748b;'>三角形態    未見形態    -        -         -       -       -</span>"

    # 表 3: 諧波預測 (🎯 重點：展示 PRZ 失效線與擊穿無效紅字警報)
    t3_header = "<span style='color:#a5b4fc;'><b>【諧波預測】  狀態      方向    預測 D點  反轉區(PRZ)  🚫結構失效線  盈虧比(R:R)</b></span>"

    if bf:
        if bf.get('is_invalidated'):
            row_bf = f"<span style='color:#f472b6;'><b>蝴蝶形態</b></span>    <span style='color:#ef4444; background:#450a0a; border:1px solid #ef4444; padding:1px 5px; border-radius:3px;'><b>⚠️ 形態已被主力擊穿無效，嚴禁左側交易！</b></span> (失效線 ${bf['invalidation']:.2f})"
        else:
            st_c = "#00e676" if "反轉" in bf['status'] else "#38bdf8"
            dir_c = "#00e676" if "看漲" in bf['type'] else "#f87171"
            rr_b = bf['rr_info']['rr_badge']
            row_bf = f"<span style='color:#f472b6;'><b>蝴蝶形態</b></span>    <span style='color:{st_c};'><b>{bf['status'][:5]}</b></span> <span style='color:{dir_c};'>{bf['direction']}</span>    <span style='color:#fbbf24;'><b>{bf['d_price']:.2f}</b></span>  <span style='color:#38bdf8;'><b>{bf['prz_str']}</b></span>  <span style='color:#f87171;'><b>{bf['invalidation']:.2f}</b></span>       {rr_b}"
    else:
        row_bf = "<span style='color:#64748b;'>蝴蝶形態    未見形態    -        -         -            -            -</span>"

    if abcd:
        if abcd.get('is_invalidated'):
            row_abcd = f"<span style='color:#38bdf8;'><b>AB=CD</b></span>       <span style='color:#ef4444; background:#450a0a; border:1px solid #ef4444; padding:1px 5px; border-radius:3px;'><b>⚠️ 形態已被主力擊穿無效，嚴禁左側交易！</b></span> (失效線 ${abcd['invalidation']:.2f})"
        else:
            st_c = "#00e676" if "抵達" in abcd['status'] else "#38bdf8"
            dir_c = "#00e676" if "看漲" in abcd['type'] else "#f87171"
            rr_b = abcd['rr_info']['rr_badge']
            row_abcd = f"<span style='color:#38bdf8;'><b>AB=CD</b></span>       <span style='color:{st_c};'><b>{abcd['status'][:5]}</b></span> <span style='color:{dir_c};'>{abcd['direction']}</span>    <span style='color:#fbbf24;'><b>{abcd['d_price']:.2f}</b></span>  <span style='color:#38bdf8;'><b>{abcd['prz_str']}</b></span>  <span style='color:#f87171;'><b>{abcd['invalidation']:.2f}</b></span>       {rr_b}"
    else:
        row_abcd = "<span style='color:#64748b;'>AB=CD       未見形態    -        -         -            -            -</span>"

    vcp_str = f"<span style='color:#94a3b8;'>VCP · 未見形態 · 截至 {last_date}</span>"

    return f"{hs_str}<br><br>{t1_header}<br>{row_dt}<br>{row_db}<br><br>{t2_header}<br>{row_tri}<br><br>{t3_header}<br>{row_bf}<br>{row_abcd}<br><br>{vcp_str}"