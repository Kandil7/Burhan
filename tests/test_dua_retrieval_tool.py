"""
Tests for Dua Retrieval Tool.

Tests retrieval by occasion, category, and search.
"""
import pytest
from src.tools.dua_retrieval_tool import DuaRetrievalTool


class TestDuaRetrievalTool:
    """Test suite for DuaRetrievalTool."""
    
    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return DuaRetrievalTool()
    
    # ==========================================
    # Initialization Tests
    # ==========================================
    
    def test_load_duas(self, tool):
        """Test duas are loaded from database."""
        assert len(tool.duas) > 0
    
    def test_dua_structure(self, tool):
        """Test dua has required fields."""
        dua = tool.duas[0]
        required_fields = [
            "id", "category", "occasion", "arabic_text",
            "translation", "source", "reference", "grade"
        ]
        for field in required_fields:
            assert field in dua
    
    # ==========================================
    # Occasion Retrieval Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_retrieve_by_occasion_morning(self, tool):
        """Test retrieving morning adhkar."""
        result = await tool.execute(occasion="morning")
        
        assert result.success
        assert result.result["count"] > 0
        for dua in result.result["duas"]:
            assert dua["occasion"] == "morning"
    
    @pytest.mark.asyncio
    async def test_retrieve_by_occasion_evening(self, tool):
        """Test retrieving evening adhkar."""
        result = await tool.execute(occasion="evening")
        
        assert result.success
        assert result.result["count"] > 0
    
    @pytest.mark.asyncio
    async def test_retrieve_by_occasion_travel(self, tool):
        """Test retrieving travel duas."""
        result = await tool.execute(occasion="traveling")
        
        assert result.success
    
    # ==========================================
    # Category Retrieval Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_retrieve_by_category(self, tool):
        """Test retrieving by category."""
        result = await tool.execute(category="food")
        
        assert result.success
        for dua in result.result["duas"]:
            assert dua["category"] == "food"
    
    # ==========================================
    # Search Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_search_by_query(self, tool):
        """Test searching duas by query."""
        result = await tool.execute(query="morning")
        
        assert result.success
        # Should return morning-related duas
    
    @pytest.mark.asyncio
    async def test_search_arabic(self, tool):
        """Test searching Arabic text."""
        result = await tool.execute(query="الله")
        
        assert result.success
        # Should return multiple duas containing "Allah"
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, tool):
        """Test search with no matching results."""
        result = await tool.execute(query="xyznonexistent")
        
        assert result.success
        assert result.result["count"] == 0
    
    # ==========================================
    # Limit Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_limit_results(self, tool):
        """Test limiting number of results."""
        result = await tool.execute(limit=2)
        
        assert result.success
        assert result.result["count"] <= 2
    
    # ==========================================
    # Metadata Tests
    # ==========================================
    
    @pytest.mark.asyncio
    async def test_source_metadata(self, tool):
        """Test metadata includes source information."""
        result = await tool.execute(occasion="morning")
        
        assert "source" in result.metadata
        assert "Hisn al-Muslim" in result.metadata["source"]
    
    @pytest.mark.asyncio
    async def test_verified_sources(self, tool):
        """Test all duas have verified sources."""
        result = await tool.execute(limit=10)
        
        for dua in result.result["duas"]:
            assert "source" in dua
            assert "reference" in dua
            assert "grade" in dua
    
    # ==========================================
    # Helper Methods Tests
    # ==========================================
    
    def test_get_occasions(self, tool):
        """Test getting list of occasions."""
        occasions = tool.get_occasions()
        
        assert len(occasions) > 0
        assert "morning" in occasions
        assert "evening" in occasions
    
    def test_get_categories(self, tool):
        """Test getting list of categories."""
        categories = tool.get_categories()
        
        assert len(categories) > 0
        assert "morning_evening" in categories
        assert "travel" in categories
