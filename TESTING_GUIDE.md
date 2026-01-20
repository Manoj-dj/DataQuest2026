# Testing Guide for Predictive Disaster Intelligence System

## 🧪 Quick Test

Run the test script:
```bash
python test_predictions.py
```

This will test:
1. ✅ Health endpoint
2. ✅ Predictions API endpoint
3. ✅ WebSocket connection

## 📋 Manual Testing Steps

### 1. Backend Testing

#### Test Health Endpoint
```bash
curl http://localhost:8080/api/health
```
Expected: JSON response with status "healthy"

#### Test Predictions Endpoint
```bash
curl http://localhost:8080/api/predictions
```
Expected: JSON with `predictions` array, `total` count, and `timestamp`

#### Test WebSocket (using wscat or browser console)
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/predictions');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### 2. Frontend Testing

1. **Start the frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

2. **Navigate to Predictions:**
   - Click "Predictions" in the sidebar (⚡ icon)
   - Should see the predictions dashboard

3. **Check WebSocket Connection:**
   - Open browser console (F12)
   - Should see "Prediction WebSocket connected" message
   - Should receive connection confirmation

4. **Test Predictions Display:**
   - If events exist: Should see prediction cards
   - If no events: Should see "No predictions available" message
   - Click "Refresh" button to reload

5. **Test Live Alerts:**
   - Alerts appear in top-right corner when patterns detected
   - Auto-dismiss after 10 seconds
   - Animated slide-in effect

### 3. Integration Testing

#### Test Full Flow:
1. Ensure backend is running with events in database
2. Open frontend and navigate to Predictions
3. Verify predictions load automatically
4. Check WebSocket connection in console
5. Verify auto-refresh every 30 seconds

## 🔍 Expected Behavior

### Predictions Endpoint Response:
```json
{
  "predictions": [
    {
      "event_id": "gdacs:12345",
      "event_title": "Earthquake - California",
      "prediction": "**Expected Impact:** ...",
      "confidence": "HIGH",
      "severity": "Red",
      "risk_score": 7.5,
      "timestamp": "2026-01-18T..."
    }
  ],
  "total": 1,
  "timestamp": "2026-01-18T..."
}
```

### WebSocket Messages:
- `{"type": "connected", "message": "...", "timestamp": "..."}` - On connect
- `{"type": "ping", "timestamp": "..."}` - Keep-alive
- `{"type": "PREDICTION_ALERT", ...}` - When pattern detected

## ⚠️ Common Issues

### Issue: "No predictions available"
**Cause:** No events in database or events older than 24 hours
**Solution:** Wait for events to be ingested, or check if pipeline is running

### Issue: WebSocket connection fails
**Cause:** Backend not running or wrong port
**Solution:** Verify backend is on port 8080, check CORS settings

### Issue: Predictions endpoint times out
**Cause:** AI model taking too long or no similar events found
**Solution:** This is normal - predictions can take 10-30 seconds

### Issue: "Cannot connect to API"
**Cause:** Backend not running
**Solution:** Start backend with `./run_backend.sh` or `python src/main.py`

## ✅ Success Criteria

- [ ] Health endpoint returns 200 OK
- [ ] Predictions endpoint returns JSON (even if empty)
- [ ] WebSocket connects and receives messages
- [ ] Frontend displays predictions (or empty state)
- [ ] WebSocket shows connected in console
- [ ] Refresh button works
- [ ] Auto-refresh works (check after 30 seconds)

## 🐛 Debugging

### Check Backend Logs:
```bash
tail -f logs/disasterlens_*.log
```

### Check Frontend Console:
- Open browser DevTools (F12)
- Check Console for errors
- Check Network tab for API calls

### Test API Directly:
```bash
# Health check
curl http://localhost:8080/api/health

# Get predictions
curl http://localhost:8080/api/predictions | jq

# Check events
curl http://localhost:8080/api/events/latest?limit=5 | jq
```

## 📊 Performance Notes

- Predictions generation: 5-30 seconds per event
- WebSocket latency: < 100ms
- Auto-refresh interval: 30 seconds
- Alert display duration: 10 seconds
