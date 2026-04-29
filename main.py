import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

# [1. crews_config 및 fetch_data 로직은 기존과 동일하므로 생략 - 그대로 유지하세요]

# 색상 가이드 수정: 숫자는 가독성을 위해 밝은색 유지, 게이지와 증감 수치에만 포인트 컬러 부여
def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "point": "#ef4444"}
    elif count >= 800000: return {"grad": "linear-gradient(90deg, #9a3412, #f97316)", "point": "#f97316"}
    elif count >= 400000: return {"grad": "linear-gradient(90deg, #a16207, #eab308)", "point": "#eab308"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #166534, #22c55e)", "point": "#22c55e"}
    elif count >= 100000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "point": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "point": "#9ca3af"}

def generate_html():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    y, m, d = now.year, now.month, now.day
    
    # [데이터 수집 logic 동일]
    all_tasks = []
    for crew, info in crews_config.items():
        for nick, uid in info['members'].items():
            all_tasks.append({'crew': crew, 'nick': nick, 'uid': uid})
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, d)}, all_tasks))
    final_data = []
    for crew_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == crew_name], key=lambda x: x['v']['monthly'], reverse=True)
        total = sum(m['v']['monthly'] for m in m_list)
        final_data.append({"name": crew_name, "color": info['color'], "total": total, "avg": int(total/len(m_list)) if m_list else 0, "member_count": len(m_list), "members": m_list, "max": m_list[0]['v']['monthly'] if m_list else 1})
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    body {{ background: #0f172a; color: #f8fafc; font-family: 'Pretendard', sans-serif; margin: 0; padding: 40px; width: 1600px; }}
    .top-bar {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 25px; border-bottom: 2px solid #334155; padding-bottom: 15px; }}
    
    .grid {{ display: grid; gap: 20px; grid-template-columns: repeat(3, 1fr); }}
    .crew-card {{ background: #1e293b; border: 1px solid #475569; border-radius: 16px; padding: 15px 20px; box-shadow: 0 6px 20px rgba(0,0,0,0.4); }}
    
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #334155; padding-bottom: 10px; margin-bottom: 15px; }}
    .crew-title {{ font-size: 1.45rem; font-weight: 900; }}
    .stats {{ text-align: right; font-size: 0.9rem; color: #94a3b8; font-weight: 700; line-height: 1.5; }}
    
    /* 멤버 행 디자인 개선 */
    .member-row {{ 
        display: flex; align-items: center; gap: 15px; 
        margin-bottom: 18px; height: 36px; position: relative; 
    }} 
    .nick {{ width: 140px; font-size: 1.05rem; font-weight: 700; color: #f1f5f9; }}
    
    /* 2. 게이지 바 시인성 개선: 배경 트랙 색상을 더 밝게 (#334155) */
    .bar-bg {{ flex-grow: 1; background: #334155; height: 10px; border-radius: 5px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 5px; transition: width 0.3s ease; }}
    
    /* 1. 우측 숫자 열 정렬 및 여백 개선 */
    .count-container {{ 
        width: 145px; text-align: right; 
        height: 36px; position: relative;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .count-main {{ 
        font-size: 1.2rem; font-weight: 900; 
        color: #ffffff; /* 3. 숫자 색상을 흰색으로 통일하여 가독성 증대 */
        line-height: 1;
        letter-spacing: -0.02em;
    }}
    .count-today {{ 
        font-size: 0.8rem; font-weight: 800; 
        position: absolute; bottom: -12px; right: 0; 
        margin-top: 2px; /* 증감 수치 숨통 트기 */
        white-space: nowrap;
    }}
    
    .c-red {{ color: #f87171; }} .c-white {{ color: #fff; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 1.1rem; font-weight: 800;">UPDATED: {now.strftime('%Y.%m.%d %H:%M')}</div>
            <div style="font-size: 0.9rem; color: #64748b; font-weight: 500;">DATA SOURCE: POONG.TODAY</div>
        </div>
        <div class="grid">"""

    for c in final_data:
        html += f"""
        <div class="crew-card">
            <div class="header">
                <div class="crew-title {c['color']}">{c['name']} <span style="font-size:0.75em; opacity:0.8;">({c['member_count']}명)</span></div>
                <div class="stats">TOTAL: {c['total']:,}<br>AVG: {c['avg']:,}</div>
            </div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['v']['monthly'])
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "&nbsp;&nbsp;&nbsp;"
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            
            # 당일 증감 수치에만 포인트 컬러 적용
            today_label = f'<div class="count-today" style="color:{style["point"]}">(+{m["v"]["daily"]:,})</div>' if m['v']['daily'] > 0 else ''
            
            html += f"""
            <div class="member-row">
                <div class="nick">{medal} {m['nick']}</div>
                <div class="bar-bg"><div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div></div>
                <div class="count-container">
                    <div class="count-main">{m['v']['monthly']:,}</div>
                    {today_label}
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

# [이하 save_chart_image 및 __main__ 함수 동일]