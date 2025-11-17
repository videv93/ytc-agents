# LangSmith Quick Start

Visualize your trading workflow in 5 minutes.

## Setup

1. **Get API Key**
   ```
   https://smith.langchain.com → Settings → API Keys → Copy
   ```

2. **Add to `.env`**
   ```bash
   LANGSMITH_API_KEY=ls_xxxx...
   LANGSMITH_PROJECT=ytc-trading-system
   ```

3. **Install**
   ```bash
   pip install -e .
   ```

## Visualize Graph

### Option 1: Local PNG
```bash
python3 examples/visualize_workflow.py --output graphs/workflow.png
```

### Option 2: ASCII (no dependencies)
```bash
python3 examples/visualize_workflow.py --ascii
```

### Option 3: LangSmith Dashboard
```bash
python3 examples/visualize_workflow.py --langsmith
```
Then visit: `https://smith.langchain.com/projects/ytc-trading-system`

## Auto-Trace Trading Sessions

Just run normally:
```bash
python3 main.py
```

LangSmith automatically traces everything if `LANGSMITH_API_KEY` is set.

View traces: `https://smith.langchain.com/projects/ytc-trading-system`

---

**Full guide:** See `docs/LANGSMITH_SETUP.md`
