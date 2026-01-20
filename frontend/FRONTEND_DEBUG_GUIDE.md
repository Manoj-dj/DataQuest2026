# Frontend Debug & Fix Guide

## Problem Identified

You have **TWO different frontend apps** in the same directory:
1. **Old Vanilla JS app**: `frontend/index.html.old` (loads `app.js`)
2. **React/Vite app**: `frontend/index.html` (loads `/src/index.jsx`)

Vite was likely serving the wrong HTML file or the browser was caching the old one.

## Fixes Applied

### 1. ✅ Fixed Vite Configuration
- Updated `vite.config.js` with proper HMR settings
- Added error overlay for better debugging
- Ensured proper proxy configuration

### 2. ✅ Created Proper React Entry Point
- Created `frontend/index.html` that loads the React app
- Backed up old `index.html` to `index.html.old`

### 3. ✅ Added Debug Logs
- Added console logs in `index.jsx`, `App.jsx`, and `QueryPanel.jsx`
- Added visible debug indicator in QueryPanel: `[React v2.0.0-DEBUG]`

## How to Verify & Run

### Step 1: Stop Any Running Dev Server
```bash
# Press Ctrl+C in the terminal where dev server is running
```

### Step 2: Clear Browser Cache
**Option A: Hard Refresh**
- Chrome/Edge: `Ctrl + Shift + R` or `Ctrl + F5`
- Firefox: `Ctrl + Shift + R`
- Or open DevTools (F12) → Right-click refresh button → "Empty Cache and Hard Reload"

**Option B: Clear Cache Completely**
- Chrome: Settings → Privacy → Clear browsing data → Cached images and files
- Or use Incognito/Private window

### Step 3: Start Dev Server (from frontend directory)
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.0.11  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Step 4: Verify React App is Loading

1. **Open Browser Console** (F12)
2. **Look for these console logs:**
   ```
   📄 HTML file loaded at [timestamp]
   🚀 React entry point loaded at [timestamp]
   🚀 Root element: <div id="root"></div>
   ✅ React App loaded at [timestamp]
   ✅ App.jsx version: 2.0.0-DEBUG
   ✅ QueryPanel.jsx loaded at [timestamp]
   ```

3. **Check the UI:**
   - Navigate to "Query" in the sidebar
   - You should see `[React v2.0.0-DEBUG]` next to "Key Insight" heading
   - This confirms the React app is running

### Step 5: Test Hot Reload

1. Edit `frontend/src/components/Query/QueryPanel.jsx`
2. Change the debug text from `[React v2.0.0-DEBUG]` to `[React v2.0.1-TEST]`
3. Save the file
4. The browser should automatically update (HMR)
5. Check console for: `✅ QueryPanel.jsx loaded at [new timestamp]`

## Troubleshooting

### If you still see the old app:

1. **Check which HTML is being served:**
   - View page source (Ctrl+U)
   - Look for `<script src="app.js">` → This is the OLD app
   - Should see `<script type="module" src="/src/index.jsx">` → This is the React app

2. **Verify you're in the right directory:**
   ```bash
   cd frontend
   pwd  # Should show .../DataQuest2026/frontend
   npm run dev
   ```

3. **Check if port 3000 is already in use:**
   ```bash
   # Windows
   netstat -ano | findstr :3000
   
   # Kill the process if needed
   taskkill /PID <PID> /F
   ```

4. **Try a different port:**
   ```bash
   npm run dev -- --port 3001
   ```

### If HMR (Hot Module Reload) isn't working:

1. **Check Vite config:**
   - `vite.config.js` should have `hmr: { overlay: true }`

2. **Check browser console for errors:**
   - Look for WebSocket connection errors
   - HMR uses WebSocket, so proxy must be working

3. **Try manual refresh:**
   - If HMR fails, manually refresh (F5) after each change

### If you see "Cannot GET /" or blank page:

1. **Verify index.html exists:**
   ```bash
   ls frontend/index.html  # Should exist
   ```

2. **Check index.html content:**
   - Should have `<div id="root"></div>`
   - Should have `<script type="module" src="/src/index.jsx"></script>`

3. **Restart dev server:**
   ```bash
   # Stop server (Ctrl+C)
   # Start again
   npm run dev
   ```

## Files Changed

1. `frontend/vite.config.js` - Updated HMR and server config
2. `frontend/index.html` - Created React entry point (old one backed up)
3. `frontend/src/index.jsx` - Added debug logs
4. `frontend/src/App.jsx` - Added debug logs
5. `frontend/src/components/Query/QueryPanel.jsx` - Added debug logs and visible indicator

## Expected Behavior

✅ **Correct Setup:**
- Browser console shows React logs
- UI shows `[React v2.0.0-DEBUG]` in Query panel
- Changes to `.jsx` files trigger HMR automatically
- No errors in console

❌ **Wrong Setup:**
- Browser console shows "Map initialized" from old app.js
- No React logs
- Changes don't reflect
- Old vanilla JS UI visible

## Next Steps After Verification

Once you confirm the React app is loading:

1. **Remove debug logs** (optional):
   - Remove console.log statements
   - Remove `[React v2.0.0-DEBUG]` text from QueryPanel

2. **Test all features:**
   - Navigate through all sidebar items
   - Test Query panel
   - Test Predictions
   - Test new features (Alerts, Simulator, etc.)

3. **If everything works, you can delete:**
   - `frontend/index.html.old` (old vanilla JS app)
   - `frontend/app.js` and `frontend/app.jsx` (if not needed)
