# Eval dataset README
This directory contains evaluation datasets for the customer support agent.

## Dataset format
Each JSON file follows the ADK eval schema:
```json
{
  "eval_cases": [
    {
      "eval_case_id": "unique_id",
      "prompt": {
        "role": "user",
        "parts": [{"text": "user query"}]
      }
    }
  ]
}
```

## Running evaluations
```bash
agents-cli eval generate
agents-cli eval grade
```
