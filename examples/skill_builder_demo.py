#!/usr/bin/env python3
"""
Demonstration of SkillBuilder service.

This script shows how to use the SkillBuilder to create progressive skills
programmatically using templates.

Run this from the project root:
    python3 examples/skill_builder_demo.py
"""

import sys
from pathlib import Path

# Add src to path for standalone execution
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_skills.services.skill_builder import SkillBuilder


def demo_base_template():
    """Demonstrate base template usage."""
    print("\n" + "=" * 80)
    print("DEMO 1: Base Template")
    print("=" * 80)

    builder = SkillBuilder()

    result = builder.build_skill(
        name="Redis Caching Patterns",
        description="Design and implement Redis caching strategies for web applications with TTL and invalidation patterns",
        domain="caching",
        tags=["redis", "caching", "performance", "distributed-systems"],
        version="1.0.0",
        toolchain=["Redis 7+", "Python", "redis-py"],
        template="base",  # Use base template
        deploy=False,  # Don't deploy, just generate
    )

    print(f"Status: {result['status']}")
    print(f"Skill ID: {result['skill_id']}")
    print(f"Message: {result['message']}")
    print(f"Warnings: {result.get('warnings', 'None')}")


def demo_web_development_template():
    """Demonstrate web development template."""
    print("\n" + "=" * 80)
    print("DEMO 2: Web Development Template")
    print("=" * 80)

    builder = SkillBuilder()

    result = builder.build_skill(
        name="FastAPI Testing",
        description="Test FastAPI endpoints with pytest, httpx, and async support for modern Python web applications",
        domain="web development",
        tags=["fastapi", "pytest", "testing", "async", "httpx"],
        version="1.0.0",
        category="Web Development",
        toolchain=["Python 3.11+", "FastAPI 0.100+", "pytest 7+", "httpx"],
        frameworks=["FastAPI", "pytest"],
        related_skills=["api-development", "testing", "async-programming"],
        template="web-development",
        deploy=False,
    )

    print(f"Status: {result['status']}")
    print(f"Skill ID: {result['skill_id']}")
    print(f"Message: {result['message']}")
    print(f"Warnings: {result.get('warnings', 'None')}")


def demo_api_development_template():
    """Demonstrate API development template."""
    print("\n" + "=" * 80)
    print("DEMO 3: API Development Template")
    print("=" * 80)

    builder = SkillBuilder()

    result = builder.build_skill(
        name="GraphQL API Design",
        description="Design and implement GraphQL APIs with schema-first approach, resolvers, and Apollo Server",
        domain="api development",
        tags=["graphql", "api", "apollo", "schema", "resolvers"],
        version="1.0.0",
        category="API Development",
        toolchain=["Node.js 18+", "Apollo Server 4", "GraphQL 16+"],
        frameworks=["Apollo Server", "GraphQL"],
        related_skills=["web-development", "testing", "database-optimization"],
        template="api-development",
        deploy=False,
    )

    print(f"Status: {result['status']}")
    print(f"Skill ID: {result['skill_id']}")
    print(f"Message: {result['message']}")
    print(f"Warnings: {result.get('warnings', 'None')}")


def demo_testing_template():
    """Demonstrate testing template."""
    print("\n" + "=" * 80)
    print("DEMO 4: Testing Template")
    print("=" * 80)

    builder = SkillBuilder()

    result = builder.build_skill(
        name="Playwright E2E Testing",
        description="End-to-end testing with Playwright for web applications including page objects and fixtures",
        domain="testing",
        tags=["playwright", "e2e", "testing", "automation", "typescript"],
        version="1.0.0",
        category="Testing",
        toolchain=["Node.js 18+", "Playwright 1.40+", "TypeScript 5+"],
        frameworks=["Playwright", "TypeScript"],
        related_skills=["web-development", "testing", "debugging"],
        template="testing",
        deploy=False,
    )

    print(f"Status: {result['status']}")
    print(f"Skill ID: {result['skill_id']}")
    print(f"Message: {result['message']}")
    print(f"Warnings: {result.get('warnings', 'None')}")


def demo_validation():
    """Demonstrate skill validation."""
    print("\n" + "=" * 80)
    print("DEMO 5: Validation")
    print("=" * 80)

    builder = SkillBuilder()

    # Valid skill
    valid_skill = """---
name: test-skill
description: This is a valid test skill with sufficient description length
version: "1.0.0"
category: Testing
tags:
  - test
  - validation
---

# Test Skill

## Overview

Valid skill content with examples.

## Examples

```python
def test():
    pass
```
"""

    print("Validating VALID skill...")
    result = builder.validate_skill(valid_skill)
    print(f"  Valid: {result.valid}")
    print(f"  Errors: {result.errors}")
    print(f"  Warnings: {result.warnings}")

    # Invalid skill (security issue)
    invalid_skill = """---
name: bad-skill
description: Skill with hardcoded credentials for demonstration
---

# Bad Skill

```python
api_key = "sk-1234567890"
password = "secret123"
```
"""

    print("\nValidating INVALID skill (security violation)...")
    result = builder.validate_skill(invalid_skill)
    print(f"  Valid: {result.valid}")
    print(f"  Errors: {result.errors}")
    print(f"  Warnings: {result.warnings}")


def demo_list_templates():
    """Demonstrate listing available templates."""
    print("\n" + "=" * 80)
    print("DEMO 6: List Available Templates")
    print("=" * 80)

    builder = SkillBuilder()
    templates = builder.list_templates()

    print(f"Available templates: {', '.join(templates)}")
    print(f"Total: {len(templates)} templates")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("SKILLBUILDER SERVICE DEMONSTRATION")
    print("=" * 80)
    print("\nThis demo shows the SkillBuilder service for creating progressive skills.")
    print("Skills follow the Claude Code format with YAML frontmatter and markdown body.")

    try:
        demo_list_templates()
        demo_base_template()
        demo_web_development_template()
        demo_api_development_template()
        demo_testing_template()
        demo_validation()

        print("\n" + "=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("\nAll demos completed successfully!")
        print("\nNext steps:")
        print("  1. Review generated skills in ~/.claude/skills/")
        print("  2. Run tests: pytest tests/services/test_skill_builder.py")
        print("  3. Create custom templates in src/mcp_skills/templates/skills/")
        print("  4. Integrate with CLI or MCP tools")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
