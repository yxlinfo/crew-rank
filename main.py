import requests
import time

# 1. 10개 크루 및 126명 전원 명단 (정확한 ID 매칭)
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

# 2. 구간별 그라데이션 및 텍스트 색상 설정
def get_gauge_style(count):
    if count >= 1000000: return {"grad": "linear-gradient(90deg, #991b1b, #ef4444)", "text": "#ef4444"}
    elif count >= 800000: return {"grad": "linear-gradient(90deg, #9a3412, #f97316)", "text": "#f97316"}
    elif count >= 400000: return {"grad": "linear-gradient(90deg, #a16207, #eab308)", "text": "#eab308"}
    elif count >= 200000: return {"grad": "linear-gradient(90deg, #166534, #22c55e)", "text": "#22c55e"}
    elif count >= 100000: return {"grad": "linear-gradient(90deg, #1e3a8a, #3b82f6)", "text": "#3b82f6"}
    else: return {"grad": "linear-gradient(90deg, #4b5563, #9ca3af)", "text": "#9ca3af"}

# 3. 데이터 수집 함수 (사용자 성공 로직)
def fetch_b_value(uid):
    api_url = f"https://static.poong.today/bj/detail/get?id={uid}&year=2026&month=4"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://poong.today/"}
    try:
        res = requests.get(api_url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get('b', 0)
        return 0
    except: return 0

def run():
    final_data = []
    print("📡 126명 전원 실시간 데이터 수집 중... (약 1분 소요)")

    for crew_name, info in crews_config.items():
        print(f"📥 {crew_name} 분석 중 ({len(info['members'])}명)...")
        m_list = []
        for nick, uid in info['members'].items():
            count = fetch_b_value(uid)
            m_list.append({"nick": nick, "count": count})
            time.sleep(0.05) # 서버 부하 방지
        
        m_list.sort(key=lambda x: x['count'], reverse=True)
        total = sum(m['count'] for m in m_list)
        final_data.append({
            "name": crew_name, "color": info['color'], "total": total,
            "avg": int(total/len(m_list)) if m_list else 0, 
            "member_count": len(m_list), "members": m_list, 
            "max": m_list[0]['count'] if m_list else 1
        })

    # 크루 평균별 정렬
    final_data.sort(key=lambda x: x['avg'], reverse=True)

    # HTML 렌더링
    html = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><style>
    body { background: #0f172a; color: #f8fafc; font-family: sans-serif; margin: 20px; }
    .grid { display: grid; gap: 20px; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); }
    .crew-card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #334155; padding-bottom: 12px; margin-bottom: 15px; }
    .crew-name { font-size: 1.35rem; font-weight: 800; }
    .m-num { font-size: 0.85rem; opacity: 0.6; margin-left: 5px; font-weight: 400; }
    .stats { text-align: right; font-size: 0.85rem; color: #94a3b8; }
    .member-row { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
    .nick { width: 130px; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #e2e8f0; }
    .rank-1 { color: #fbbf24; font-weight: 800; } .rank-2 { color: #cbd5e1; } .rank-3 { color: #d97706; }
    .bar-bg { flex-grow: 1; background: #020617; height: 16px; border-radius: 10px; overflow: hidden; position: relative; }
    .bar-fill { height: 100%; position: relative; border-radius: 10px; }
    .bar-fill::after { content: ''; position: absolute; top:0; left:0; right:0; bottom:50%; background: rgba(255,255,255,0.1); }
    .count { width: 90px; text-align: right; font-size: 0.85rem; font-weight: 800; font-family: monospace; }
    /* 크루 포인트 색상 */
    .c-red { color: #f87171; } .c-white { color: #fff; } .c-gold { color: #fbbf24; } .c-pink { color: #f472b6; }
    .c-cyan { color: #22d3ee; } .c-purple { color: #c084fc; } .c-orange { color: #fb923c; } 
    .c-teal { color: #2dd4bf; } .c-lime { color: #a3e635; } .c-green { color: #4ade80; }
    </style></head><body><div class="grid">"""

    for c in final_data:
        html += f"""<div class="crew-card"><div class="header">
            <div class="crew-name {c['color']}">{c['name']}<span class="m-num">({c['member_count']}명)</span></div>
            <div class="stats">TOTAL: {c['total']:,}<br>AVG: {c['avg']:,}</div>
        </div>"""
        for i, m in enumerate(c['members']):
            style = get_gauge_style(m['count'])
            rank_class = f"rank-{i+1}" if i < 3 else ""
            medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "&nbsp;&nbsp;&nbsp;"
            w = (m['count'] / c['max'] * 100) if c['max'] > 0 else 0
            
            html += f"""<div class="member-row">
                <div class="nick {rank_class}">{medal} {m['nick']}</div>
                <div class="bar-bg"><div class="bar-fill" style="width:{w}%; background:{style['grad']};"></div></div>
                <div class="count" style="color:{style['text']}">{m['count']:,}</div>
            </div>"""
        html += "</div>"

    html += "</div></body></html>"
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)
    print("\n✅ 126명 전원 명단 및 시각화가 완료된 index.html이 생성되었습니다!")

if __name__ == "__main__": run()