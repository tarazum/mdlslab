"""SQLite-backed persistent episode memory (arm B MVP, stdlib only).

Scope: append-only episodic store with provenance, deterministic
keyword/substring retrieval, and a portable JSON export/import. The export
format is deliberately model-neutral plain data — it is the future CONT-002
state carrier (an agent "restored" onto another core imports exactly these
episodes; nothing here references prompts, models, or harness internals).

Design decisions (recorded in LOG.md 2026-10-01 M2):
- One store per run; retrieval is scoped by `scenario` so cross-scenario
  contamination cannot confound the arm A vs arm B contrast.
- Scoring: whole-word keyword hits count 1.0, additional substring-only hits
  (morphology, e.g. "flash" inside "flashes") count 0.5. Ties break toward
  the more recent episode (higher id). Fully deterministic.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

EXPORT_FORMAT = "continuity-memory-export"
EXPORT_VERSION = 1

# Small fixed stopword set for query tokenization (deterministic, order-free).
_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "for", "from",
        "had", "has", "have", "he", "her", "his", "i", "in", "is", "it",
        "its", "my", "no", "not", "of", "on", "or", "our", "she", "that",
        "the", "their", "them", "they", "this", "to", "was", "we", "were",
        "what", "when", "which", "who", "will", "with", "you", "your",
    }
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_utc TEXT NOT NULL,
    run_id TEXT NOT NULL,
    scenario TEXT NOT NULL,
    session INTEGER NOT NULL,
    turn_ref TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.5,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_episodes_scenario ON episodes(scenario);
"""

_REQUIRED_EPISODE_FIELDS = (
    "created_utc", "run_id", "scenario", "session", "turn_ref", "role", "content",
)


def tokenize(text: str) -> list[str]:
    """Lowercase alnum tokens, stopwords removed, order preserved, dups kept out."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in dict.fromkeys(tokens) if t not in _STOPWORDS and len(t) >= 2]


def score_content(query_keywords: list[str], content: str) -> float:
    """Deterministic keyword/substring relevance of one episode body.

    1.0 per whole-word occurrence of a query keyword, 0.5 per additional
    occurrence only as a substring (prefix morphology). Stopwords never reach
    here (tokenize removes them).
    """
    lowered = content.lower()
    score = 0.0
    for kw in query_keywords:
        pattern = rf"\b{re.escape(kw)}\b"
        word_hits = len(re.findall(pattern, lowered))
        substr_hits = lowered.count(kw)
        score += word_hits + 0.5 * max(0, substr_hits - word_hits)
    return score


class MemoryStore:
    """Append-only episode store over one SQLite file."""

    def __init__(self, path: str) -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # -- write -----------------------------------------------------------

    def append_episode(
        self,
        *,
        run_id: str,
        scenario: str,
        session: int,
        turn_ref: str,
        role: str,
        content: str,
        importance: float = 0.5,
        meta: dict[str, Any] | None = None,
        created_utc: str | None = None,
    ) -> int:
        """Append one episode; returns its id. Appends are the only writes."""
        if not content.strip():
            raise ValueError("episode content must be non-empty")
        cur = self._conn.execute(
            "INSERT INTO episodes (created_utc, run_id, scenario, session, turn_ref,"
            " role, content, importance, meta) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                created_utc or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                run_id,
                scenario,
                int(session),
                turn_ref,
                role,
                content,
                float(importance),
                json.dumps(meta or {}, ensure_ascii=True, sort_keys=True),
            ),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    # -- read ------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        *,
        scenario: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        """Top-`limit` episodes of `scenario` ranked by keyword relevance.

        Ties break toward recency (higher id). Deterministic.
        """
        keywords = tokenize(query)
        rows = self._conn.execute(
            "SELECT * FROM episodes WHERE scenario = ? ORDER BY id", (scenario,)
        ).fetchall()
        scored = [
            (score_content(keywords, row["content"]), row) for row in rows
        ]
        scored = [(s, r) for s, r in scored if s > 0.0]
        scored.sort(key=lambda pair: (-pair[0], -pair[1]["id"]))
        return [dict(row) for _, row in scored[:limit]]

    def count(self, scenario: str | None = None) -> int:
        if scenario is None:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM episodes").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM episodes WHERE scenario = ?", (scenario,)
            ).fetchone()
        return int(row["n"])

    # -- portable export/import -------------------------------------------

    def export_dict(self) -> dict[str, Any]:
        """Model-neutral portable representation (the CONT-002 state carrier)."""
        rows = self._conn.execute("SELECT * FROM episodes ORDER BY id").fetchall()
        episodes = []
        for row in rows:
            episodes.append(
                {
                    "id": row["id"],
                    "created_utc": row["created_utc"],
                    "run_id": row["run_id"],
                    "scenario": row["scenario"],
                    "session": row["session"],
                    "turn_ref": row["turn_ref"],
                    "role": row["role"],
                    "content": row["content"],
                    "importance": row["importance"],
                    "meta": json.loads(row["meta"]),
                }
            )
        return {
            "format": EXPORT_FORMAT,
            "version": EXPORT_VERSION,
            "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "episode_count": len(episodes),
            "episodes": episodes,
        }

    def export_json(self, path: str) -> dict[str, Any]:
        data = self.export_dict()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        return data

    def import_dict(self, data: dict[str, Any], *, require_empty: bool = True) -> int:
        """Import episodes from a portable dict into this store.

        Ids are preserved; fails if the format/version is unknown or (by
        default) the store already holds episodes. Returns the imported count.
        """
        if data.get("format") != EXPORT_FORMAT:
            raise ValueError(f"unknown export format: {data.get('format')!r}")
        if data.get("version") != EXPORT_VERSION:
            raise ValueError(f"unsupported export version: {data.get('version')!r}")
        if require_empty and self.count() != 0:
            raise ValueError("import requires an empty store (use require_empty=False to append)")
        imported = 0
        for episode in data.get("episodes", []):
            missing = [f for f in _REQUIRED_EPISODE_FIELDS if f not in episode]
            if missing:
                raise ValueError(f"episode missing fields: {missing}")
            self._conn.execute(
                "INSERT OR REPLACE INTO episodes (id, created_utc, run_id, scenario,"
                " session, turn_ref, role, content, importance, meta)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    episode.get("id"),
                    episode["created_utc"],
                    episode["run_id"],
                    episode["scenario"],
                    int(episode["session"]),
                    episode["turn_ref"],
                    episode["role"],
                    episode["content"],
                    float(episode.get("importance", 0.5)),
                    json.dumps(episode.get("meta", {}), ensure_ascii=True, sort_keys=True),
                ),
            )
            imported += 1
        self._conn.commit()
        return imported

    def import_json(self, path: str, *, require_empty: bool = True) -> int:
        return self.import_dict(
            json.loads(Path(path).read_text(encoding="utf-8")),
            require_empty=require_empty,
        )

    def close(self) -> None:
        self._conn.close()


def _selftest() -> int:
    """Offline round-trip check: append, retrieve, export, import, compare."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store_path = str(Path(tmp) / "selftest.sqlite3")
        store = MemoryStore(store_path)
        store.append_episode(
            run_id="selftest", scenario="dr-0001", session=1, turn_ref="s1t1",
            role="environment",
            content="The lighthouse on Verdin Isle flashes every 7 minutes.",
        )
        store.append_episode(
            run_id="selftest", scenario="dr-0001", session=1, turn_ref="s1t1",
            role="assistant", content="Logged.",
        )
        store.append_episode(
            run_id="selftest", scenario="dr-0002", session=1, turn_ref="s1t1",
            role="environment", content="The observatory assistant is named Doran.",
        )
        hits = store.retrieve(
            "how many minutes pass between two flashes of the verdin isle lighthouse",
            scenario="dr-0001",
        )
        assert hits and "7 minutes" in hits[0]["content"], hits
        assert all(h["scenario"] == "dr-0001" for h in hits)  # scope respected
        assert store.retrieve("lighthouse", scenario="dr-0002") == []  # no leakage
        export = store.export_json(str(Path(tmp) / "export.json"))
        assert export["episode_count"] == 3
        restored = MemoryStore(str(Path(tmp) / "restored.sqlite3"))
        n = restored.import_json(str(Path(tmp) / "export.json"))
        assert n == 3
        assert restored.export_dict()["episodes"] == export["episodes"]  # round-trip
        hits2 = restored.retrieve(
            "how many minutes pass between two flashes of the verdin isle lighthouse",
            scenario="dr-0001",
        )
        assert [h["id"] for h in hits2] == [h["id"] for h in hits]  # same ranking
        store.close()
        restored.close()
    print("memory selftest ok: append/retrieve/export/import round-trip deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
