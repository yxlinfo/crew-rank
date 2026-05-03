import sqlite3
import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

COLOR_MAP = {
    "c-red": "#f87171", "c-white": "#f8fafc", "c-gold": "#fbbf24", 
    "c-pink": "#f472b6", "c-cyan": "#22d3ee", "c-purple": "#c084fc", 
    "c-orange": "#fb923c", "c-teal": "#2dd4bf", "c-lime": "#a3e635", 
    "c-green": "#4ade80"
}

def load_config_from_db():
    """SQLite DB에서 크루 및 멤버 데이터를 읽어옵니다."""
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
    # 1. DB에서 설정 로드
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
    body {{ background: #0b1120; color: #f8fafc; font-family: 'Pretendard', -apple-system, sans-serif; padding: 15px; width: 100vw; overflow-x: hidden; }}
    
    .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: rgba(30, 41, 59, 0.7); padding: 10px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); backdrop-filter: blur(10px); }}
    
    .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(3, 1fr); padding-bottom: 60px; }}
    
    .crew-card {{ 
        background: linear-gradient(145deg, #131c2d, #0d131f);
        border: 1px solid #1e293b; border-top: 3px solid var(--theme-color); border-radius: 14px; 
        padding: 16px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4); position: relative; overflow: hidden;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); z-index: 1;
    }}
    .crew-card::before {{
        content: ''; position: absolute; top: -40%; left: -20%; width: 150%; height: 150%;
        background: radial-gradient(circle at 50% 0%, var(--theme-color), transparent 50%); opacity: 0.04; pointer-events: none; transition: opacity 0.3s ease;
    }}
    .crew-card:hover {{ 
        transform: translateY(-8px) scale(1.02); box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8), 0 0 25px var(--theme-color); 
        border-color: var(--theme-color); filter: brightness(1.15); z-index: 10; 
    }}
    .crew-card:hover::before {{ opacity: 0.15; }}
    
    .header {{ display: flex; flex-direction: column; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 14px; margin-bottom: 18px; z-index: 1; position: relative; }}
    .header-top {{ display: flex; justify-content: space-between; align-items: center; gap: 5px; }}
    .crew-title {{ font-size: 1.3rem; font-weight: 900; letter-spacing: -0.5px; text-shadow: 0 0 8px rgba(255,255,255,0.2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }}
    .crew-count {{ font-size: 0.85rem; color: #64748b; font-weight: 700; white-space: nowrap; flex-shrink: 0; }}
    
    .header-stats {{ display: flex; flex-direction: column; gap: 8px; background: rgba(0, 0, 0, 0.3); padding: 12px 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03); box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); }}
    .stat-item {{ display: flex; justify-content: space-between; align-items: center; width: 100%; }}
    .stat-label {{ font-size: 0.75rem; color: var(--theme-color); opacity: 0.85; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; white-space: nowrap; }}
    .stat-value {{ font-size: 1.25rem; font-weight: 900; color: #ffffff; font-family: 'Consolas', monospace; text-shadow: 0 0 10px var(--theme-color), 0 0 20px rgba(0,0,0,0.4); white-space: nowrap; }}

    .member-module {{ position: relative; margin-bottom: 12px; padding: 12px 14px 22px 14px; background: rgba(15, 23, 42, 0.4); border-radius: 10px; border: 1px solid rgba(255,255,255,0.02); z-index: 1; transition: transform 0.2s, background 0.2s; }}
    .member-module:hover {{ transform: scale(1.02); background: rgba(255,255,255,0.05); }}
    
    .member-info {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; gap: 4px; }}
    .nick {{ font-size: 0.95rem; font-weight: 700; color: #cbd5e1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0; letter-spacing: -0.5px; }}
    .count-main {{ font-size: 1.05rem; font-weight: 900; color: #ffffff; flex-shrink: 0; font-family: 'Consolas', monospace; letter-spacing: -0.5px; }}

    .bar-container {{ position: relative; width: 100%; height: 6px; background: rgba(0, 0, 0, 0.4); border-radius: 4px; box-shadow: inset 0 1px 2px rgba(0,0,0,0.5); }}
    .bar-fill {{ height: 100%; border-radius: 4px; box-shadow: 0 0 5px rgba(255,255,255,0.2); }}
    .count-today {{ font-size: 0.75rem; font-weight: 800; position: absolute; left: 50%; transform: translateX(-50%); bottom: -18px; white-space: nowrap; }}

    @media (max-width: 768px) {{ 
        .grid {{ grid-template-columns: repeat(2, 1fr); gap: 6px; }}
        body {{ padding: 6px; }}
        .crew-card {{ padding: 8px; border-radius: 10px; }}
        .header {{ padding-bottom: 8px; margin-bottom: 10px; gap: 6px; }}
        .crew-title {{ font-size: 1rem; }}
        .crew-count {{ font-size: 0.7rem; }}
        .header-stats {{ padding: 8px 10px; gap: 4px; }}
        .stat-label {{ font-size: 0.65rem; }}
        .stat-value {{ font-size: 0.9rem; letter-spacing: -0.5px; }}
        .member-module {{ padding: 8px 6px 18px 6px; margin-bottom: 8px; border-radius: 8px; }}
        .member-info {{ margin-bottom: 6px; gap: 2px; }}
        .nick {{ font-size: 0.7rem; letter-spacing: -0.8px; padding-right: 2px; }}
        .count-main {{ font-size: 0.75rem; letter-spacing: -0.8px; padding-left: 0; }}
        .count-today {{ font-size: 0.65rem; bottom: -15px; letter-spacing: -0.5px; }}
    }}

    .c-red {{ color: #f87171; }} .c-white {{ color: #f8fafc; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 1rem; font-weight: 900; color: #e2e8f0; letter-spacing: 1px;">CREW<span style="color:#38bdf8;">DASHBOARD</span></div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 4px 10px; border-radius: 12px;">{now.strftime('%y.%m.%d %H:%M')}</div>
        </div>
        <div class="grid">"""

    for c in final_data:
        theme_hex = COLOR_MAP.get(c['color'], '#ffffff')
        html += f"""
        <div class="crew-card" style="--theme-color: {theme_hex};">
            <div class="header">
                <div class="header-top">
                    <div class="crew-title {c['color']}">{c['name']}</div>
                    <div class="crew-count">{len(c['members'])} MEM</div>
                </div>
                <div class="header-stats">
                    <div class="stat-item">
                        <span class="stat-label">Total</span>
                        <span class="stat-value">{c['total']:,}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Avg</span>
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

def save_chart_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 950, 'height': 3500}, device_scale_factor=2)
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