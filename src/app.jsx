// TEAMSHEET '26 — src/app.jsx
// React 18 (UMD), Babel standalone — no build step required
const { useState, useEffect } = React;

// ─────────────────────────────────────────────
// フォーメーション図コンポーネント
// ─────────────────────────────────────────────
const rowsOf = (formation) => [1, ...formation.split("-").map(Number)];

function playerPositions(team, side) {
  const rows = rowsOf(team.formation);
  const W = 420;
  const pts = [];
  let idx = 0;
  rows.forEach((count, r) => {
    const t = rows.length === 1 ? 0 : r / (rows.length - 1);
    const y = side === "home" ? 598 - t * 245 : 44 + t * 243;
    for (let j = 0; j < count; j++) {
      let x = (W * (j + 1)) / (count + 1);
      if (side === "away") x = W - x;
      pts.push({ ...team.xi[idx], x, y });
      idx++;
    }
  });
  return pts;
}

// 名前を最大8文字に切り詰める(重なり防止)
const shortName = (name) => {
  const last = name.split(" ").pop();
  return last.length <= 8 ? last : last.slice(0, 7) + "…";
};

function Pitch({ home, away, homeColor, awayColor, homeName, awayName }) {
  const homePts = playerPositions(home, "home");
  const awayPts = playerPositions(away, "away");
  return (
    <svg viewBox="0 0 420 700" className="pitch" role="img" aria-label="フォーメーション図">
      {/* グラウンド背景 */}
      {Array.from({ length: 10 }, (_, i) => (
        <rect key={i} x="0" y={29 + i * 64.2} width="420" height="64.2" fill={i % 2 ? "#1A6540" : "#1E6F45"} />
      ))}
      {/* ピッチライン */}
      <g stroke="rgba(255,255,255,.78)" strokeWidth="2" fill="none">
        <rect x="12" y="41" width="396" height="618" />
        <line x1="12" y1="350" x2="408" y2="350" />
        <circle cx="210" cy="350" r="52" />
        <rect x="100" y="41" width="220" height="86" />
        <rect x="158" y="41" width="104" height="34" />
        <rect x="100" y="573" width="220" height="86" />
        <rect x="158" y="625" width="104" height="34" />
      </g>
      <circle cx="210" cy="350" r="3" fill="rgba(255,255,255,.78)" />
      {/* チームラベル(上=アウェイ・下=ホーム) */}
      <rect x="0" y="0" width="420" height="28" fill={awayColor} opacity="0.92" />
      <text x="210" y="19" textAnchor="middle" fill="#fff"
        style={{fontSize:"12px", fontFamily:"'Oswald',sans-serif", fontWeight:600, letterSpacing:".06em"}}>
        ▲ AWAY — {awayName}
      </text>
      <rect x="0" y="672" width="420" height="28" fill={homeColor} opacity="0.92" />
      <text x="210" y="691" textAnchor="middle" fill="#fff"
        style={{fontSize:"12px", fontFamily:"'Oswald',sans-serif", fontWeight:600, letterSpacing:".06em"}}>
        ▼ HOME — {homeName}
      </text>
      {/* 選手(アウェイ) */}
      {awayPts.map((p) => (
        <g key={"a" + p.n} transform="translate(0,29)">
          <circle cx={p.x} cy={p.y} r="14" fill={awayColor} stroke="rgba(255,255,255,.92)" strokeWidth="1.6" />
          <text x={p.x} y={p.y + 4.5} textAnchor="middle" className="kit-num">{p.n}</text>
          <text x={p.x} y={p.y + 28} textAnchor="middle" className="kit-name">{shortName(p.name)}</text>
        </g>
      ))}
      {/* 選手(ホーム) */}
      {homePts.map((p) => (
        <g key={"h" + p.n} transform="translate(0,29)">
          <circle cx={p.x} cy={p.y} r="14" fill={homeColor} stroke="rgba(255,255,255,.92)" strokeWidth="1.6" />
          <text x={p.x} y={p.y + 4.5} textAnchor="middle" className="kit-num">{p.n}</text>
          <text x={p.x} y={p.y + 28} textAnchor="middle" className="kit-name">{shortName(p.name)}</text>
        </g>
      ))}
    </svg>
  );
}

// ─────────────────────────────────────────────
// 試合詳細
// ─────────────────────────────────────────────
// GK先頭、その後は背番号昇順
const sortSubs = (subs) => [
  ...subs.filter((s) => s.gk).sort((a, b) => a.n - b.n),
  ...subs.filter((s) => !s.gk).sort((a, b) => a.n - b.n),
];

function SubsList({ title, color, subs }) {
  return (
    <div className="subs-col">
      <div className="subs-head">
        <span className="swatch" style={{ background: color }} />
        {title}
      </div>
      <ul>
        {sortSubs(subs).map((s) => (
          <li key={s.n}>
            <span className="sub-num">{s.n}</span>
            <span>{s.name}</span>
            {s.gk && <span className="gk-tag">GK</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}

function MatchDetail({ match, onBack }) {
  const { home, away, lineup } = match;
  return (
    <div className="detail">
      <button className="back" onClick={onBack}>← 試合一覧へ</button>
      <div className="detail-head">
        <div className="eyebrow">{match.group ? `グループ${match.group}・` : ""}{match.matchday}</div>
        <h2 className="vs-line">
          <span>{home.code}</span>
          <span className="vs">vs</span>
          <span>{away.code}</span>
        </h2>
        <div className="jp-teams">{home.name} — {away.name}</div>
        <div className="meta">
          {match.dateLabel} {match.timeJST} キックオフ（日本時間）／ {match.stadium}（{match.city}）
        </div>
        <div className="frozen-note">🔒 {match.capturedAt}・以降このデータは更新されません</div>
      </div>

      <div className="formation-bar">
        <span>
          <span className="swatch" style={{ background: home.color }} />
          {home.name} {lineup.home.formation}{lineup.home.coach && `／監督: ${lineup.home.coach}`}
        </span>
        <span>
          <span className="swatch" style={{ background: away.color }} />
          {away.name} {lineup.away.formation}{lineup.away.coach && `／監督: ${lineup.away.coach}`}
        </span>
      </div>

      <Pitch home={lineup.home} away={lineup.away} homeColor={home.color} awayColor={away.color} homeName={home.name} awayName={away.name} />

      <h3 className="section-title">サブメンバー</h3>
      <div className="subs">
        <SubsList title={home.name} color={home.color} subs={lineup.home.subs} />
        <SubsList title={away.name} color={away.color} subs={lineup.away.subs} />
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// 試合カード
// ─────────────────────────────────────────────
function MatchCard({ match, onOpen }) {
  const released = match.status === "released";
  return (
    <button
      className={"card" + (released ? " card-open" : "")}
      onClick={() => released && onOpen(match)}
      aria-disabled={!released}
    >
      <div className="card-top">
        <span className="group-badge">{match.group ? `グループ${match.group}` : match.matchday}</span>
        <span className={"pill " + (released ? "pill-ok" : "pill-wait")}>
          {released ? "✓ スタメン確定" : "発表待ち"}
        </span>
      </div>
      <div className="card-teams">
        <div className="team">
          <div className="code">{match.home.code}</div>
          <div className="jp">{match.home.name}</div>
        </div>
        <div className="kick">
          <div className="time">{match.timeJST}</div>
          <div className="tz">JST</div>
        </div>
        <div className="team right">
          <div className="code">{match.away.code}</div>
          <div className="jp">{match.away.name}</div>
        </div>
      </div>
      <div className="card-foot">
        <span>{match.stadium}（{match.city}）</span>
        {released
          ? <span className="open-hint">スタメンを見る →</span>
          : <span className="wait-hint">スタメン発表後に自動公開</span>}
      </div>
    </button>
  );
}

// ─────────────────────────────────────────────
// アプリ本体
// ─────────────────────────────────────────────
function App() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    fetch("data/matches/index.json")
      .then((r) => {
        if (!r.ok) throw new Error("データの取得に失敗しました");
        return r.json();
      })
      .then((data) => { setMatches(data); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, []);

  const dates = [...new Set(matches.map((m) => m.dateLabel))];

  return (
    <div className="app">
      <div className="trust-bar">このサイトはスコア・試合結果・途中経過を一切表示しません</div>
      <header>
        <h1>TEAMSHEET<span className="tm">'26</span></h1>
        <p className="tagline">遅れ視聴のための、ネタバレなしスタメン速報 — FIFAワールドカップ2026</p>
      </header>

      {loading && <div className="state-msg">試合データを読み込んでいます…</div>}
      {error && <div className="state-msg error">{error}</div>}

      {!loading && !error && (
        selected ? (
          <MatchDetail match={selected} onBack={() => setSelected(null)} />
        ) : (
          <main>
            {dates.map((d) => (
              <section key={d}>
                <h2 className="date-head">{d}</h2>
                {matches.filter((m) => m.dateLabel === d).map((m) => (
                  <MatchCard key={m.id} match={m} onOpen={setSelected} />
                ))}
              </section>
            ))}
          </main>
        )
      )}

      <footer>
        スタメン・サブはキックオフ前にAPIから自動取得し、その時点で凍結。
        試合開始後のデータには一切アクセスしません。
      </footer>
    </div>
  );
}

// ─────────────────────────────────────────────
// スタイル
// ─────────────────────────────────────────────
const styleEl = document.createElement("style");
styleEl.textContent = `
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600&family=IBM+Plex+Mono:wght@600&display=swap');
.app{
  --paper:#EEF3EC;--ink:#15231B;--line:#CBD6C6;
  --ok:#0E6B3F;--okbg:#DCEDE2;--wait:#75806F;
  min-height:100vh;background:var(--paper);color:var(--ink);
  font-family:'Hiragino Kaku Gothic ProN','Noto Sans JP',system-ui,sans-serif;
  max-width:760px;margin:0 auto;padding:0 16px 48px;
}
.trust-bar{margin:0 -16px;background:var(--ink);color:#E9F2EA;font-size:12px;
  letter-spacing:.08em;text-align:center;padding:7px 12px;}
header{padding:26px 0 6px;border-bottom:2px solid var(--ink);}
h1{font-family:'Oswald','Arial Narrow',sans-serif;font-size:44px;font-weight:600;
  letter-spacing:.04em;margin:0;line-height:1;}
.tm{color:var(--ok);margin-left:4px;}
.tagline{margin:8px 0 14px;font-size:13px;color:#46544A;}
.state-msg{padding:24px 0;font-size:14px;color:var(--wait);}
.state-msg.error{color:#b33;}
.date-head{font-family:'Oswald',sans-serif;font-size:17px;letter-spacing:.06em;
  margin:26px 0 10px;padding-left:10px;border-left:4px solid var(--ok);}
.card{display:block;width:100%;text-align:left;background:#fff;border:1px solid var(--line);
  border-radius:10px;padding:14px 16px;margin-bottom:10px;cursor:default;font:inherit;color:inherit;box-sizing:border-box;}
.card-open{cursor:pointer;transition:box-shadow .15s,transform .15s;}
.card-open:hover{box-shadow:0 3px 14px rgba(21,35,27,.12);transform:translateY(-1px);}
.card-open:focus-visible,.back:focus-visible{outline:2px solid var(--ok);outline-offset:2px;}
.card-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;}
.group-badge{font-size:11px;letter-spacing:.06em;color:#46544A;}
.pill{font-size:11px;padding:3px 9px;border-radius:999px;letter-spacing:.04em;}
.pill-ok{background:var(--okbg);color:var(--ok);font-weight:600;}
.pill-wait{border:1px solid var(--line);color:var(--wait);}
.card-teams{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:8px;}
.team .code{font-family:'Oswald',sans-serif;font-size:30px;font-weight:600;letter-spacing:.05em;}
.team.right{text-align:right;}
.team .jp{font-size:12px;color:#46544A;}
.kick{text-align:center;}
.kick .time{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:600;}
.kick .tz{font-size:10px;color:#75806F;letter-spacing:.15em;}
.card-foot{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;
  margin-top:10px;padding-top:9px;border-top:1px dashed var(--line);font-size:12px;color:#46544A;}
.open-hint{color:var(--ok);font-weight:600;}
.wait-hint{color:var(--wait);}
.back{background:none;border:none;font:inherit;color:var(--ok);font-weight:600;
  padding:14px 0 4px;cursor:pointer;}
.detail-head{margin:8px 0 14px;}
.eyebrow{font-size:12px;letter-spacing:.08em;color:#46544A;}
.vs-line{font-family:'Oswald',sans-serif;font-size:46px;font-weight:600;margin:2px 0;
  display:flex;gap:14px;align-items:baseline;letter-spacing:.04em;}
.vs{font-size:20px;color:#75806F;}
.jp-teams{font-size:14px;margin-bottom:6px;}
.meta{font-size:13px;color:#46544A;}
.frozen-note{margin-top:8px;font-size:12px;color:var(--ok);background:var(--okbg);
  display:inline-block;padding:4px 10px;border-radius:6px;}
.formation-bar{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;
  font-size:12.5px;margin:14px 0 8px;}
.swatch{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:baseline;}
.pitch{width:100%;height:auto;border-radius:12px;display:block;box-shadow:0 4px 18px rgba(21,35,27,.18);}
.kit-num{font-family:'IBM Plex Mono',monospace;font-size:12px;font-weight:600;fill:#fff;}
.kit-name{font-size:10px;fill:#fff;paint-order:stroke;stroke:rgba(15,40,25,.85);stroke-width:2.6px;}
.section-title{font-family:'Oswald',sans-serif;font-size:17px;letter-spacing:.06em;
  margin:22px 0 10px;padding-left:10px;border-left:4px solid var(--ok);}
.subs{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.subs-col{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px;}
.subs-head{font-size:13px;font-weight:600;margin-bottom:8px;}
.subs-col ul{list-style:none;margin:0;padding:0;}
.subs-col li{display:flex;align-items:center;gap:8px;font-size:13px;padding:4px 0;
  border-bottom:1px dashed #E4EAE0;}
.subs-col li:last-child{border-bottom:none;}
.sub-num{font-family:'IBM Plex Mono',monospace;font-weight:600;width:22px;text-align:right;color:#46544A;}
.gk-tag{font-size:10px;border:1px solid var(--line);border-radius:4px;padding:0 4px;color:#75806F;}
footer{margin-top:34px;padding-top:12px;border-top:1px solid var(--line);font-size:11.5px;color:#75806F;line-height:1.7;}
@media(max-width:520px){h1{font-size:34px;}.vs-line{font-size:34px;}.subs{grid-template-columns:1fr;}}
@media(prefers-reduced-motion:reduce){.card-open{transition:none;}}
`;
document.head.appendChild(styleEl);

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
