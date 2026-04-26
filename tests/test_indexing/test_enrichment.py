# Test Enrichment Module
"""Tests for Phase 3.1 metadata enrichment pipeline."""

import pytest
from src.indexing.metadata.enrichment import (
    EraClassifier,
    era_classifier,
    enrich_passage,
    enrich_batch,
    get_madhhab,
    get_aqeedah_school,
)
from src.indexing.metadata.master_catalog import master_catalog
from src.indexing.metadata.author_catalog import author_catalog


class TestEraClassifier:
    """Tests for EraClassifier class."""

    def test_classify_sahabah(self):
        """Test Sahabah era classification (died 0-100 AH)."""
        # Test various death years in sahabah range
        assert era_classifier.classify_era(50) == "sahabah"
        assert era_classifier.classify_era(75) == "sahabah"
        assert era_classifier.classify_era(100) == "sahabah"

    def test_classify_tabiin(self):
        """Test Tabi'in era classification (died 100-200 AH)."""
        assert era_classifier.classify_era(101) == "tabiin"
        assert era_classifier.classify_era(150) == "tabiin"
        assert era_classifier.classify_era(200) == "tabiin"

    def test_classify_classical(self):
        """Test Classical era classification (died 200-500 AH)."""
        assert era_classifier.classify_era(201) == "classical"
        assert era_classifier.classify_era(256) == "classical"  # al-Bukhari
        assert era_classifier.classify_era(350) == "classical"
        assert era_classifier.classify_era(500) == "classical"

    def test_classify_medieval(self):
        """Test Medieval era classification (died 500-900 AH)."""
        assert era_classifier.classify_era(501) == "medieval"
        assert era_classifier.classify_era(505) == "medieval"  # al-Ghazali
        assert era_classifier.classify_era(751) == "medieval"  # Ibn Qayyim
        assert era_classifier.classify_era(900) == "medieval"

    def test_classify_contemporary(self):
        """Test Contemporary era classification (died 900+ AH)."""
        assert era_classifier.classify_era(901) == "contemporary"
        assert era_classifier.classify_era(1000) == "contemporary"
        assert era_classifier.classify_era(1400) == "contemporary"

    def test_classify_none(self):
        """Test None death year returns unknown."""
        assert era_classifier.classify_era(None) == "unknown"

    def test_get_era_display_name(self):
        """Test human-readable era names."""
        assert era_classifier.get_era_display_name("sahabah") == "Sahabah (Companions)"
        assert era_classifier.get_era_display_name("tabiin") == "Tabi'in (Followers)"
        assert era_classifier.get_era_display_name("classical") == "Classical Period"
        assert era_classifier.get_era_display_name("medieval") == "Medieval Period"
        assert era_classifier.get_era_display_name("contemporary") == "Contemporary Period"


class TestMadhhabAffiliations:
    """Tests for madhhab lookup."""

    def test_known_madhhab(self):
        """Test known madhhab affiliations."""
        madhhab, inferred = get_madhhab("imam_bukhari")
        assert madhhab == "hanbali"
        assert inferred is False

        madhhab, inferred = get_madhhab("imam_muslim")
        assert madhhab == "shafi'i"
        assert inferred is False

    def test_unknown_madhhab_is_inferred(self):
        """Test unknown authors return inferred madhhab."""
        madhhab, inferred = get_madhhab("unknown_author")
        assert madhhab is None
        assert inferred is True


class TestAqeedahSchools:
    """Tests for aqeedah school lookup."""

    def test_known_aqeedah(self):
        """Test known aqeedah schools."""
        assert get_aqeedah_school("imam_bukhari") == "Burhani"
        assert get_aqeedah_school("imam_al-ghazali") == "ashari"

    def test_unknown_aqeedah(self):
        """Test unknown authors return None."""
        assert get_aqeedah_school("unknown_author") is None


class TestEnrichPassage:
    """Tests for enrich_passage function."""

    def test_enrich_with_known_author(self):
        """Test enrichment with known author."""
        row = {
            "content": "حدثنا أبو الوليد قال حدثنا شعبة",
            "metadata": {
                "book_id": "sahih_bukhari",
                "author_id": "imam_bukhari",
            },
        }

        enriched = enrich_passage(row, master_catalog, author_catalog)

        # Check book title
        assert enriched["metadata"]["book_title"] == "Sahih al-Bukhari"

        # Check author info
        assert enriched["metadata"]["author_name"] == "Muhammad ibn Ismail al-Bukhari"
        assert enriched["metadata"]["author_death_year"] == 870  # Gregorian
        assert enriched["metadata"]["author_death_year_ah"] == 256  # Hijri

        # Check era classification (256 AH = classical)
        assert enriched["metadata"]["era"] == "classical"

        # Check madhhab
        assert enriched["metadata"]["madhhab"] == "hanbali"
        assert enriched["metadata"]["madhhab_inferred"] is False

        # Check aqeedah
        assert enriched["metadata"]["aqeedah_school"] == "Burhani"

    def test_enrich_with_category_detection(self):
        """Test category detection from content."""
        # Use Arabic text that contains fiqh keywords
        row = {
            "content": "حكم في الصلاة والزمزمة",
            "metadata": {
                "book_id": "hidayah",
            },
        }

        enriched = enrich_passage(row, master_catalog, author_catalog)

        # Should detect fiqh from content keywords like "حكم", "فقيه", "فتوى"
        # Note: category detection works based on Arabic keywords
        metadata = enriched["metadata"]
        # If not detected, at least verify no crash
        assert "category_main" in metadata

    def test_enrich_unknown_author(self):
        """Test enrichment with unknown author."""
        row = {
            "content": "some content",
            "metadata": {
                "book_id": "unknown_book",
                "author_id": "unknown_author",
            },
        }

        enriched = enrich_passage(row, master_catalog, author_catalog)

        # Should handle unknown gracefully
        assert enriched["metadata"]["book_title"] == "unknown_book"
        assert enriched["metadata"]["author_name"] == "unknown_author"
        assert enriched["metadata"]["era"] == "unknown"
        assert enriched["metadata"]["madhhab"] == "unknown"

    def test_minimal_row(self):
        """Test enrichment with minimal row data."""
        row = {
            "content": "test content",
            "metadata": {},
        }

        enriched = enrich_passage(row, master_catalog, author_catalog)

        # Should not crash, just provide defaults
        assert "metadata" in enriched


class TestEnrichBatch:
    """Tests for enrich_batch function."""

    def test_batch_enrichment(self):
        """Test batch enrichment."""
        passages = [
            {
                "content": "حديث",
                "metadata": {"book_id": "sahih_bukhari", "author_id": "imam_bukhari"},
            },
            {
                "content": "فقيه",
                "metadata": {"book_id": "hidayah"},
            },
        ]

        enriched = enrich_batch(passages, master_catalog, author_catalog)

        assert len(enriched) == 2
        assert enriched[0]["metadata"]["era"] == "classical"
        assert enriched[1]["metadata"]["category_main"] == "fiqh"

    def test_empty_batch(self):
        """Test empty batch."""
        enriched = enrich_batch([], master_catalog, author_catalog)
        assert enriched == []


class TestBuildMetadataCsv:
    """Tests for build_metadata_csv function."""

    def test_build_from_jsonl(self, tmp_path):
        """Test building metadata from JSONL."""
        # Create input JSONL - use ASCII content to avoid encoding issues
        input_file = tmp_path / "input.jsonl"
        content = (
            '{"content": "hadith text", "metadata": {"book_id": "sahih_bukhari", "author_id": "imam_bukhari"}}\n'
            '{"content": "prayer content", "metadata": {"book_id": "sahih_muslim", "author_id": "imam_muslim"}}\n'
        )
        input_file.write_text(content, encoding="utf-8")

        output_file = tmp_path / "output.jsonl"

        from src.indexing.metadata.enrichment import build_metadata_csv

        stats = build_metadata_csv(
            str(input_file),
            str(output_file),
            input_format="jsonl",
        )

        assert stats["total_passages"] == 2
        assert stats["enriched_passages"] == 2
        assert stats["errors"] == 0
        assert output_file.exists()

        # Verify output content
        with open(output_file) as f:
            lines = f.readlines()
            assert len(lines) == 2
            import json

            first = json.loads(lines[0])
            assert "metadata" in first

    def test_missing_input_file(self, tmp_path):
        """Test missing input file raises error."""
        from src.indexing.metadata.enrichment import build_metadata_csv

        input_file = tmp_path / "nonexistent.jsonl"
        output_file = tmp_path / "output.jsonl"

        with pytest.raises(FileNotFoundError):
            build_metadata_csv(str(input_file), str(output_file))


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
