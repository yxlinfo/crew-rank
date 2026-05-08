import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# (이전 데이터 및 DB 로드 함수는 동일하게 유지 - COLOR_MAP 등)
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
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "point": "#ef4444"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "point": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "point": "#9ca3af"}

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
    
    /* 🚀 별빛 가루 효과 렌더링 최적화 및 레퍼런스 스타일을 위해 투명도 조절 */
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
    
    /* 🚀 카드 스타일 대공사: 반투명/블러 제거, 자로 잰 듯한 깔끔한 표 테두리 */
    .crew-card {{ 
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 10px; 
        box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.8);
        position: relative; overflow: hidden; 
        transition: transform 0.3s ease, border-color 0.3s ease;
        transform: translateZ(0); 
        will-change: transform; 
    }}
    
    .crew-card:hover {{ 
        transform: translateY(-4px) translateZ(0); 
        border-color: var(--theme-color); 
        z-index: 10; 
    }}
    
    .header {{ display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid #262626; padding-bottom: 10px; margin-bottom: 12px; }}
    
    /* 🎯 크루 이름 중앙 배치 및 네온 효과 제거, 깔끔한 폰트 */
    .header-top {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; }}
    .crew-title {{ 
        font-size: 1.15rem; font-weight: 900; letter-spacing: -0.5px; 
        color: var(--theme-color);
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;
    }}
    .crew-count {{ font-size: 0.7rem; color: #64748b; font-weight: 700; opacity: 1; }}
    
    /* 🚀 통계 표 스타일: 자로 잰 듯한 깔끔한 행 */
    .header-stats {{ display: flex; flex-direction: column; gap: 6px; background: #080808; padding: 8px 10px; border-radius: 6px; border: 1px solid #1a1a1a; }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.65rem; color: var(--theme-color); font-weight: 800; letter-spacing: 1px; opacity: 1; text-transform: uppercase; }}
    .stat-value {{ font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; white-space: nowrap; letter-spacing: -0.5px; }}

    /* 🚀 레퍼런스 표 스타일로 대공사: 1위 일본 5699 완벽 구현 */
    .member-module {{ 
        display: flex; /* 가로 배열: 순위, 내용 */
        align-items: center;
        position: relative; margin-bottom: 0; padding: 8px 10px; 
        background: transparent;
        border-radius: 0; border: none; border-bottom: 1px solid #1a1a1a; /* 표의 행 같은 느낌 */
        transition: background 0.2s ease; 
        transform: translateZ(0);
    }}
    .member-module:hover {{ background: #1a1a1a; }} /* 행 전체 호버 */
    
    /* 레퍼런스 스타일: 순위 열 (1위) */
    .member-rank-col {{
        width: 25px; text-align: left;
        font-size: 0.75rem; font-weight: 700; color: #64748b; /* '1위' 색상 */
        flex-shrink: 0;
    }}
    
    /* 레퍼런스 스타일: 그래프 및 내용 열 (일본 5699) */
    .member-bar-container {{ 
        flex-grow: 1; position: relative; height: 18px; /* 바의 높이를 높여 글씨가 들어가도록 설정 */
        background: #1a1a1a; border-radius: 3px; overflow: hidden;
    }}
    .member-bar-fill {{ 
        height: 100%; border-radius: 3px; 
        position: absolute; left: 0; top: 0;
        will-change: transform;
    }}
    
    /* 레퍼런스 스타일: 바 위에 올라가는 텍스트 (완벽한 타이포그래피) */
    .member-bar-content {{
        display: flex; justify-content: space-between; align-items: center;
        position: absolute; left: 0; top: 0; width: 100%; height: 100%;
        padding: 0 6px; z-index: 2; /* 바 위에 올라가야 함 */
    }}
    
    /* 레퍼런스 스타일: 이름 (일본) */
    .nick {{ 
        font-size: 0.75rem; font-weight: 700; color: white; /* 어두운 바에서도 잘 보이도록 흰색 */
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0; letter-spacing: -0.8px; padding-right: 2px;
    }}
    
    /* 레퍼런스 스타일: 점수 (5699) */
    .count-main {{ 
        font-size: 0.85rem; font-weight: 900; color: #ffffff; flex-shrink: 0; font-family: 'Consolas', monospace; letter-spacing: -0.8px;
    }}
    
    /* 레퍼런스 스타일: 오늘 풍은 깔끔하게 점수 옆에 작게 (+123) */
    .count-today {{ font-size: 0.65rem; font-weight: 800; white-space: nowrap; margin-left: 3px; }}

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
        # 🚀 멤버 목록: 레퍼런스 스타일 완벽 구현
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['v']['monthly'])
            # 너비 계산
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            # 오늘 풍 깔끔하게 점수 옆에 붙임
            today = f'<span class="count-today" style="color:{style["point"]}">(+{m["v"]["daily"]:,})</span>' if m['v']['daily'] > 0 else ''
            
            html += f"""
            <div class="member-module">
                <div class="member-rank-col">{i + 1}</div>
                <div class="member-bar-container">
                    <div class="member-bar-fill" style="width:{w}%; background:${style['grad']};"></div>
                    <div class="member-bar-content">
                        <div class="nick">${m['nick']}</div>
                        <div class="count-main">${m['v']['monthly']:,}${today}</div>
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
    print("Success: 레퍼런스 완벽 구현 대시보드 갱신 완료!")