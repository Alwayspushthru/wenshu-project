"""种子数据：部门 / 术语表 / FAQ / 校历 / 默认 Rules&Hooks。

用法：python -m scripts.seed_data
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.deps import build_container
from app.loop.default_skills import seed_default_skills

DEPARTMENTS = [
    {"_id": "dept_jwc", "name": "教务处", "name_en": "Academic Affairs", "category": "academic"},
    {"_id": "dept_xsc", "name": "学生处", "name_en": "Student Affairs", "category": "student"},
    {"_id": "dept_cwc", "name": "财务处", "name_en": "Finance", "category": "finance"},
    {"_id": "dept_rsc", "name": "人事处", "name_en": "Human Resources", "category": "admin"},
    {"_id": "dept_yjsy", "name": "研究生院", "name_en": "Graduate School", "category": "academic"},
    {"_id": "dept_zfxy", "name": "电子信息学院", "name_en": "School of Electronic Information", "category": "academic"},
    {"_id": "dept_hqaq", "name": "安全保卫部", "name_en": "Security Department", "category": "logistics"},
    {"_id": "dept_tsg", "name": "图书馆", "name_en": "Library", "category": "academic"},
]

GLOSSARY = [
    {"canonical": "辅导员", "synonyms": ["班主任", "导师", "辅导员老师"]},
    {"canonical": "退课", "synonyms": ["退选", "撤销选课", "drop 课"]},
    {"canonical": "学费", "synonyms": ["培养费", "学杂费"]},
    {"canonical": "选课", "synonyms": ["选课系统", "抢课", "课程注册"]},
    {"canonical": "学分", "synonyms": ["学分制", "学分数"]},
    {"_id": "glossary_hdu_security", "canonical": "安全保卫部", "synonyms": ["保卫处"]},
]

CALENDAR = json.loads(
    (Path(__file__).resolve().parents[1] / "app/school_profiles/hdu_calendar_2025_2026.json").read_text(encoding="utf-8")
)


async def seed_school_profile(store, global_memory) -> None:
    """更新学校资料，同时保留已有部门的管理员、审核进度与 Agent 配置。"""
    now = datetime.now(timezone.utc).isoformat()
    for dept in DEPARTMENTS:
        d = {**(await store.get_department(dept["_id"]) or {}), **dept}
        d.setdefault("admin_users", [])
        d.setdefault("agent_config", {"model": "deepseek-v4-flash", "temperature": 0.1, "max_tokens": 2048})
        d.setdefault("loop_phase", "human_in_loop")
        d.setdefault("review_stats", {"total": 0, "correct": 0, "accuracy": 0.0})
        d.setdefault("created_at", now)
        d["updated_at"] = now
        await store.upsert_department(d)
        print(f"[dept] {d['_id']} {d['name']}")

    for i, g in enumerate(GLOSSARY):
        entry = {
            "_id": g.get("_id", f"glossary_seed_{i}"),
            "canonical": g["canonical"],
            "synonyms": g["synonyms"],
            "dept_id": "",
            "created_by": "seed",
            "created_at": now,
        }
        await store.upsert_glossary(entry)
    print(f"[glossary] {len(GLOSSARY)} 条")

    await global_memory.set_calendar(CALENDAR)
    print("[calendar] 校历已写入全局记忆")


async def main() -> None:
    settings = get_settings()
    container = build_container(settings)
    if container.mongo is not None:
        await container.mongo.connect()
    if hasattr(container.session_store, "connect"):
        try:
            await container.session_store.connect()
        except Exception:
            pass

    await seed_school_profile(container.store, container.global_memory)
    await container.rule_engine.seed_defaults()
    await container.hook_engine.seed_defaults()
    print("[rules/hooks] 默认规则与钩子已种子化")
    created_skills = await seed_default_skills(container.store)
    print(f"[skills] 可执行基线 Skill 已就绪（本次新增 {created_skills}）")

    if container.mongo is not None:
        await container.mongo.close()


if __name__ == "__main__":
    asyncio.run(main())
