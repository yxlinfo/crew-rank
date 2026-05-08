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
    # 🚀 API 호출 시 차단을 방지하기 위해 더 완전한 헤더 정보를 추가합니다.
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year={year}&month={month:02d}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://poong.today/",
        "Origin": "https://poong.today"
    }
    # 데이터가 0으로 나올 경우를 대비해 3회 재시도 로직을 강화합니다.
    for attempt in range(3):
        try:
            res = session.get(api_url, headers=headers, timeout=10)
            if res.status_code == 200:
                json_data = res.json()
                # 'b' 값이 실제 별풍선 데이터입니다.
                m_val = json_data.get('b', 0)
                if m_val > 0: return {"monthly": m_val}
            time.sleep(1) # 재시도 간격 증가
        except Exception as e:
            print(f"Error fetching {uid}: {e}")
            time.sleep(1)
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
    # 현재 시간이 오전 10시 이전이면 전날 데이터를, 이후면 오늘 데이터를 가져옵니다.
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m = target_date.year, target_date.month
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
    session.mount('https://', adapter)
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, session)}, all_tasks))

    final_data = []
    for c_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == c_name], key=lambda x: x['v']['monthly'], reverse=True)
        total = sum(m['v']['monthly'] for m in m_list)
        final_data.append({
            "name": c_name, 
            "color": info['color'], 
            "total": total, 
            "avg": int(total/len(m_list)) if m_list else 0, 
            "members": m_list, 
            "max": max([m['v']['monthly'] for m in m_list]) if m_list and any(m['v']['monthly'] > 0 for m in m_list) else 1
        })
    # 평균 점수 기준으로 정렬
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #000; color: #f8fafc; font-family: 'Pretendard', sans-serif; padding: 10px; width: 100vw; overflow-x: hidden; }}
    body::before {{ content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-image: radial-gradient(white, rgba(255,255,255,.1) 1px, transparent 20px); background-size: 400px 400px; opacity: 0.15; pointer-events: none; }}
    
    .grid {{ display: grid; gap: 12px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; }}

    @keyframes rotateCore {{ 0% {{ transform: translate(-50%, -50%) rotate(0deg); }} 100% {{ transform: translate(-50%, -50%) rotate(360deg); }} }}
    @keyframes fadeInUp {{ 0% {{ opacity: 0; transform: translateY(20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes fillGauge {{ 0% {{ width: 0%; }} 100% {{ width: var(--target-width); }} }}

    .crew-card {{ 
        background: #0d0d0d; border: 1px solid #1a1a1a; border-top: 3px solid var(--theme-color); 
        border-radius: 14px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.6);
        position: relative; overflow: hidden; opacity: 0; 
        animation: fadeInUp 0.6s ease forwards; animation-delay: var(--delay);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .crew-card:hover {{ transform: translateY(-4px); box-shadow: 0 10px 30px rgba(0,0,0,0.8); }}

    .header {{ position: relative; padding-bottom: 15px; margin-bottom: 15px; border-bottom: 1px solid #222; text-align: center; z-index: 2; }}
    .energy-core {{
        position: absolute; top: 35%; left: 50%; width: 120px; height: 120px;
        background: radial-gradient(circle, var(--theme-color) 0%, transparent 70%);
        opacity: 0.15; filter: blur(20px); z-index: 0; pointer-events: none;
        animation: rotateCore 10s linear infinite;
    }}
    .crew-card:hover .energy-core {{ opacity: 0.3; animation-duration: 4s; filter: blur(15px); }}

    .crew-title {{ font-size: 1.3rem; font-weight: 900; color: #fff; text-shadow: 0 0 10px var(--theme-color); position: relative; z-index: 1; }}
    .crew-count {{ font-size: 0.75rem; color: #64748b; font-weight: 700; margin-top: 4px; position: relative; z-index: 1; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 5px; background: rgba(0,0,0,0.4); padding: 10px; border-radius: 10px; border: 1px solid #1a1a1a; margin-top: 10px; position: relative; z-index: 1; }}
    .stat-item {{ display: flex; justify-content: space-between; font-size: 0.75rem; }}
    .stat-label {{ color: var(--theme-color); font-weight: 800; text-transform: uppercase; }}
    .stat-value {{ color: #fff; font-weight: 900; font-family: 'Consolas', monospace; }}

    .member-module {{ position: relative; margin-bottom: 8px; background: #111; border: 1px solid #1e1e1e; border-radius: 6px; overflow: hidden; }}
    .member-bg-bar {{ position: absolute; left: 0; bottom: 0; height: 2.5px; background: linear-gradient(90deg, transparent, var(--bar-color)); width: 0; animation: fillGauge 1s ease forwards; animation-delay: calc(var(--delay) + 0.4s); }}
    .member-bg-bar::after {{ content: ''; position: absolute; right: 0; top: -2px; width: 6px; height: 6px; background: #fff; border-radius: 50%; box-shadow: 0 0 8px var(--bar-color); }}
    .member-content {{ display: flex; justify-content: space-between; align-items: center; height: 32px; padding: 0 10px; position: relative; z-index: 2; }}
    .nick {{ font-size: 0.8rem; font-weight: 800; color: #e2e8f0; text-shadow: 1px 1px 2px #000; }}
    .count-main {{ font-size: 0.9rem; font-weight: 900; color: #fff; font-family: 'Consolas', monospace; text-shadow: 1px 1px 2px #000; }}

    @media (max-width: 768px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }} }}
    </style></head><body>
    <div class="grid">"""

    for i, c in enumerate(final_data):
        theme_hex = COLOR_MAP.get(c['color'], '#fff')
        display_name = CREW_NAME_MAP.get(c['name'], c['name'])
        html += f"""
        <div class="crew-card" style="--theme-color: {theme_hex}; --delay: {i*0.1}s;">
            <div class="header">
                <div class="energy-core"></div>
                <div class="crew-title">{display_name}</div>
                <div class="crew-count">{len(c['members'])} MEMBERS</div>
                <div class="header-stats">
                    <div class="stat-item"><span class="stat-label">Total</span><span class="stat-value">{c['total']:,}</span></div>
                    <div class="stat-item"><span class="stat-label">Average</span><span class="stat-value">{c['avg']:,}</span></div>
                </div>
            </div>"""
        for j, m in enumerate(c['members']):
            bar_color = get_gauge_style(m['v']['monthly'])
            # 0% 방지를 위해 최소 너비를 1%로 설정하거나 분모가 0이 되는 것을 방지합니다.
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
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
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(generated_html)
    print("Success: 데이터 수집 및 에너지 코어 UI 생성 완료!")