"""Tests for MCP server implementation using FastMCP SDK."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_skills.mcp.server import (
    configure_services,
    get_indexing_engine,
    get_repo_manager,
    get_skill_manager,
    get_toolchain_detector,
)
from mcp_skills.mcp.tools.find_tool import find
from mcp_skills.mcp.tools.skill_tool import skill
from mcp_skills.models.skill import Skill
from mcp_skills.services.indexing import ScoredSkill
from mcp_skills.services.toolchain_detector import ToolchainInfo


@pytest.fixture
def mock_skill():
    """Create a mock Skill object."""
    return Skill(
        id="pytest-skill",
        name="pytest",
        description="Professional pytest testing for Python",
        instructions="# Pytest Skill\n\nDetailed instructions...",
        category="testing",
        tags=["python", "pytest", "tdd"],
        dependencies=[],
        examples=["Example 1", "Example 2"],
        file_path=Path("/fake/path/pytest/SKILL.md"),
        repo_id="anthropics-skills",
        version="1.0.0",
        author="Test Author",
    )


@pytest.fixture
def mock_scored_skill(mock_skill):
    """Create a mock ScoredSkill object."""
    return ScoredSkill(skill=mock_skill, score=0.92, match_type="hybrid")


@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    base_dir = tmp_path / "mcp-skillset"
    storage_path = base_dir / "storage"
    repos_dir = base_dir / "repos"

    base_dir.mkdir()
    storage_path.mkdir()
    repos_dir.mkdir()

    return {
        "base_dir": base_dir,
        "storage_path": storage_path,
        "repos_dir": repos_dir,
    }


class TestConfigureServices:
    """Test service configuration."""

    def test_configure_services_with_paths(self, temp_dirs):
        """Test configuring services with custom paths."""
        configure_services(
            base_dir=temp_dirs["base_dir"],
            storage_path=temp_dirs["storage_path"],
        )

        # Should not raise errors
        skill_manager = get_skill_manager()
        indexing_engine = get_indexing_engine()
        toolchain_detector = get_toolchain_detector()
        repo_manager = get_repo_manager()

        assert skill_manager is not None
        assert indexing_engine is not None
        assert toolchain_detector is not None
        assert repo_manager is not None

    def test_configure_services_default_paths(self, tmp_path):
        """Test configuring services with default paths."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            configure_services()

            # Should create default directory
            default_dir = tmp_path / ".mcp-skillset"
            assert default_dir.exists()

    def test_get_services_before_configuration(self):
        """Test getting services before configuration raises error."""
        # Reset global services
        import mcp_skills.mcp.server as server_module

        server_module._skill_manager = None
        server_module._indexing_engine = None
        server_module._toolchain_detector = None
        server_module._repo_manager = None

        with pytest.raises(RuntimeError, match="Services not configured"):
            get_skill_manager()

        with pytest.raises(RuntimeError, match="Services not configured"):
            get_indexing_engine()

        with pytest.raises(RuntimeError, match="Services not configured"):
            get_toolchain_detector()

        with pytest.raises(RuntimeError, match="Services not configured"):
            get_repo_manager()


class TestSearchSkills:
    """Test find tool with semantic search."""

    @pytest.mark.asyncio
    async def test_search_skills_success(self, mock_scored_skill):
        """Test successful skill search."""
        mock_engine = MagicMock()
        mock_engine.search = MagicMock(return_value=[mock_scored_skill])

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await find(query="pytest testing", by="semantic", limit=10)

            assert result["status"] == "completed"
            assert len(result["skills"]) == 1
            assert result["skills"][0]["id"] == "pytest-skill"
            assert result["skills"][0]["score"] == 0.92
            assert result["search_method"] == "hybrid_rag_70_30"
            assert result["count"] == 1

    @pytest.mark.asyncio
    async def test_search_skills_with_filters(self, mock_scored_skill):
        """Test search with filters."""
        mock_engine = MagicMock()
        mock_engine.search = MagicMock(return_value=[mock_scored_skill])

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await find(
                query="testing",
                by="semantic",
                toolchain="python",
                category="testing",
                tags=["pytest"],
                limit=5,
            )

            assert result["status"] == "completed"
            assert result["filters_applied"] == {
                "toolchain": "python",
                "category": "testing",
                "tags": ["pytest"],
            }

            # Verify search was called with correct parameters
            mock_engine.search.assert_called_once()
            call_args = mock_engine.search.call_args
            assert call_args.kwargs["query"] == "testing"
            assert call_args.kwargs["toolchain"] == "python"
            assert call_args.kwargs["category"] == "testing"
            assert call_args.kwargs["top_k"] == 5

    @pytest.mark.asyncio
    async def test_search_skills_limit_capped(self, mock_scored_skill):
        """Test that limit is capped at 50."""
        mock_engine = MagicMock()
        mock_engine.search = MagicMock(return_value=[mock_scored_skill])

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            await find(query="test", by="semantic", limit=100)

            # Verify limit was capped
            mock_engine.search.assert_called_once()
            call_args = mock_engine.search.call_args
            assert call_args.kwargs["top_k"] == 50

    @pytest.mark.asyncio
    async def test_search_skills_error(self):
        """Test search error handling."""
        mock_engine = MagicMock()
        mock_engine.search = MagicMock(side_effect=Exception("Search failed"))

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await find(query="test", by="semantic")

            assert result["status"] == "error"
            assert "Search failed" in result["error"]


class TestGetSkill:
    """Test skill tool with read action."""

    @pytest.mark.asyncio
    async def test_get_skill_success(self, mock_skill):
        """Test successful skill retrieval."""
        mock_manager = Mock()
        mock_manager.load_skill = Mock(return_value=mock_skill)

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await skill(action="read", skill_id="pytest-skill")

            assert result["status"] == "completed"
            assert result["skill"]["id"] == "pytest-skill"
            assert result["skill"]["name"] == "pytest"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self):
        """Test skill not found."""
        mock_manager = Mock()
        mock_manager.load_skill = Mock(return_value=None)

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await skill(action="read", skill_id="nonexistent")

            assert result["status"] == "error"
            assert "not found" in result["message"]

    @pytest.mark.asyncio
    async def test_get_skill_error(self):
        """Test get_skill error handling."""
        mock_manager = Mock()
        mock_manager.load_skill = Mock(side_effect=Exception("Load failed"))

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await skill(action="read", skill_id="pytest-skill")

            assert result["status"] == "error"
            assert "Load failed" in result["message"]


class TestRecommendSkills:
    """Test find tool with recommend mode."""

    @pytest.mark.asyncio
    async def test_recommend_skills_project_based(self, mock_scored_skill, tmp_path):
        """Test project-based recommendations."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        mock_detector = Mock()
        mock_toolchain = ToolchainInfo(
            primary_language="Python",
            secondary_languages=[],
            frameworks=[],
            build_tools=[],
            package_managers=[],
            test_frameworks=[],
            confidence=0.95,
        )
        mock_detector.detect = Mock(return_value=mock_toolchain)

        mock_engine = MagicMock()
        mock_engine.search = MagicMock(return_value=[mock_scored_skill])

        with (
            patch(
                "mcp_skills.mcp.tools.find_tool.get_toolchain_detector",
                return_value=mock_detector,
            ),
            patch(
                "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
                return_value=mock_engine,
            ),
        ):
            result = await find(by="recommend", project_path=str(project_dir), limit=5)

            assert result["status"] == "completed"
            assert result["recommendation_type"] == "project_based"
            assert len(result["recommendations"]) == 1
            assert result["recommendations"][0]["id"] == "pytest-skill"
            assert result["context"]["detected_toolchains"] == ["Python"]
            assert result["context"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_recommend_skills_skill_based(self, mock_skill):
        """Test skill-based recommendations."""
        mock_manager = Mock()
        mock_manager.load_skill = Mock(return_value=mock_skill)

        related_skill = Skill(
            id="unittest-skill",
            name="unittest",
            description="Python unittest framework",
            instructions="# Unittest\n\n...",
            category="testing",
            tags=["python", "unittest"],
            dependencies=[],
            examples=[],
            file_path=Path("/fake/path/unittest/SKILL.md"),
            repo_id="anthropics-skills",
        )

        mock_engine = MagicMock()
        mock_engine.get_related_skills = MagicMock(return_value=[related_skill])

        with (
            patch(
                "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
                return_value=mock_engine,
            ),
            patch(
                "mcp_skills.mcp.tools.find_tool.get_skill_manager",
                return_value=mock_manager,
            ),
        ):
            result = await find(by="recommend", skill_id="pytest-skill", limit=5)

            assert result["status"] == "completed"
            assert result["recommendation_type"] == "skill_based"
            assert result["context"]["base_skill"] == "pytest-skill"
            assert len(result["recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_recommend_skills_no_params(self):
        """Test recommendations with no parameters."""
        result = await find(by="recommend")

        assert result["status"] == "error"
        assert "required" in result["error"]

    @pytest.mark.asyncio
    async def test_recommend_skills_invalid_project_path(self):
        """Test recommendations with invalid project path."""
        with (
            patch(
                "mcp_skills.mcp.tools.find_tool.get_toolchain_detector",
                return_value=Mock(),
            ),
            patch(
                "mcp_skills.mcp.tools.find_tool.get_indexing_engine",
                return_value=MagicMock(),
            ),
        ):
            result = await find(by="recommend", project_path="/nonexistent/path")

            assert result["status"] == "error"
            assert "does not exist" in result["error"]


class TestListCategories:
    """Test find tool with category mode."""

    @pytest.mark.asyncio
    async def test_list_categories_success(self, mock_skill):
        """Test successful category listing."""
        skills = [mock_skill]

        mock_manager = Mock()
        mock_manager.discover_skills = Mock(return_value=skills)

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await find(by="category")

            assert result["status"] == "completed"
            assert len(result["categories"]) == 1
            assert result["categories"][0]["name"] == "testing"
            assert result["categories"][0]["count"] == 1
            assert result["total_categories"] == 1

    @pytest.mark.asyncio
    async def test_list_categories_multiple(self, mock_skill):
        """Test listing multiple categories."""
        skill1 = mock_skill
        skill2 = Skill(
            id="deployment-skill",
            name="deployment",
            description="Deployment automation",
            instructions="# Deployment\n\n...",
            category="deployment",
            tags=["ci", "cd"],
            dependencies=[],
            examples=[],
            file_path=Path("/fake/path/deployment/SKILL.md"),
            repo_id="anthropics-skills",
        )

        mock_manager = Mock()
        mock_manager.discover_skills = Mock(return_value=[skill1, skill2])

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await find(by="category")

            assert result["status"] == "completed"
            assert result["total_categories"] == 2
            category_names = [cat["name"] for cat in result["categories"]]
            assert "testing" in category_names
            assert "deployment" in category_names

    @pytest.mark.asyncio
    async def test_list_categories_error(self):
        """Test category listing error handling."""
        mock_manager = Mock()
        mock_manager.discover_skills = Mock(side_effect=Exception("Discovery failed"))

        with patch(
            "mcp_skills.mcp.tools.find_tool.get_skill_manager",
            return_value=mock_manager,
        ):
            result = await find(by="category")

            assert result["status"] == "error"
            assert "Discovery failed" in result["error"]


class TestReindexSkills:
    """Test skill tool with reindex action."""

    @pytest.mark.asyncio
    async def test_reindex_skills_success(self, mock_skill):
        """Test successful reindexing."""
        from mcp_skills.services.indexing import IndexStats

        mock_stats = IndexStats(
            total_skills=1,
            vector_store_size=1024,
            graph_nodes=1,
            graph_edges=0,
            last_indexed="2025-01-01T00:00:00",
        )

        mock_engine = MagicMock()
        mock_engine.reindex_all = MagicMock(return_value=mock_stats)

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await skill(action="reindex")

            assert result["status"] == "completed"
            assert result["indexed_count"] == 1
            assert result["graph_nodes"] == 1
            assert result["forced"] is False

    @pytest.mark.asyncio
    async def test_reindex_skills_force(self, mock_skill):
        """Test forced reindexing."""
        from mcp_skills.services.indexing import IndexStats

        mock_stats = IndexStats(
            total_skills=1,
            vector_store_size=1024,
            graph_nodes=1,
            graph_edges=0,
            last_indexed="2025-01-01T00:00:00",
        )

        mock_engine = MagicMock()
        mock_engine.reindex_all = MagicMock(return_value=mock_stats)

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await skill(action="reindex", force=True)

            assert result["status"] == "completed"
            assert result["forced"] is True
            # Verify reindex_all was called with force=True
            mock_engine.reindex_all.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_reindex_skills_no_skills(self):
        """Test reindexing with no skills."""
        from mcp_skills.services.indexing import IndexStats

        mock_stats = IndexStats(
            total_skills=0,
            vector_store_size=0,
            graph_nodes=0,
            graph_edges=0,
            last_indexed="never",
        )

        mock_engine = MagicMock()
        mock_engine.reindex_all = MagicMock(return_value=mock_stats)

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await skill(action="reindex")

            assert result["status"] == "completed"
            assert result["indexed_count"] == 0

    @pytest.mark.asyncio
    async def test_reindex_skills_error(self):
        """Test reindexing error handling."""
        mock_engine = MagicMock()
        mock_engine.reindex_all = MagicMock(side_effect=Exception("Indexing failed"))

        with patch(
            "mcp_skills.mcp.tools.skill_tool.get_indexing_engine",
            return_value=mock_engine,
        ):
            result = await skill(action="reindex")

            assert result["status"] == "error"
            assert "Indexing failed" in result["message"]


class TestListSkillTemplates:
    """Test find tool with template mode."""

    @pytest.mark.asyncio
    async def test_list_skill_templates_success(self):
        """Test successful template listing."""
        result = await find(by="template")

        assert result["status"] == "completed"
        assert "templates" in result
        assert "default" in result
        assert "total" in result

        # Verify we have 4 templates
        assert result["total"] == 4
        assert result["default"] == "base"

        # Verify template structure
        templates = result["templates"]
        assert len(templates) == 4

        template_names = [t["name"] for t in templates]
        assert "base" in template_names
        assert "web-development" in template_names
        assert "api-development" in template_names
        assert "testing" in template_names

        # Verify each template has required fields
        for template in templates:
            assert "name" in template
            assert "description" in template
            assert "use_cases" in template
            assert isinstance(template["use_cases"], list)
            assert len(template["use_cases"]) > 0


class TestSkillCreate:
    """Test skill tool with create action."""

    @pytest.mark.asyncio
    async def test_skill_create_preview(self, tmp_path):
        """Test skill creation preview (no deploy)."""
        with patch("pathlib.Path.home", return_value=tmp_path):
            result = await skill(
                action="create",
                name="Test Skill",
                description="This is a test skill for unit testing purposes",
                domain="testing",
                tags=["test", "python"],
                template="testing",
                deploy=False,
            )

            # Preview mode doesn't deploy
            assert result["status"] == "completed"
            assert result["action"] == "preview"
            assert result["skill_id"] == "test-skill"
            assert "content" in result
            assert result.get("skill_path") is None

    @pytest.mark.asyncio
    async def test_skill_create_name_normalization(self, tmp_path):
        """Test skill name normalization to kebab-case."""
        test_cases = [
            ("FastAPI Testing", "fastapi-testing"),
            ("My Cool Skill!", "my-cool-skill"),
            ("skill_with_underscores", "skill-with-underscores"),
            ("Multiple   Spaces", "multiple-spaces"),
        ]

        for name, expected_id in test_cases:
            with patch("pathlib.Path.home", return_value=tmp_path):
                result = await skill(
                    action="create",
                    name=name,
                    description="Testing name normalization to kebab-case format",
                    domain="testing",
                    template="testing",
                    deploy=False,
                )

                assert (
                    result["status"] == "completed"
                ), f"Failed for {name}: {result.get('message')}"
                assert result["skill_id"] == expected_id


class TestBackwardCompatibility:
    """Test backward compatibility wrapper."""

    def test_mcp_server_import(self):
        """Test importing from services.mcp_server."""
        from mcp_skills.services.mcp_server import (
            MCPSkillsServer,
            configure_services,
            main,
            mcp,
        )

        assert MCPSkillsServer is not None
        assert configure_services is not None
        assert main is not None
        assert mcp is not None

    def test_mcp_server_instantiation(self, temp_dirs):
        """Test instantiating deprecated MCPSkillsServer."""
        from mcp_skills.services.mcp_server import MCPSkillsServer

        with patch(
            "mcp_skills.services.mcp_server.configure_services"
        ) as mock_configure:
            server = MCPSkillsServer(config={"test": "value"})

            assert server.config == {"test": "value"}
            mock_configure.assert_called_once()
