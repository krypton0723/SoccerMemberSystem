# TEAMSHEET '26

**ディレイ視聴のための、ネタバレなしスタメン速報サイト**  
FIFAワールドカップ2026の試合スタメン・サブだけを表示します。  
スコア・試合結果・途中経過は一切表示しません。

---

## 仕組み

```
GitHub Actions (15分ごと)
    ↓  API-Football からスタメン取得(キックオフ45分前〜)
    ↓  取得成功した時点で data/matches/index.json を更新・凍結
    ↓  以降その試合のデータは二度と上書きしない
GitHub Pages がホスティング → ブラウザで表示
```

スタメンが確定したら `status: "released"` に変わり、フォーメーション図が表示されます。  
試合が始まった後もスコアを取りに行かないため、ディレイ視聴していてもネタバレしません。

---

## セットアップ手順

### 1. リポジトリをフォーク or クローン

```bash
git clone https://github.com/<yourname>/teamsheet26.git
cd teamsheet26
```

### 2. API キーを取得

[api-football.com](https://www.api-football.com/) で無料アカウントを作成し、API キーを取得します。  
無料プランで **1日100リクエスト** まで使えます（W杯期間中は十分）。

### 3. GitHub Secrets に登録

リポジトリの **Settings → Secrets and variables → Actions** から:

| Name | Value |
|------|-------|
| `API_FOOTBALL_KEY` | 取得した API キー |

### 4. GitHub Pages を有効化

リポジトリの **Settings → Pages** で:
- Source: **Deploy from a branch**
- Branch: `main` / `(root)`

数分後に `https://<yourname>.github.io/teamsheet26/` で公開されます。

### 5. Actions を有効化

**Actions タブ** を開き、ワークフローを有効化します。  
あとは自動で15分ごとに動きます。手動実行も可能です。

---

## ファイル構成

```
teamsheet26/
├── index.html                  # エントリポイント
├── src/
│   └── app.jsx                 # React アプリ本体
├── data/
│   └── matches/
│       └── index.json          # 試合データ(自動生成)
├── scripts/
│   └── fetch_lineups.py        # スタメン取得スクリプト
└── .github/
    └── workflows/
        └── fetch-lineups.yml   # GitHub Actions 定義
```

---

## data/matches/index.json のフォーマット

```json
[
  {
    "id": "fixture_id",
    "group": "A",
    "matchday": "グループステージ 第1節",
    "dateLabel": "6月12日（金）",
    "timeJST": "04:00",
    "stadium": "エスタディオ・アステカ",
    "city": "メキシコシティ",
    "home": { "name": "メキシコ", "code": "MEX", "color": "#0E6B3F" },
    "away": { "name": "南アフリカ", "code": "RSA", "color": "#B8860B" },
    "status": "released",          // "pending" or "released"
    "capturedAt": "キックオフ前 03:22 JST に取得",
    "lineup": {                    // status="released" のときのみ存在
      "home": {
        "formation": "4-3-3",
        "coach": "アギーレ",
        "xi":   [{ "n": 13, "name": "マラゴン" }, ...],
        "subs": [{ "n": 1,  "name": "オチョア", "gk": true }, ...]
      },
      "away": { ... }
    }
  }
]
```

`score`, `events`, `statistics` などの試合結果フィールドは  
**設計上このファイルに存在しません**。

---

## ライセンス

MIT
