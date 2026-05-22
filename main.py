import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

# [설정] 느좋 감성에 맞춘 세련된 파스텔 네온 컬러 매핑
COLOR_MAP = {
    "c-red": "#ff6b6b", "c-white": "#f1f5f9", "c-gold": "#f59e0b", 
    "c-pink": "#f472b6", "c-cyan": "#06b6d4", "c-purple": "#a855f7", 
    "c-orange": "#f97316", "c-teal": "#14b8a6", "c-lime": "#84cc16", 
    "c-green": "#22c55e"
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
    if count >= 1000000: return "#ff6b6b" 
    elif count >= 500000: return "#f59e0b"  
    elif count >= 200000: return "#38bdf8"  
    else: return "#64748b" 

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
        max_val = max([m['v']['monthly'] for m in m_list]) if m_list and any(m['v']['monthly'] > 0 for m in m_list) else 1
        final_data.append({
            "name": c_name, "color": info['color'], "total": total, 
            "avg": int(total/len(m_list)) if m_list else 0, 
            "members": m_list, "max": max_val,
            "member_count": len(m_list)
        })
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    
    body {{ 
        background: #09090b; 
        color: #f8fafc; 
        font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', sans-serif; 
        padding: 16px 8px; 
        overflow-x: hidden; 
    }}
    
    /* 🚀 3번 반영: 시선을 해치지 않는 하이엔드 마이크로 도트 매트릭스 배경 */
    body::before {{ 
        content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
        background-image: radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
        background-size: 20px 20px; pointer-events: none; z-index: 0;
    }}
    
    .header-main {{ 
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        margin-bottom: 24px; padding: 12px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px; backdrop-filter: blur(8px);
    }}
    .main-title {{ font-size: 1.25rem; font-weight: 800; letter-spacing: 4px; color: #fff; opacity: 0.9; }}
    .update-time {{ font-size: 0.65rem; color: #71717a; font-weight: 500; margin-top: 4px; letter-spacing: 1px; }}

    .grid {{ 
        display: grid; 
        gap: 12px; 
        grid-template-columns: repeat(4, 1fr); 
        padding-bottom: 40px; 
        width: 100%;
    }}

    @keyframes fadeInUp {{ 0% {{ opacity: 0; transform: translateY(10px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes fillGauge {{ 0% {{ width: 0%; }} 100% {{ width: var(--target-width); }} }}
    @keyframes pulseCore {{ 0%, 100% {{ opacity: 0.12; filter: blur(15px); transform: scale(1); }} 50% {{ opacity: 0.25; filter: blur(10px); transform: scale(1.1); }} }}
    @keyframes topRankBreathing {{ 0%, 100% {{ background: rgba(20, 20, 25, 0.7); }} 50% {{ background: rgba(25, 25, 35, 0.75); }} }}
    
    /* 🚀 1번 반영: 테두리를 순회하는 레이저 플로우 애니메이션 */
    @keyframes laserRotate {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}

    .crew-card {{ 
        background: rgba(20, 20, 25, 0.7); 
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-top: 3px solid var(--theme-color); 
        border-radius: 16px; padding: 14px; 
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.7);
        position: relative; overflow: hidden; opacity: 0; 
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: var(--delay);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        backdrop-filter: blur(10px);
    }}
    
    /* 1~3위 크루 상시 브리딩 효과 */
    .top-rank-glow {{
        animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards, topRankBreathing 4s ease-in-out infinite;
        animation-delay: var(--delay), var(--delay);
    }}
    
    /* 🚀 1번 반영: 1~3위 크루 카드 뒤쪽에 회전하는 레이저 광원 배치 가이드 트랙 */
    .top-rank-glow::before {{
        content: ""; position: absolute;
        top: -50%; left: -50%; width: 200%; height: 200%;
        background: conic-gradient(transparent, var(--theme-color), transparent 30%);
        animation: laserRotate 6s linear infinite;
        z-index: 0; pointer-events: none; opacity: 0.25;
    }}
    /* 카드 내부 콘텐츠를 감싸 레이저 선이 바깥 테두리 1px 형태로만 남기도록 마스킹 처리 */
    .top-rank-glow::after {{
        content: ""; position: absolute;
        top: 1px; left: 1px; right: 1px; bottom: 1px;
        background: #0d0d11; border-radius: 15px;
        z-index: 1; pointer-events: none; opacity: 0.93;
    }}

    .crew-card:hover {{ 
        transform: translateY(-3px); 
        border-color: var(--theme-color) !important;
        box-shadow: 0 12px 30px -5px rgba(0, 0, 0, 0.8), 0 0 15px -3px var(--theme-color);
        z-index: 10;
    }}

    .corner-rank-tab {{
        position: absolute;
        top: 0; left: 0; width: 32px; height: 32px;
        background: linear-gradient(135deg, var(--theme-color) 50%, transparent 50%);
        opacity: 0.18; z-index: 4; transition: opacity 0.25s ease;
    }}
    .crew-card:hover .corner-rank-tab {{ opacity: 0.4; }}
    
    .corner-rank-text {{
        position: absolute; top: 3px; left: 5px;
        font-family: 'SF Pro Display', 'Consolas', monospace;
        font-size: 0.58rem; font-weight: 900; color: #fff; opacity: 0.8; z-index: 5; letter-spacing: -0.5px;
    }}

    /* 레이저 마스킹 레이어 위로 콘텐츠들을 띄우기 위해 z-index 조정 */
    .header-card {{ position: relative; padding-top: 4px; padding-bottom: 10px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); text-align: left; z-index: 2; }}
    
    .energy-core {{
        position: absolute; top: -20px; left: -20px; width: 80px; height: 80px;
        background: radial-gradient(circle, var(--theme-color) 0%, transparent 80%);
        opacity: 0.12; z-index: 0; pointer-events: none;
        animation: pulseCore 4s ease-in-out infinite;
    }}

    .crew-title {{ font-size: 1.1rem; font-weight: 800; color: #fff; letter-spacing: -0.5px; padding-left: 12px; }}
    .crew-member-count {{ font-size: 0.6rem; font-weight: 700; color: #52525b; letter-spacing: 0.5px; margin-top: 1px; padding-left: 12px; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.02); padding: 8px 10px; border-radius: 10px; margin-top: 8px; border: 1px solid rgba(255,255,255,0.03); }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; }}
    .stat-label {{ color: #71717a; font-weight: 700; font-size: 0.6rem; letter-spacing: 0.5px; }}
    .stat-value {{ color: #ffffff; font-family: 'SF Pro Display', 'Consolas', monospace; font-weight: 700; font-size: 1.05rem; }}

    .member-module {{ position: relative; margin-bottom: 5px; background: rgba(255,255,255,0.01); border-radius: 8px; overflow: hidden; z-index: 2; }}
    .member-module:hover {{ background: rgba(255,255,255,0.03); }}
    
    .member-track-guide {{
        position: absolute; left: 0; bottom: 0; width: 100%; height: 1.5px;
        background: rgba(255, 255, 255, 0.03); z-index: 1;
    }}
    
    .member-bg-bar {{ 
        position: absolute; left: 0; bottom: 0; height: 1.5px; 
        background: var(--bar-color); opacity: 0.85; width: 0; 
        animation: fillGauge 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
        animation-delay: calc(var(--delay) + 0.3s); 
        z-index: 2;
    }}
    
    .member-content {{ display: flex; justify-content: space-between; align-items: center; height: 28px; padding: 0 6px; position: relative; z-index: 3; }}
    
    .nick {{ font-size: 0.68rem; font-weight: 600; color: #a1a1aa; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .count-main {{ font-size: 0.78rem; font-weight: 850; color: #ffffff; font-family: 'SF Pro Display', 'Consolas', monospace; }}

    @media (max-width: 768px) {{ 
        .grid {{ 
            grid-template-columns: repeat(2, 1fr) !important; 
            gap: 6px; 
        }}
        .main-title {{ font-size: 1.1rem; letter-spacing: 2px; }}
        .crew-title {{ font-size: 1rem; }}
        .stat-value {{ font-size: 0.95rem; }}
    }}
    </style></head><body>
    
    <div class="header-main">
        <div class="main-title">CREW RANKING</div>
        <div class="update-time">LATEST UPDATE: {now.strftime('%Y.%m.%d %H:%M')} KST</div>
    </div>

    <div class="grid">"""

    for i, c in enumerate(final_data):
        theme_hex = COLOR_MAP.get(c['color'], '#fff')
        display_name = CREW_NAME_MAP.get(c['name'], c['name'])

        # 1~3위 크루 카드에만 레이저 가이드 트랙과 브리딩 동시 부여
        top_rank_class = "top-rank-glow" if i < 3 else ""

        html += f"""
        <div class="crew-card {top_rank_class}" style="--theme-color: {theme_hex}; --delay: {i*0.06}s;">
            <div class="corner-rank-tab"></div>
            <div class="corner-rank-text">{i+1}</div>
            
            <div class="header-card">
                <div class="energy-core"></div>
                <div class="crew-title">{display_name}</div>
                <div class="crew-member-count">{c['member_count']} MEMBERS</div>
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
                <div class="member-track-guide"></div>
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