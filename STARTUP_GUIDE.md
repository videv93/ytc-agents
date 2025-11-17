# YTC Trading System Startup Guide

## Problem: Process Hangs Without Logs

If `python3 main.py` hangs and displays no logs after the banner, follow this guide.

### Root Cause

The system runs multiple initialization steps that can fail silently if not properly configured:

1. **Database Connection** - PostgreSQL must be running
2. **Hummingbot Gateway** - Must be accessible at configured URL
3. **Environment Variables** - Must have valid Anthropic API key
4. **Logging Output** - Uses structured JSON logging which may not appear immediately

### Quick Diagnosis

Run the diagnostic script to identify the issue:

```bash
python3 debug_startup.py
```

This will test each component in order and tell you exactly what's failing:
- ✓ Environment loading
- ✓ Database connectivity
- ✓ Configuration loading
- ✓ Hummingbot Gateway connection
- ✓ Orchestrator initialization

### Common Issues & Solutions

#### 1. Database Connection Error

**Error:** `connection_test_failed` or `database_initialization_failed`

**Solution:**
```bash
# Check if PostgreSQL is running
psql -h localhost -U ytc_trader -d ytc_trading -c "SELECT 1"

# If not running, start it:
brew services start postgresql@15  # macOS
sudo systemctl start postgresql     # Linux

# Or verify credentials in .env file:
cat .env | grep POSTGRES_
```

**Fix:** Update `.env` with correct PostgreSQL credentials

#### 2. Hummingbot Gateway Not Accessible

**Error:** `gateway_api_request` fails or times out

**Solution:**
```bash
# Check if Hummingbot Gateway is running
curl http://localhost:8000/portfolio/state

# If not running, start it (Hummingbot must be running separately)
hummingbot start

# Or change the gateway URL in .env:
HUMMINGBOT_GATEWAY_URL=http://your-gateway-url:8000
```

**Fix:** Ensure Hummingbot Gateway is running on the configured URL

#### 3. Missing Anthropic API Key

**Error:** `ANTHROPIC_API_KEY` is placeholder value

**Solution:**
```bash
# Edit .env and add your real API key:
ANTHROPIC_API_KEY=sk-ant-...your-real-key-here...

# Verify it's set:
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Key set' if os.getenv('ANTHROPIC_API_KEY').startswith('sk-') else 'Invalid key')"
```

**Fix:** Get API key from [console.anthropic.com](https://console.anthropic.com)

#### 4. Logs Not Appearing

**Issue:** System is running but no output visible

**Solution:**

The system uses **JSON structured logging**. Output appears but in JSON format, not human-readable.

**Option A: View JSON logs directly**
```bash
python3 main.py 2>&1 | python3 -m json.tool
```

**Option B: Redirect to file**
```bash
python3 main.py > logs/system.log 2>&1
tail -f logs/system.log
```

**Option C: Change logging format (development)**

Edit `main.py` line 26 and change:
```python
# OLD:
structlog.processors.JSONRenderer()

# NEW:
structlog.dev.ConsoleRenderer()
```

Then re-run `python3 main.py` for human-readable output.

### Step-by-Step Startup

1. **Verify Database**
   ```bash
   psql -h localhost -U ytc_trader -d ytc_trading -c "SELECT 1"
   ```
   
2. **Verify Hummingbot Gateway**
   ```bash
   curl http://localhost:8000/portfolio/state
   ```
   
3. **Verify Environment**
   ```bash
   python3 debug_startup.py
   ```
   
4. **Run System with Logging**
   ```bash
   python3 -u main.py 2>&1 | tee logs/startup.log
   ```

5. **Monitor in Real-time**
   ```bash
   tail -f logs/startup.log | grep -E "error|failed|phase"
   ```

### What Success Looks Like

After startup, you should see:
1. Banner output
2. Logs showing:
   - Database connection successful
   - Hummingbot balance fetch
   - Orchestrator initialization
   - Session started with phase: `pre_market`
3. Workflow begins executing agents

Example JSON log (formatted):
```json
{
  "timestamp": "2025-11-17T17:53:40...",
  "event": "orchestrator_initialized",
  "session_id": "abc123...",
  "phase": "pre_market"
}
```

### Enable Debug Logging

For detailed troubleshooting, edit `.env`:

```bash
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### Force Non-Blocking Startup

If you want the system to print logs in real-time rather than buffering:

```bash
python3 -u main.py
```

The `-u` flag sets Python to unbuffered mode.

### Still Stuck?

Check logs with:
```bash
# See last 50 lines
tail -50 logs/ytc_system.log

# Search for errors
grep -i "error\|failed\|exception" logs/ytc_system.log

# Watch logs in real-time
tail -f logs/ytc_system.log
```

### Next Steps

Once startup succeeds:
- View the workflow: `python3 examples/visualize_workflow.py --ascii`
- Monitor trading: Watch logs in a separate terminal
- Enable LangSmith: Add `LANGSMITH_API_KEY` to `.env` for detailed tracing

See `docs/LANGSMITH_SETUP.md` for workflow visualization.
