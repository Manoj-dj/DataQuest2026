# Backend Restart Instructions

## Current Status
✅ Backend is running and responding  
❌ New endpoints (alerts, settings, simulate) are returning 404  
**Reason:** Server needs restart to load new routes

## How to Restart Backend

### Option 1: If running in WSL terminal
1. Find the terminal where backend is running
2. Press `Ctrl+C` to stop it
3. Restart with:
   ```bash
   cd /mnt/c/Users/HP/Downloads/DataQuest1/DataQuest2026
   python3 src/main.py
   # OR if using uv:
   uv run python3 src/main.py
   ```

### Option 2: Using the run script
```bash
cd /mnt/c/Users/HP/Downloads/DataQuest1/DataQuest2026
./run_backend.sh
```

### Option 3: If using systemd or service
```bash
sudo systemctl restart disasterlens
# OR
sudo service disasterlens restart
```

## Verify Restart Worked

After restarting, run the test again:
```bash
cd /mnt/c/Users/HP/Downloads/DataQuest1/DataQuest2026
python3 test_backend.py
```

You should see all 6 tests pass:
- ✅ Health Endpoints
- ✅ Events Endpoint  
- ✅ Predictions Endpoint
- ✅ Alerts Endpoint (should work after restart)
- ✅ Alert Settings Endpoint (should work after restart)
- ✅ Simulate Endpoint (should work after restart)

## Expected Output After Restart

```
============================================================
Test Summary
============================================================
Health Endpoints........................ [PASS]
Events Endpoint......................... [PASS]
Predictions Endpoint.................... [PASS]
Alerts Endpoint......................... [PASS]  ← Should work
Alert Settings Endpoint................. [PASS]  ← Should work
Simulate Endpoint....................... [PASS]  ← Should work

[SUCCESS] All tests passed! Backend is working correctly.
```

## Troubleshooting

If endpoints still return 404 after restart:

1. **Check server logs** for errors during startup
2. **Verify routes are registered:**
   ```bash
   curl http://localhost:8080/docs
   # Should show all endpoints in Swagger UI
   ```
3. **Check if server actually restarted:**
   ```bash
   # Check uptime
   curl http://localhost:8080/health
   # Uptime should be low (few seconds) if just restarted
   ```
