"""
fetch_lineups.py
────────────────────────────────────────────────────
ESPN の非公開 JSON API から W杯2026 のスタメンを取得し、
data/matches/index.json を更新する。APIキー不要。

【スポイラー防止ルール】
- status が "released" になった試合は二度と上書きしない
- API レスポンスのうち score / winner / subbedIn /
  subbedOut / stats など試合結果に関わるフィールドは
  一切保存しない(保存するのはラインナップ情報のみ)
────────────────────────────────────────────────────
"""

import json, time, datetime, requests
from pathlib import Path

LEAGUE     = "fifa.world"
SCOREBOARD = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}/scoreboard"
SUMMARY    = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}/summary"
STANDINGS  = f"https://site.api.espn.com/apis/v2/sports/soccer/{LEAGUE}/standings"
DATA_PATH  = Path("data/matches/index.json")
HEADERS    = {"User-Agent": "teamsheet26/1.0 (spoiler-free pre-match lineups)"}

JST = datetime.timezone(datetime.timedelta(hours=9))

# ESPN displayName → 日本語名(2026年大会出場48チーム)
JP_NAMES = {
    "Algeria": "アルジェリア", "Argentina": "アルゼンチン", "Australia": "オーストラリア",
    "Austria": "オーストリア", "Belgium": "ベルギー", "Bosnia-Herzegovina": "ボスニア・ヘルツェゴビナ",
    "Brazil": "ブラジル", "Canada": "カナダ", "Cape Verde": "カーボベルデ",
    "Colombia": "コロンビア", "Congo DR": "コンゴ民主共和国", "Croatia": "クロアチア",
    "Curaçao": "キュラソー", "Czechia": "チェコ", "Ecuador": "エクアドル",
    "Egypt": "エジプト", "England": "イングランド", "France": "フランス",
    "Germany": "ドイツ", "Ghana": "ガーナ", "Haiti": "ハイチ",
    "Iran": "イラン", "Iraq": "イラク", "Ivory Coast": "コートジボワール",
    "Japan": "日本", "Jordan": "ヨルダン", "Mexico": "メキシコ",
    "Morocco": "モロッコ", "Netherlands": "オランダ", "New Zealand": "ニュージーランド",
    "Norway": "ノルウェー", "Panama": "パナマ", "Paraguay": "パラグアイ",
    "Portugal": "ポルトガル", "Qatar": "カタール", "Saudi Arabia": "サウジアラビア",
    "Scotland": "スコットランド", "Senegal": "セネガル", "South Africa": "南アフリカ",
    "South Korea": "韓国", "Spain": "スペイン", "Sweden": "スウェーデン",
    "Switzerland": "スイス", "Tunisia": "チュニジア", "Türkiye": "トルコ",
    "United States": "アメリカ", "Uruguay": "ウルグアイ", "Uzbekistan": "ウズベキスタン",
}

ROUND_NAMES = {
    "group-stage": "グループステージ",
    "round-of-32": "ラウンド32",
    "round-of-16": "ラウンド16",
    "quarterfinals": "準々決勝",
    "semifinals": "準決勝",
    "third-place-playoff": "3位決定戦",
    "final": "決勝",
}

WEEKDAYS = "月火水木金土日"

# ポーリング対象の時間窓
POLL_BEFORE_MIN = 100          # キックオフ100分前から取得を試みる
POLL_AFTER_MIN  = 3 * 24 * 60  # 過去3日以内の試合は未取得なら遡って取得


def jst_now():
    return datetime.datetime.now(JST)


def api_get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def load_current():
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return []


def save(matches):
    DATA_PATH.write_text(
        json.dumps(matches, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def fetch_group_map():
    """standings から チーム名 → グループ文字(A〜L)の対応を作る。
    順位・勝点などの結果情報は一切使わない。"""
    groups = {}
    try:
        data = api_get(STANDINGS, {"season": 2026})
        for child in data.get("children", []):
            name = child.get("name", "")          # "Group A"
            letter = name.replace("Group ", "").strip()
            for entry in child.get("standings", {}).get("entries", []):
                groups[entry["team"]["displayName"]] = letter
    except Exception as e:
        print(f"standings 取得失敗(グループ表示なしで続行): {e}")
    return groups


def fetch_events():
    """昨日〜7日後の試合を取得"""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    span = f"{(today - datetime.timedelta(days=3)):%Y%m%d}-{(today + datetime.timedelta(days=7)):%Y%m%d}"
    data = api_get(SCOREBOARD, {"dates": span})
    return data.get("events", [])


def fetch_rosters(event_id):
    """試合のスタメンを取得。未発表なら None"""
    data = api_get(SUMMARY, {"event": event_id})
    rosters = data.get("rosters", [])
    if len(rosters) < 2:
        return None
    for r in rosters:
        starters = [p for p in r.get("roster", []) if p.get("starter")]
        if len(starters) != 11:
            return None
    return rosters


def build_team_meta(team):
    name = team.get("displayName", "")
    return {
        "name": JP_NAMES.get(name, name),
        "code": team.get("abbreviation", name[:3].upper()),
        "color": "#" + (team.get("color") or "555555"),
    }


def build_lineup(roster_obj):
    """ESPN roster → ネタバレなしのラインナップ。
    subbedIn / subbedOut / stats などは捨てる。"""
    players = roster_obj.get("roster", [])
    starters = sorted(
        (p for p in players if p.get("starter")),
        key=lambda p: int(p.get("formationPlace") or 99),
    )
    subs = [p for p in players if not p.get("starter")]

    def fmt(p, with_gk=False):
        d = {
            "n": int(p.get("jersey") or 0),
            "name": p.get("athlete", {}).get("displayName", ""),
        }
        if with_gk and p.get("position", {}).get("abbreviation") == "G":
            d["gk"] = True
        return d

    return {
        "formation": roster_obj.get("formation", ""),
        "coach": "",  # ESPN の summary には監督情報がないため空
        "xi":   [fmt(p) for p in starters],
        "subs": [fmt(p, with_gk=True) for p in subs],
    }


def event_to_match(ev, group_map, rosters=None):
    comp = ev["competitions"][0]
    home = next(c for c in comp["competitors"] if c["homeAway"] == "home")
    away = next(c for c in comp["competitors"] if c["homeAway"] == "away")

    kick_utc = datetime.datetime.fromisoformat(ev["date"].replace("Z", "+00:00"))
    kick_jst = kick_utc.astimezone(JST)
    venue = comp.get("venue", {}) or {}
    slug = ev.get("season", {}).get("slug", "")
    home_name = home["team"].get("displayName", "")

    entry = {
        "id":        str(ev["id"]),
        "kickoff":   kick_jst.isoformat(),  # ソート用(結果情報は含まない)
        "group":     group_map.get(home_name, ""),
        "matchday":  ROUND_NAMES.get(slug, slug),
        "dateLabel": f"{kick_jst.month}月{kick_jst.day}日（{WEEKDAYS[kick_jst.weekday()]}）",
        "timeJST":   kick_jst.strftime("%H:%M"),
        "stadium":   venue.get("fullName", ""),
        "city":      (venue.get("address", {}) or {}).get("city", ""),
        "home":      build_team_meta(home["team"]),
        "away":      build_team_meta(away["team"]),
        "status":    "pending",
    }

    if rosters:
        home_id = home["team"]["id"]
        r_home = next(r for r in rosters if r.get("team", {}).get("id") == home_id)
        r_away = next(r for r in rosters if r.get("team", {}).get("id") != home_id)
        entry["status"] = "released"
        entry["capturedAt"] = f"{jst_now().strftime('%-m/%-d %H:%M')} JST に取得・凍結"
        entry["lineup"] = {
            "home": build_lineup(r_home),
            "away": build_lineup(r_away),
        }
    return entry


def main():
    now = jst_now()
    current_by_id = {m["id"]: m for m in load_current()}
    group_map = fetch_group_map()
    events = fetch_events()
    updated = False

    for ev in events:
        eid = str(ev["id"])
        kick_jst = datetime.datetime.fromisoformat(
            ev["date"].replace("Z", "+00:00")).astimezone(JST)

        # すでに確定済みの試合はスキップ(凍結)
        if current_by_id.get(eid, {}).get("status") == "released":
            print(f"SKIP (frozen): {eid}")
            continue

        minutes_to_kick = (kick_jst - now).total_seconds() / 60

        # ポーリング窓の外 → 発表待ちとして載せるだけ
        if not (-POLL_AFTER_MIN <= minutes_to_kick <= POLL_BEFORE_MIN):
            if eid not in current_by_id:
                current_by_id[eid] = event_to_match(ev, group_map)
                updated = True
            continue

        print(f"FETCHING lineup for {eid} ({ev.get('name', '')})…")
        rosters = fetch_rosters(eid)

        if rosters:
            print("  → 取得成功、凍結します")
            current_by_id[eid] = event_to_match(ev, group_map, rosters)
            updated = True
        else:
            print("  → まだ未発表")
            if eid not in current_by_id:
                current_by_id[eid] = event_to_match(ev, group_map)
                updated = True

        time.sleep(0.5)  # 行儀よく間隔を空ける

    if updated:
        sorted_matches = sorted(
            current_by_id.values(),
            key=lambda m: m.get("kickoff", "")
        )
        save(sorted_matches)
        print(f"✓ index.json を更新しました ({len(sorted_matches)} 試合)")
    else:
        print("変更なし")


if __name__ == "__main__":
    main()
