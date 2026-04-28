import requests
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright  # 추가

# 1. 크루 명단 설정 (기존과 동일)
crews_config = {
    "광우상사": {"color": "c-red", "members": {"파미": "hhyounooo", "아이빈": "iluvbin", "이온♥": "qor0919", "임주연♥": "ektnrnrgml", "미디♡.": "kkok7816", "가을이♡": "fall1128", "원영님♥": "yui0902", "서윤슬@": "dbstmf3497", "맹이.zip": "hellparty1", "안둥♥": "andoong0227", "미숑.♥": "pms999"}},
    "씨나인": {"color": "c-white", "members": {"체온_♡": "leeso0403", "혜루찡": "epsthddus", "쁠리vvely": "alwl1047", "초초": "chocho12", "[윤이솔]": "oosuoey", "BJ채리": "lcy011027", "애순이": "yunyeson3015", "하이희야♡": "jkmjkm1236", "인지연JYEON": "dlswldus107", "아윤♡": "ayoona", "리하♥": "ksdd7856", "#초린": "dhtnqls1238", "히나_♥": "luaa0803"}},
    "더케이": {"color": "c-gold", "members": {"! 채채": "dreamch77", "앙체리♥": "tkxkd9187", "퀸다미♧": "damikim", "[BJ]에디양": "yhm777", "차시월": "kcktksal12", "유더♥": "wgdbtjs3715", "소냥이에요": "ssoi0911", "엘♥": "elleeayo", "한슬댕": "eeseuu", "푸린♡": "pu1030", "채리나": "sso123", "강한빛♡": "vvkk80", "포카린": "kerin0308", "지아콩": "mxxjiaa2358", "우아한♡우와": "onevley77"}},
    "정선컴퍼니": {"color": "c-pink", "members": {"♡김베리♡": "hhy789", "나의유주♥": "youxzu", "김규리♥": "xgyuri2", "바미♡": "gys01083", "윤수♥": "whdbstn7", "햇동이♥": "kariveal", "윤세빈♥": "yuyu0929", "율비♡": "yulbee", "채보미=3=": "coqhal1992", "♥백설♥": "yin3745", "유서림♥": "elixxir", "한아영♡": "knmy1127"}},
    "YXL": {"color": "c-cyan", "members": {"리윤_♥": "sladk51", "후잉♥": "jaeha010", "냥냥수주": "star49", "류서하♥": "smkim82372", "#율무": "offside629", "하랑짱♥": "asy1218", "미로。": "fhwm0602", "유나연º-º": "jeewon1202", "김유정S2": "tkek55", "소다♥": "zbxlzzz", "백나현": "wk3220", "서니_♥": "iluvpp", "ZO아름♡": "ahrum0912", "너의˚멜로디": "meldoy777"}},
    "이노레이블": {"color": "c-purple", "members": {"꽃부기♥": "flowerboogie", "#누리-": "nooree", "이월♥": "bc3yu2fl", "설탱♥": "baek224983", "애지니♡": "yeeeee00", "밤비♥": "sonhj2244", "리에♡": "lia0322", "이리원♥": "nrini1213", "히냥이♥": "qkrrkgml1231", "설인_♥": "sul0509", "연보민": "duzzangg", "유복이!": "ekffl1031", "[SO]박소연": "ss2312"}},
    "GD컴퍼니": {"color": "c-orange", "members": {"설인아님♥": "inaa04", "♥유현♥": "kyhkyh825", "E윤아♡": "jssisabel", "쥬브리": "dbswn2312", "은아린!!": "pinepine0", "아링": "jungym0116", "해리님♥": "haeri0324"}},
    "쇼케이": {"color": "c-teal", "members": {"송화양": "sejin453", "＠서단": "banghyo9724", "쏘피♥": "1frogmonkey1", "도하정♥": "pig24680", "♥제니♥": "dooly44", "송유이♥": "dm0229", "재온ly": "awdrgy45", "도예빈♥": "doyebean", "정인♥": "wjddls10", "한유나♥": "xodrnaka95", "이로♥": "akikxxo", "@유톨": "imyutol", "유이나.♡": "todayjm", "새봄_♡": "fm0307"}},
    "문에이": {"color": "c-lime", "members": {"표냥이♥": "pgysvt", "서언수": "talmud98", "박재열": "woduf1365", "하임*": "y0urxixi", "#다인": "mrk9178", "뮤엘♥": "qordjrxhfl", "천시아S2": "kakaak2457", "미지수♥": "zxll6721", "현강림2": "hkl1102", "설현미": "wkdalgusrla", "슈나♥": "dbstldbs", "김하연님♥": "hgkdusy", "강형민이": "hhmmnn", "E-;이은♥": "salgu1004", ".장지민": "lillillll", "예니__": "songlime1126"}},
    "771": {"color": "c-green", "members": {"예란": "jyssing", "나래~~~": "narae282", "박예솜:)": "tgqnpji1xc", "이밍+♥": "aighty9", "지숙♥_.": "uyrt8888", "푸글리♡": "vnfmadl93", "이나율♥": "cmj20822", "한채아♥": "snfkddl1024"}}
}

now = datetime.now()
target_year, target_month = now.year, now.month

def fetch_b_value(uid):
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year={target_year}&month={target_month}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Referer": "https://poong.today/"}
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        return res.json().get('b', 0) if res.status_code == 200 else 0
    except: return 0

def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "text": "#ef4444"}
    elif count >= 800000: return {"grad": "linear-gradient(90deg, #9a3412, #f97316)", "text": "#f97316"}
    elif count >= 400000: return {"grad": "linear-gradient(90deg, #a16207, #eab308)", "text": "#eab308"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #166534, #22c55e)", "text": "#22c55e"}
    elif count >= 100000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "text": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "text": "#9ca3af"}

def generate_html():
    all_tasks = []
    for crew_name, info in crews_config.items():
        for nick, uid in info['members'].items():
            all_tasks.append({'crew': crew_name, 'nick': nick, 'uid': uid})

    with ThreadPoolExecutor(max_workers=15) as executor:
        results = list(executor.map(lambda t: {**t, 'count': fetch_b_value(t['uid'])}, all_tasks))

    final_data = []
    for crew_name, info in crews_config.items():
        m_list = sorted([r for r in results if r['crew'] == crew_name], key=lambda x: x['count'], reverse=True)
        total = sum(m['count'] for m in m_list)
        final_data.append({"name": crew_name, "color": info['color'], "total": total, "avg": int(total/len(m_list)), "member_count": len(m_list), "members": m_list, "max": m_list[0]['count'] if m_list else 1})

    final_data.sort(key=lambda x: x['avg'], reverse=True)

    html = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 20px; width: 1200px; }} /* 너비 고정 */
    .grid {{ display: grid; gap: 20px; grid-template-columns: repeat(2, 1fr); }} /* 이미지용 2열 배치 */
    .crew-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 18px; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #334155; padding-bottom: 12px; margin-bottom: 15px; }}
    .crew-name {{ font-size: 1.35rem; font-weight: 800; }}
    .stats {{ text-align: right; font-size: 0.85rem; color: #94a3b8; }}
    .member-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
    .nick {{ width: 130px; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .bar-bg {{ flex-grow: 1; background: #020617; height: 16px; border-radius: 10px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 10px; }}
    .count {{ width: 90px; text-align: right; font-size: 0.85rem; font-weight: 800; }}
    .c-red {{ color: #f87171; }} .c-white {{ color: #fff; }} .c-gold {{ color: #fbbf24; }} .c-pink {{ color: #f472b6; }}
    .c-cyan {{ color: #22d3ee; }} .c-purple {{ color: #c084fc; }} .c-orange {{ color: #fb923c; }} 
    .c-teal {{ color: #2dd4bf; }} .c-lime {{ color: #a3e635; }} .c-green {{ color: #4ade80; }}
    </style></head><body><h2 style="text-align:center;">📊 {target_year}년 {target_month}월 실적 현황</h2><div class="grid">"""

    for c in final_data:
        html += f"""<div class="crew-card"><div class="header"><div class="crew-name {c['color']}">{c['name']} <small style="font-size:0.7em; opacity:0.6;">({c['member_count']}명)</small></div><div class="stats">TOTAL: {c['total']:,}<br>AVG: {c['avg']:,}</div></div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['count'])
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "&nbsp;&nbsp;&nbsp;"
            w = (m['count'] / c['max'] * 100) if c['max'] > 0 else 0
            html += f"""<div class="member-row"><div class="nick">{medal} {m['nick']}</div><div class="bar-bg"><div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div></div><div class="count" style="color:{style['text']}">{m['count']:,}</div></div>"""
        html += "</div>"
    html += "</div></body></html>"
    return html

# [핵심 수정] HTML을 이미지로 저장하는 함수
def save_chart_image(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1250, 'height': 2000})
        page.set_content(html_content)
        # 페이지 로딩 대기
        time.sleep(2) 
        # grid 영역을 캡처하거나 전체 페이지 캡처
        page.screenshot(path="chart.png", full_page=True, animations="disabled")
        browser.close()

if __name__ == "__main__":
    print("🚀 데이터 수집 및 이미지 생성 시작...")
    generated_html = generate_html()
    
    # 1. HTML 파일 저장
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(generated_html)
        
    # 2. 이미지 파일 저장
    try:
        save_chart_image(generated_html)
        print("✅ 이미지(chart.png) 생성 완료!")
    except Exception as e:
        print(f"❌ 이미지 생성 실패: {e}")