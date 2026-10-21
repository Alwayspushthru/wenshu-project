"""学校资料同步必须保留既有治理状态，并将新素材路由到正确部门。"""
from pathlib import Path

import pytest

from app.memory.global_memory import GlobalMemory
from app.harness.agents.dept_router import DeptRouter
from app.harness.agents.intent_agent import IntentAgent
from app.storage.store import MemoryStore
from scripts.ingest_department_files import resolve_dept
from scripts.seed_data import seed_school_profile


@pytest.mark.asyncio
async def test_school_profile_refresh_preserves_department_state():
    store = MemoryStore()
    existing = {
        "_id": "dept_hqaq", "name": "保卫处",
        "admin_users": ["security_admin"],
        "agent_config": {"model": "custom-model", "temperature": 0.2},
        "review_stats": {"total": 20, "correct": 19, "accuracy": 0.95},
        "loop_phase": "human_on_loop", "created_at": "2025-01-01",
    }
    await store.upsert_department(existing)
    memory = GlobalMemory(store)
    await seed_school_profile(store, memory)
    await seed_school_profile(store, memory)

    refreshed = await store.get_department("dept_hqaq")
    assert refreshed["name"] == "安全保卫部"
    for field in ("admin_users", "agent_config", "review_stats", "loop_phase", "created_at"):
        assert refreshed[field] == existing[field]
    aliases = await store.find("glossary", {"canonical": "安全保卫部"})
    assert len(aliases) == 1
    assert "保卫处" in aliases[0]["synonyms"]
    assert (await store.get_department("dept_tsg"))["name"] == "图书馆"
    calendar = await memory.get_calendar()
    assert calendar["academic_year"] == "2025-2026"
    assert calendar["current_semester"] is None
    assert len(calendar["semesters"]) == 2
    assert "week16_20" not in calendar


@pytest.mark.parametrize(("directory", "dept_id"), [
    ("教务处", "dept_jwc"),
    ("图书馆", "dept_tsg"),
    ("电子信息学院", "dept_zfxy"),
    ("安全保卫部", "dept_hqaq"),
    ("保卫处", "dept_hqaq"),
])
def test_new_material_directories_have_department_routes(directory, dept_id):
    assert resolve_dept(Path("/app/department_files/杭州电子科技大学") / directory / "指南.md") == dept_id


@pytest.mark.parametrize(("query", "expected_dept"), [
    ("杭电毕业证明书补办需要哪些材料，可以委托办理吗？", "dept_jwc"),
    ("在校外怎样访问杭电图书馆数据库？", "dept_tsg"),
    ("研究生导师变更申请表需要哪些签字？", "dept_zfxy"),
    ("研究生申请退修课程需要什么表？", "dept_zfxy"),
    ("保卫处可以办理哪些事项？", "dept_hqaq"),
])
def test_school_questions_reach_departments_with_matching_materials(query, expected_dept):
    valid = {"dept_jwc", "dept_tsg", "dept_zfxy", "dept_yjsy", "dept_hqaq"}
    matched, _ = DeptRouter._keyword_match(query, valid)
    assert expected_dept in matched
    assert expected_dept in IntentAgent._keyword_fallback(query).depts
