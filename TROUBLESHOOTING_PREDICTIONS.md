# Troubleshooting: Can't See Predictions Component

## ✅ Verification Checklist

### 1. Check Sidebar Menu
The "Predictions" menu item should appear in the sidebar:
- Look for a ⚡ (Zap) icon
- Label: "Predictions"
- Position: Between "Query" and "Settings"

### 2. If Menu Item is Missing

**Solution 1: Restart Frontend Dev Server**
```bash
# Stop the current dev server (Ctrl+C)
cd frontend
npm run dev
```

**Solution 2: Hard Refresh Browser**
- Windows/Linux: `Ctrl + Shift + R`
- Mac: `Cmd + Shift + R`

**Solution 3: Clear Browser Cache**
- Open DevTools (F12)
- Right-click refresh button → "Empty Cache and Hard Reload"

### 3. If Menu Item Exists But Clicking Does Nothing

**Check Browser Console:**
1. Open DevTools (F12)
2. Go to Console tab
3. Look for errors
4. Should see: "✅ PredictionsDashboard component loaded"

**Check Network Tab:**
1. Open DevTools (F12)
2. Go to Network tab
3. Click "Predictions" menu item
4. Check if `/api/predictions` request is made

### 4. Verify Files Exist

Check these files exist:
- ✅ `frontend/src/components/Predictions/PredictionsDashboard.jsx`
- ✅ `frontend/src/components/Predictions/PredictionsDashboard.css`
- ✅ Import in `frontend/src/App.jsx`
- ✅ Menu item in `frontend/src/components/Sidebar/Sidebar.jsx`

### 5. Quick Test

Open browser console and run:
```javascript
// Check if component is imported
console.log(window.React);

// Check if route exists
// Navigate to: http://localhost:3000
// Then click "Predictions" in sidebar
```

## 🔧 Quick Fixes

### Fix 1: Restart Everything
```bash
# Terminal 1: Backend
cd /mnt/c/Users/HP/Downloads/DataQuest1/DataQuest2026
./run_backend.sh

# Terminal 2: Frontend  
cd /mnt/c/Users/HP/Downloads/DataQuest1/DataQuest2026/frontend
npm run dev
```

### Fix 2: Verify Import
Check `frontend/src/App.jsx` line 9:
```javascript
import { PredictionsDashboard } from './components/Predictions/PredictionsDashboard';
```

### Fix 3: Check Sidebar
Check `frontend/src/components/Sidebar/Sidebar.jsx` line 20:
```javascript
{ id: 'predictions', label: 'Predictions', icon: Zap },
```

## 📍 Where to Look

1. **Sidebar Navigation** (left side of screen)
   - Should see: Dashboard, Events, Map, Query, **Predictions**, Settings
   - "Predictions" has a ⚡ icon

2. **After Clicking Predictions**
   - Main content area should show:
     - Title: "AI-Powered Disaster Predictions" with ⚡ icon
     - Refresh button
     - Either prediction cards OR "No predictions available" message

## 🐛 Common Issues

### Issue: Menu item not visible
**Cause:** Sidebar might be collapsed or scrolled
**Fix:** Click the sidebar toggle button, or scroll down in sidebar

### Issue: Component doesn't load
**Cause:** Import error or build issue
**Fix:** Restart dev server, check console for errors

### Issue: Blank screen
**Cause:** Component error or API not responding
**Fix:** Check browser console, verify backend is running

## ✅ Expected Behavior

When you click "Predictions" in the sidebar:
1. Main content area changes
2. Shows "AI-Powered Disaster Predictions" header
3. Shows either:
   - Prediction cards (if events exist)
   - "No predictions available" message (if no events)
4. Browser console shows: "✅ PredictionsDashboard component loaded"
5. WebSocket connection message appears in console
