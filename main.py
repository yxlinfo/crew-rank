import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

# [1. crews_config 및 fetch_data, get_gauge_style 로직은 기존과 동일하므로 유지]

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
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ 
        background: #0f172a; color: #f8fafc; font-family: sans-serif; 
        padding: 15px; width: 900px; /* 1080px에서 900px로 대폭 축소 */
        -webkit-font-smoothing: antialiased;
        overflow: hidden;
    }}
    
    .top-bar {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15px; border-bottom: 2px solid #334155; padding-bottom: 8px; }}
    
    .grid {{ display: grid; gap: 10px; grid-template-columns: repeat(3, 1fr); }}
    .crew-card {{ background: #1e293b; border: 1px solid #475569; border-radius: 10px; padding: 10px 12px; }}
    
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #334155; padding-bottom: 6px; margin-bottom: 10px; }}
    .crew-title {{ font-size: 1.1rem; font-weight: 900; }} /* 타이틀 크기 축소 */
    .stats {{ text-align: right; font-size: 0.75rem; color: #cbd5e1; font-weight: 700; line-height: 1.3; }}
    
    .member-row {{ display: flex; align-items: center; gap: 6px; margin-bottom: 12px; height: 28px; position: relative; }} 
    .nick {{ width: 95px; font-size: 0.85rem; font-weight: 700; color: #f1f5f9; white-space: nowrap; overflow: hidden; }}
    
    .bar-bg {{ flex-grow: 1; background: #334155; height: 6px; border-radius: 3px; }}
    .bar-fill {{ height: 100%; border-radius: 3px; }}
    
    .count-container {{ 
        width: 95px; text-align: right; 
        height: 28px; position: relative;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .count-main {{ 
        font-size: 0.95rem; font-weight: 900; color: #ffffff; line-height: 28px; 
    }}
    .count-today {{ 
        font-size: 0.7rem; font-weight: 800; 
        position: absolute; bottom: -10px; right: 0; 
        white-space: nowrap;
    }}
    
    .c-red {{ color: #f87171; }} .c-white {{ color: #fff; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 0.9rem; font-weight: 800;">UPDATED: {now.strftime('%Y.%m.%d %H:%M')}</div>
            <div style="font-size: 0.75rem; color: #64748b;">DATA SOURCE: POONG.TODAY</div>
        </div>
        <div class="grid">"""

    for c in final_data:
        html += f"""
        <div class="crew-card">
            <div class="header">
                <div class="crew-title {c['color']}">{c['name']} <span style="font-size:0.7em; opacity:0.8;">({c['member_count']})</span></div>
                <div class="stats">T: {c['total']:,}<br>A: {c['avg']:,}</div>
            </div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['v']['monthly'])
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "&nbsp;&nbsp;"
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            today_label = f'<div class="count-today" style="color:{style["point"]}">(+{m["v"]["daily"]:,})</div>' if m['v']['daily'] > 0 else ''
            
            html += f"""
            <div class="member-row">
                <div class="nick">{medal}{m['nick']}</div>
                <div class="bar-bg"><div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div></div>
                <div class="count-container">
                    <div class="count-main">{m['v']['monthly']:,}</div>
                    {today_label}
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

def save_chart_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 캡처 폭을 900px로 맞춤
        context = browser.new_context(viewport={'width': 900, 'height': 3000}, device_scale_factor=2)
        page = context.new_page()
        page.set_content(html_content)
        time.sleep(3)
        page.screenshot(path="chart.png", full_page=True, animations="disabled")
        browser.close()

if __name__ == "__main__":
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: f.write(generated_html)
    try:
        save_chart_image(generated_html)
        print("Success")
    except Exception as e: print(f"Error: {e}")