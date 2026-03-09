from __future__ import annotations

from pathlib import Path

import pytest

from chem_api.chem.analyze import analyze_chem_payload
from chem_api.narrative.narrative_engine import (
    NarrativeReport,
    build_narrative,
    load_clusters,
)


_NARRATIVE_DIR = Path(__file__).resolve().parent.parent / "chem_api" / "narrative"
_TEMPLATES_DIR = _NARRATIVE_DIR / "templates"



class TestClustersConfig:

    def test_clusters_yaml_exists(self):
        assert (_NARRATIVE_DIR / "clusters.yaml").exists()

    def test_clusters_load(self):
        clusters = load_clusters()
        assert isinstance(clusters, list)
        assert len(clusters) == 48, f"Expected 48 clusters, got {len(clusters)}"

    def test_clusters_have_required_keys(self):
        for c in load_clusters():
            assert "id" in c, f"cluster missing id: {c}"
            assert isinstance(c, dict)

    def test_cluster_ids_unique(self):
        ids = [c["id"] for c in load_clusters()]
        assert len(ids) == len(set(ids))



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
        assert len(uk_files) == 48
        assert len(en_files) == 48

    def test_templates_non_empty(self):
        for p in _TEMPLATES_DIR.glob("*.md"):
            assert p.stat().st_size > 0, f"empty template: {p.name}"

    def test_no_orphan_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for p in _TEMPLATES_DIR.glob("*.md"):
            stem_parts = p.name.rsplit(".", 2)
            cid = stem_parts[0]
            assert cid in cluster_ids, f"orphan: {p.name}"



class TestBuildNarrative:

    def test_returns_narrative_report(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        assert isinstance(narr, NarrativeReport)

    def test_iron_deficiency_story(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        assert narr.lang == "uk"
        assert len(narr.stories) > 0
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert "iron_deficiency" in cluster_ids

    def test_english_renders(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        narr = build_narrative(r, lang="en")
        assert narr.lang == "en"
        assert len(narr.stories) > 0

    def test_healthy_returns_all_normal(self, healthy_male):
        r = analyze_chem_payload(healthy_male)
        narr = build_narrative(r, lang="uk")
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert "all_normal" in cluster_ids or len(narr.stories) == 0

    def test_incomplete_returns_incomplete_cluster(self, incomplete_panel):
        r = analyze_chem_payload(incomplete_panel)
        narr = build_narrative(r, lang="uk")
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert "incomplete" in cluster_ids

    def test_diabetes_renders_diabetes_pattern(self, diabetes):
        r = analyze_chem_payload(diabetes)
        narr = build_narrative(r, lang="uk")
        cluster_ids = {s.cluster_id for s in narr.stories}
        assert any("diabetes" in cid for cid in cluster_ids)

    def test_stories_have_required_fields(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        for story in narr.stories:
            assert story.title
            assert story.body
            assert story.cluster_id

    def test_to_dict_works(self, iron_deficiency):
        r = analyze_chem_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        d = narr.to_dict()
        assert isinstance(d, dict)
        assert "stories" in d



class TestClusterTemplateIntegrity:

    def test_every_cluster_has_both_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            uk_path = _TEMPLATES_DIR / f"{cid}.uk.md"
            en_path = _TEMPLATES_DIR / f"{cid}.en.md"
            assert uk_path.exists(), f"missing {cid}.uk.md"
            assert en_path.exists(), f"missing {cid}.en.md"
