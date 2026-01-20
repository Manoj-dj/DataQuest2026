# How to See Changes in Frontend

## 🔄 Restart Frontend Dev Server

The frontend dev server needs to be **restarted** to pick up new components and changes.

### Steps:

1. **Stop the current dev server:**
   - Find the terminal where `npm run dev` is running
   - Press `Ctrl + C` to stop it

2. **Restart the dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Wait for it to compile:**
   - You should see: "VITE v5.x.x ready in XXX ms"
   - Look for: "Local: http://localhost:3000"

4. **Refresh browser:**
   - Go to http://localhost:3000
   - Press `Ctrl + Shift + R` (hard refresh)

## ✅ What You Should See

After restarting, in the header (top right), you should see:
- ✅ **Connected** (green) - WebSocket status
- ✅ **⚡ Predictions** (gray) or **⚡ Predictions Active** (yellow) - NEW!
- ✅ **healthy** (green) - API status
- ✅ **X Events** - Active events count

## 🐛 If Still Not Working

1. **Check browser console (F12):**
   - Look for any red errors
   - Check if component is loading

2. **Clear browser cache completely:**
   - Chrome: Settings → Privacy → Clear browsing data → Cached images and files
   - Or use Incognito/Private window

3. **Verify files exist:**
   ```bash
   # Check Header file
   cat frontend/src/components/Header/Header.jsx | grep -i "predictions"
   
   # Should show the predictions code
   ```

4. **Check dev server output:**
   - Look for compilation errors
   - Check if Vite is watching files

## 📝 Quick Test

Open browser console (F12) and run:
```javascript
// Check if React is loaded
console.log(window.React);

// Check if component exists
// Navigate to the page and check Network tab for Header.jsx
```
