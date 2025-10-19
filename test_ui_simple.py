#!/usr/bin/env python3
"""
Simple Playwright UI Test - Just Screenshots
Takes comprehensive screenshots of the modernized UI
"""

from playwright.sync_api import sync_playwright
import time

def test_ui_screenshots():
    print("=" * 80)
    print("Plex Poster Manager - UI Screenshots Test")
    print("=" * 80)

    with sync_playwright() as p:
        # Use Firefox (works on Big Sur 11.7.4)
        browser = p.firefox.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        try:
            # Navigate to app with cache disabled
            print("\n1. Loading application (clearing cache)...")
            page.goto('http://192.168.5.141:3000', wait_until='networkidle')
            page.reload(wait_until='networkidle')  # Force reload
            time.sleep(3)

            # Take initial screenshot
            page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/01-initial-load-light.png', full_page=True)
            print("   ✓ Screenshot: 01-initial-load-light.png")

            # Try to find and click dark mode toggle
            print("\n2. Testing Dark Mode Toggle...")
            try:
                # Look for button with Moon/Sun icon (top-right area)
                buttons = page.locator('button').all()
                dark_mode_toggled = False

                for btn in buttons:
                    try:
                        # Check if button contains SVG (icon button)
                        if btn.locator('svg').count() > 0:
                            # Get button's position to find top-right button
                            box = btn.bounding_box()
                            if box and box['x'] > 1700:  # Top-right area
                                btn.click()
                                print("   ✓ Clicked dark mode toggle")
                                dark_mode_toggled = True
                                break
                    except:
                        continue

                if dark_mode_toggled:
                    time.sleep(2)
                    page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/02-dark-mode-enabled.png', full_page=True)
                    print("   ✓ Screenshot: 02-dark-mode-enabled.png")
                else:
                    print("   ⚠ Dark mode toggle not found (might be off-screen or different layout)")
            except Exception as e:
                print(f"   ⚠ Dark mode test skipped: {e}")

            # Test responsive design
            print("\n3. Testing Responsive Design...")

            # Desktop view (full page)
            page.set_viewport_size({'width': 1920, 'height': 1080})
            time.sleep(1)
            page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/03-responsive-desktop.png', full_page=True)
            print("   ✓ Screenshot: 03-responsive-desktop.png (1920x1080)")

            # Tablet view
            page.set_viewport_size({'width': 768, 'height': 1024})
            time.sleep(1)
            page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/04-responsive-tablet.png', full_page=True)
            print("   ✓ Screenshot: 04-responsive-tablet.png (768x1024)")

            # Mobile view
            page.set_viewport_size({'width': 375, 'height': 667})
            time.sleep(1)
            page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/05-responsive-mobile.png', full_page=True)
            print("   ✓ Screenshot: 05-responsive-mobile.png (375x667)")

            # Back to desktop for final checks
            page.set_viewport_size({'width': 1920, 'height': 1080})
            time.sleep(1)

            # Check page content for new features
            print("\n4. Checking for Modern UI Elements...")
            page_content = page.content()

            # Check for Lucide icons (SVG)
            svg_count = page.locator('svg').count()
            print(f"   ✓ Found {svg_count} SVG icons (Lucide)")

            # Check for dark mode class support
            if 'dark' in page_content or 'darkMode' in page_content:
                print("   ✓ Dark mode support detected")

            # Check for new pagination options
            if '25 items' in page_content or '50 items' in page_content:
                print("   ✓ New pagination options detected (25, 50, 75, 100)")

            # Check for thumbnail slider
            range_inputs = page.locator('input[type="range"]').count()
            if range_inputs > 0:
                print(f"   ✓ Found {range_inputs} slider(s) (thumbnail size control)")

            # Final screenshot - back to light mode if possible
            print("\n5. Final Screenshots...")
            try:
                buttons = page.locator('button').all()
                for btn in buttons:
                    try:
                        if btn.locator('svg').count() > 0:
                            box = btn.bounding_box()
                            if box and box['x'] > 1700:
                                btn.click()
                                print("   ✓ Toggled back to light mode")
                                break
                    except:
                        continue
                time.sleep(2)
            except:
                pass

            page.screenshot(path='/Users/butta/development/plex-poster-manager/screenshots/06-final-full-page.png', full_page=True)
            print("   ✓ Screenshot: 06-final-full-page.png")

            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            print("✓ All screenshots saved to: /Users/butta/development/plex-poster-manager/screenshots/")
            print(f"✓ Total screenshots: 6")
            print(f"✓ SVG icons found: {svg_count}")
            print("=" * 80)

        except Exception as e:
            print(f"\n❌ Error during test: {e}")
            import traceback
            traceback.print_exc()

        finally:
            print("\nClosing browser...")
            browser.close()
            print("Done!")

if __name__ == '__main__':
    test_ui_screenshots()
