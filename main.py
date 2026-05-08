import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# 크루별 테마 색상 맵핑
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

# 🚀 최적화된 데이터 수집 (일일 증가분 제거, 월간 총합만 광속 수집)
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

def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #7f1d1d, #ef4444)"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)"}
    else: return {"grad": "linear-gradient(90deg, #374151, #9ca3af)"}

def generate_html():
    crews_config = load_config_from_db()
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    target_date = now - timedelta(days=1) if now.hour < 10 else now
    y, m = target_date.year, target_date.month
    
    # 🚀 커넥션 풀링으로 통신 랙 제거
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    
    all_tasks = [{'crew': c, 'nick': n, 'uid': u} for c, info in crews_config.items() for n, u in info['members'].items()]
    
    # 🚀 20명 동시 수집으로 속도 극대화
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
    
    /* 🌌 배경 별빛 효과 (GPU 가속) */
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
    
    /* 💻 PC 4열 레이아웃 */
    .grid {{ display: grid; gap: 10px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; position: relative; z-index: 1; }}
    
    .crew-card {{ 
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 12px; 
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.9);
        position: relative; overflow: hidden; 
        transform: translateZ(0); 
        will-change: transform; 
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

    /* 💎 럭셔리 바 차트 (선택 느낌 호버 효과 포함) */
    .member-module {{ 
        position: relative; margin-bottom: 8px; 
        transform: translateZ(0);
        cursor: pointer; 
        transition: transform 0.2s ease, box-shadow 0.2s ease; 
        border-radius: 6px;
    }}
    
    .member-module:hover {{
        transform: translateX(4px) translateZ(0); 
        z-index: 2; 
    }}
    
    .member-info-col {{ 
        width: 100%; position: relative; height: 28px; 
        background: #111111;
        border-radius: 6px; overflow: hidden;
        border: 1px solid #222;
        box-shadow: inset 0 2px 5px rgba(0,0,0,0.8);
        transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    
    /* 호버 시 왼쪽 테마 컬러 포인트 생성 및 미세 하이라이트 */
    .member-module:hover .member-info-col {{
        background: rgba(255,255,255,0.06); 
        border-color: rgba(255,255,255,0.15); 
        box-shadow: inset 3px 0 0 0 var(--theme-color), 
                    inset 0 2px 5px rgba(0,0,0,0.8); 
    }}
    
    .member-bg-bar {{ 
        height: 100%; border-radius: 5px; 
        position: absolute; left: 0; top: 0;
        border-right: 1px solid rgba(255,255,255,0.2);
        box-shadow: inset 0 0 10px rgba(0,0,0,0.4);
    }}
    
    .member-content {{
        display: flex; justify-content: space-between; align-items: center;
        position: absolute; left: 0; top: 0; width: 100%; height: 100%;
        padding: 0 10px; z-index: 2; 
    }}
    
    .nick {{ 
        font-size: 0.8rem; font-weight: 800; color: #ffffff; 
        text-shadow: 1px 1px 4px rgba(0,0,0,1);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        flex: 1; padding-right: 8px; letter-spacing: -0.5px;
        transition: color 0.2s ease, text-shadow 0.2s ease;
    }}
    
    /* 호버 시 이름 텍스트 화이트 글로우 효과 (막대 자체는 변하지 않음) */
    .member-module:hover .nick {{
        color: #ffffff;
        text-shadow: 0 0 8px #ffffff, 1px 1px 4px rgba(0,0,0,1); 
    }}
    
    .count-main {{ 
        font-size: 0.9rem; font-weight: 900; color: #ffffff; 
        font-family: 'Consolas', monospace; letter-spacing: -0.5px;
        text-shadow: 1px 1px 4px rgba(0,0,0,1);
        flex-shrink: 0;
    }}

    /* 📱 모바일 2열 레이아웃 최적화 */
    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 10px; border-radius: 10px; }}
        .crew-title {{ font-size: 1.05rem; }}
        
        .member-info-col {{ height: 26px; }}
        .member-content {{ padding: 0 8px; }}
        .nick {{ font-size: 0.75rem; letter-spacing: -0.8px; padding-right: 4px; }}
        .count-main {{ font-size: 0.85rem; letter-spacing: -0.8px; }}
        
        .member-module:hover {{
            transform: translateX(3px) translateZ(0);
        }}
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
            
            # 상위 3명 메달 표시 (순위 숫자 대체)
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
            medal_str = f"{medal} " if medal else ""
            
            html += f"""
            <div class="member-module">
                <div class="member-info-col">
                    <div class="member-bg-bar" style="width:{w}%; background:{style['grad']};"></div>
                    <div class="member-content">
                        <div class="nick">{medal_str}{m['nick']}</div>
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
    print("Success: 최종 럭셔리 대시보드 갱신 완료!")