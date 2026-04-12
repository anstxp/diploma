from __future__ import annotations

from pathlib import Path

import pytest

from neuro_api.narrative.narrative_engine import (
    NarrativeReport,
    build_narrative,
    load_clusters,
)


_NARRATIVE_DIR = Path(__file__).resolve().parent.parent / "neuro_api" / "narrative"
_TEMPLATES_DIR = _NARRATIVE_DIR / "templates"


class TestClustersConfig:

    def test_clusters_yaml_exists(self):
        assert (_NARRATIVE_DIR / "clusters.yaml").exists()

    def test_clusters_load(self):
        clusters = load_clusters()
        assert isinstance(clusters, list)
        assert len(clusters) == 13, f"Expected 13 clusters, got {len(clusters)}"

    def test_clusters_have_required_keys(self):
        for c in load_clusters():
            assert "id" in c
            assert "tier" in c
            assert "priority" in c

    def test_cluster_ids_unique(self):
        ids = [c["id"] for c in load_clusters()]
        assert len(ids) == len(set(ids))

    def test_priorities_are_numeric(self):
        for c in load_clusters():
            assert isinstance(c["priority"], (int, float))

    def test_safety_critical_clusters_present(self):
        ids = {c["id"] for c in load_clusters()}
        has_depression = any("depression" in cid for cid in ids)
        has_sleep = any("sleep" in cid for cid in ids)
        assert has_depression, f"No depression cluster in {ids}"
        assert has_sleep, f"No sleep cluster in {ids}"


class TestTemplateFiles:

    def test_templates_dir_exists(self):
        assert _TEMPLATES_DIR.is_dir()

    def test_templates_pair_uk_and_en(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        uk = {p.stem.replace(".uk", "") for p in _TEMPLATES_DIR.glob("*.uk.md")}
        en = {p.stem.replace(".en", "") for p in _TEMPLATES_DIR.glob("*.en.md")}
        missing_uk = cluster_ids - uk
        missing_en = cluster_ids - en
        assert not missing_uk, f"Missing UK: {missing_uk}"
        assert not missing_en, f"Missing EN: {missing_en}"

    def test_template_count(self):
        assert len(list(_TEMPLATES_DIR.glob("*.uk.md"))) == 13
        assert len(list(_TEMPLATES_DIR.glob("*.en.md"))) == 13

    def test_templates_non_empty(self):
        for p in _TEMPLATES_DIR.glob("*.md"):
            assert p.stat().st_size > 0, f"empty: {p.name}"

    def test_no_orphan_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for p in _TEMPLATES_DIR.glob("*.md"):
            stem_parts = p.name.rsplit(".", 2)
            cid = stem_parts[0]
            assert cid in cluster_ids, f"orphan: {p.name}"


class TestBuildNarrative:

    def test_returns_narrative_report(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        narr = build_narrative(result, lang="uk")
        assert isinstance(narr, NarrativeReport)

    def test_uk_lang(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        narr = build_narrative(result, lang="uk")
        assert narr.lang == "uk"

    def test_en_lang(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        narr = build_narrative(result, lang="en")
        assert narr.lang == "en"

    def test_to_dict_serializable(self, predictor, metabolic_at_risk):
        import json
        result = predictor.predict(metabolic_at_risk)
        narr = build_narrative(result, lang="uk")
        d = narr.to_dict()
        json.dumps(d)

    def test_insufficient_renders_cluster(self, predictor, empty_payload):
        result = predictor.predict(empty_payload)
        narr = build_narrative(result, lang="uk")
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert any(
            "insufficient" in cid or "incomplete" in cid or "low_overall" in cid
            for cid in cluster_ids
        )

    def test_stories_have_required_fields(self, predictor, metabolic_at_risk):
        result = predictor.predict(metabolic_at_risk)
        narr = build_narrative(result, lang="uk")
        for story in narr.stories:
            assert story.title
            assert story.body
            assert story.cluster_id
