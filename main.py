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

def fetch_data(uid, year, month, day, session):
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
                d_list = json_data.get('d', [])
                if not d_list:
                    d_val = 0
                else:
                    d_val = next((i.get('b', 0) for i in d_list if int(i.get('d', -1)) == int(day)), 0)
                return {"monthly": m_val, "daily": d_val}
            time.sleep(0.5)
        except: 
            time.sleep(0.5)
    return {"monthly": 0, "daily": 0}

def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)"}

def generate_html():
    crews_config = load_config_from_db()
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m, d = target_date.year, target_date.month, target_date.day
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, d, session)}, all_tasks))

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
        border-radius: 12px; padding: 10px; 
        box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.8);
        position: relative; overflow: hidden; 
        transform: translateZ(0); 
        will-change: transform; 
    }}
    
    .header {{ display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid #262626; padding-bottom: 10px; margin-bottom: 12px; }}
    
    .header-top {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; }}
    .crew-title {{ 
        font-size: 1.15rem; font-weight: 900; letter-spacing: -0.5px; 
        color: var(--theme-color);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;
    }}
    .crew-count {{ font-size: 0.7rem; color: #64748b; font-weight: 700; opacity: 1; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 6px; background: #080808; padding: 8px 10px; border-radius: 6px; border: 1px solid #1a1a1a; }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.65rem; color: var(--theme-color); font-weight: 800; letter-spacing: 1px; opacity: 1; text-transform: uppercase; }}
    .stat-value {{ font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; white-space: nowrap; letter-spacing: -0.5px; }}

    .member-module {{ 
        display: flex; align-items: center;
        position: relative; margin-bottom: 5px; padding: 0; 
        background: transparent;
        transform: translateZ(0);
    }}
    
    .member-rank-col {{
        width: 20px; text-align: center;
        font-size: 0.75rem; font-weight: 800; color: #94a3b8; 
        flex-shrink: 0; margin-right: 4px;
    }}
    
    .member-info-col {{ 
        flex-grow: 1; position: relative; height: 26px; 
        background: #1a1a1a;
        border-radius: 4px; overflow: hidden;
        border: 1px solid #262626;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.5);
    }}
    
    .member-bg-bar {{ 
        height: 100%; border-radius: 3px; 
        position: absolute; left: 0; top: 0;
        opacity: 1; 
        border-right: 1px solid rgba(255,255,255,0.4);
        box-shadow: inset 0 0 5px rgba(0,0,0,0.2);
    }}
    
    .member-content {{
        display: flex; justify-content: space-between; align-items: center;
        position: absolute; left: 0; top: 0; width: 100%; height: 100%;
        padding: 0 8px; z-index: 2; 
    }}
    
    /* 🚀 왼쪽 그룹 (닉네임 + 증가분)을 묶어서 침범 방지 */
    .left-group {{
        display: flex; align-items: center; gap: 6px;
        flex: 1; min-width: 0; /* 모바일에서 글씨가 넘치면 말줄임표(...)를 만들기 위한 필수 요소 */
        margin-right: 8px; /* 우측 누적별풍선과의 여백 */
    }}
    
    .nick {{ 
        font-size: 0.75rem; font-weight: 700; color: #ffffff; 
        text-shadow: 0 1px 2px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.8);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        flex-shrink: 1; /* 자리가 부족하면 닉네임이 우선적으로 줄어듦 */
        letter-spacing: -0.5px;
    }}
    
    /* 🚀 새 위치로 이사 온 당일 증가분 */
    .count-today {{ 
        font-size: 0.65rem; font-weight: 800; color: #4ade80; 
        font-family: 'Consolas', monospace; letter-spacing: -0.5px;
        text-shadow: 0 1px 2px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.8);
        flex-shrink: 0; /* 증가분 숫자는 절대 찌그러지지 않음 */
    }}
    
    /* 🚀 완벽한 오와 열을 맞추게 된 누적 별풍선 */
    .count-main {{ 
        font-size: 0.85rem; font-weight: 900; color: #ffffff; 
        font-family: 'Consolas', monospace; letter-spacing: -0.5px;
        text-shadow: 0 1px 2px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.8);
        flex-shrink: 0; text-align: right; /* 항상 우측 끝에 고정 */
    }}

    /* 📱 모바일 환경 최적화 (2열 및 겹침 방지) */
    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 6px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 8px; border-radius: 10px; }}
        .crew-title {{ font-size: 1rem; }}
        .stat-value {{ font-size: 0.95rem; }}
        
        .member-rank-col {{ width: 16px; font-size: 0.65rem; margin-right: 2px; }}
        .left-group {{ gap: 3px; margin-right: 4px; }}
        
        .nick {{ font-size: 0.7rem; letter-spacing: -0.8px; }}
        .count-today {{ font-size: 0.6rem; letter-spacing: -0.8px; }}
        .count-main {{ font-size: 0.75rem; letter-spacing: -0.8px; }}
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
            style = get_gauge_style(m['v']['monthly'])
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            
            # 메달 문자열 깔끔하게 처리
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
            medal_str = f"{medal} " if medal else ""
            
            # 당일 증가분 텍스트
            today = f'<div class="count-today">+{m["v"]["daily"]:,}</div>' if m['v']['daily'] > 0 else ''
            
            html += f"""
            <div class="member-module">
                <div class="member-rank-col">{i + 1}</div>
                <div class="member-info-col">
                    <div class="member-bg-bar" style="width:{w}%; background:{style['grad']};"></div>
                    <div class="member-content">
                        <div class="left-group">
                            <div class="nick">{medal_str}{m['nick']}</div>
                            {today}
                        </div>
                        <div class="count-main">{m['v']['monthly']:,}</div>
                    </div>
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

if __name__ == "__main__":
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: 
        f.write(generated_html)
    print("Success: 정렬 문제 및 모바일 간섭 해결 완료!")