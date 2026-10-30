<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,21,30&height=180&section=header&text=Personal%20Mini%20Projects&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=AI%20Agents%20%7C%20Machine%20Learning%20%7C%20Automation&descSize=16&descAlignY=55"/>

<br/>

![Python](https://img.shields.io/badge/Python-3.10+-14354C?style=for-the-badge&logo=python&logoColor=white)
![Google ADK](https://img.shields.io/badge/Google_ADK_2.0-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_AI-886FBF?style=for-the-badge&logo=googlegemini&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

<br/>

A collection of small, focused projects exploring **AI agents**, **machine learning**, and **modern development tools**.

---

[Expense Agent](#-ambient-expense-agent) · [Support Agent](#-customer-support-agent) · [Cancer Classification](#-breast-cancer-classification) · [License](#-license)

</div>

<br/>

## 📂 Project Overview

| # | Project | Category | Highlights | Tech Stack |
|---|---------|----------|-----------|------------|
| 1 | [**Ambient Expense Agent**](./ambient-expense-agent/) | 🤖 AI Agent | Event-driven expense approval with LLM risk analysis, PII scrubbing, and human-in-the-loop review | Google ADK 2.0, Gemini, FastAPI, Pydantic |
| 2 | [**Customer Support Agent**](./customer-support-agent/) | 🤖 AI Agent | Graph-workflow support agent with intelligent routing to specialist sub-agents | Google ADK 2.0, Gemini, pytest |
| 3 | [**Breast Cancer Classification**](./breast_cancer_ml_project/) | 🧬 ML | Multi-model comparison pipeline with EDA, hyperparameter tuning, and Streamlit deployment | scikit-learn, Streamlit, Matplotlib |

---

## 🧾 Ambient Expense Agent

<img align="right" width="80" src="https://img.icons8.com/fluency/96/receipt-dollar.png" alt="expense"/>

An **event-driven expense approval agent** that autonomously processes corporate expenses in real-time — auto-approving low-risk items and routing high-value expenses through LLM risk analysis and human review.

**What makes it "Ambient"** — unlike chatbot-style AI that waits for prompts, this agent operates **continuously in the background**:

- 📡 **Listens** for expense events via Pub/Sub or webhook
- ⚡ **Auto-approves** routine expenses under $100 instantly
- 🛡️ **Guards** against PII leaks and prompt injection attacks
- 🧠 **LLM Risk Analysis** for high-value expense review
- 🤖 **Escalates** intelligently when human judgment is required

```
   Pub/Sub / Webhook ──► parse_expense ──► route_expense
                                               │
                              ┌────────────────┴────────────────┐
                         < $100 (auto)                    ≥ $100 (review)
                              │                                 │
                        auto_approve              security_check ──► risk_reviewer (LLM)
                              │                                 │
                              └──────── notify_result ──────────┘
```

<div align="right">

[📖 Full Documentation →](./ambient-expense-agent/README.md)

</div>

---

## 📦 Customer Support Agent

<img align="right" width="80" src="https://img.icons8.com/fluency/96/customer-support.png" alt="support"/>

A **graph-workflow customer support agent** that classifies incoming queries and routes them to specialist sub-agents for shipping FAQ, order tracking, and refund processing.

- 🧠 **Intelligent Routing** — Hybrid keyword + LLM classifier with deterministic fast-path and LLM fallback
- 🔀 **Multi-Agent Workflow** — Three specialist agents with domain-specific tools and instructions
- 🛠️ **Tool-Augmented** — Order lookup, shipment tracking, and refund processing tools
- 📊 **Eval-Ready** — Ships with evaluation datasets and LLM-as-judge quality metric
- 🧪 **Fully Tested** — Unit tests (offline) + integration tests (full workflow)

```
   User Query ──► classify_query (keyword + LLM)
                         │
          ┌──────────────┼──────────────┬──────────────┐
     "shipping_faq"  "order_status"  "refund"     "unrelated"
          │              │              │              │
   shipping_faq    order_status    refund_agent   polite_decline
      _agent          _agent
```

<div align="right">

[📖 Full Documentation →](./customer-support-agent/README.md)

</div>

---

## 🧬 Breast Cancer Classification

<img align="right" width="80" src="https://img.icons8.com/fluency/96/microscope.png" alt="ml"/>

A comprehensive **ML pipeline** for binary classification on the Wisconsin Breast Cancer dataset — comparing multiple algorithms with proper evaluation, hyperparameter tuning, and a Streamlit web app for interactive predictions.

- 📊 **Exploratory Data Analysis** — Feature distributions, correlations, and class balance
- 🔬 **Multi-Model Comparison** — Logistic Regression, Random Forest, SVM, KNN, and more
- 🎯 **Hyperparameter Tuning** — Grid search for optimized model performance
- 📈 **Evaluation Metrics** — Accuracy, Precision, Recall, F1-Score, ROC-AUC
- 🌐 **Streamlit App** — Interactive web interface for real-time predictions

```
breast_cancer_ml_project/
├── train.py               # Full training pipeline
├── app.py                 # Streamlit deployment
├── src_utils.py           # Utility functions
├── report.md              # Detailed analysis report
├── plots/                 # Generated visualizations
├── results/               # Model comparison CSVs
└── artifacts/             # Trained model + metadata
```

> ⚠️ **Disclaimer:** This project is for educational purposes only. It is not a medical device and must not be used for healthcare decisions.

<div align="right">

[📖 Full Documentation →](./breast_cancer_ml_project/README.md)

</div>

---

## 🛠️ Tech Stack

<div align="center">

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.10+ |
| **AI Agents** | Google ADK 2.0, Gemini API |
| **ML/Data** | scikit-learn, NumPy, Pandas, Matplotlib |
| **Web** | FastAPI, Streamlit, Pydantic |
| **Testing** | pytest |
| **DevOps** | Docker, Git |

</div>

---

## 🚀 Getting Started

Each project has its own setup instructions. Click the links below to get started:

| Project | Setup Guide |
|---------|-------------|
| Ambient Expense Agent | [README →](./ambient-expense-agent/README.md) |
| Customer Support Agent | [README →](./customer-support-agent/README.md) |
| Breast Cancer Classification | [README →](./breast_cancer_ml_project/README.md) |

---

## 📝 License

Apache License 2.0 — see [LICENSE](./LICENSE) for details.

---

<div align="center">

**Built by [Soham Sahana](https://github.com/Soham-Sahana)**

<a href="https://www.linkedin.com/in/soham-sahana-17a674347/"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
&nbsp;
<a href="mailto:sohamssahana@gmail.com"><img src="https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white"/></a>

<br/><br/>

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,21,30&height=100&section=footer"/>

</div>
