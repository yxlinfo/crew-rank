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

def fetch_data(uid, year, month, session):
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year={year}&month={month:02d}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://poong.today/"
    }
    for _ in range(3):
        try:
            res = session.get(api_url, headers=headers, timeout=10)
            if res.status_code == 200:
                json_data = res.json()
                m_val = json_data.get('b', 0)
                return {"monthly": m_val}
            time.sleep(0.5)
        except: 
            time.sleep(0.5)
    return {"monthly": 0}

# 🚀 혜성 꼬리의 '코어 색상'만 심플하게 반환하도록 수정 (백만, 50만, 20만 단위로 세분화)
def get_gauge_style(count):
    if count >= 1000000: return "#ef4444" # Red
    elif count >= 500000: return "#fbbf24"  # Gold
    elif count >= 200000: return "#38bdf8"  # Sky Blue
    else: return "#94a3b8" # Slate

def generate_html():
    crews_config = load_config_from_db()
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m = target_date.year, target_date.month
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, session)}, all_tasks))

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
    
    body {{ 
        background: #000000;
        color: #f8fafc; font-family: 'Pretendard', -apple-system, sans-serif; 
        padding: 10px; width: 100vw; overflow-x: hidden; min-height: 100vh;
    }}
    
    body::before {{
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background-image: 
            radial-gradient(white, rgba(255,255,255,.2) 1px, transparent 20px),
            radial-gradient(white, rgba(255,255,255,.1) 1px, transparent 15px);
        background-size: 550px 550px, 350px 350px;
        background-position: 0 0, 40px 60px;
        opacity: 0.1; pointer-events: none; z-index: 0;
        will-change: transform; 
    }}
    
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; background: rgba(0, 0, 0, 0.9); padding: 8px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);backdrop-filter: blur(5px); position: relative; z-index: 1; transform: translateZ(0); }}
    
    .grid {{ display: grid; gap: 10px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; position: relative; z-index: 1; }}
    
    .crew-card {{ 
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 12px; 
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
        position: relative; overflow: hidden; 
        transform: translateZ(0); 
        will-change: transform; 
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }}
    
    .crew-card:hover {{
        transform: translateY(-2px) translateZ(0); 
        border-color: #2a2a2a; 
        box-shadow: 0 8px 25px rgba(0, 0, 0, 1); 
        z-index: 10; 
    }}
    
    .header {{ display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid #222; padding-bottom: 12px; margin-bottom: 14px; }}
    
    .header-top {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; }}
    .crew-title {{ 
        font-size: 1.2rem; font-weight: 900; letter-spacing: -0.5px; 
        color: var(--theme-color);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;
    }}
    .crew-count {{ font-size: 0.7rem; color: #64748b; font-weight: 700; opacity: 1; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 6px; background: #080808; padding: 8px 10px; border-radius: 8px; border: 1px solid #1a1a1a; }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.65rem; color: var(--theme-color); font-weight: 800; letter-spacing: 1px; opacity: 1; text-transform: uppercase; }}
    .stat-value {{ font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; white-space: nowrap; letter-spacing: -0.5px; }}

    .member-module {{ 
        position: relative; margin-bottom: 6px; 
        background: #111111; 
        border: 1px solid #1e1e1e;
        border-radius: 4px; overflow: hidden;
        transform: translateZ(0);
        cursor: pointer; 
        transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease; 
    }}
    
    .member-module:hover {{
        transform: translateX(2px) translateZ(0); 
        background: #181818; 
        border-color: rgba(255,255,255,0.1);
        z-index: 2; 
    }}
    
    /* 🚀 새로운 혜성(Comet) 게이지 라인 */
    .member-bg-bar {{ 
        position: absolute; left: 0; bottom: 0;
        height: 2px; /* 아주 얇고 날렵한 선 */
        background: linear-gradient(90deg, transparent, var(--bar-color));
        transition: width 0.5s ease;
        z-index: 1;
    }}
    
    /* 🚀 혜성의 빛나는 코어(머리 부분) */
    .member-bg-bar::after {{
        content: '';
        position: absolute; right: 0; top: -2px; /* 선의 중앙에 오도록 위로 당김 */
        width: 6px; height: 6px;
        background: #ffffff;
        border-radius: 50%;
        box-shadow: 0 0 6px 1px var(--bar-color), 0 0 12px 3px var(--bar-color); /* 코어 주변의 네온 글로우 */
    }}
    
    .member-content {{
        display: flex; justify-content: space-between; align-items: center;
        position: relative; 
        width: 100%; height: 30px; 
        padding: 0 10px; z-index: 2; 
    }}
    
    .nick {{ 
        font-size: 0.8rem; font-weight: 800; color: #e2e8f0; 
        text-shadow: 1px 1px 2px rgba(0,0,0,1);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        flex: 1; padding-right: 8px; letter-spacing: -0.5px;
        transition: color 0.2s ease, text-shadow 0.2s ease;
    }}
    
    .member-module:hover .nick {{
        color: #ffffff;
        text-shadow: 0 0 5px rgba(255,255,255,0.4); 
    }}
    
    .count-main {{ 
        font-size: 0.9rem; font-weight: 900; color: #ffffff; 
        font-family: 'Consolas', monospace; letter-spacing: -0.5px;
        text-shadow: 1px 1px 2px rgba(0,0,0,1);
        flex-shrink: 0;
    }}

    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 10px; border-radius: 10px; }}
        .crew-title {{ font-size: 1.05rem; }}
        
        .member-content {{ height: 28px; padding: 0 8px; }}
        .nick {{ font-size: 0.75rem; letter-spacing: -0.8px; padding-right: 4px; }}
        .count-main {{ font-size: 0.85rem; letter-spacing: -0.8px; }}
        
        .member-module:hover {{ transform: translateX(1px) translateZ(0); }}
        .crew-card:hover {{ transform: none; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }} 
    }}

    .c-red {{ color: #f87171; }} .c-white {{ color: #f8fafc; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 1rem; font-weight: 900; color: #e2e8f0; letter-spacing: 2px;">CREW <span style="color:var(--theme-color, #38bdf8);">RANKING</span></div>
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
                        <span class="stat-label">Total</span>
                        <span class="stat-value">{c['total']:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Average</span>
                        <span class="stat-value">{c['avg']:,}</span>
                    </div>
                </div>
            </div>"""
        
        for i, m in enumerate(c['members']):
            # 게이지의 테마 컬러 가져오기
            bar_color = get_gauge_style(m['v']['monthly'])
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
            medal_str = f"{medal} " if medal else ""
            
            html += f"""
            <div class="member-module">
                <div class="member-bg-bar" style="width:{w}%; --bar-color: {bar_color};"></div>
                <div class="member-content">
                    <div class="nick">{medal_str}{m['nick']}</div>
                    <div class="count-main">{m['v']['monthly']:,}</div>
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

if __name__ == "__main__":
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(generated_html)
    print("Success: 혜성(Comet) 게이지 갱신 완료!")