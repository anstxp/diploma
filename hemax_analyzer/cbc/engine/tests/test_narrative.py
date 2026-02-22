from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cbc_api.analyze import analyze_cbc_payload
from cbc_api.narrative.narrative_engine import (
    NarrativeReport,
    NarrativeStory,
    build_narrative,
    chrome,
    load_clusters,
)



_NARRATIVE_DIR = Path(__file__).resolve().parent.parent / "cbc_api" / "narrative"
_TEMPLATES_DIR = _NARRATIVE_DIR / "templates"


class TestClustersConfig:

    def test_clusters_yaml_exists(self):
        assert (_NARRATIVE_DIR / "clusters.yaml").exists()

    def test_clusters_load(self):
        clusters = load_clusters()
        assert isinstance(clusters, list)
        assert len(clusters) >= 30

    def test_clusters_have_required_keys(self):
        clusters = load_clusters()
        for c in clusters:
            assert "id" in c
            assert "tier" in c
            assert c["tier"] in ("critical", "abnormal", "info", "minor", "normal")

    def test_cluster_ids_are_unique(self):
        ids = [c["id"] for c in load_clusters()]
        assert len(ids) == len(set(ids))

    def test_total_cluster_count(self):
        clusters = load_clusters()
        assert len(clusters) == 31

    def test_priority_field_present(self):
        for c in load_clusters():
            assert "priority" in c, f"cluster {c['id']} has no priority"



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
        assert len(uk_files) == 31
        assert len(en_files) == 31

    def test_neutrophilic_leukocytosis_en_template_exists(self):
        assert (_TEMPLATES_DIR / "neutrophilic_leukocytosis.en.md").exists()

    def test_templates_non_empty(self):
        for p in _TEMPLATES_DIR.glob("*.md"):
            assert p.stat().st_size > 0, f"empty template: {p.name}"

    def test_templates_have_frontmatter_separator(self):
        for p in _TEMPLATES_DIR.glob("*.md"):
            text = p.read_text(encoding="utf-8")
            assert "---" in text, f"missing --- separator in {p.name}"



class TestBuildNarrative:

    def test_returns_narrative_report(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        assert isinstance(narr, NarrativeReport)

    def test_iron_deficiency_uk_story(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        assert narr.lang == "uk"
        assert len(narr.stories) > 0
        assert isinstance(narr.stories[0], NarrativeStory)

    def test_english_renders(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        narr = build_narrative(r, lang="en")
        assert narr.lang == "en"
        assert len(narr.stories) > 0

    def test_healthy_returns_all_normal_cluster(self, healthy_male):
        r = analyze_cbc_payload(healthy_male)
        narr = build_narrative(r, lang="uk")
        cluster_ids = {st.cluster_id for st in narr.stories}
        assert "all_normal" in cluster_ids

    def test_incomplete_returns_incomplete_cluster(self, incomplete_panel):
        r = analyze_cbc_payload(incomplete_panel)
        narr = build_narrative(r, lang="uk")
        cluster_ids = {st.cluster_id for st in narr.stories}
        assert "incomplete" in cluster_ids

    def test_story_has_title_and_body(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        for story in narr.stories:
            assert story.title
            assert story.body
            assert story.severity in ("high", "medium", "low", "info", "normal")

    def test_story_lists_signals_used(self, iron_deficiency):
        r = analyze_cbc_payload(iron_deficiency)
        narr = build_narrative(r, lang="uk")
        relevant_sigs = set()
        for st in narr.stories:
            relevant_sigs.update(st.signals_used or [])
        assert relevant_sigs



class TestChrome:

    def test_uk_labels_present(self):
        c = chrome("uk")
        for key in ("tier_label", "summary", "actions_header", "red_flags_header"):
            assert key in c

    def test_en_labels_present(self):
        c = chrome("en")
        for key in ("tier_label", "summary", "actions_header", "red_flags_header"):
            assert key in c

    def test_all_tier_labels_present(self):
        for lang in ("uk", "en"):
            c = chrome(lang)
            for tier in ("critical", "abnormal", "info", "minor", "normal"):
                assert tier in c["tier_label"]

    def test_uk_and_en_differ(self):
        assert chrome("uk")["actions_header"] != chrome("en")["actions_header"]



class TestClusterTemplateIntegrity:

    def test_every_cluster_has_at_least_one_template_file(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for cid in cluster_ids:
            uk_path = _TEMPLATES_DIR / f"{cid}.uk.md"
            en_path = _TEMPLATES_DIR / f"{cid}.en.md"
            assert uk_path.exists() and en_path.exists(), (
                f"cluster '{cid}' missing template: "
                f"uk={uk_path.exists()}, en={en_path.exists()}"
            )

    def test_no_orphan_templates(self):
        cluster_ids = {c["id"] for c in load_clusters()}
        for p in _TEMPLATES_DIR.glob("*.md"):
            stem_parts = p.name.rsplit(".", 2)
            cluster_id = stem_parts[0]
            assert cluster_id in cluster_ids, (
                f"orphan template file {p.name} — no matching cluster"
            )
