import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

COLOR_MAP = {
    "c-red": "#f87171", "c-white": "#f8fafc", "c-gold": "#fbbf24", 
    "c-pink": "#f472b6", "c-cyan": "#22d3ee", "c-purple": "#c084fc", 
    "c-orange": "#fb923c", "c-teal": "#2dd4bf", "c-lime": "#a3e635", 
    "c-green": "#4ade80"
}

def load_config_from_db():
    conn = sqlite3.connect('crew_data.db')
    cursor = conn.cursor()
    crews_config = {}
    cursor.execute("SELECT id, name, color FROM crews")
    crews = cursor.fetchall()
    
    for crew_id, name, color in crews:
        cursor.execute("SELECT nick, uid FROM members WHERE crew_id = ?", (crew_id,))
        members = {row[0]: row[1] for row in cursor.fetchall()}
        crews_config[name] = {"color": color, "members": members}
        
    conn.close()
    return crews_config

def fetch_data(uid, year, month, day):
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year={year}&month={month:02d}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://poong.today/"
    }
    for _ in range(5):
        try:
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                json_data = res.json()
                m_val = json_data.get('b', 0)
                d_list = json_data.get('d', [])
                if not d_list:
                    d_val = 0
                else:
                    d_val = next((i.get('b', 0) for i in d_list if int(i.get('d', -1)) == int(day)), 0)
                return {"monthly": m_val, "daily": d_val}
            time.sleep(1)
        except: 
            time.sleep(1)
    return {"monthly": 0, "daily": 0}

def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "point": "#ef4444"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "point": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "point": "#9ca3af"}

def generate_html():
    crews_config = load_config_from_db()
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m, d = target_date.year, target_date.month, target_date.day
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, d)}, all_tasks))

    final_data = []
    for c_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == c_name], key=lambda x: x['v']['monthly'], reverse=True)
        total = sum(m['v']['monthly'] for m in m_list)
        final_data.append({"name": c_name, "color": info['color'], "total": total, "avg": int(total/len(m_list)) if m_list else 0, "members": m_list, "max": m_list[0]['v']['monthly'] if m_list else 1})
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    /* 🌌 우주 배경: 딥 네이비 그라데이션 및 가상 별빛 효과 */
    body {{ 
        background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%);
        color: #f8fafc; font-family: 'Pretendard', -apple-system, sans-serif; 
        padding: 10px; width: 100vw; overflow-x: hidden; min-height: 100vh;
    }}
    
    /* 별빛 가루 효과 (CSS) */
    body::before {{
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 40px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 30px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 40px);
        background-size: 550px 550px, 350px 350px, 250px 250px;
        background-position: 0 0, 40px 60px, 130px 270px;
        opacity: 0.2; pointer-events: none; z-index: 0;
    }}
    
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; background: rgba(15, 23, 42, 0.6); padding: 8px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); backdrop-filter: blur(10px); position: relative; z-index: 1; }}
    
    .grid {{ display: grid; gap: 10px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; position: relative; z-index: 1; }}
    
    /* 🛸 우주선/행성 느낌의 반투명 카드 디자인 */
    .crew-card {{ 
        background: rgba(13, 19, 33, 0.7); 
        border: 1px solid rgba(255,255,255,0.1); 
        border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 10px; 
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(4px);
        position: relative; overflow: hidden; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        z-index: 1; 
    }}
    
    .crew-card:hover {{ 
        transform: translateY(-8px) scale(1.03); 
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.9), 0 0 15px var(--theme-color); 
        border-color: var(--theme-color); 
        background: rgba(20, 30, 48, 0.9);
        filter: brightness(1.2); z-index: 10; 
    }}
    
    .header {{ display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px; margin-bottom: 12px; }}
    
    /* 🎯 크루 이름 중앙 배치 */
    .header-top {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; }}
    .crew-title {{ 
        font-size: 1.15rem; font-weight: 900; letter-spacing: -0.5px; 
        text-shadow: 0 0 10px var(--theme-color); /* 테마색 네온 효과 */
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;
    }}
    .crew-count {{ font-size: 0.7rem; color: #94a3b8; font-weight: 700; opacity: 0.8; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 6px; background: rgba(0, 0, 0, 0.4); padding: 8px 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.65rem; color: var(--theme-color); font-weight: 800; letter-spacing: 1px; opacity: 0.9; }}
    .stat-value {{ font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; text-shadow: 0 0 10px var(--theme-color); white-space: nowrap; letter-spacing: -0.5px; }}

    .member-module {{ position: relative; margin-bottom: 8px; padding: 8px 8px 18px 8px; background: rgba(0, 0, 0, 0.2); border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); z-index: 1; transition: all 0.2s; }}
    .member-module:hover {{ background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); }}
    
    .member-info {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 2px; }}
    .nick {{ font-size: 0.75rem; font-weight: 700; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0; letter-spacing: -0.8px; padding-right: 2px; }}
    .count-main {{ font-size: 0.85rem; font-weight: 900; color: #ffffff; flex-shrink: 0; font-family: 'Consolas', monospace; letter-spacing: -0.8px; }}

    .bar-container {{ position: relative; width: 100%; height: 5px; background: rgba(0, 0, 0, 0.5); border-radius: 4px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 4px; box-shadow: 0 0 10px rgba(255,255,255,0.3); }}
    .count-today {{ font-size: 0.65rem; font-weight: 800; position: absolute; left: 50%; transform: translateX(-50%); bottom: -16px; white-space: nowrap; letter-spacing: -0.5px; text-shadow: 0 0 5px rgba(0,0,0,0.8); }}

    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 6px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 8px; border-radius: 10px; }}
        .crew-title {{ font-size: 1rem; }}
        .stat-value {{ font-size: 0.95rem; }}
        .nick {{ font-size: 0.7rem; }}
        .count-main {{ font-size: 0.75rem; }}
    }}

    .c-red {{ color: #f87171; }} .c-white {{ color: #f8fafc; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 1rem; font-weight: 900; color: #e2e8f0; letter-spacing: 2px;">COSMOS <span style="color:var(--theme-color, #38bdf8);">RANKING</span></div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">{now.strftime('%y.%m.%d %H:%M')}</div>
        </div>
        <div class="grid">"""

    for c in final_data:
        theme_hex = COLOR_MAP.get(c['color'], '#ffffff')
        html += f"""
        <div class="crew-card" style="--theme-color: {theme_hex};">
            <div class="header">
                <div class="header-top">
                    <div class="crew-title {c['color']}">{c['name']}</div>
                    <div class="crew-count">{len(c['members'])} MEMBERS</div>
                </div>
                <div class="header-stats">
                    <div class="stat-item">
                        <span class="stat-label">Monthly</span>
                        <span class="stat-value">{c['total']:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Average</span>
                        <span class="stat-value">{c['avg']:,}</span>
                    </div>
                </div>
            </div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['v']['monthly'])
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            today = f'<div class="count-today" style="color:{style["point"]}">(+{m["v"]["daily"]:,})</div>' if m['v']['daily'] > 0 else ''
            
            html += f"""
            <div class="member-module">
                <div class="member-info">
                    <div class="nick">{medal}{m['nick']}</div>
                    <div class="count-main">{m['v']['monthly']:,}</div>
                </div>
                <div class="bar-container">
                    <div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div>
                    {today}
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

if __name__ == "__main__":
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(generated_html)
    print("Success: 우주 테마 대시보드 갱신 완료!")