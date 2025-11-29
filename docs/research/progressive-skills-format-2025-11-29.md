# Progressive Skills Document Format Research

**Research Date:** 2025-11-29
**Status:** Complete
**Purpose:** Define specification for progressive skills in `.claude/skills` directory

---

## Executive Summary

**Progressive skills** are modular capabilities for Claude Code stored in the `.claude/skills/` directory that use a **progressive disclosure architecture** to maintain efficiency while providing expert-level capabilities. The format consists of a lightweight YAML frontmatter (~100 tokens) that determines activation, and a markdown body (<5k tokens) that loads only when triggered.

**Key Findings:**
1. **Format:** Single `SKILL.md` file with YAML frontmatter + markdown body
2. **Location:** `~/.claude/skills/skill-name/SKILL.md`
3. **Loading:** Skills are loaded at Claude Code startup (static loading)
4. **Activation:** Triggered by `description` field matching in frontmatter
5. **Structure:** Minimal frontmatter (name + description only), comprehensive body
6. **Resources:** Optional bundled files in `scripts/`, `references/`, `assets/` subdirectories

**Gap Identified:** No official tooling exists for **building skills programmatically** or **on-demand based on agent-identified needs**. This represents an opportunity for mcp-skillset enhancement.

---

## 1. Progressive Skills Document Format Specification

### 1.1 File Structure

```
~/.claude/skills/
└── skill-name/
    ├── SKILL.md                 # Required: Skill definition
    └── Bundled Resources (Optional)
        ├── scripts/             # Executable scripts
        ├── references/          # Documentation, schemas, examples
        └── assets/              # Images, data files
```

### 1.2 SKILL.md Format

```markdown
---
name: skill-identifier
description: |
  What the skill does and when Claude should use it.
  This field determines activation - must include clear triggers/contexts.
---

# Skill Instructions

## Core Principles
[Fundamental concepts with code examples]

## Best Practices
[Production-ready patterns]

## Common Patterns
[Real-world implementation examples]

## Anti-Patterns
[What NOT to do with corrections]

## Related Skills
[Integration points]
```

### 1.3 YAML Frontmatter Schema

**Required Fields:**
- `name` (string): Unique skill identifier (kebab-case recommended)
- `description` (string): Activation trigger and usage context

**Optional Fields (Extended Schema from Templates):**
- `skill_id` (string): Alternative to `name` for unique identification
- `version` (string): Semantic version (e.g., "1.0.0")
- `category` (string): Technology domain classification
- `tags` (array): Technology keywords for discovery
- `toolchain` (array): Required tools and versions
- `frameworks` (array): Primary frameworks
- `related_skills` (array): Dependency/integration skills
- `author` (string): Skill author/organization
- `license` (string): License identifier (e.g., "MIT")
- `created` (date): Creation date (YYYY-MM-DD)
- `last_updated` (date): Last modification date

**Example Frontmatter:**

```yaml
---
name: fastapi-web-development
skill_id: fastapi-modern-development
version: 1.0.0
description: |
  Production-grade FastAPI development with async patterns, Pydantic v2,
  dependency injection, and ML/AI endpoint design. Use when building RESTful
  APIs, ML services, or async Python web applications.
category: Python Web Development
tags:
  - fastapi
  - python
  - async
  - pydantic
  - rest-api
  - ml-endpoints
toolchain:
  - Python 3.11+
  - FastAPI 0.100+
  - Pydantic v2
frameworks:
  - FastAPI
  - Pydantic
  - SQLAlchemy 2.0
related_skills:
  - test-driven-development
  - systematic-debugging
  - postgresql-optimization
author: mcp-skillset
license: MIT
created: 2025-11-25
last_updated: 2025-11-29
---
```

---

## 2. Progressive Disclosure Architecture

### 2.1 Two-Stage Loading Model

**Stage 1: Frontmatter Scanning (~100 tokens per skill)**
- Claude Code loads all `SKILL.md` frontmatter at startup
- Scans `description` field to determine applicability
- Builds activation index for trigger matching

**Stage 2: Body Loading (<5k tokens)**
- Triggered when `description` matches user request context
- Full markdown body injected into context
- Bundled resources loaded on-demand via references

### 2.2 Token Efficiency

| Component | Size | When Loaded |
|-----------|------|-------------|
| Frontmatter | ~100 tokens | Startup (always) |
| Body | <5000 tokens | On activation |
| Scripts | Variable | On explicit read |
| References | Variable | On explicit read |

**Total Context Impact:**
- Inactive skill: ~100 tokens (frontmatter only)
- Active skill: ~5100 tokens (frontmatter + body)
- With resources: Variable (as referenced)

### 2.3 Design Principles

1. **Conciseness:** Challenge every explanation - does Claude really need this?
2. **Progressive Disclosure:** Keep body under 500 lines; use external files for details
3. **Imperative Form:** Use action-oriented language (not explanatory)
4. **Context Efficiency:** Only include information Claude doesn't already know
5. **No Duplication:** Don't repeat what's in frontmatter

---

## 3. Skill Building Workflow Design

### 3.1 Current State (Manual Workflow)

**Existing Tools:**
1. **skill-creator** (Official Anthropic): Interactive Q&A-based skill creation
2. **metaskills/skill-builder**: Natural language skill creation via agent
3. **Template-based**: Copy and customize from existing skills

**Limitations:**
- ❌ No programmatic skill generation API
- ❌ No auto-detection of project needs → skill creation
- ❌ No integration with agent workflows
- ❌ Skills must be created manually before use

### 3.2 Proposed Progressive Skill Building Workflow

**Two Modes:**

#### Mode 1: Prompting-Based Skill Creation

```
User Prompt: "Create a skill for testing FastAPI endpoints"
    ↓
Agent Analysis:
    - Parse intent and domain
    - Identify skill components (testing + FastAPI)
    - Generate metadata and structure
    ↓
Skill Generation:
    - Create YAML frontmatter (name, description, tags, toolchain)
    - Generate body sections (principles, patterns, anti-patterns)
    - Add code examples from knowledge base
    - Include related skills links
    ↓
Validation:
    - Check SKILL.md syntax
    - Validate YAML schema
    - Ensure progressive disclosure (size limits)
    - Security scan (no secrets, safe patterns)
    ↓
Deployment:
    - Save to ~/.claude/skills/skill-name/SKILL.md
    - Optional: Add to mcp-skillset index
    - Optional: Commit to version control
```

#### Mode 2: Agent-Identified Needs

```
Agent Working Context:
    - Detects repeated patterns in current task
    - Identifies missing domain expertise
    - Recognizes need for specialized guidance
    ↓
Skill Need Detection:
    - Pattern: "User has asked about FastAPI testing 3+ times"
    - Missing: "No skill available for this domain"
    - Benefit: "Could save time on future requests"
    ↓
Proactive Skill Suggestion:
    Agent: "I notice you're working with FastAPI testing. Would you like
           me to create a reusable skill for this pattern?"
    User: "Yes" / "No"
    ↓
Skill Generation (if approved):
    - Extract patterns from conversation history
    - Synthesize best practices from current context
    - Generate skill with examples from actual work
    - Deploy to ~/.claude/skills/
```

### 3.3 Workflow Implementation Components

**Required Capabilities:**

1. **Skill Template Engine**
   - Input: Domain keywords, intent, examples
   - Output: Complete SKILL.md with valid structure
   - Templates: Pre-built for common domains (web, testing, data, etc.)

2. **Context Analyzer**
   - Parse user prompts for skill creation intent
   - Extract domain from conversation history
   - Identify repeated patterns requiring skills

3. **Metadata Generator**
   - Auto-generate name, skill_id from domain
   - Suggest tags based on technology keywords
   - Infer toolchain from project context
   - Recommend related_skills from existing catalog

4. **Content Synthesizer**
   - Generate "Core Principles" from best practices knowledge
   - Create "Best Practices" from framework documentation
   - Produce "Common Patterns" from code examples
   - Identify "Anti-Patterns" from known issues

5. **Validator**
   - YAML syntax validation
   - Progressive disclosure enforcement (size limits)
   - Security scanning (no hardcoded secrets)
   - Quality checks (required sections, code examples)

6. **Deployer**
   - Save to ~/.claude/skills/skill-name/SKILL.md
   - Create directory structure
   - Optional: Git commit and push
   - Optional: Index in mcp-skillset

---

## 4. Existing Skill Creation Tools Analysis

### 4.1 skill-creator (Official Anthropic)

**Source:** https://github.com/anthropics/skills/tree/main/skill-creator

**Approach:** Interactive Q&A guided workflow

**Workflow:**
1. User triggers skill-creator skill
2. Claude asks structured questions:
   - What does the skill do?
   - When should it activate?
   - What instructions should it contain?
   - What resources does it need?
3. Claude generates SKILL.md based on answers
4. User reviews and refines

**Strengths:**
- ✅ Official Anthropic implementation
- ✅ Ensures correct format and structure
- ✅ Guides users through best practices
- ✅ Handles bundled resources (scripts/, references/)

**Limitations:**
- ❌ Requires manual Q&A interaction
- ❌ Not programmatic/API-driven
- ❌ Doesn't detect needs proactively
- ❌ One-time generation (no iteration based on usage)

### 4.2 metaskills/skill-builder (Community)

**Source:** https://github.com/metaskills/skill-builder
**Author:** Ken Collins (AWS Serverless Hero)

**Approach:** Natural language skill creation

**Workflow:**
1. User: "Help me create a skill for deploying AWS Lambda functions"
2. Agent interprets intent and generates skill
3. Skill created with appropriate structure
4. User can iterate and refine

**Strengths:**
- ✅ Natural language interface (no Q&A required)
- ✅ Faster than interactive approach
- ✅ Flexible iteration

**Limitations:**
- ❌ Community implementation (not official)
- ❌ Quality depends on agent interpretation
- ❌ Still requires explicit user request
- ❌ No proactive skill detection

### 4.3 Template-Based Approach (mcp-skillset)

**Source:** `docs/skill-templates/` in this repository

**Approach:** Copy and customize pre-built templates

**Workflow:**
1. Browse template directory
2. Copy template for relevant domain
3. Customize YAML frontmatter
4. Edit body sections as needed
5. Deploy to ~/.claude/skills/

**Strengths:**
- ✅ High-quality, research-backed content
- ✅ 2024-2025 best practices included
- ✅ Production-ready code examples
- ✅ 7 critical domains covered

**Limitations:**
- ❌ Manual copy-paste workflow
- ❌ Limited to pre-defined templates
- ❌ No customization automation
- ❌ Requires user awareness of templates

---

## 5. Integration Strategy with mcp-skillset

### 5.1 Recommended Architecture

```
┌─────────────────────────────────────────────────────────┐
│              User Interaction Layer                      │
│  - CLI: mcp-skillset build-skill                        │
│  - MCP Tool: skill_create                               │
│  - Agent: Proactive skill suggestion                    │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│            Skill Builder Service                         │
│  - Template Engine (Jinja2)                            │
│  - Metadata Generator                                   │
│  - Content Synthesizer                                  │
│  - Context Analyzer                                     │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│            Validation Layer                              │
│  - YAML Schema Validator                                │
│  - Progressive Disclosure Checker                       │
│  - Security Scanner                                     │
│  - Quality Analyzer                                     │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│            Deployment Layer                              │
│  - File Writer (~/.claude/skills/)                      │
│  - Git Integration (optional)                           │
│  - mcp-skillset Indexer (optional)                      │
└─────────────────────────────────────────────────────────┘
```

### 5.2 CLI Command Design

```bash
# Interactive mode (guided Q&A)
mcp-skillset build-skill --interactive
> Skill name: fastapi-testing
> Domain: web development
> Description: Testing FastAPI endpoints with pytest and httpx
> Generate skill? [y/N]: y
✓ Skill created: ~/.claude/skills/fastapi-testing/SKILL.md

# Prompt-based mode (one-shot)
mcp-skillset build-skill \
  --name "fastapi-testing" \
  --domain "web development" \
  --description "Testing FastAPI endpoints with pytest and httpx" \
  --tags "fastapi,pytest,testing,python" \
  --toolchain "Python 3.11+,FastAPI,pytest,httpx"

# From template
mcp-skillset build-skill \
  --template "docs/skill-templates/fastapi-web-development" \
  --customize

# From conversation history (agent mode)
mcp-skillset build-skill --from-context
> Analyzing recent conversations...
> Detected pattern: PostgreSQL query optimization
> Create skill for this pattern? [y/N]: y
```

### 5.3 MCP Tool Design

```python
# Tool: skill_create
{
  "name": "skill_create",
  "description": "Create a new progressive skill for Claude Code",
  "input_schema": {
    "name": "string",           # Skill identifier (kebab-case)
    "description": "string",    # Activation trigger and usage context
    "domain": "string",         # Technology domain
    "tags": "array[string]?",   # Optional tags
    "toolchain": "array[string]?",  # Optional toolchain
    "template": "string?",      # Optional template name
    "examples": "array[string]?",   # Optional code examples
    "deploy": "boolean?"        # Auto-deploy to ~/.claude/skills/
  }
}

# Usage from agent:
skill_create(
  name="fastapi-endpoint-testing",
  description="Test FastAPI REST endpoints using pytest with async support, fixtures, and httpx client",
  domain="web development",
  tags=["fastapi", "pytest", "testing", "async"],
  toolchain=["Python 3.11+", "FastAPI 0.100+", "pytest 7+", "httpx"],
  deploy=True
)
```

### 5.4 Proactive Skill Detection Agent

**Trigger Conditions:**
1. **Pattern Repetition:** User asks about same domain 3+ times
2. **Missing Expertise:** Agent struggles with specific domain
3. **Manual Workflow:** User performs repetitive manual steps
4. **New Technology:** Project uses tech not in existing skills

**Detection Algorithm:**

```python
class SkillNeedDetector:
    """Detect when a new skill would be beneficial."""

    def __init__(self, conversation_history, existing_skills):
        self.history = conversation_history
        self.skills = existing_skills
        self.pattern_threshold = 3  # Repetitions to trigger

    def detect_patterns(self) -> list[SkillSuggestion]:
        """Analyze conversation for skill needs."""
        patterns = []

        # Check for repeated domain queries
        domain_counts = self._count_domain_mentions()
        for domain, count in domain_counts.items():
            if count >= self.pattern_threshold:
                if not self._has_skill_for_domain(domain):
                    patterns.append(SkillSuggestion(
                        domain=domain,
                        reason=f"Asked about {domain} {count} times",
                        confidence=min(count / 10, 1.0)
                    ))

        # Check for missing toolchain coverage
        project_tools = self._detect_project_toolchain()
        for tool in project_tools:
            if not self._has_skill_for_tool(tool):
                patterns.append(SkillSuggestion(
                    domain=tool,
                    reason=f"Project uses {tool} but no skill exists",
                    confidence=0.8
                ))

        return patterns
```

### 5.5 Integration with Existing mcp-skillset Components

**SkillManager Integration:**
```python
# Extend existing SkillManager
class SkillManager:
    """Existing skill discovery and loading."""

    def build_skill(
        self,
        name: str,
        description: str,
        domain: str,
        template: str | None = None,
        **kwargs
    ) -> Path:
        """Create new skill from scratch or template.

        Returns:
            Path to created SKILL.md file
        """
        builder = SkillBuilder(templates_dir=self.templates_dir)
        skill_path = builder.generate(
            name=name,
            description=description,
            domain=domain,
            template=template,
            **kwargs
        )

        # Validate
        validator = SkillValidator()
        result = validator.validate(skill_path)
        if not result.is_valid:
            raise ValueError(f"Skill validation failed: {result.errors}")

        # Deploy
        deploy_path = Path.home() / ".claude" / "skills" / name / "SKILL.md"
        deploy_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(skill_path, deploy_path)

        # Optional: Index in mcp-skillset
        if kwargs.get("index", False):
            self.discover_skills()  # Refresh skill cache

        return deploy_path
```

**New SkillBuilder Service:**
```python
class SkillBuilder:
    """Generate progressive skills from templates or prompts."""

    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir)
        )

    def generate(
        self,
        name: str,
        description: str,
        domain: str,
        template: str | None = None,
        **kwargs
    ) -> Path:
        """Generate skill from template or scratch."""
        if template:
            return self._from_template(template, name, description, **kwargs)
        else:
            return self._from_scratch(name, description, domain, **kwargs)

    def _from_template(self, template: str, name: str, description: str, **kwargs) -> Path:
        """Generate from existing template."""
        template_file = self.jinja_env.get_template(f"{template}/SKILL.md.j2")

        context = {
            "name": name,
            "skill_id": kwargs.get("skill_id", name),
            "description": description,
            "version": kwargs.get("version", "1.0.0"),
            "category": kwargs.get("category", "General"),
            "tags": kwargs.get("tags", []),
            "toolchain": kwargs.get("toolchain", []),
            "frameworks": kwargs.get("frameworks", []),
            "related_skills": kwargs.get("related_skills", []),
            "author": kwargs.get("author", "mcp-skillset"),
            "license": kwargs.get("license", "MIT"),
            "created": kwargs.get("created", datetime.now().strftime("%Y-%m-%d")),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
        }

        rendered = template_file.render(**context)

        output_path = Path(f"/tmp/mcp-skillset-build/{name}/SKILL.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered)

        return output_path

    def _from_scratch(self, name: str, description: str, domain: str, **kwargs) -> Path:
        """Generate skill from scratch using AI synthesis."""
        # Use LLM to generate skill content based on domain knowledge
        # This would integrate with Claude API to synthesize skill content
        raise NotImplementedError("From-scratch generation requires LLM integration")
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Create `SkillBuilder` service class
- [ ] Implement Jinja2 template engine
- [ ] Convert existing skill templates to `.j2` format
- [ ] Add YAML schema validator
- [ ] Implement progressive disclosure checker (size limits)

### Phase 2: CLI Integration (Week 3)
- [ ] Add `mcp-skillset build-skill` command
- [ ] Implement interactive mode with Q&A
- [ ] Add prompt-based mode (one-shot creation)
- [ ] Add template customization workflow
- [ ] Integrate with existing SkillManager

### Phase 3: MCP Tool (Week 4)
- [ ] Create `skill_create` MCP tool
- [ ] Expose via MCP server
- [ ] Add skill validation and security scanning
- [ ] Implement auto-deployment to ~/.claude/skills/

### Phase 4: Proactive Detection (Week 5-6)
- [ ] Implement `SkillNeedDetector` service
- [ ] Add conversation history analysis
- [ ] Create skill suggestion agent
- [ ] Add approval workflow for auto-generation
- [ ] Integrate with agent delegation system

### Phase 5: Polish & Testing (Week 7)
- [ ] Comprehensive test suite
- [ ] Documentation and examples
- [ ] User guide for skill building
- [ ] Integration tests with Claude Code

---

## 7. Example: Building a Skill Programmatically

### CLI Workflow

```bash
# 1. Build skill interactively
$ mcp-skillset build-skill --interactive

? Skill name: postgres-query-optimization
? Domain: database
? Description: Optimize PostgreSQL queries using EXPLAIN ANALYZE, indexes, and query planning
? Tags (comma-separated): postgresql,database,optimization,performance,explain
? Toolchain (comma-separated): PostgreSQL 14+,pgAdmin,pg_stat_statements
? Use template? (y/N): y
? Select template:
  > postgresql-optimization
    fastapi-web-development
    terraform-infrastructure

✓ Generating skill from template...
✓ Validating SKILL.md...
✓ Deploying to ~/.claude/skills/postgres-query-optimization/SKILL.md
✓ Skill created successfully!

Next steps:
  1. Review: open ~/.claude/skills/postgres-query-optimization/SKILL.md
  2. Test: Restart Claude Code to load the skill
  3. Use: Ask Claude about PostgreSQL query optimization

# 2. Build skill from prompt
$ mcp-skillset build-skill \
  --name "redis-caching-patterns" \
  --domain "caching" \
  --description "Design and implement Redis caching strategies for web applications" \
  --tags "redis,caching,performance,distributed-systems" \
  --toolchain "Redis 7+,Python,redis-py" \
  --template "general-backend"

✓ Skill created: ~/.claude/skills/redis-caching-patterns/SKILL.md

# 3. Build from conversation context
$ mcp-skillset build-skill --from-context

Analyzing recent conversations...
Detected patterns:
  1. Docker containerization (mentioned 5 times)
  2. Kubernetes deployment (mentioned 4 times)
  3. CI/CD pipelines (mentioned 3 times)

Create skill for: Docker containerization? [y/N]: y

✓ Generating skill from conversation history...
✓ Skill created: ~/.claude/skills/docker-containerization/SKILL.md
```

### MCP Tool Workflow

```python
# Agent detects skill need and creates it
await skill_create(
    name="graphql-api-design",
    description="Design and implement GraphQL APIs with schema-first approach, resolvers, and Apollo Server",
    domain="api development",
    tags=["graphql", "api", "apollo", "schema", "resolvers"],
    toolchain=["Node.js 18+", "Apollo Server 4", "GraphQL 16+"],
    examples=[
        "Define GraphQL schema with types and queries",
        "Implement resolvers with data loaders",
        "Add authentication and authorization"
    ],
    deploy=True
)
```

---

## 8. Quality Assurance and Validation

### 8.1 Validation Checklist

**YAML Frontmatter:**
- [ ] Valid YAML syntax
- [ ] Required fields present (name, description)
- [ ] Description is clear and includes triggers
- [ ] Tags are relevant and specific
- [ ] Toolchain versions are specified

**Body Structure:**
- [ ] Under 500 lines (progressive disclosure)
- [ ] Imperative language used
- [ ] No duplication of frontmatter
- [ ] Code examples are complete and runnable
- [ ] References to bundled resources are clear

**Content Quality:**
- [ ] 5+ core principles with examples
- [ ] 10+ best practices
- [ ] 5+ anti-patterns with corrections
- [ ] 3+ related skills mentioned
- [ ] No hardcoded secrets or credentials

**Security:**
- [ ] No sensitive information
- [ ] Safe code patterns
- [ ] No malicious scripts
- [ ] Trusted resource references

### 8.2 Automated Validation

```python
class SkillValidator:
    """Validate progressive skill format and quality."""

    def validate(self, skill_path: Path) -> ValidationResult:
        """Comprehensive skill validation."""
        errors = []
        warnings = []

        # Parse SKILL.md
        content = skill_path.read_text()
        frontmatter, body = self._parse_skill(content)

        # YAML validation
        if not frontmatter.get("name"):
            errors.append("Missing required field: name")
        if not frontmatter.get("description"):
            errors.append("Missing required field: description")

        # Progressive disclosure check
        body_lines = body.count("\n")
        if body_lines > 500:
            warnings.append(f"Body exceeds 500 lines ({body_lines}). Consider using bundled resources.")

        # Security scan
        if re.search(r"(password|secret|api_key)\s*=\s*['\"][\w]+['\"]", body):
            errors.append("Hardcoded credentials detected")

        # Quality checks
        if body.count("```") < 10:
            warnings.append("Consider adding more code examples (found < 5)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

---

## 9. Recommendations

### 9.1 Implementation Approach

**Recommended:** CLI + MCP Tool Hybrid

**Rationale:**
1. **CLI for manual creation:** Developers want explicit control
2. **MCP Tool for automation:** Agents can create skills proactively
3. **Both use same SkillBuilder:** Code reuse and consistency

**Priority:**
1. **High:** CLI with template-based generation (fastest ROI)
2. **Medium:** MCP tool for programmatic creation
3. **Low:** Proactive skill detection (requires conversation analysis)

### 9.2 Template Strategy

**Use Existing Templates:**
- Leverage `docs/skill-templates/` as base templates
- Convert to Jinja2 format with variable substitution
- Maintain high-quality, research-backed content

**Template Categories:**
- Web Development (FastAPI, Node.js, React)
- Infrastructure (Terraform, Kubernetes, Docker)
- Data & AI (PostgreSQL, Redis, Vector DBs)
- Security (SAST, DAST, Compliance)
- Testing (pytest, Jest, E2E)

### 9.3 Integration Points

**With Existing mcp-skillset:**
- `SkillManager.build_skill()` method
- `mcp-skillset build-skill` CLI command
- `skill_create` MCP tool
- Templates in `docs/skill-templates/`

**With Claude Code:**
- Deploy to `~/.claude/skills/`
- Follow progressive disclosure format
- Use standard SKILL.md structure
- Compatible with existing skill loading

**With Version Control:**
- Optional Git integration
- Auto-commit generated skills
- Track skill evolution over time

---

## 10. Conclusion

**Progressive skills** represent a powerful extensibility mechanism for Claude Code, but currently lack **programmatic creation capabilities**. This research identifies:

1. **Clear Format Specification:** YAML frontmatter + markdown body
2. **Progressive Disclosure Architecture:** Efficient two-stage loading
3. **Existing Gaps:** No tooling for automated/agent-driven skill creation
4. **Implementation Path:** CLI + MCP Tool using template-based generation

**Recommended Next Steps:**
1. Implement `SkillBuilder` service with Jinja2 templates
2. Add `mcp-skillset build-skill` CLI command
3. Create `skill_create` MCP tool
4. Convert existing templates to `.j2` format
5. Add validation and security scanning

**Success Criteria:**
- ✅ Users can build skills via CLI in <2 minutes
- ✅ Agents can create skills programmatically via MCP
- ✅ Generated skills pass validation and security checks
- ✅ Skills deploy correctly to ~/.claude/skills/
- ✅ Claude Code loads and activates generated skills

---

## Appendix A: File Format Examples

### Minimal Valid SKILL.md

```markdown
---
name: example-skill
description: Example skill for demonstration purposes. Use when testing skill creation workflow.
---

# Example Skill

## Core Principle

Always validate inputs before processing.

## Example

\`\`\`python
def process(data):
    if not data:
        raise ValueError("Data required")
    return data.upper()
\`\`\`
```

### Full Featured SKILL.md

```markdown
---
name: fastapi-modern-development
skill_id: fastapi-web-dev
version: 1.0.0
description: |
  Production-grade FastAPI development with async patterns, Pydantic v2,
  dependency injection, and ML/AI endpoint design. Use when building RESTful
  APIs, ML services, or async Python web applications.
category: Python Web Development
tags:
  - fastapi
  - python
  - async
  - pydantic
  - rest-api
  - ml-endpoints
toolchain:
  - Python 3.11+
  - FastAPI 0.100+
  - Pydantic v2
frameworks:
  - FastAPI
  - Pydantic
  - SQLAlchemy 2.0
related_skills:
  - test-driven-development
  - systematic-debugging
  - postgresql-optimization
author: mcp-skillset
license: MIT
created: 2025-11-25
last_updated: 2025-11-29
---

# FastAPI Modern Web Development

## Overview

This skill provides comprehensive guidance for building production-grade FastAPI applications with modern Python patterns (2024-2025 best practices).

## When to Use This Skill

Use this skill when:
- Building RESTful APIs for ML/AI services
- Creating high-performance async Python web services
- Developing data-intensive applications requiring concurrent request handling

## Core Principles

### 1. Async-First Architecture

**Always prefer async/await for I/O-bound operations**

\`\`\`python
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    # Async database call
    user = await db.get(User, user_id)
    return user
\`\`\`

[... more sections ...]

## Related Skills

- **test-driven-development**: Write tests before implementing endpoints
- **systematic-debugging**: Debug async issues and race conditions
- **postgresql-optimization**: Optimize database queries for FastAPI
```

---

## Appendix B: References

**Official Documentation:**
- Anthropic Skills: https://github.com/anthropics/skills
- skill-creator: https://github.com/anthropics/skills/tree/main/skill-creator

**Community Tools:**
- metaskills/skill-builder: https://github.com/metaskills/skill-builder
- Skills Marketplace: https://skillsmp.com

**Research Documents:**
- Open Source Skill Repositories: `docs/research/open-source-skill-repositories-2025-11-25.md`
- Skill Templates: `docs/skill-templates/README.md`
- Architecture Design: `docs/architecture/README.md`

---

**Research Completion Date:** 2025-11-29
**Status:** ✅ Complete and ready for implementation
