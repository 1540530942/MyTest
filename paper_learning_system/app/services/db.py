from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for field in ("analysis",):
        if data.get(field):
            data[field] = json.loads(data[field])
    return data


def ensure_db(db_path: Path) -> None:
    with connect(db_path) as db:
        db.executescript(
            """
            create table if not exists papers (
              id integer primary key autoincrement,
              external_id text unique,
              source text not null default 'manual',
              title text not null,
              authors text not null default '',
              abstract text not null default '',
              url text not null default '',
              pdf_url text not null default '',
              published text not null default '',
              categories text not null default '',
              analysis text,
              created_at text not null,
              updated_at text not null
            );

            create table if not exists notes (
              id integer primary key autoincrement,
              paper_id integer not null references papers(id) on delete cascade,
              content text not null,
              created_at text not null
            );

            create table if not exists practice_items (
              id integer primary key autoincrement,
              paper_id integer not null references papers(id) on delete cascade,
              question text not null,
              answer text not null,
              kind text not null default 'concept',
              created_at text not null
            );
            """
        )


def normalize_paper(raw: dict[str, Any]) -> dict[str, Any]:
    external_id = str(raw.get("external_id") or raw.get("id") or "").strip() or None
    authors = raw.get("authors") or ""
    if isinstance(authors, list):
        authors = ", ".join(str(author) for author in authors)
    categories = raw.get("categories") or ""
    if isinstance(categories, list):
        categories = ", ".join(str(category) for category in categories)

    return {
        "external_id": external_id,
        "source": str(raw.get("source") or "manual").strip(),
        "title": str(raw.get("title") or "Untitled paper").strip(),
        "authors": str(authors).strip(),
        "abstract": str(raw.get("abstract") or raw.get("summary") or "").strip(),
        "url": str(raw.get("url") or raw.get("entry_url") or "").strip(),
        "pdf_url": str(raw.get("pdf_url") or "").strip(),
        "published": str(raw.get("published") or "").strip(),
        "categories": str(categories).strip(),
    }


def save_paper(db_path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    paper = normalize_paper(raw)
    now = utc_now()
    with connect(db_path) as db:
        if paper["external_id"]:
            existing = db.execute("select * from papers where external_id = ?", (paper["external_id"],)).fetchone()
            if existing:
                db.execute(
                    """
                    update papers
                    set source = ?, title = ?, authors = ?, abstract = ?, url = ?, pdf_url = ?,
                        published = ?, categories = ?, updated_at = ?
                    where external_id = ?
                    """,
                    (
                        paper["source"],
                        paper["title"],
                        paper["authors"],
                        paper["abstract"],
                        paper["url"],
                        paper["pdf_url"],
                        paper["published"],
                        paper["categories"],
                        now,
                        paper["external_id"],
                    ),
                )
                row = db.execute("select * from papers where external_id = ?", (paper["external_id"],)).fetchone()
                assert row is not None
                return row_to_dict(row) or {}

        cursor = db.execute(
            """
            insert into papers
              (external_id, source, title, authors, abstract, url, pdf_url, published, categories, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper["external_id"],
                paper["source"],
                paper["title"],
                paper["authors"],
                paper["abstract"],
                paper["url"],
                paper["pdf_url"],
                paper["published"],
                paper["categories"],
                now,
                now,
            ),
        )
        row = db.execute("select * from papers where id = ?", (cursor.lastrowid,)).fetchone()
        assert row is not None
        return row_to_dict(row) or {}


def create_manual_paper(db_path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    raw = dict(raw)
    raw.setdefault("source", "manual")
    return save_paper(db_path, raw)


def list_papers(db_path: Path) -> list[dict[str, Any]]:
    with connect(db_path) as db:
        rows = db.execute("select * from papers order by updated_at desc, id desc").fetchall()
        return [row_to_dict(row) or {} for row in rows]


def get_paper(db_path: Path, paper_id: int) -> dict[str, Any] | None:
    with connect(db_path) as db:
        row = db.execute("select * from papers where id = ?", (paper_id,)).fetchone()
        return row_to_dict(row)


def save_analysis(db_path: Path, paper_id: int, analysis: dict[str, Any]) -> None:
    with connect(db_path) as db:
        db.execute(
            "update papers set analysis = ?, updated_at = ? where id = ?",
            (json.dumps(analysis, ensure_ascii=False), utc_now(), paper_id),
        )


def save_practice_items(db_path: Path, paper_id: int, items: list[dict[str, str]]) -> None:
    now = utc_now()
    with connect(db_path) as db:
        db.execute("delete from practice_items where paper_id = ?", (paper_id,))
        db.executemany(
            """
            insert into practice_items (paper_id, question, answer, kind, created_at)
            values (?, ?, ?, ?, ?)
            """,
            [
                (
                    paper_id,
                    item.get("question", ""),
                    item.get("answer", ""),
                    item.get("kind", "concept"),
                    now,
                )
                for item in items
            ],
        )


def list_practice_items(db_path: Path, paper_id: int) -> list[dict[str, Any]]:
    with connect(db_path) as db:
        rows = db.execute(
            """
            select id, paper_id, question, answer, kind, created_at
            from practice_items
            where paper_id = ?
            order by id asc
            """,
            (paper_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def add_note(db_path: Path, paper_id: int, content: str) -> dict[str, Any]:
    with connect(db_path) as db:
        cursor = db.execute(
            "insert into notes (paper_id, content, created_at) values (?, ?, ?)",
            (paper_id, content, utc_now()),
        )
        row = db.execute("select * from notes where id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row) if row else {}


def list_notes(db_path: Path, paper_id: int) -> list[dict[str, Any]]:
    with connect(db_path) as db:
        rows = db.execute("select * from notes where paper_id = ? order by id desc", (paper_id,)).fetchall()
        return [dict(row) for row in rows]
