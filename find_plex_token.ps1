# Plex Token Finder Script
# Searches for Plex Preferences.xml and extracts the authentication token

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Plex Token Finder" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Common Plex installation paths on Windows
$possiblePaths = @(
    "$env:LOCALAPPDATA\Plex Media Server\Preferences.xml",
    "$env:APPDATA\Plex Media Server\Preferences.xml",
    "$env:ProgramData\Plex Media Server\Preferences.xml",
    "C:\ProgramData\Plex Media Server\Preferences.xml",
    "$env:USERPROFILE\AppData\Local\Plex Media Server\Preferences.xml",
    "$env:USERPROFILE\AppData\Roaming\Plex Media Server\Preferences.xml"
)

Write-Host "Searching for Plex Preferences.xml in common locations...`n" -ForegroundColor Yellow

$foundPath = $null

foreach ($path in $possiblePaths) {
    Write-Host "Checking: $path" -ForegroundColor Gray
    if (Test-Path $path) {
        Write-Host "  [FOUND]" -ForegroundColor Green
        $foundPath = $path
        break
    } else {
        Write-Host "  [NOT FOUND]" -ForegroundColor DarkGray
    }
}

if ($foundPath) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Found Preferences.xml" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Location: $foundPath`n" -ForegroundColor White

    try {
        $content = Get-Content $foundPath -Raw

        # Extract PlexOnlineToken
        if ($content -match 'PlexOnlineToken="([^"]+)"') {
            $token = $matches[1]
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "PLEX TOKEN FOUND:" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host $token -ForegroundColor Yellow
            Write-Host "`n========================================" -ForegroundColor Green
            Write-Host "`nNEXT STEPS:" -ForegroundColor Cyan
            Write-Host "1. Copy the token above (the yellow text)"
            Write-Host "2. Open the Plex Poster Manager launcher"
            Write-Host "3. Paste the token in the 'Plex Token' field"
            Write-Host "4. Click 'Test Token' to verify"
            Write-Host "5. Click 'Save Configuration' to save"
            Write-Host "`n========================================" -ForegroundColor Cyan

            # Copy to clipboard if possible
            try {
                Set-Clipboard -Value $token
                Write-Host "`n[BONUS] Token copied to clipboard! Just paste it." -ForegroundColor Green
            } catch {
                Write-Host "`n[INFO] Could not auto-copy to clipboard. Please copy manually." -ForegroundColor Yellow
            }
        } else {
            Write-Host "ERROR: Could not find PlexOnlineToken in the file." -ForegroundColor Red
            Write-Host "The file exists but may not contain a token." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "ERROR: Could not read the file: $_" -ForegroundColor Red
    }
} else {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host "ERROR: Preferences.xml not found" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "`nThe Plex Preferences file was not found in any standard location." -ForegroundColor Yellow
    Write-Host "`nPossible reasons:" -ForegroundColor Cyan
    Write-Host "1. Plex Media Server is not installed on this machine"
    Write-Host "2. Plex is installed in a custom/non-standard location"
    Write-Host "3. You're running this on the wrong computer"
    Write-Host "`nALTERNATIVE METHOD:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Get token from Plex Web App:" -ForegroundColor Yellow
    Write-Host "1. Open your browser and go to: http://192.168.5.141:32400/web"
    Write-Host "2. Log in to Plex"
    Write-Host "3. Press F12 to open Developer Tools"
    Write-Host "4. Go to the 'Console' tab"
    Write-Host "5. Type this command and press Enter:"
    Write-Host "   localStorage.getItem('myPlexAccessToken')" -ForegroundColor Cyan
    Write-Host "6. Copy the token (without quotes)"
    Write-Host "`nOR use the HTML helper:" -ForegroundColor Yellow
    Write-Host "1. Open: get_plex_token.html (in the project folder)"
    Write-Host "2. Follow the instructions on the page"
    Write-Host "`n========================================" -ForegroundColor Green

    # Try to find Plex installation directory
    Write-Host "`nSearching for Plex installation directory..." -ForegroundColor Yellow
    $plexExe = Get-Process -Name "Plex Media Server" -ErrorAction SilentlyContinue
    if ($plexExe) {
        $plexPath = $plexExe.Path
        Write-Host "Plex is running from: $plexPath" -ForegroundColor Green

        # Try to find data directory based on process
        Write-Host "`nYou can try manually searching for Preferences.xml near this location." -ForegroundColor Yellow
    } else {
        Write-Host "Plex Media Server process is not currently running." -ForegroundColor Red
        Write-Host "Start Plex and run this script again." -ForegroundColor Yellow
    }
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
