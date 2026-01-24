import os
import time
import re
import requests
import subprocess
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
class ZoukScraper:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv("ZOUK_EMAIL")
        self.password = os.getenv("ZOUK_PASSWORD")
        
        self.output_dir = "bric_video_downloads"
        self.target_level = 1
        os.makedirs(self.output_dir, exist_ok=True)
        # Cookies and LocalStorage captured from browser session
        self.cookies = [
            {"name": "XSRF-TOKEN", "value": "1768505472|ZnissiXXvULb", "domain": ".brgalhardo.com", "path": "/"},
            {"name": "bSession", "value": "63a77e32-6975-4645-8c99-28eca38d3d57|1", "domain": ".brgalhardo.com", "path": "/"}
        ]
        self.local_storage_data = {
            "__wix.memberDetails": '{"memberId":"635c71e4-00b0-40e5-9f7c-09d903629084"}'
        }

    def sanitize_filename(self, name):
        """Sanitize string to be used as a filename."""
        return re.sub(r'[\\/*?:"<>|]', "", name).strip().replace(" ", "_")

    def download_with_ytdlp(self, url, filename):
        """Download video using yt-dlp."""
        print(f"Downloading {filename} via yt-dlp...")
        path = os.path.join(self.output_dir, filename)
        
        # yt-dlp command
        cmd = [
            "yt-dlp",
            url,
            "-o", path,
            "--no-part"  # Write directly to file
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Saved: {path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"yt-dlp failed for {filename}: {e}")
            return False

    def download_video(self, url, filename):
        """Deprecated: Download video content to a file."""
        return self.download_with_ytdlp(url, filename)

    def login_with_credentials(self, page):
        print("Falling back to credentials login...")
        if not self.email or not self.password:
            print("Error: ZOUK_EMAIL or ZOUK_PASSWORD not set in .env")
            return
        
        # Check if we are on the main page or already at a login modal
        # If "Sign In" is visible, click it.
        try:
            sign_in_btn = page.locator("button:has-text('Sign In')")
            if sign_in_btn.is_visible():
                print("Clicking 'Sign In'...")
                sign_in_btn.click()
                time.sleep(2) # Animation
        except:
            pass
        
        # Click "Log in with Email" if visible
        try:
             print("Looking for 'Log in with Email' option...")
             # Wait for the modal/option
             # Try text first
             email_choice = page.get_by_text("Log in with Email", exact=False)
             try:
                 email_choice.wait_for(state="visible", timeout=10000)
                 print("Found 'Log in with Email' via text, clicking...")
                 email_choice.click()
             except:
                 print("Text selector timed out, trying aria-label...")
                 email_btn = page.locator("button[aria-label='Log in with Email']")
                 if email_btn.count() > 0 and email_btn.is_visible():
                      email_btn.click()
                 else:
                      print("Could not find 'Log in with Email' button. Assuming we might be at input or already logged in?")
        except Exception as e:
            print(f"Error selecting email option: {e}")

        # Fill Credentials
        print("Filling credentials...")
        try:
            # Wait for email input
            email_input = page.locator("input[id^='input_input_emailInput']")
            email_input.wait_for(state="visible", timeout=15000)
            email_input.fill(self.email)
            
            pw_input = page.locator("input[id^='input_input_passwordInput']")
            pw_input.fill(self.password)
            
            # Submit
            print("Submitting...")
            login_btn = page.locator("button[aria-label='Log In']")
            # Verify if enabled
            if login_btn.is_visible():
                login_btn.click()
            else:
                # Fallback text
                page.get_by_text("Log In", exact=True).click()
            
            # Wait for login to complete
            print("Waiting for login completion...")
            page.wait_for_load_state('networkidle')
            time.sleep(5)
            # Check if login modal is gone
            if email_input.is_visible():
                print("Warning: Login modal still visible. Potentially failed login.")
                page.screenshot(path="debug_login_failed.png")
            else:
                print("Login successful (modal closed).")
                
        except Exception as e:
            print(f"Login failed or timed out: {e}")
            page.screenshot(path="debug_login_error.png")

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            
            # 1. Login with Credentials (Force fresh session)
            print("Starting login flow...")
            page = context.new_page()
            page.goto("https://en.brgalhardo.com/")
            try:
                self.login_with_credentials(page)
            except Exception as e:
                print(f"Login flow error: {e}")
            
            # 2. Navigate to Course List
            print("Navigating to Course List...")
            page.goto("https://en.brgalhardo.com/brickonline")
            page.wait_for_load_state('networkidle')
            time.sleep(3) 

            # CHECK LOGIN STATE (Just in case)
            if page.locator("button:has-text('Sign In')").is_visible() or "Log In" in page.title():
                print("Still seeing login cues after login flow. Retrying...")
                self.login_with_credentials(page)
                page.goto("https://en.brgalhardo.com/brickonline")
                page.wait_for_load_state('networkidle')
            
            # 3. Enter Level Course
            print(f"Entering 'BRICK IMPROVEMENT COURSE - LEVEL {self.target_level}'...")
            
            # Use get_by_text with exact=False for partial match/whitespace tolerance
            course_link = page.get_by_text(f"BRICK IMPROVEMENT COURSE - LEVEL {self.target_level}", exact=False)
            
            try:
                course_link.wait_for(state="visible", timeout=10000)
                course_link.scroll_into_view_if_needed()
                print("Found course link, clicking...")
                course_link.click()
                page.wait_for_load_state('networkidle')
            except Exception as e:
                print(f"Failed to click course link: {e}")
                print(f"Current Title: {page.title()}")
                page.screenshot(path="debug_course_list.png")
                # Attempt fallback: direct URL if known?
                print("Attempting direct navigation...")
                try:
                    page.goto("https://en.brgalhardo.com/participant-page/89ffd0ce-8274-49fb-a298-446f4fb9f0c4?programId=89ffd0ce-8274-49fb-a298-446f4fb9f0c4&participantId=27804ab5-6e00-4cdb-9abf-801266ddc731", timeout=60000)
                    page.wait_for_load_state('domcontentloaded') 
                    time.sleep(5)
                    
                    # Check login again after direct nav
                    if "Log In" in page.title() or page.locator("button[aria-label='Log In']").count() > 0:
                         print("Redirected to login on direct link. Attempting login...")
                         self.login_with_credentials(page)
                         page.wait_for_load_state('domcontentloaded')
                         time.sleep(5)

                except Exception as ex:
                    print(f"Navigation warning: {ex}")
                
                time.sleep(5) # Allow render
                page.screenshot(path="debug_level1_page.png")
            
            # 4. Handle Popups (e.g. Completion / Welcome)
            print("Checking for popups...")
            time.sleep(3) # Wait for animations
            # Try to close any overlay if present. Subagent saw an "X" button.
            # Generic approach: look for common close buttons or just click outside?
            # Or assume we can interact with sidebar anyway.
            # Let's try to click a close button if visible.
            try:
                close_btn = page.locator("button[aria-label='Close'], button.wixui-lightbox__close-button, svg[data-bbox='...']") 
                # Better: get by role?
                if close_btn.count() > 0:
                     for i in range(close_btn.count()):
                         if close_btn.nth(i).is_visible():
                             print("Closing popup...")
                             close_btn.nth(i).click()
                             time.sleep(1)
            except:
                pass

            # 5. Expand Accordions
            print("Expanding accordions...")
            # Use reliable ID selector for headers
            accordions = page.locator("button[id^='accordion-section-']")
            try:
                # Wait for at least one accordion to be present
                accordions.first.wait_for(timeout=10000)
            except:
                print("No accordions found via ID selector.")
                # fallback debug
                print("Dumping all buttons on page for debug:")
                buttons = page.locator("button")
                for i in range(min(20, buttons.count())):
                    print(f"Btn {i}: {buttons.nth(i).inner_text()} | Class: {buttons.nth(i).get_attribute('class')}")
                
                with open("debug_dump.html", "w") as f:
                    f.write(page.content())
                print("Saved debug_dump.html")

            count_acc = accordions.count()
            print(f"Found {count_acc} accordions.")
            
            for i in range(count_acc):
                try:
                    acc = accordions.nth(i)
                    # Check if expanded using aria-expanded if available, or just click?
                    # Wix usually toggles. Let's check aria-expanded.
                    is_expanded = acc.get_attribute("aria-expanded")
                    if is_expanded == "false":
                        print(f"Expanding accordion {i+1}...")
                        acc.click()
                        time.sleep(1) # Wait for animation
                except Exception as e:
                    print(f"Error expanding accordion {i}: {e}")

            # 6. Extract Lessons
            print("Extracting lessons...")
            
            # Setup network capture
            captured_urls = []
            def handle_response(response):
                url = response.url
                # Look for typical video extensions or media playlists
                if ".m3u8" in url or ".mp4" in url:
                    captured_urls.append(url)

            page.on("response", handle_response)

            # Selector for sidebar items from subagent: button.s__2SBGhr
            # Ensure sidebar is loaded
            try:
                page.wait_for_selector("button.s__2SBGhr", timeout=10000)
            except:
                print("Warning: Lesson buttons selector timed out. Maybe no lessons or wrong selector.")

            lesson_buttons = page.locator("button.s__2SBGhr")
            count = lesson_buttons.count()
            print(f"Found {count} lessons.")
            
            for i in range(count):
                try:
                    # Clear previous captures
                    captured_urls.clear()
                    
                    # Re-locate to avoid stale reference
                    btn = page.locator("button.s__2SBGhr").nth(i)
                    lesson_title = btn.inner_text().split("\n")[0] # Sometimes has duration text
                    print(f"Processing ({i+1}/{count}): {lesson_title}")
                    
                    # Click lesson
                    btn.click(force=True)
                    time.sleep(5) # Wait for content and network requests
                    
                    # Check for video URL in captured requests
                    video_url = None
                    # Prioritize m3u8 master playlists, then mp4
                    for url in captured_urls:
                        if ".m3u8" in url and "master" in url:
                            video_url = url
                            break
                    if not video_url:
                        # Fallback to any m3u8
                        for url in captured_urls:
                            if ".m3u8" in url:
                                video_url = url
                                break
                    if not video_url:
                        # Fallback to mp4
                        for url in captured_urls:
                            if ".mp4" in url:
                                video_url = url
                                break
                                
                    if video_url:
                        filename = f"Level_{self.target_level}_{i+1:02d}_{self.sanitize_filename(lesson_title)}.mp4"
                        
                        # Skip if already downloaded
                        if os.path.exists(os.path.join(self.output_dir, filename)):
                            print("  Skipping (already exists).")
                            continue
                        
                        self.download_with_ytdlp(video_url, filename)
                    else:
                        print("  No video URL intercepted for this lesson.")
                        
                except Exception as e:
                    print(f"Error processing lesson {i}: {e}")
            
            # Cleanup
            page.remove_listener("response", handle_response)
            browser.close()

if __name__ == "__main__":
    scraper = ZoukScraper()
    scraper.run()
