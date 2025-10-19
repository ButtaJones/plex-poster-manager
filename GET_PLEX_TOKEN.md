# How to Get Your Plex Authentication Token

## The Problem
Your Plex token `4RCeUWbo65-5Ezz6myzE` is **expired or invalid**, which is why posters aren't loading. You're getting `401 Unauthorized` errors from the Plex server.

## Solution: Get a Fresh Token

We've created 3 methods to help you retrieve a valid Plex token. Choose the one that works best for you:

---

## 📋 METHOD 1: PowerShell Script (Recommended for Windows)

**This is the easiest method if you're on the Windows machine running Plex.**

1. Open PowerShell on your Windows machine (192.168.5.141)
2. Navigate to the project folder:
   ```powershell
   cd C:\path\to\plex-poster-manager
   ```
3. Run the token finder script:
   ```powershell
   .\find_plex_token.ps1
   ```
4. The script will:
   - Search for Plex Preferences.xml in all common locations
   - Extract the token automatically
   - Copy it to your clipboard
   - Show you next steps

5. If found, the token will be displayed in yellow. Copy it!

---

## 🌐 METHOD 2: Browser HTML Helper

**Use this if you prefer a graphical interface.**

1. On your Windows machine, open the file:
   ```
   get_plex_token.html
   ```
   (Double-click it to open in your browser)

2. Click **"Open Plex Web App"** button to open Plex in a new tab

3. Log in to Plex if you're not already logged in

4. Go back to the `get_plex_token.html` tab

5. Click **"Get My Plex Token"** button

6. If it works, the token will be displayed. Click **"Copy Token"**

7. If it doesn't work due to browser security, follow the **Alternative Method** shown on the page

---

## 💻 METHOD 3: Browser Console (Manual)

**This is the most reliable method and works on any browser.**

### Steps:

1. **Open Plex Web App**
   - Go to: `http://192.168.5.141:32400/web`
   - Log in if prompted

2. **Open Developer Tools**
   - Press `F12` on your keyboard
   - OR right-click anywhere → "Inspect" → "Console" tab

3. **Run this command in the Console**
   ```javascript
   localStorage.getItem('myPlexAccessToken')
   ```

4. **Copy the token**
   - The token will be displayed (it looks like: `"aBcDeFgHiJkLmNoPqRsTuVwXyZ12"`)
   - Copy the token **without the quotes**

5. **Paste into Launcher**
   - Open the Plex Poster Manager launcher
   - Paste the token in the "Plex Token" field
   - Click **"Test Token"** to verify it works
   - Click **"Save Configuration"**

---

## ✅ Verify It's Working

After updating the token:

1. The launcher should show: **"Token valid for user: [your username]"**
2. Libraries should load when you click "Refresh Libraries"
3. Posters should now appear in the scan results

---

## 🆘 Still Having Issues?

If none of these methods work:

### Check if Plex is Running
- Make sure Plex Media Server is running on 192.168.5.141
- Verify you can access: `http://192.168.5.141:32400/web`

### Check Your Network
- Make sure you can reach the Plex server from your browser
- Try: `http://192.168.5.141:32400/identity` (should return XML)

### Token Expiration
- Plex tokens can expire if:
  - You changed your Plex password
  - You logged out of all devices
  - Your Plex account had security changes

### Get a New Token from Plex.tv
1. Go to: https://www.plex.tv/claim/
2. Log in with your Plex account
3. You'll see a claim code (this is NOT your token)
4. Instead, use Method 3 above after logging in

---

## 📝 Technical Details

- **Current Token**: `4RCeUWbo65-5Ezz6myzE` (EXPIRED/INVALID)
- **Error**: `401 Unauthorized` when fetching thumbnails
- **Plex Server**: v1.42.1.10060 running on 192.168.5.141:32400
- **Machine ID**: cabc36aa860acb0de02120ab3de3d98788b6451f

The token is used to authenticate all API requests to your Plex server, including fetching artwork thumbnails.

---

## 🎯 Quick Summary

**Problem**: Expired Plex token → 401 errors → Missing posters

**Solution**: Get fresh token using one of the 3 methods above → Update in launcher → Posters work!

**Time Required**: 2-5 minutes

---

Good luck! Once you get the token, the posters should load immediately. 🎬
