# Aegis Monitor Architecture

## Overview

Aegis Monitor is designed using a modular, pluggable architecture that allows users to:
1. Evaluate LLM outputs against expected values
2. Track costs per evaluation
3. Compare multiple models
4. Detect quality regressions
5. Extend with custom adapters and scorers

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI (typer)                              │
│    eval, eval_baseline, compare, cost, run                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                 Orchestration Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Evaluator   │  │ CostTracking │  │   Comparison │      │
│  │   (async)    │  │   (calc)     │  │  (ranking)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬────────────┐
        │          │          │            │
┌───────▼──┐ ┌────▼────┐ ┌──▼──────┐ ┌──▼─────┐
│ Adapters │ │ Scorers │ │ Storage │ │ Costs  │
├──────────┤ ├─────────┤ ├─────────┤ ├────────┤
│OpenAI    │ │ExactMat │ │SQLite   │ │Pricing │
│Anthropic │ │Semantic │ │Memory   │ │Calc    │
│Mock      │ │Composite│ │Backend  │ │Limiter │
│Custom    │ │Custom   │ │Custom   │ │Custom  │
└──────────┘ └─────────┘ └─────────┘ └────────┘
```

## Core Components

### 1. Adapter System (aegis/adapters/)

**Purpose**: Abstract different LLM providers into a unified interface

**Base Class**: `BaseModelAdapter`
```python
class BaseModelAdapter(ABC):
    def __init__(self, model: str)
    @property
    @abstractmethod
    def provider_name(self) -> str

    @abstractmethod
    async def generate(prompt, system_prompt, **kwargs) -> ModelResponse

    @abstractmethod
    def get_model_info() -> dict
```

**Concrete Implementations**:
- **OpenAIAdapter**: GPT-4, GPT-3.5-turbo, etc.
- **AnthropicAdapter**: Claude 3 Opus, Sonnet, Haiku
- **MockAdapter**: For testing without API calls
- **Custom**: Users can extend `BaseModelAdapter`

**Token Management**:
- OpenAI uses `tiktoken` library
- Anthropic uses `anthropic.Tokenizer`
- Mock uses character-based estimation

### 2. Evaluation Engine (aegis/core/)

**Purpose**: Orchestrate evaluation workflows

**Key Classes**:
- `Dataset`: Loads test cases from YAML
- `Evaluator`: Runs async evaluation pipeline
- `EvaluationResult`: Aggregates metrics and results
- `TestCaseResult`: Individual result record

**Evaluation Flow**:
```python
evaluator = Evaluator(
    adapter=OpenAIAdapter("gpt-4"),
    scorer=CompositeScorer(...),
    storage=SQLiteBackend(...),
    cost_calculator=CostCalculator(...)
)

result = await evaluator.run(
    dataset=my_dataset,
    system_prompt="You are helpful...",
    temperature=0.7
)

# result contains:
# - avg_score: 0.92
# - total_cost: $0.15
# - cases: [TestCaseResult, ...]
# - metadata: {adapter, scorer, dataset_size, ...}
```

### 3. Scoring System (aegis/scoring/)

**Purpose**: Evaluate quality of model outputs

**Base Class**: `BaseScorer`
```python
class BaseScorer(ABC):
    @property
    @abstractmethod
    def name(self) -> str

    @abstractmethod
    def score(expected: str, actual: str) -> ScoringResult
```

**Concrete Implementations**:
- **ExactMatchScorer**: Binary 0/1 matching
- **SemanticSimilarityScorer**: Uses sentence-transformers (0-1)
- **CompositeScorer**: Weighted combination
- **Custom**: Users can extend `BaseScorer`

**Scoring Pipeline**:
```python
scorer = CompositeScorer(
    scorers={
        "exact": ExactMatchScorer(),
        "semantic": SemanticSimilarityScorer()
    },
    weights={"exact": 0.4, "semantic": 0.6}
)

result = scorer.score(
    expected="Paris",
    actual="The capital of France is Paris"
)
# result.score: 0.75 (40% exact + 60% semantic)
```

### 4. Cost Intelligence (aegis/cost/)

**Purpose**: Track and analyze model usage costs

**Components**:
- **CostCalculator**: Token → $ conversion
- **CostAggregator**: Aggregate costs by model/period
- **CostLimiter**: Budget enforcement
- **PricingRegistry**: Model pricing data

**Pricing Model**:
```python
pricing = {
    "gpt-4": {
        "input": 0.03,      # $ per 1K tokens
        "output": 0.06
    },
    "claude-3-opus": {
        "input": 0.015,
        "output": 0.075
    }
}

cost = calculator.calculate_request_cost(
    model="gpt-4",
    input_tokens=150,
    output_tokens=300
)
# cost = (150 * 0.03 + 300 * 0.06) / 1000 = $0.0225
```

**CPQ Metric** (Cost-Per-Quality):
```python
# Lower CPQ = better value
cpq = total_cost / avg_score

# Example:
# Model A: cost=$0.20, score=0.90 → CPQ=0.222
# Model B: cost=$0.10, score=0.80 → CPQ=0.125 (better)
cpq_ranking = sorted(models, key=lambda m: m['cpq'])
```

### 5. Storage Backend (aegis/storage/)

**Purpose**: Persist evaluation runs and baselines

**Base Class**: `BaseStorage`
```python
class BaseStorage(ABC):
    @abstractmethod
    def save_run(run_data: dict, run_id: str) -> None

    @abstractmethod
    def load_run(run_id: str) -> dict | None

    @abstractmethod
    def save_baseline(dataset_name: str, baseline: dict) -> None

    @abstractmethod
    def load_baseline(dataset_name: str) -> dict | None
```

**Concrete Implementations**:
- **SQLiteBackend**: Relational database (production)
- **MemoryBackend**: In-memory (testing)
- **Custom**: Users can extend `BaseStorage`

**Database Schema**:
```sql
-- Runs table
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    dataset_name TEXT,
    model TEXT,
    created_at TIMESTAMP,
    run_json TEXT  -- Full result JSON
);

-- Baselines table
CREATE TABLE baselines (
    dataset_name TEXT PRIMARY KEY,
    model TEXT,
    baseline_json TEXT  -- Baseline metrics
);
```

### 6. CLI Interface (aegis/cli/)

**Framework**: Typer (async-first)

**Commands**:
```bash
# Evaluate single model
aegis eval --dataset data.yaml --model gpt-4

# Compare multiple models
aegis compare --dataset data.yaml \
  --models gpt-4,gpt-3.5-turbo,claude-3-opus

# Manage baselines
aegis baseline set --dataset qa --model gpt-4
aegis baseline show --dataset qa

# Track costs
aegis cost --dataset data.yaml --mode daily|weekly|monthly

# Legacy compatibility
aegis run --dataset data.yaml --model gpt-4
```

## Data Flow

### Evaluation Flow
```
Dataset YAML
    ↓
Dataset.from_yaml() → Load test cases
    ↓
For each test case:
    ├→ Adapter.generate(prompt)
    ├→ Scorer.score(expected, actual)
    ├→ CostCalculator.calculate_cost(tokens)
    └→ TestCaseResult
    ↓
EvaluationResult (aggregated)
    ↓
Storage.save_run(result)
```

### Comparison Flow
```
Dataset YAML
    ↓
For each model:
    ├→ Evaluation Flow
    ├→ Collect metrics
    └→ Calculate CPQ
    ↓
Sort by CPQ (ascending)
    ↓
Output (text table or JSON)
```

## Extension Points

### Adding a Custom Adapter
```python
from aegis.adapters.base import BaseModelAdapter, ModelResponse

class MyAdapter(BaseModelAdapter):
    @property
    def provider_name(self) -> str:
        return "my_provider"

    async def generate(self, prompt, system_prompt=None, **kwargs):
        # Call your LLM API
        response = await my_llm_client.complete(prompt)
        return ModelResponse(
            text=response.text,
            input_tokens=response.usage.input,
            output_tokens=response.usage.output,
            latency_ms=response.duration_ms,
            model=self.model,
            raw_metadata=response.metadata
        )

    def get_model_info(self) -> dict:
        return {
            "context_window": 4096,
            "training_date": "2024-01",
            "supports_vision": False
        }
```

### Adding a Custom Scorer
```python
from aegis.scoring.base import BaseScorer, ScoringResult

class MyScorer(BaseScorer):
    @property
    def name(self) -> str:
        return "my_scorer"

    def score(self, expected: str, actual: str) -> ScoringResult:
        # Custom scoring logic
        similarity = calculate_similarity(expected, actual)
        return ScoringResult(
            score=similarity,
            explanation=f"Similarity: {similarity:.2%}"
        )
```

## Performance Considerations

### Async/Sync
- **Evaluator.run()**: Async method (preferred)
- **Evaluator.run_sync()**: Wrapper using asyncio.run()
- CLI automatically handles async execution

### Token Counting
- **OpenAI**: Uses tiktoken (~instant)
- **Anthropic**: Uses anthropic SDK tokenizer (~instant)
- **Semantic Similarity**: First load ~2s, subsequent <50ms

### Cost Calculation
- Pre-computed pricing tables
- O(1) per-token calculation
- Batch aggregation available

### Storage
- SQLite indexes on run_id, dataset_name
- Connection pooling in production
- Prepared statements prevent SQL injection

## Error Handling Strategy

### Graceful Degradation
1. **Missing Optional Dependencies**
   - Anthropic SDK: Tests skipped, adapter unavailable
   - Transformers: Semantic scorer unavailable
   - Fallback to available alternatives

2. **API Failures**
   - Timeout handling with retries
   - Circuit breaker pattern for repeated failures
   - User-friendly error messages

3. **Data Validation**
   - Dataset schema validation
   - Model name existence checks
   - Cost limits enforcement

## Integration Patterns

### Batch Evaluation
```python
# Evaluate multiple models
for model_name in ["gpt-4", "gpt-3.5-turbo"]:
    adapter = OpenAIAdapter(model_name)
    evaluator = Evaluator(adapter, scorer, storage)
    result = await evaluator.run(dataset)
```

### Cost-Aware Evaluation
```python
# Stop evaluation if cost exceeds limit
limiter = CostLimiter(budget=10.0)  # $10 max
for case in dataset.cases:
    cost = calculate_cost(...)
    if not limiter.can_proceed(cost):
        break  # Budget exhausted
```

### Regression Detection
```python
# Compare against baseline
baseline = storage.load_baseline("qa_dataset")
current = evaluation_result

if current.avg_score < baseline["avg_score"] * 0.95:
    print("⚠️  20% score regression detected!")
```

## Dependencies Graph

```
aegis/
├── adapters/
│   ├── (optional) anthropic
│   └── (optional) openai
├── core/
│   └── yaml (for dataset)
├── scoring/
│   └── (optional) sentence-transformers
├── cost/
│   └── (none)
├── storage/
│   └── sqlite3 (stdlib)
├── cli/
│   ├── typer
│   ├── rich (for tables)
│   └── pydantic (validation)
└── utils/
    └── (standard library)
```

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Cover happy path and error cases

### Integration Tests
- Test component interactions
- Use real storage backends (in-memory)
- Mock API calls with fixtures

### Performance Tests
- Benchmark cost calculations
- Test with 1000+ test cases
- Verify async scaling

## Deployment Considerations

### Development
```bash
pip install -e ".[dev]"  # Includes all dependencies
```

### Production
```bash
pip install aegis-ai  # Minimal dependencies
# Add optional adapters as needed:
pip install anthropic          # For Claude models
pip install sentence-transformers  # For semantic similarity
```

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AEGIS_LOG_LEVEL=INFO
AEGIS_STORAGE_PATH=./data/aegis.db
```

### Monitoring
- Log all evaluations (dataset, model, score, cost)
- Track cost by model and user
- Alert on cost threshold exceeded
- Monitor API error rates

## Future Architecture Improvements

1. **Distributed Evaluation**: Multi-worker evaluation with job queue
2. **Streaming Results**: Real-time result reporting
3. **Caching Layer**: Cache same prompts across evaluations
4. **Vector Database**: Store embeddings for semantic search
5. **Observability**: OpenTelemetry integration
6. **Multi-User**: Authentication and per-user cost tracking

---

This architecture ensures:
- ✅ **Extensibility**: Add adapters, scorers, storage backends
- ✅ **Reliability**: Error handling and graceful degradation
- ✅ **Performance**: Async operations and efficient calculations
- ✅ **Testability**: Mockable components and clear interfaces
- ✅ **Production-Ready**: Logging, monitoring, and cost controls
