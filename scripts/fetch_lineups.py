"""
fetch_lineups.py
────────────────────────────────────────────────────
API-Football から W杯2026(league=1, season=2026)の
スタメンを取得し、data/matches/index.json を更新する。

【スポイラー防止ルール】
- status が "released" になった試合は二度と上書きしない
- API レスポンスから score / events / statistics など
  試合結果に関わるフィールドは一切保存しない
────────────────────────────────────────────────────
"""

import os, json, time, datetime, requests
from pathlib import Path

API_KEY  = os.environ["API_FOOTBALL_KEY"]
BASE_URL = "https://v3.football.api-sports.io"
HEADERS  = {"x-apisports-key": API_KEY}
DATA_PATH = Path("data/matches/index.json")

# チームの表示色(code → hex)  ※適宜追加
TEAM_COLORS = {
    "MEX": "#0E6B3F", "RSA": "#B8860B", "KOR": "#C8102E", "CZE": "#11457E",
    "CAN": "#D80621", "BIH": "#003087", "QAT": "#7B2D8B", "SUI": "#D20000",
    "BRA": "#009C3B", "MAR": "#C1272D", "NED": "#E8590C", "JPN": "#0A1E5C",
    "USA": "#B22234", "PAR": "#D52B1E", "ARG": "#6CACE4", "FRA": "#002395",
    "ENG": "#CF081F", "GER": "#000000", "ESP": "#AA151B", "POR": "#006600",
}

JST = datetime.timezone(datetime.timedelta(hours=9))

def jst_now():
    return datetime.datetime.now(JST)

def api_get(endpoint, params=None):
    r = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=15)
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

def fetch_fixtures():
    """今後7日以内の W杯試合を取得"""
    data = api_get("fixtures", {"league": 1, "season": 2026, "next": 50})
    return data.get("response", [])

def fetch_lineup(fixture_id):
    """試合のスタメンを取得。未発表なら None を返す"""
    data = api_get("fixtures/lineups", {"fixture": fixture_id})
    resp = data.get("response", [])
    if len(resp) < 2:
        return None
    return resp  # [home_lineup, away_lineup]

def build_team_meta(team_obj, fixture_team):
    code = team_obj.get("code") or team_obj["name"][:3].upper()
    return {
        "name": team_obj["name"],
        "code": code,
        "color": TEAM_COLORS.get(code, "#555555"),
    }

def format_players(players):
    return [
        {"n": p["player"]["number"], "name": p["player"]["name"]}
        for p in players
    ]

def build_lineup(raw_lineup):
    """
    API レスポンスの lineup オブジェクトから
    ネタバレなし情報だけを抽出する
    """
    return {
        "formation": raw_lineup.get("formation", ""),
        "coach":     raw_lineup.get("coach", {}).get("name", ""),
        "xi":        format_players(raw_lineup.get("startXI", [])),
        "subs":      format_players(raw_lineup.get("substitutes", [])),
    }

def fixture_to_match(fix, home_meta, away_meta, lineup_data=None):
    """API fixture → index.json の1エントリに変換"""
    kick_utc = datetime.datetime.fromisoformat(fix["fixture"]["date"].replace("Z", "+00:00"))
    kick_jst = kick_utc.astimezone(JST)

    status = "pending"
    captured_at = None
    lineup = None

    if lineup_data:
        status = "released"
        captured_at = f"キックオフ前 {jst_now().strftime('%H:%M')} JST に取得"
        lineup = {
            "home": build_lineup(lineup_data[0]),
            "away": build_lineup(lineup_data[1]),
        }

    entry = {
        "id":        str(fix["fixture"]["id"]),
        "kickoff":   kick_jst.isoformat(),  # ソート用(結果情報は含まない)
        "group":     fix.get("league", {}).get("round", "")[-1:] or "?",
        "matchday":  fix.get("league", {}).get("round", ""),
        "dateLabel": kick_jst.strftime("%-m月%-d日（%a）").replace(
            "Mon","月").replace("Tue","火").replace("Wed","水").replace(
            "Thu","木").replace("Fri","金").replace("Sat","土").replace("Sun","日"),
        "timeJST":   kick_jst.strftime("%H:%M"),
        "stadium":   fix["fixture"]["venue"]["name"] or "",
        "city":      fix["fixture"]["venue"]["city"] or "",
        "home":      home_meta,
        "away":      away_meta,
        "status":    status,
    }
    if captured_at:
        entry["capturedAt"] = captured_at
    if lineup:
        entry["lineup"] = lineup
    return entry

def main():
    now = jst_now()
    current_by_id = {m["id"]: m for m in load_current()}
    fixtures = fetch_fixtures()
    updated = False

    for fix in fixtures:
        fid = str(fix["fixture"]["id"])
        kick_utc = datetime.datetime.fromisoformat(
            fix["fixture"]["date"].replace("Z", "+00:00"))
        kick_jst = kick_utc.astimezone(JST)

        # すでに確定済みの試合はスキップ(凍結)
        if fid in current_by_id and current_by_id[fid].get("status") == "released":
            print(f"SKIP (frozen): {fid}")
            continue

        # キックオフまでの残り時間
        minutes_to_kick = (kick_jst - now).total_seconds() / 60

        # キックオフ45分前〜0分前の試合だけポーリング
        if not (-5 <= minutes_to_kick <= 45):
            # 今日じゃない試合も index.json に載せておく(発表待ち)
            home_meta = build_team_meta(fix["teams"]["home"], fix)
            away_meta = build_team_meta(fix["teams"]["away"], fix)
            if fid not in current_by_id:
                current_by_id[fid] = fixture_to_match(fix, home_meta, away_meta)
                updated = True
            continue

        # ラインナップ取得を試みる
        print(f"FETCHING lineup for {fid} ({fix['teams']['home']['name']} vs {fix['teams']['away']['name']})…")
        lineup_data = fetch_lineup(fid)
        home_meta = build_team_meta(fix["teams"]["home"], fix)
        away_meta = build_team_meta(fix["teams"]["away"], fix)

        if lineup_data:
            print(f"  → 取得成功、凍結します")
            current_by_id[fid] = fixture_to_match(fix, home_meta, away_meta, lineup_data)
            updated = True
        else:
            print(f"  → まだ未発表")
            if fid not in current_by_id:
                current_by_id[fid] = fixture_to_match(fix, home_meta, away_meta)
                updated = True

        time.sleep(0.5)  # API レート制限対策

    if updated:
        # 日付順に並べて保存
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
