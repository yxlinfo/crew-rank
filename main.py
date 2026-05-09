import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# [설정] 테마 색상 및 크루 이름 매핑
COLOR_MAP = {
    "c-red": "#f87171", "c-white": "#f8fafc", "c-gold": "#fbbf24", 
    "c-pink": "#f472b6", "c-cyan": "#22d3ee", "c-purple": "#c084fc", 
    "c-orange": "#fb923c", "c-teal": "#2dd4bf", "c-lime": "#a3e635", 
    "c-green": "#4ade80"
}

CREW_NAME_MAP = {
    "광우상사": "GW", "씨나인": "C9", "이노레이블": "INOLABLE",
    "YXL": "YXL", "정선컴퍼니": "JS", "771": "771",
    "더케이": "The K", "GD컴퍼니": "GD", "문에이": "Moon A", "쇼케이": "Show K"
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://poong.today/",
        "Origin": "https://poong.today"
    }
    for attempt in range(3):
        try:
            res = session.get(api_url, headers=headers, timeout=8)
            if res.status_code == 200:
                val = res.json().get('b', 0)
                if val >= 0: return {"monthly": val}
            time.sleep(0.5)
        except:
            time.sleep(0.5)
    return {"monthly": 0}

def get_gauge_style(count):
    if count >= 1000000: return "#ef4444" 
    elif count >= 500000: return "#fbbf24"  
    elif count >= 200000: return "#38bdf8"  
    else: return "#94a3b8" 

def generate_html():
    crews_config = load_config_from_db()
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m = target_date.year, target_date.month
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=50)
    session.mount('https://', adapter)
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, session)}, all_tasks))

    final_data = []
    for c_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == c_name], key=lambda x: x['v']['monthly'], reverse=True)
        total = sum(m['v']['monthly'] for m in m_list)
        # 0 출력 문제 방지: max_val이 0이면 1로 대체하여 나눗셈 오류 방지
        max_val = max([m['v']['monthly'] for m in m_list]) if m_list and any(m['v']['monthly'] > 0 for m in m_list) else 1
        final_data.append({
            "name": c_name, "color": info['color'], "total": total, 
            "avg": int(total/len(m_list)) if m_list else 0, 
            "members": m_list, "max": max_val
        })
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #000; color: #f8fafc; font-family: 'Pretendard', sans-serif; padding: 10px; overflow-x: hidden; }}
    body::before {{ content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-image: radial-gradient(white, rgba(255,255,255,.05) 1px, transparent 20px); background-size: 300px 300px; opacity: 0.2; pointer-events: none; }}
    
    .grid {{ display: grid; gap: 12px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; }}

    @keyframes rotateCore {{ 0% {{ transform: translate(-50%, -50%) rotate(0deg); }} 100% {{ transform: translate(-50%, -50%) rotate(360deg); }} }}
    @keyframes fadeInUp {{ 0% {{ opacity: 0; transform: translateY(15px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes fillGauge {{ 0% {{ width: 0%; }} 100% {{ width: var(--target-width); }} }}

    .crew-card {{ 
        background: #0d0d0d; border: 1px solid #1a1a1a; border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        position: relative; overflow: hidden; opacity: 0; 
        animation: fadeInUp 0.5s ease forwards; animation-delay: var(--delay);
    }}
    .header {{ position: relative; padding-bottom: 12px; margin-bottom: 12px; border-bottom: 1px solid #222; text-align: center; z-index: 2; }}
    .energy-core {{
        position: absolute; top: 40%; left: 50%; width: 100px; height: 100px;
        background: radial-gradient(circle, var(--theme-color) 0%, transparent 75%);
        opacity: 0.1; filter: blur(15px); z-index: 0; animation: rotateCore 12s linear infinite;
    }}
    .crew-card:hover .energy-core {{ opacity: 0.25; animation-duration: 5s; }}

    .crew-title {{ font-size: 1.2rem; font-weight: 900; color: #fff; text-shadow: 0 0 8px var(--theme-color); }}
    .header-stats {{ display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; margin-top: 10px; border: 1px solid rgba(255,255,255,0.05); }}
    .stat-item {{ display: flex; justify-content: space-between; font-size: 0.7rem; }}
    .stat-label {{ color: var(--theme-color); font-weight: 800; }}
    .stat-value {{ color: #fff; font-family: 'Consolas', monospace; font-weight: 700; }}

    .member-module {{ position: relative; margin-bottom: 6px; background: #111; border: 1px solid #1e1e1e; border-radius: 4px; overflow: hidden; transition: transform 0.2s; }}
    .member-module:hover {{ transform: translateX(2px); background: #161616; }}
    .member-bg-bar {{ position: absolute; left: 0; bottom: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--bar-color)); width: 0; animation: fillGauge 1s ease forwards; animation-delay: calc(var(--delay) + 0.5s); }}
    .member-content {{ display: flex; justify-content: space-between; align-items: center; height: 30px; padding: 0 10px; position: relative; z-index: 2; }}
    .nick {{ font-size: 0.75rem; font-weight: 800; color: #cbd5e1; text-shadow: 1px 1px 2px #000; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }}
    .count-main {{ font-size: 0.85rem; font-weight: 900; color: #fff; font-family: 'Consolas', monospace; }}

    @media (max-width: 768px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }} }}
    </style></head><body><div class="grid">"""

    for i, c in enumerate(final_data):
        theme_hex = COLOR_MAP.get(c['color'], '#fff')
        display_name = CREW_NAME_MAP.get(c['name'], c['name'])
        html += f"""
        <div class="crew-card" style="--theme-color: {theme_hex}; --delay: {i*0.08}s;">
            <div class="header">
                <div class="energy-core"></div>
                <div class="crew-title">{display_name}</div>
                <div class="header-stats">
                    <div class="stat-item"><span class="stat-label">TOTAL</span><span class="stat-value">{c['total']:,}</span></div>
                    <div class="stat-item"><span class="stat-label">AVG</span><span class="stat-value">{c['avg']:,}</span></div>
                </div>
            </div>"""
        for j, m in enumerate(c['members']):
            bar_color = get_gauge_style(m['v']['monthly'])
            w = (m['v']['monthly'] / c['max'] * 100)
            medal = ["🥇", "🥈", "🥉"][j] if j < 3 else ""
            html += f"""
            <div class="member-module">
                <div class="member-bg-bar" style="--target-width:{w}%; --bar-color: {bar_color};"></div>
                <div class="member-content">
                    <div class="nick">{medal} {m['nick']}</div>
                    <div class="count-main">{m['v']['monthly']:,}</div>
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

if __name__ == "__main__":
    with open("index.html", "w", encoding="utf-8") as f: f.write(generate_html())
    print("Optimization Complete: index.html has been updated.")