# 📦 Customer Support Agent

A **graph-workflow customer support agent** built with [Google ADK 2.0](https://adk.dev/) that classifies incoming queries and routes them to specialist sub-agents for shipping FAQ, order tracking, and refund processing.

## ✨ Highlights

- 🧠 **Intelligent Routing** — Hybrid keyword + LLM classifier for deterministic fast-path with LLM fallback
- 🔀 **Multi-Agent Workflow** — Three specialist agents, each with domain-specific tools and instructions
- 🛠️ **Tool-Augmented Agents** — Order lookup, shipment tracking, and refund processing tools
- 📊 **Eval-Ready** — Ships with evaluation datasets and an LLM-as-judge quality metric
- 🧪 **Tested** — Unit tests (offline, no API keys) + integration tests (full workflow)

## 🏗️ Architecture

```
                                ┌──────────────────────┐
        User Query  ──────────►│   classify_query      │
                                │  (keyword + LLM)     │
                                └──────────┬───────────┘
                                           │
                    ┌──────────────────────┬┴┬──────────────────────┐
                    │                      │ │                      │
              "shipping_faq"        "order_status"           "refund"          "unrelated"
                    │                      │                      │                  │
           ┌────────▼────────┐   ┌─────────▼────────┐   ┌────────▼────────┐  ┌──────▼──────┐
           │ shipping_faq    │   │ order_status      │   │ refund_agent    │  │ polite      │
           │ _agent          │   │ _agent            │   │                 │  │ _decline    │
           │                 │   │                   │   │                 │  │             │
           │ Gemini LLM      │   │ Gemini LLM        │   │ Gemini LLM      │  │ Static msg  │
           │ (rates, policy) │   │ + lookup_order    │   │ + lookup_order  │  └─────────────┘
           └─────────────────┘   │ + track_shipment  │   │ + request_refund│
                                 └──────────────────┘   └─────────────────┘
```

| Node | Type | Description |
|---|---|---|
| `classify_query` | FunctionNode | Keyword rules + optional LLM classifier → routes to one of 4 paths |
| `shipping_faq_agent` | LLM Agent | Answers shipping rate & policy questions with injected business data |
| `order_status_agent` | LLM Agent | Looks up orders and tracks shipments via tool calls |
| `refund_agent` | LLM Agent | Validates refund eligibility and processes returns via tool calls |
| `polite_decline` | FunctionNode | Returns a polite message declining out-of-scope queries |

## 📁 Project Structure

```
customer-support-agent/
├── app/
│   ├── __init__.py              # Package export
│   ├── agent.py                 # Workflow graph — classifier + 3 specialist agents
│   ├── config.py                # Shipping rates, return policy, mock order database
│   └── tools/
│       ├── __init__.py
│       ├── order_lookup.py      # Tool: look up order details by ID
│       ├── tracking.py          # Tool: track shipment by tracking number
│       └── refund.py            # Tool: validate & process refund requests
├── tests/
│   ├── unit/
│   │   └── test_classifier.py   # 15+ offline tests — classifier, tools, edge cases
│   ├── integration/
│   │   └── test_agent.py        # End-to-end workflow tests (requires API key)
│   └── eval/
│       ├── eval_config.yaml     # LLM-as-judge + turn-count metrics
│       └── datasets/
│           └── basic-dataset.json  # 6 eval cases across all 4 categories
├── pyproject.toml               # Dependencies, linting, and build config
├── .env.example                 # Environment variable template
├── .gitignore
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **Gemini API Key** — get one at [aistudio.google.com](https://aistudio.google.com/)

### Setup

```bash
# Clone the repo
git clone https://github.com/Soham-Sahana/Personal-Mini-Projects.git
cd Personal-Mini-Projects/customer-support-agent

# Install dependencies
uv sync

# Configure your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Run Locally

```bash
# Set your API key (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"
$env:GOOGLE_GENAI_USE_ENTERPRISE="FALSE"

# Launch the ADK playground (interactive web UI)
uv run adk web .

# Or run in terminal
uv run adk run .
```

### Run Tests

```bash
# Unit tests (no API key needed)
uv run pytest tests/unit/ -v

# Integration tests (requires API key)
uv run pytest tests/integration/ -v

# All tests
uv run pytest tests/ -v
```

## 💬 Example Interactions

| You Say | Agent Route | What Happens |
|---|---|---|
| *"What are your shipping rates?"* | `shipping_faq_agent` | Returns rates with free shipping threshold |
| *"Where is order ORD-1001?"* | `order_status_agent` | Calls `lookup_order` → `track_shipment` → timeline |
| *"I want to return ORD-1002"* | `refund_agent` | Calls `lookup_order` → validates eligibility → `request_refund` |
| *"What's the meaning of life?"* | `polite_decline` | Politely declines with scope reminder |

## 🔧 How the Classifier Works

1. **Fast path** — keyword matching against curated word sets for each category (zero latency, zero cost)
2. **LLM fallback** — if keywords don't match and API credentials are available, uses `gemini-flash-latest` for zero-shot classification
3. **Safe default** — if both fail, routes to `polite_decline`

This hybrid approach means **most queries are classified instantly** without an LLM call, while edge cases still get intelligent routing.

## ⚙️ Configuration

Edit [`app/config.py`](app/config.py) to customize:

| Setting | Default | Description |
|---|---|---|
| `SHIPPING_RATES` | 3 tiers | Standard, Express, Overnight with prices & timelines |
| `FREE_SHIPPING_THRESHOLD` | $50.00 | Minimum order total for free shipping |
| `RETURN_WINDOW_DAYS` | 30 | Days after delivery to request a refund |
| `MOCK_ORDERS` | 3 orders | Sample orders for demo (replace with real DB in production) |

## 🛠️ Tech Stack

- **[Google ADK 2.0](https://adk.dev/)** — Agent Development Kit with declarative Workflow graphs
- **[Gemini](https://ai.google.dev/)** — LLM for specialist agents and fallback classification
- **[uv](https://docs.astral.sh/uv/)** — Fast Python package manager & runner
- **[pytest](https://docs.pytest.org/)** — Testing framework

## 📄 License

Apache License 2.0 — see [LICENSE](../LICENSE) for details.
