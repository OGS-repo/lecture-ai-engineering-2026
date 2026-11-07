"""ツールのテスト（LLMもAPIキーも使わない）。"""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} の related に存在しない id: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start タグ"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("エージェント"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "見つかりませんでした" in tools.search_glossary("存在しない用語xyz")


def test_lecture_summary():
    assert "エージェント" in tools.get_lecture_summary(3)
    assert "まだありません" in tools.get_lecture_summary(99)


def test_make_quiz_selects_term_from_requested_lecture(monkeypatch):
    monkeypatch.setattr(
        tools.random,
        "choice",
        lambda terms: next(entry for entry in terms if entry["term"] == "LoRA"),
    )

    quiz = json.loads(tools.make_quiz(2))

    assert quiz["question"] == "LoRAの意味は？"
    assert quiz["answer"] == next(
        entry["definition"] for entry in tools.load_glossary()
        if entry["term"] == "LoRA"
    )


def test_make_quiz_reports_when_lecture_has_no_terms():
    assert "第99回" in tools.make_quiz(99)
    assert "ありません" in tools.make_quiz(99)


def test_save_learning_log_writes_utf8_file(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LEARNING_LOG_DIR", tmp_path)

    message = tools.save_learning_log("今日の学び: 承認フロー")

    saved_files = list(tmp_path.glob("*.md"))
    assert len(saved_files) == 1
    assert saved_files[0].read_text(encoding="utf-8") == "今日の学び: 承認フロー"
    assert saved_files[0].name in message


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """第1回の既定の質問（app.ask）は、第3回のエージェントが用語集で正しく答えられること。"""
    from app.ask import DEFAULT_QUESTION

    assert "3レベル" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3レベル"))
    assert hits[0]["term"] == "宿題の3レベル"
