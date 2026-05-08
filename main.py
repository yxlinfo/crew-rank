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
    "광우상사": "GW",
    "씨나인": "C9",
    "이노레이블": "INOLABLE",
    "YXL": "YXL",
    "정선컴퍼니": "JS",
    "771": "771",
    "더케이": "The K",
    "GD컴퍼니": "GD",
    "문에이": "Moon A",
    "쇼케이": "Show K"
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
    
    /* 🃏 3D 효과를 위해 grid에 perspective(원근감) 부여 */
    .grid {{ display: grid; gap: 10px; grid-template-columns: repeat(4, 1fr); padding-bottom: 40px; position: relative; z-index: 1; perspective: 1200px; }}
    
    @keyframes fadeInUp {{
        0% {{ opacity: 0; transform: translateY(30px) translateZ(0); }}
        100% {{ opacity: 1; transform: translateY(0) translateZ(0); }}
    }}
    
    @keyframes firstPlacePulse {{
        0%, 100% {{ box-shadow: 0 4px 15px rgba(0,0,0,0.6), inset 0 0 0 transparent; border-color: #1a1a1a; }}
        50% {{ box-shadow: 0 8px 30px rgba(0,0,0,1), 0 0 12px var(--theme-color), inset 0 0 10px rgba(255, 255, 255, 0.05); border-color: var(--theme-color); }}
    }}
    
    @keyframes crownShine {{
        0%, 100% {{ filter: drop-shadow(0 0 2px #fbbf24); transform: rotate(0deg) scale(1); }}
        50% {{ filter: drop-shadow(0 0 8px #fbbf24) brightness(1.2); transform: rotate(-12deg) scale(1.15); }}
    }}
    
    @keyframes fillGauge {{
        0% {{ width: 0%; }}
        100% {{ width: var(--target-width); }}
    }}
    
    .crew-card {{ 
        background: #0d0d0d;
        border: 1px solid #1a1a1a;
        border-top: 3px solid var(--theme-color); 
        border-radius: 12px; padding: 12px; 
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
        position: relative; overflow: hidden; 
        will-change: transform, opacity, box-shadow; 
        
        /* 🃏 3D 틸트를 위한 필수 속성 */
        transform-style: preserve-3d;
        
        opacity: 0; 
        animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        animation-delay: var(--anim-delay);
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease, border-color 0.4s ease;
    }}
    
    /* 🃏 홀로그램 빛 반사 효과 (카드 위를 덮는 투명한 층) */
    .crew-card::after {{
        content: ""; position: absolute; top: -100%; left: -100%;
        width: 300%; height: 300%;
        background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,0.03) 45%, rgba(255,255,255,0.12) 50%, rgba(255,255,255,0.03) 55%, transparent 60%);
        transform: translate3d(0, 0, 0);
        transition: transform 0.6s cubic-bezier(0.1, 0.7, 1.0, 0.1);
        pointer-events: none; z-index: 10;
    }}
    
    .crew-card.rank-1 {{
        animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards,
                   firstPlacePulse 3s ease-in-out infinite alternate;
        animation-delay: var(--anim-delay), calc(var(--anim-delay) + 0.7s);
    }}
    
    /* 🚀 초하이엔드 마우스 호버 효과 (틸트 + 앰비언트 동시 적용) */
    .crew-card:hover {{
        /* 🃏 카드가 앞으로 튀어나오며 우측 상단을 향해 살짝 기울어짐 (3D Tilt) */
        transform: translateY(-8px) scale(1.02) rotateX(4deg) rotateY(-4deg) translateZ(15px) !important; 
        border-color: var(--theme-color) !important;
        
        /* 🌌 앰비언트 글로우: 카드 주변을 넘어 어두운 배경 전체로 뻗어나가는 거대한 테마색 빛! */
        box-shadow: 0 20px 40px rgba(0,0,0,0.9), 0 0 120px -10px var(--theme-color) !important;
        z-index: 20; 
    }}
    
    /* 🃏 마우스를 올릴 때 홀로그램 띠가 대각선으로 스윽 지나감 */
    .crew-card:hover::after {{
        transform: translate3d(50%, 50%, 0);
    }}
    
    .header {{ display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid #222; padding-bottom: 12px; margin-bottom: 14px; transform: translateZ(20px); /* 헤더도 입체적으로 살짝 뜸 */ }}
    
    .header-top {{ display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; }}
    
    .crew-title {{ font-size: 1.25rem; font-weight: 900; letter-spacing: -0.5px; color: #ffffff; text-shadow: 0 0 6px var(--theme-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%; display: flex; justify-content: center; align-items: center; }}
    
    .crown-icon {{ display: inline-block; margin-right: 6px; font-size: 1.1rem; animation: crownShine 2s infinite ease-in-out; }}
    
    .crew-count {{ font-size: 0.75rem; color: #e2e8f0; font-weight: 800; text-shadow: 0 0 3px rgba(255, 255, 255, 0.3); }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 6px; background: #080808; padding: 8px 10px; border-radius: 8px; border: 1px solid #1a1a1a; }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.65rem; color: #ffffff; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; text-shadow: 0 0 4px var(--theme-color); }}
    .stat-value {{ font-size: 1.1rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; white-space: nowrap; letter-spacing: -0.5px; text-shadow: 0 0 5px var(--theme-color); }}

    .member-module {{ position: relative; margin-bottom: 6px; background: #111111; border: 1px solid #1e1e1e; border-radius: 4px; overflow: hidden; transform: translateZ(10px); cursor: pointer; transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease; }}
    
    .member-module:hover {{ transform: translateX(2px) translateZ(15px); background: #181818; border-color: rgba(255,255,255,0.1); z-index: 2; }}
    
    .member-bg-bar {{ position: absolute; left: 0; bottom: 0; height: 2px; background: linear-gradient(90deg, transparent, var(--bar-color)); z-index: 1; width: 0; animation: fillGauge 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards; animation-delay: calc(var(--anim-delay) + 0.3s); }}
    .member-bg-bar::after {{ content: ''; position: absolute; right: 0; top: -2px; width: 6px; height: 6px; background: #ffffff; border-radius: 50%; box-shadow: 0 0 6px 1px var(--bar-color), 0 0 12px 3px var(--bar-color); }}
    
    .member-content {{ display: flex; justify-content: space-between; align-items: center; position: relative; width: 100%; height: 30px; padding: 0 10px; z-index: 2; }}
    
    .nick {{ font-size: 0.8rem; font-weight: 800; color: #e2e8f0; text-shadow: 1px 1px 2px rgba(0,0,0,1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; padding-right: 8px; letter-spacing: -0.5px; transition: color 0.2s ease, text-shadow 0.2s ease; }}
    .member-module:hover .nick {{ color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.4); }}
    .count-main {{ font-size: 0.9rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; letter-spacing: -0.5px; text-shadow: 1px 1px 2px rgba(0,0,0,1); flex-shrink: 0; }}

    /* 📱 모바일 환경 최적화 (모바일에서는 3D 및 과부하 애니메이션을 줄여 버벅임 방지) */
    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 8px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 10px; border-radius: 10px; }}
        .crew-title {{ font-size: 1.1rem; }}
        .member-content {{ height: 28px; padding: 0 8px; }}
        .nick {{ font-size: 0.75rem; letter-spacing: -0.8px; padding-right: 4px; }}
        .count-main {{ font-size: 0.85rem; letter-spacing: -0.8px; }}
        
        .member-module:hover {{ transform: translateX(1px) translateZ(0); }}
        
        /* 모바일: 3D 회전 끄기 및 앰비언트 글로우 축소 */
        .crew-card:hover {{ 
            transform: translateY(-2px) translateZ(0) !important; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.8), 0 0 40px -5px var(--theme-color) !important; 
        }}
        .crew-card::after {{ display: none; }} /* 모바일 홀로그램 OFF */
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

    for card_idx, c in enumerate(final_data):
        theme_hex = COLOR_MAP.get(c['color'], '#ffffff')
        display_name = CREW_NAME_MAP.get(c['name'], c['name'])
        
        is_first_place = (card_idx == 0)
        rank_class = " rank-1" if is_first_place else ""
        crown_html = '<span class="crown-icon">👑</span>' if is_first_place else ""
        
        anim_delay = f"{card_idx * 0.15}s"
        
        html += f"""
        <div class="crew-card{rank_class}" style="--theme-color: {theme_hex}; --anim-delay: {anim_delay};">
            <div class="header">
                <div class="header-top">
                    <div class="crew-title {c['color']}">{crown_html}{display_name}</div>
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
            bar_color = get_gauge_style(m['v']['monthly'])
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
            medal_str = f"{medal} " if medal else ""
            
            html += f"""
            <div class="member-module">
                <div class="member-bg-bar" style="--target-width:{w}%; --bar-color: {bar_color};"></div>
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
    print("Success: 초하이엔드 3D 틸트 & 앰비언트 동기화 완료!")