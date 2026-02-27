# OpenCM 1.0 — Structural Causal Model Interchange Standard

**Version**: 1.0 (Stable)  
**Status**: Published  
**Authors**: Jamie Nixx - Founder - Cognition Universal Intel  
**Date**: February 2026

---

## 1. Abstract

OpenCM is a language-agnostic, JSON-based specification for representing **Structural Causal Models (SCMs)**. While standards exist for machine learning models (ONNX) and APIs (OpenAPI), causal inference has lacked a portable, versionable interchange format. OpenCM fills this gap — enabling researchers and engineers to share, validate, and compose causal structures across different software ecosystems.

An OpenCM file encodes a Directed Acyclic Graph (DAG) augmented with structural equations, noise parameters, business metadata, and explicit assumptions.

---

## 2. File Conventions

| Property | Rule |
|---|---|
| **Extension** | `.opencm.json` |
| **Encoding** | UTF-8 |
| **Top-level** | Single JSON object |
| **Model ID** | Lowercase alphanumeric with underscores: `^[a-z][a-z0-9_]*$` |
| **Versioning** | SemVer (`MAJOR.MINOR.PATCH`) |

---

## 3. Top-Level Structure

Every `.opencm.json` file **must** contain these fields:

```json
{
  "opencm_version": "1.0",
  "model": { ... },
  "variables": { ... },
  "edges": [ ... ]
}
```

**Optional** fields:

```json
{
  "structural_equations": { ... },
  "assumptions": [ ... ],
  "validation": { ... },
  "metadata": { ... }
}
```

---

## 4. Model Identity (`model`)

Every model must declare its identity:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | ✅ | Unique slug (`porters_five_forces`) |
| `name` | string | ✅ | Human-readable title |
| `version` | string | ❌ | SemVer string (default `"1.0.0"`) |
| `domain` | string | ❌ | Feature area (see §11) |
| `description` | string | ❌ | Technical summary |

---

## 5. Variables (`variables`)

Variables are the **nodes** of the causal graph. Each key is the variable ID (PascalCase recommended), mapping to a definition object.

| Field | Type | Required | Description |
|---|---|---|---|
| `type` | string | ❌ | `continuous` (default), `discrete`, `binary`, `categorical` |
| `domain` | `[min, max]` | ❌ | Value range for continuous variables (default `[0, 1]`) |
| `unit` | string | ❌ | Business unit (`$`, `%`, `users`, `index`, `score`) |
| `description` | string | ❌ | What the variable represents |
| `observed` | boolean | ❌ | Is this variable measurable? (default `true`) |
| `default_value` | number | ❌ | Starting value if known |
| `categories` | string[] | ❌ | Valid values for `categorical` type |

**Constraints:**
- `domain[0]` must be strictly less than `domain[1]`
- `categorical` variables should provide `categories`
- Variable IDs must appear in at least one edge (`source` or `target`)

---

## 6. Causal Relationships (`edges`)

Edges define the directed causal structure. The array is ordered but order has no semantic meaning.

| Field | Type | Required | Description |
|---|---|---|---|
| `source` | string | ✅ | Parent variable ID |
| `target` | string | ✅ | Child variable ID |
| `type` | string | ❌ | Relationship type (default `"causes"`) |
| `strength` | number | ❌ | Absolute influence `[-1.0, 1.0]` (default `0.5`) |
| `description` | string | ❌ | Narrative justification |
| `confidence` | number | ❌ | Confidence in this edge `[0, 1]` (default `1.0`) |
| `is_learned` | boolean | ❌ | Was this edge derived from data? (default `false`) |

### 6.1 Edge Types

| Type | Semantics | Strength Convention |
|---|---|---|
| `causes` | X → Y (direct cause) | Positive = amplifies |
| `inhibits` | X ⊣ Y (suppresses) | Positive value auto-negated during simulation |
| `correlates` | X ↔ Y (shared cause) | Non-directional association |
| `mediates` | X → M → Y (M mediates) | Mediation pathway |
| `moderates` | X modulates Z → Y | Interaction effect |

**Constraints:**
- `source` and `target` must exist in `variables`
- No self-loops (`source ≠ target`)
- The edge set must form a **Directed Acyclic Graph (DAG)** — cycles are invalid

---

## 7. Structural Equations (`structural_equations`)

The heart of OpenCM. Equations define how parent variables determine child values beyond simple linear weights.

### 7.1 Simple Format (string)

```json
"structural_equations": {
  "IndustryProfitability": "0.7 - 0.15*SupplierPower - 0.20*BuyerPower + 0.20*PricingPower"
}
```

A plain string expression. Default equation type is `linear`, default noise is `normal(0, 0.05)`.

### 7.2 Rich Format (object)

```json
"structural_equations": {
  "ConversionRate": {
    "type": "logistic",
    "expression": "1 / (1 + exp(-3 * (Desire - 0.5)))",
    "noise_distribution": "normal",
    "noise_params": { "mean": 0.0, "std": 0.02 }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `type` | string | `linear`, `polynomial`, `exponential`, `logistic`, `interaction`, `synergy`, `custom` |
| `expression` | string | Python-style arithmetic expression |
| `noise_distribution` | string | `normal` or `uniform` |
| `noise_params` | object | Distribution parameters (`mean`/`std` or `low`/`high`) |

### 7.3 Expression Syntax

- **Arithmetic:** `+`, `-`, `*`, `/`, `**` (exponentiation)
- **Built-in functions:** `abs()`, `min()`, `max()`, `log()`, `exp()`, `sqrt()`
- **Constants:** numeric literals (`0.5`, `3.14`)
- **Variable references:** must reference direct parents only (as defined in `edges`)

**Constraints:**
- Equation targets must exist in `variables`
- Referenced variables must be direct parents per the edge set
- Not all variables require equations — variables without equations are exogenous (root nodes)

---

## 8. Assumptions

A list of explicit boundary conditions. Models should be transparent about what they assume.

```json
"assumptions": [
  "Static equilibrium analysis — does not model dynamic responses",
  "Forces are assumed independent at the input level",
  "Industry boundaries are clearly defined"
]
```

Models without assumptions will trigger a validation **warning** (not error).

---

## 9. Validation (`validation`)

Optional requirements for calibrating the model against real data.

| Field | Type | Description |
|---|---|---|
| `min_data_points` | integer | Minimum observations needed (default `20`) |
| `required_variables` | string[] | Variables that must have observed data |
| `suggested_datasets` | string[] | Recommended data sources |

---

## 10. Metadata (`metadata`)

Provenance and attribution.

| Field | Type | Description |
|---|---|---|
| `author` | string | Creator or adaptor |
| `citation` | string | Academic source |
| `license` | string | Usage rights (default `"CC0-1.0-Universal"`) |
| `tags` | string[] | Searchable keywords |
| `source_url` | string | Original framework URL |
| `adaptation_notes` | string | How the model was adapted for OpenCM |
| `created_at` | string | ISO-8601 timestamp |
| `updated_at` | string | ISO-8601 timestamp |

---

## 11. Domain Registry

Recognized domain values for `model.domain`:

| Domain | Scope |
|---|---|
| `strategy` | Competitive strategy, positioning |
| `marketing` | Demand, funnel, brand |
| `finance` | Valuation, capital, risk |
| `operations` | Supply chain, throughput |
| `organization` | Culture, motivation, structure |
| `technology` | Adoption, network effects |
| `economics` | Macro/micro theory |
| `psychology` | Behavioral, cognitive |
| `healthcare` | Clinical, epidemiological |
| `supply_chain` | Logistics, procurement |
| `general` | Cross-domain |

---

## 12. Validation Rules (Normative)

A file is **valid OpenCM 1.0** if and only if:

1. ✅ Contains `opencm_version`, `model`, `variables`, `edges`
2. ✅ `model.id` matches `^[a-z][a-z0-9_]*$`
3. ✅ `model.name` is a non-empty string
4. ✅ At least one variable is defined
5. ✅ All `source`/`target` IDs in edges exist in `variables`
6. ✅ No self-loops
7. ✅ Edge set forms a **DAG** (no directed cycles)
8. ✅ Variable domains satisfy `min < max`
9. ✅ Edge strengths are in `[-1.0, 1.0]`
10. ✅ Equation targets exist in `variables`

Items that trigger **warnings** (not errors):
- Unknown `model.domain`
- Missing `assumptions`
- Unknown edge type

---

## 13. Composition Protocol

OpenCM models are designed to be **composable**. Two or more models can be merged into a single unified graph.

### 13.1 Merge Algorithm

```
COMPOSE(Model_A, Model_B) → Model_C:
  1. Union all variables; skip duplicates (first model wins)
  2. Union all edges; for duplicate (source, target) pairs,
     keep higher-confidence edge
  3. Merge equations; first model wins for shared targets
  4. Concatenate assumptions with model-ID prefixes
  5. Validate merged graph for DAG acyclicity
```

### 13.2 Shared Variables as Join Points

When models share variable names (e.g., `CompetitiveRivalry` in both Porter's and PESTLE), those variables become **join points** that bridge the two causal structures. This enables cross-domain analysis without manual graph surgery.

### 13.3 Lensing

A model can be **applied as a lens** — configuring an inference engine to reason through a specific causal structure. Multiple lenses can be compared by running the same intervention through each and contrasting outcomes.

---

## 14. Example: Porter's Five Forces

```json
{
  "opencm_version": "1.0",
  "model": {
    "id": "porters_five_forces",
    "name": "Porter's Five Forces",
    "version": "1.0.0",
    "domain": "strategy",
    "description": "Analyzing competitive intensity through five structural forces."
  },
  "variables": {
    "SupplierPower":        { "type": "continuous", "domain": [0, 1], "unit": "index" },
    "BuyerPower":           { "type": "continuous", "domain": [0, 1], "unit": "index" },
    "ThreatOfSubstitutes":  { "type": "continuous", "domain": [0, 1], "unit": "index" },
    "ThreatOfNewEntrants":  { "type": "continuous", "domain": [0, 1], "unit": "index" },
    "CompetitiveRivalry":   { "type": "continuous", "domain": [0, 1], "unit": "index" },
    "IndustryProfitability":{ "type": "continuous", "domain": [0, 1], "unit": "margin" },
    "MarketShare":          { "type": "continuous", "domain": [0, 1], "unit": "%" },
    "PricingPower":         { "type": "continuous", "domain": [0, 1], "unit": "index" }
  },
  "edges": [
    { "source": "SupplierPower",       "target": "IndustryProfitability", "type": "inhibits", "strength": 0.65 },
    { "source": "BuyerPower",          "target": "IndustryProfitability", "type": "inhibits", "strength": 0.70 },
    { "source": "CompetitiveRivalry",  "target": "IndustryProfitability", "type": "inhibits", "strength": 0.80 },
    { "source": "PricingPower",        "target": "IndustryProfitability", "type": "causes",   "strength": 0.75 },
    { "source": "MarketShare",         "target": "IndustryProfitability", "type": "causes",   "strength": 0.60 }
  ],
  "structural_equations": {
    "IndustryProfitability": "0.7 - 0.15*SupplierPower - 0.20*BuyerPower - 0.25*CompetitiveRivalry + 0.20*PricingPower + 0.15*MarketShare"
  },
  "assumptions": [
    "Static equilibrium — does not model dynamic responses",
    "Forces are independent at the input level"
  ],
  "metadata": {
    "author": "GetCognition (adapted from Porter, 1979)",
    "citation": "Porter, M.E. (1979). How Competitive Forces Shape Strategy. HBR.",
    "license": "CC0-1.0-Universal",
    "tags": ["competition", "industry-analysis", "strategy"]
  }
}
```

---

---

To the extent possible under law, Jamie Nixx and the GetCognition team have waived all copyright and related or neighboring rights to the OpenCM 1.0 Specification. This work is published from: United States.

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](http://creativecommons.org/publicdomain/zero/1.0/)
