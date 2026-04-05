# 🌿 Git Branch Strategy for Athar

Comprehensive branching strategy for systematic development of the Athar Islamic QA system.

---

## 📋 Branch Strategy Overview

We use **GitHub Flow** with **Semantic Commit Messages** for clean, traceable development.

### Branch Types

```
main                    # Production-ready code (deployed)
├── phase-1/*          # Phase 1: Foundation (Week 1-2)
├── phase-2/*          # Phase 2: Tools Implementation (Week 3-4)
├── phase-3/*          # Phase 3: Quranic Pipeline (Week 5-6)
├── phase-4/*          # Phase 4: RAG Pipelines (Week 7-8)
└── phase-5/*          # Phase 5: Frontend & Deployment
```

### Naming Convention

```
{type}/{description}

Types:
- phase-N/*    Major phase features
- feature/*    New features
- bugfix/*     Bug fixes
- hotfix/*     Production fixes
- refactor/*   Code refactoring
- docs/*       Documentation only
```

---

## 🗂️ Current Branch Status

### ✅ Phase 1: Foundation (CURRENT - Branch: `phase-1/foundation`)

**Status:** Complete  
**Commits:** 1  
**Files:** 11 files (2,261 insertions)

**Branches:**
```
main                      # Production
└── phase-1/foundation   # ✅ COMPLETE - Ready to merge
    ├── Configuration files (pyproject.toml, .env, Makefile)
    ├── Docker environment (docker-compose, Dockerfiles)
    ├── Database schema (migrations/)
    ├── Core logic (router, orchestrator, citation)
    ├── API layer (FastAPI, routes, schemas)
    ├── Infrastructure (DB, Redis, LLM client)
    └── Tests (router, API)
```

**Next Action:**
```bash
# Merge to main after review
git checkout main
git merge phase-1/foundation
git push origin main
```

---

### 🔄 Phase 2: Tools Implementation (Branch: `phase-2/tools`)

**Status:** Not Started  
**Parent:** `main`

**Planned Branches:**
```
main
└── phase-2/tools
    ├── phase-2/zakat-calculator
    ├── phase-2/inheritance-calculator
    ├── phase-2/prayer-times-tool
    ├── phase-2/hijri-calendar-tool
    └── phase-2/dua-retrieval-tool
```

**Commits Strategy:**
```bash
# 1. Zakat Calculator
git checkout -b phase-2/zakat-calculator
# ... implement ...
git add src/tools/zakat_calculator.py tests/test_zakat.py
git commit -m "feat(tools): Add deterministic Zakat calculator

- Implement nisab calculation (gold/silver)
- Asset aggregation (cash, gold, trade, stocks)
- Debt deduction logic
- 2.5% zakat rate application
- Madhhab-aware (Hanafi includes receivables)
- Comprehensive unit tests"

# 2. Inheritance Calculator
git checkout -b phase-2/inheritance-calculator
# ... implement ...
git commit -m "feat(tools): Add Inheritance calculator (fara'id)

- Fixed shares (furood): spouse, parents, daughters
- Residuary (asabah): sons, brothers
- 'Awl (proportional reduction)
- Radd (redistribution)
- Madhhab branching (Hanafi vs Jumhur)"

# 3. Prayer Times
git checkout -b phase-2/prayer-times-tool
git commit -m "feat(tools): Add Prayer Times and Qibla tool

- Astronomical calculations (pyIslam)
- Multiple methods (Egyptian, MWL, ISNA)
- Qibla direction (great-circle bearing)
- Location-based (lat/lng or city)"

# 4. Hijri Calendar
git commit -m "feat(tools): Add Hijri Calendar converter

- Umm al-Qura calendar algorithm
- Gregorian ↔ Hijri conversion
- Ramadan/Eid date detection
- Vision difference disclaimer"

# 5. Dua Retrieval
git commit -m "feat(tools): Add Dua Retrieval tool

- Hisn al-Muslim database
- Occasion-based retrieval
- Arabic text + translation + reference
- No generation (exact text only)"
```

---

### 📖 Phase 3: Quranic Pipeline (Branch: `phase-3/quran`)

**Planned Branches:**
```
main
└── phase-3/quran
    ├── phase-3/quran-verse-retrieval
    ├── phase-3/quran-nl2sql
    ├── phase-3/quran-quotation-validator
    └── phase-3/quran-tafsir
```

**Commit Strategy:**
```bash
# 1. Verse Retrieval
git checkout -b phase-3/quran-verse-retrieval
git commit -m "feat(quran): Add verse retrieval engine

- Exact lookup (2:255 format)
- Fuzzy matching on surah names
- Named verse support (Ayat al-Kursi)
- Uthmani text + translations
- quran.com URL generation"

# 2. NL2SQL
git checkout -b phase-3/quran-nl2sql
git commit -m "feat(quran): Add NL2SQL analytics engine

- Natural language → SQL conversion
- Quran database schema
- Safe SELECT-only validation
- Statistics (count, length, frequency)
- 100% numeric accuracy guarantee"

# 3. Quotation Validator
git commit -m "feat(quran): Add quotation validator

- Verify user text against Uthmani corpus
- Fuzzy matching with threshold
- Prevent false Quran attribution
- Suggest correct verse if similar"

# 4. Tafsir Retrieval
git commit -m "feat(quran): Add Tafsir retrieval

- Ibn Kathir, Al-Jalalayn, Al-Qurtubi
- Verse-linked commentaries
- Multi-language support
- Source attribution"
```

---

### 🔍 Phase 4: RAG Pipelines (Branch: `phase-4/rag`)

**Planned Branches:**
```
main
└── phase-4/rag
    ├── phase-4/fiqh-rag
    ├── phase-4/general-islamic-rag
    ├── phase-4/embedding-pipeline
    └── phase-4/reranker
```

**Commit Strategy:**
```bash
# 1. Embedding Pipeline
git checkout -b phase-4/embedding-pipeline
git commit -m "feat(rag): Add embedding generation pipeline

- Qwen3-Embedding-0.5B integration
- Document chunking strategies
- Semantic boundary preservation
- Qdrant vector storage
- Embedding caching"

# 2. Fiqh RAG
git checkout -b phase-4/fiqh-rag
git commit -m "feat(rag): Add Fiqh RAG pipeline

- Document retrieval (top-k=15)
- Cross-encoder reranking (top-5)
- Grounded answer generation
- Citation normalization
- Madhhab-aware filtering
- Temperature 0.1 (deterministic)"

# 3. General Islamic RAG
git commit -m "feat(rag): Add General Islamic Knowledge RAG

- History, biography, theology corpus
- Educational tone
- Concept explanation
- No fatwa issuance"

# 4. Reranker
git commit -m "feat(rag): Add cross-encoder reranker

- bge-reranker-v2-m3 integration
- Relevance scoring
- Result reordering
- Noise reduction"
```

---

### 🎨 Phase 5: Frontend & Deployment (Branch: `phase-5/frontend`)

**Planned Branches:**
```
main
└── phase-5/frontend
    ├── phase-5/nextjs-app
    ├── phase-5/chat-ui
    └── phase-5/deployment
```

---

## 📝 Semantic Commit Message Format

### Structure

```
{type}({scope}): {description}

{body}

{footer}
```

### Types

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(tools): Add Zakat calculator` |
| `fix` | Bug fix | `fix(router): Correct Arabic language detection` |
| `docs` | Documentation | `docs(api): Add query endpoint examples` |
| `style` | Code style | `style: Format with ruff` |
| `refactor` | Refactoring | `refactor(orchestrator): Simplify routing logic` |
| `test` | Tests | `test(router): Add intent classification tests` |
| `chore` | Maintenance | `chore: Update dependencies` |

### Scopes

- `config` - Configuration files
- `router` - Intent classifier
- `orchestrator` - Response orchestrator
- `citation` - Citation normalizer
- `api` - FastAPI application
- `tools` - Calculator/utility tools
- `agents` - Agent implementations
- `db` - Database schema/migrations
- `docker` - Docker configuration
- `frontend` - Next.js frontend
- `rag` - RAG pipelines

### Examples

```bash
# Good commits
feat(tools): Add deterministic Zakat calculator
fix(router): Correct keyword pattern matching for Quran intent
docs(api): Add query endpoint request/response examples
test(router): Add parametrized intent classification tests
refactor(orchestrator): Extract agent routing to separate method
chore(deps): Upgrade FastAPI to 0.115.0

# Bad commits (DON'T DO THIS)
❌ Update files
❌ Fix stuff
❌ Changes
❌ WIP
```

---

## 🔄 Merge Strategy

### Feature Branch → Main

```bash
# 1. Ensure branch is up to date
git checkout phase-2/zakat-calculator
git pull origin main
git rebase main

# 2. Run tests
make test

# 3. Merge to main (squash merge for clean history)
git checkout main
git merge --squash phase-2/zakat-calculator
git commit -m "feat(phase-2): Add Zakat calculator tool

Complete implementation with:
- Nisab calculation (gold/silver)
- Asset aggregation
- Madhhab-aware logic
- Comprehensive tests"

# 4. Push
git push origin main
```

### Hotfix → Main (Emergency)

```bash
# 1. Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# 2. Fix and commit
git add fixed_file.py
git commit -m "hotfix: Resolve critical routing error

- Fix intent classifier threshold
- Add error handling for edge cases
- Update tests"

# 3. Merge immediately
git checkout main
git merge hotfix/critical-bug
git push origin main
```

---

## 📊 Branch Protection Rules

### `main` Branch

```
✅ Require pull request reviews (1 reviewer minimum)
✅ Require status checks to pass
   - tests (pytest)
   - lint (ruff, mypy)
   - build (docker)
✅ Require branches to be up to date
✅ Include administrators
✅ Allow squash merges only
```

### Feature Branches

```
✅ Run CI on every push
✅ Require tests to pass before merge
✅ Auto-delete branch after merge
```

---

## 🚀 Git Workflow Commands

### Daily Development

```bash
# Start work
git checkout main
git pull origin main
git checkout -b feature/my-feature

# Work on feature
# ... implement ...

git add changed_files
git commit -m "feat(scope): Description"

# Push branch
git push -u origin feature/my-feature

# Create PR on GitHub
```

### Sync with Main

```bash
# Update feature branch with main
git checkout feature/my-feature
git fetch origin
git rebase origin/main

# Resolve conflicts if any
git add resolved_files
git rebase --continue
```

### Cleanup

```bash
# Delete merged branches
git branch --merged main | grep -v "main" | xargs git branch -d

# Clean remote references
git remote prune origin

# Clean working directory
make clean
```

---

## 📈 Commit History Goals

### Phase 1 (Complete)
```
fb9e974 feat(phase-1): Complete foundation infrastructure
```

### Phase 2 (Target: 5-8 commits)
```
abc1234 feat(tools): Add Zakat calculator
def5678 feat(tools): Add Inheritance calculator
ghi9012 feat(tools): Add Prayer Times tool
jkl3456 feat(tools): Add Hijri Calendar converter
mno7890 feat(tools): Add Dua Retrieval tool
```

### Phase 3 (Target: 4-6 commits)
```
pqr1234 feat(quran): Add verse retrieval engine
stu5678 feat(quran): Add NL2SQL analytics
vwx9012 feat(quran): Add quotation validator
yza3456 feat(quran): Add Tafsir retrieval
```

### Phase 4 (Target: 4-6 commits)
```
bcd7890 feat(rag): Add embedding pipeline
efg1234 feat(rag): Add Fiqh RAG pipeline
hij5678 feat(rag): Add General Islamic RAG
klm9012 feat(rag): Add cross-encoder reranker
```

### Total Target: ~20 well-structured commits

---

## ✅ Best Practices

### DO ✅
- Small, focused commits (one feature per commit)
- Descriptive commit messages (what + why)
- Branch from latest `main`
- Rebase before merging
- Run tests before committing
- Delete branches after merge

### DON'T ❌
- Huge commits with unrelated changes
- Vague commit messages ("update", "fix")
- Commit to `main` directly
- Merge without rebasing
- Commit broken code
- Keep old branches cluttered

---

## 🔍 Viewing History

```bash
# Beautiful git log
git log --oneline --graph --all --decorate

# Phase 1 commits
git log phase-1/foundation --oneline

# Files changed in commit
git show fb9e974 --stat

# Specific file history
git log --follow -p src/core/router.py
```

---

<div align="center">

**Phase 1 Branch:** `phase-1/foundation` ✅  
**Next Branch:** `phase-2/tools` 🔄

</div>
