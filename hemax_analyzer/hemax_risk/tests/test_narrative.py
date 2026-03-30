from __future__ import annotations

from pathlib import Path

import pytest

from risk_api.narrative.narrative_engine import (
    NarrativeReport,
    build_narrative,
    load_clusters,
)


_NARRATIVE_DIR = Path(__file__).resolve().parent.parent / "risk_api" / "narrative"
_TEMPLATES_DIR = _NARRATIVE_DIR / "templates"



class TestClustersConfig:

    def test_clusters_yaml_exists(self):
        assert (_NARRATIVE_DIR / "clusters.yaml").exists()

    def test_clusters_load(self):
        clusters = load_clusters()
        assert isinstance(clusters, list)
        assert len(clusters) == 17, f"Expected 17 clusters, got {len(clusters)}"

    def test_clusters_have_required_keys(self):
        for c in load_clusters():
            assert "id" in c, f"cluster missing id: {c}"
            assert "tier" in c
            assert "priority" in c

    def test_cluster_ids_unique(self):
        ids = [c["id"] for c in load_clusters()]
        assert len(ids) == len(set(ids))

    def test_tiers_are_valid(self):
        valid = {"critical", "abnormal", "info", "normal", "high", "moderate", "low"}
        for c in load_clusters():
            assert c["tier"] in valid, f"unknown tier in {c['id']}: {c['tier']}"

    def test_priorities_are_numeric(self):
        for c in load_clusters():
            assert isinstance(c["priority"], (int, float))



class TestTemplateFiles:

    def test_templates_dir_exists(self):
        assert _TEMPLATES_DIR.is_dir()

    def test_templates_pair_uk_and_en(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        uk = {p.stem.replace(".uk", "") for p in _TEMPLATES_DIR.glob("*.uk.md")}
        en = {p.stem.replace(".en", "") for p in _TEMPLATES_DIR.glob("*.en.md")}

        missing_uk = cluster_ids - uk
        missing_en = cluster_ids - en

        assert not missing_uk, f"Clusters missing UK template: {missing_uk}"
        assert not missing_en, f"Clusters missing EN template: {missing_en}"

    def test_total_template_count(self):
        uk_files = list(_TEMPLATES_DIR.glob("*.uk.md"))
        en_files = list(_TEMPLATES_DIR.glob("*.en.md"))
        assert len(uk_files) == 17
        assert len(en_files) == 17

    def test_templates_non_empty(self):
        for p in _TEMPLATES_DIR.glob("*.md"):
            assert p.stat().st_size > 0, f"empty template: {p.name}"

    def test_no_orphan_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for p in _TEMPLATES_DIR.glob("*.md"):
            stem_parts = p.name.rsplit(".", 2)
            cid = stem_parts[0]
            assert cid in cluster_ids, f"orphan template: {p.name}"



class TestBuildNarrative:

    def test_returns_narrative_report(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="uk")
        assert isinstance(narr, NarrativeReport)

    def test_uk_lang(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="uk")
        assert narr.lang == "uk"
        assert len(narr.stories) > 0

    def test_en_lang(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="en")
        assert narr.lang == "en"

    def test_low_risk_renders_some_cluster(self, predictor, low_risk_young):
        result = predictor.predict(low_risk_young)
        narr = build_narrative(result, lang="uk")
        assert len(narr.stories) >= 1

    def test_incomplete_renders_insufficient_or_incomplete_cluster(
        self, predictor, empty_payload
    ):
        result = predictor.predict(empty_payload)
        narr = build_narrative(result, lang="uk")
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert any(
            "insufficient" in cid or "incomplete" in cid
            for cid in cluster_ids
        ), f"Expected insufficient/incomplete cluster, got: {cluster_ids}"

    def test_overall_tier_in_report(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="uk")
        assert hasattr(narr, "overall_tier")
        assert narr.overall_tier in ("very_low", "low", "moderate", "high",
                                      "very_high", "insufficient_data")

    def test_stories_have_required_fields(self, predictor, diabetic_patient):
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="uk")
        for story in narr.stories:
            assert story.title
            assert story.body
            assert story.cluster_id

    def test_to_dict_serializable(self, predictor, diabetic_patient):
        import json
        result = predictor.predict(diabetic_patient)
        narr = build_narrative(result, lang="uk")
        d = narr.to_dict()
        json.dumps(d)



class TestClusterTemplateIntegrity:

    def test_every_cluster_has_both_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            assert (_TEMPLATES_DIR / f"{cid}.uk.md").exists()
            assert (_TEMPLATES_DIR / f"{cid}.en.md").exists()
