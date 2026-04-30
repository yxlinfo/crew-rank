import requests
import time
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

# [1. crews_config 및 fetch_data, get_gauge_style 로직은 기존과 동일]
crews_config = {
    "광우상사": {"color": "c-red", "members": {"파미": "hhyounooo", "아이빈": "iluvbin", "이온♥": "qor0919", "임주연♥": "ektnrnrgml", "미디♡.": "kkok7816", "가을이♡": "fall1128", "원영님♥": "yui0902", "서윤슬@": "dbstmf3497", "맹이.zip": "hellparty1", "안둥♥": "andoong0227", "미숑.♥": "pms999"}},
    "씨나인": {"color": "c-white", "members": {"체온_♡": "leeso0403", "혜루찡": "epsthddus", "쁠리vvely": "alwl1047", "초초": "chocho12", "[윤이솔]": "oosuoey", "BJ채리": "lcy011027", "애순이": "yunyeson3015", "하이희야♡": "jkmjkm1236", "인지연JYEON": "dlswldus107", "아윤♡": "ayoona", "리하♥": "ksdd7856", "#초린": "dhtnqls1238", "히나_♥": "luaa0803", "연두": "luaa0803"}},
    "더케이": {"color": "c-gold", "members": {"! 채채": "dreamch77", "퀸다미♧": "damikim", "[BJ]에디양": "yhm777", "차시월": "kcktksal12", "소냥이에요": "ssoi0911", "엘♥": "elleeayo", "한슬댕": "eeseuu", "푸린♡": "pu1030", "채리나": "sso123", "강한빛♡": "vvkk80", "포카린": "kerin0308", "지아콩": "mxxjiaa2358", "우아한♡우와": "onevley77"}},
    "정선컴퍼니": {"color": "c-pink", "members": {"♡김베리♡": "hhy789", "나의유주♥": "youxzu", "김규리♥": "xgyuri2", "서이안": "lllloq", "윤수♥": "whdbstn7", "햇동이♥": "kariveal", "윤세빈♥": "yuyu0929", "율비♡": "yulbee", "채보미=3=": "coqhal1992", "♥백설♥": "yin3745", "유서림♥": "elixxir", "당신의채안♥": "your75", "아유님♥": "seola1420"}},
    "YXL": {"color": "c-cyan", "members": {"리윤_♥": "sladk51", "후잉♥": "jaeha010", "냥냥수주": "star49", "류서하♥": "smkim82372", "#율무": "offside629", "하랑짱♥": "asy1218", "미로。": "fhwm0602", "유나연º-º": "jeewon1202", "김유정S2": "tkek55", "소다♥": "zbxlzzz", "백나현": "wk3220", "서니_♥": "iluvpp", "ZO아름♡": "ahrum0912", "너의˚멜로디": "meldoy777"}},
    "이노레이블": {"color": "c-purple", "members": {"꽃부기♥": "flowerboogie", "#누리-": "nooree", "이월♥": "bc3yu2fl", "설탱♥": "baek224983", "애지니♡": "yeeeee00", "밤비♥": "sonhj2244", "리에♡": "lia0322", "이리원♥": "nrini1213", "히냥이♥": "qkrrkgml1231", "설인_♥": "sul0509", "연보민": "duzzangg", "유복이!": "ekffl1031", "[SO]박소연": "ss2312"}},
    "GD컴퍼니": {"color": "c-orange", "members": {"설인아님♥": "inaa04", "♥유현♥": "kyhkyh825", "E윤아♡": "jssisabel", "쥬브리": "dbswn2312", "은아린!!": "pinepine0", "아링": "jungym0116", "해리님♥": "haeri0324"}},
    "쇼케이": {"color": "c-teal", "members": {"송화양": "sejin453", "＠서단": "banghyo9724", "쏘피♥": "1frogmonkey1", "도하정♥": "pig24680", "♥제니♥": "dooly44", "송유이♥": "dm0229", "재온ly": "awdrgy45", "도예빈♥": "doyebean", "정인♥": "wjddls10", "한유나♥": "xodrnaka95", "이로♥": "akikxxo", "@유톨": "imyutol", "유이나.♡": "todayjm", "새봄_♡": "fm0307"}},
    "문에이": {"color": "c-lime", "members": {"♥채화": "tnwls8137", "서언수": "talmud98", "박재열": "woduf1365", "하임*": "y0urxixi", "#다인": "mrk9178", "뮤엘♥": "qordjrxhfl", "천시아S2": "kakaak2457", "미지수♥": "zxll6721", "현강림2": "hkl1102", "설현미": "wkdalgusrla", "슈나♥": "dbstldbs", "강형민이": "hhmmnn", "E-;이은♥": "salgu1004", ".장지민": "lillillll", "예니__": "songlime1126"}},
    "771": {"color": "c-green", "members": {"예란": "jyssing", "나래~~~": "narae282", "박예솜:)": "tgqnpji1xc", "이밍+♥": "aighty9", "지숙♥_.": "uyrt8888", "푸글리♡": "vnfmadl93", "이나율♥": "cmj20822", "한채아♥": "snfkddl1024", "김봄비": "bombbi"}}
}

def fetch_data(uid, year, month, day):
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year={year}&month={month}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://poong.today/"}
    for _ in range(5):
        try:
            res = requests.get(api_url, headers=headers, timeout=15)
            if res.status_code == 200:
                json_data = res.json()
                monthly = json_data.get('b', 0)
                daily = 0
                daily_list = json_data.get('d', []) 
                for item in daily_list:
                    if str(item.get('d')) == str(day):
                        daily = item.get('b', 0)
                        break
                time.sleep(0.1)
                return {"monthly": monthly, "daily": daily}
            time.sleep(1)
        except: time.sleep(1)
    return {"monthly": 0, "daily": 0}

def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "point": "#ef4444"}
    elif count >= 800000: return {"grad": "linear-gradient(90deg, #9a3412, #f97316)", "point": "#f97316"}
    elif count >= 400000: return {"grad": "linear-gradient(90deg, #a16207, #eab308)", "point": "#eab308"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #166534, #22c55e)", "point": "#22c55e"}
    elif count >= 100000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "point": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "point": "#9ca3af"}

def generate_html():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    y, m, d = now.year, now.month, now.day
    
    all_tasks = []
    for crew, info in crews_config.items():
        for nick, uid in info['members'].items():
            all_tasks.append({'crew': crew, 'nick': nick, 'uid': uid})

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda t: {**t, 'v': fetch_data(t['uid'], y, m, d)}, all_tasks))

    final_data = []
    for crew_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == crew_name], key=lambda x: x['v']['monthly'], reverse=True)
        total = sum(m['v']['monthly'] for m in m_list)
        final_data.append({"name": crew_name, "color": info['color'], "total": total, "avg": int(total/len(m_list)) if m_list else 0, "member_count": len(m_list), "members": m_list, "max": m_list[0]['v']['monthly'] if m_list else 1})

    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ 
        background: #0f172a; color: #f8fafc; font-family: sans-serif; 
        padding: 20px; width: 900px; /* 900px 고정 */
        margin: 0 auto; /* 중앙 정렬 핵심 */
        -webkit-font-smoothing: antialiased;
    }}
    
    .top-bar {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
    
    .grid {{ display: grid; gap: 15px; grid-template-columns: repeat(3, 1fr); padding-bottom: 40px; }}
    .crew-card {{ background: #1e293b; border: 1px solid #475569; border-radius: 12px; padding: 12px 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #334155; padding-bottom: 8px; margin-bottom: 12px; }}
    .crew-title {{ font-size: 1.2rem; font-weight: 900; margin-top: -2px; }}
    .stats {{ text-align: right; font-size: 0.85rem; color: #cbd5e1; font-weight: 700; line-height: 1.4; }}
    
    .member-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; height: 32px; position: relative; }} 
    .nick {{ width: 110px; font-size: 0.95rem; font-weight: 700; color: #f1f5f9; white-space: nowrap; }}
    .bar-bg {{ flex-grow: 1; background: #334155; height: 7px; border-radius: 4px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 4px; }}
    
    .count-container {{ 
        width: 110px; text-align: right; 
        height: 32px; position: relative;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .count-main {{ font-size: 1.05rem; font-weight: 900; color: #ffffff; line-height: 32px; }}
    .count-today {{ font-size: 0.78rem; font-weight: 800; position: absolute; bottom: -11px; right: 0; white-space: nowrap; }}
    
    .c-red {{ color: #f87171; }} .c-white {{ color: #fff; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head>
    <body>
        <div class="top-bar">
            <div style="font-size: 1rem; font-weight: 800;">UPDATED: {now.strftime('%Y.%m.%d %H:%M')}</div>
            <div style="font-size: 0.8rem; color: #64748b;">DATA SOURCE: POONG.TODAY</div>
        </div>
        <div class="grid">"""

    for c in final_data:
        html += f"""
        <div class="crew-card">
            <div class="header">
                <div class="crew-title {c['color']}">{c['name']} <span style="font-size:0.75em; opacity:0.8;">({c['member_count']}명)</span></div>
                <div class="stats">TOTAL: {c['total']:,}<br>AVG: {c['avg']:,}</div>
            </div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['v']['monthly'])
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "&nbsp;&nbsp;&nbsp;"
            w = (m['v']['monthly'] / c['max'] * 100) if c['max'] > 0 else 0
            today_label = f'<div class="count-today" style="color:{style["point"]}">(+{m["v"]["daily"]:,})</div>' if m['v']['daily'] > 0 else ''
            html += f"""
            <div class="member-row">
                <div class="nick">{medal}{m['nick']}</div>
                <div class="bar-bg"><div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div></div>
                <div class="count-container">
                    <div class="count-main">{m['v']['monthly']:,}</div>
                    {today_label}
                </div>
            </div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

def save_chart_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 캡처 환경 설정: device_scale_factor를 높여 선명도 유지
        context = browser.new_context(viewport={'width': 900, 'height': 3000}, device_scale_factor=2)
        page = context.new_page()
        page.set_content(html_content)
        time.sleep(3)
        # 하단 잘림 방지: full_page=True를 사용하여 실제 콘텐츠 끝까지 캡처
        page.screenshot(path="chart.png", full_page=True, animations="disabled")
        browser.close()

if __name__ == "__main__":
    generated_html = generate_html()
    with open("index.html", "w", encoding="utf-8") as f: f.write(generated_html)
    try:
        save_chart_image(generated_html)
        print("Success")
    except Exception as e: print(f"Error: {e}")