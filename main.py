#!/usr/bin/env python3

import time
import datetime
import random
import pytz
import os
import sys
import re
import logging
import smtplib
import ssl
from email.message import EmailMessage

# Selenium imports
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration for your Firefox Profile ---
# IMPORTANT: You need to find your Firefox profile path on your Linux system.
profile_path = "/home/kali/.mozilla/firefox/yh9x5vth.talha" # <<<--- REPLACE THIS IF NEEDED

# --- Video Files Configuration ---
# Path to the directory containing your video files on the Desktop.
video_folder_path = "/home/kali/Desktop/video"
# Path for the log file to keep track of uploaded video filenames
uploaded_log_file = "uploaded_videos.log"
# Path for the log file to keep track of the channel video number for titles
channel_counter_file = "channel_video_counter.txt"
# Path for the main automation log file
automation_log_file = "youtube_automation.log"
# Path for the daily upload counter log file
daily_upload_counter_file = "daily_upload_counter.log"
# Path to the file containing video titles
titles_file_path = "titles.txt" # Assumes titles.txt is in the same directory as the script

# --- Scheduler Configuration ---
PAKISTAN_TIMEZONE = 'Asia/Karachi'
UPLOAD_TIMES_PER_DAY = 5 # Maximum videos to upload per day
RETRY_DELAY_SECONDS = 300 # 5 minutes delay before retrying a failed upload

# --- Email Configuration ---
SENDER_EMAIL = "talha.developer.01@gmail.com" # <<<--- REPLACE THIS
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") # <<<--- REPLACE THIS (or regular password if no 2FA)
RECEIVER_EMAIL = "flutterdeveloper246@gmail.com" # <<<--- REPLACE THIS (can be same as sender)
EMAIL_SUBJECT_SUCCESS = "YouTube Short Upload Success!"
EMAIL_SUBJECT_FAILURE = "YouTube Short Upload Failed!"
EMAIL_SUBJECT_DAILY_LIMIT = "YouTube Short Daily Upload Limit Reached"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(automation_log_file), # Log to file
        logging.StreamHandler(sys.stdout) # Log to console
    ]
)

# --- Helper Functions ---

def send_email_notification(subject, body):
    """Sends an email notification."""
    em = EmailMessage()
    em['From'] = SENDER_EMAIL
    em['To'] = RECEIVER_EMAIL
    em['Subject'] = subject
    em.set_content(body)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(em)
        logging.info(f"Email notification sent successfully to {RECEIVER_EMAIL}.")
    except Exception as e:
        logging.error(f"Failed to send email notification: {e}")
        logging.error("Please check your email configuration (sender email, password, recipient, SMTP server/port).")


def open_firefox_with_profile(profile_path):
    """
    Opens Firefox with a specified user profile.

    Args:
        profile_path (str): The full path to the Firefox profile directory.

    Returns:
        webdriver.Firefox: The WebDriver instance if successful, None otherwise.
    """
    try:
        firefox_options = Options()
        firefox_options.add_argument(f"-profile")
        firefox_options.add_argument(os.path.expanduser(profile_path))
        # --- CHANGE MADE HERE: UNCOMMENTED FOR HEADLESS MODE ---
        firefox_options.add_argument("--headless") 
        # --- END CHANGE ---

        service_obj = Service() # Assumes GeckoDriver is in PATH or auto-detected
        driver = webdriver.Firefox(service=service_obj, options=firefox_options)

        logging.info(f"Successfully opened Firefox with profile: '{profile_path}' (Headless Mode: Enabled)")
        time.sleep(3) # Wait for 3 seconds

        return driver

    except Exception as e:
        logging.error(f"An error occurred during browser setup: {e}")
        logging.error("Please ensure:")
        logging.error(f"1. GeckoDriver is installed and accessible in your system's PATH, or its path is correctly specified.")
        logging.error(f"2. The 'profile_path' ('{profile_path}') is correct.")
        logging.error("   You can find your Firefox profile path by typing 'about:profiles' in your Firefox browser's address bar.")
        logging.error("\nIMPORTANT: If you're encountering a verification step, please open this Firefox profile manually once,")
        logging.error("complete any verification, and then close it. This often resolves the issue for future automated runs.")
        return None

def get_uploaded_videos(log_file):
    """Reads the log file and returns a set of uploaded video filenames."""
    uploaded = set()
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            for line in f:
                uploaded.add(line.strip())
    return uploaded

def add_to_uploaded_log(log_file, filename):
    """Appends a filename to the uploaded videos log file."""
    with open(log_file, 'a') as f:
        f.write(filename + '\n')

def get_next_channel_video_number(counter_file):
    """
    Reads the next channel video number from the counter file.
    Initializes to 16 if the file doesn't exist or contains invalid data.
    """
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
        except Exception as e:
            logging.warning(f"Could not read channel counter file. Starting from default. Error: {e}")
    return 16 # Default starting number for the channel video title

def update_channel_video_number(counter_file, next_number):
    """Writes the next channel video number to the counter file."""
    try:
        with open(counter_file, 'w') as f:
            f.write(str(next_number))
    except Exception as e:
        logging.error(f"Could not update channel counter file. Error: {e}")

def get_daily_upload_count(daily_log_file):
    """Reads the daily upload count for the current day."""
    today = get_pakistan_time().strftime('%Y-%m-%d')
    if os.path.exists(daily_log_file):
        with open(daily_log_file, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2 and parts[0] == today:
                    try:
                        return int(parts[1])
                    except ValueError:
                        logging.warning(f"Invalid count in daily log for {today}. Resetting count to 0.")
                        return 0
    return 0

def increment_daily_upload_count(daily_log_file):
    """Increments the daily upload count for the current day."""
    today = get_pakistan_time().strftime('%Y-%m-%d')
    current_count = get_daily_upload_count(daily_log_file)
    new_count = current_count + 1

    lines = []
    if os.path.exists(daily_log_file):
        with open(daily_log_file, 'r') as f:
            lines = f.readlines()

    found = False
    with open(daily_log_file, 'w') as f:
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) == 2 and parts[0] == today:
                f.write(f"{today},{new_count}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"{today},{new_count}\n")
    logging.info(f"Daily upload count for {today} updated to {new_count}.")

def get_titles_from_file(file_path):
    """Reads titles from a text file, one title per line."""
    titles = []
    if not os.path.exists(file_path):
        logging.error(f"Titles file not found: {file_path}")
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line:
                    titles.append(stripped_line)
        if not titles:
            logging.warning(f"Titles file '{file_path}' is empty or contains no valid titles.")
        return titles
    except Exception as e:
        logging.error(f"Error reading titles from '{file_path}': {e}")
        return []


def upload_youtube_short(profile_path, video_folder_path, uploaded_log_file, channel_counter_file, titles_file_path, video_to_upload_name_param=None):
    """
    Automates the process of opening Firefox, navigating to YouTube Studio,
    uploading a video, updating its title, and clicking through initial steps.
    Returns True on successful upload process completion, False otherwise.
    If video_to_upload_name_param is provided, it attempts to upload that specific video.
    """
    driver = None
    video_to_upload_name = video_to_upload_name_param
    current_channel_video_number = None
    final_video_title = "N/A"

    try:
        driver = open_firefox_with_profile(profile_path)
        if not driver:
            logging.error("Failed to open Firefox profile. Aborting upload.")
            return False

        driver.get("https://studio.youtube.com/channel/UC3cMUITF1p9eu9GXvWbzesg")
        logging.info("Navigated to YouTube Studio. You should see your specific profile logged in.")

        uploaded_videos = get_uploaded_videos(uploaded_log_file)
        logging.info(f"Already uploaded video filenames (from log): {uploaded_videos}")

        current_channel_video_number = get_next_channel_video_number(channel_counter_file)
        logging.info(f"Next channel video number for title: {current_channel_video_number}")

        if video_to_upload_name_param is None:
            all_video_files = []
            for f in os.listdir(video_folder_path):
                if f.endswith(('.mp4', '.mov', '.avi', '.webm')):
                    match = re.match(r'(\d+)\.(mp4|mov|avi|webm)', f, re.IGNORECASE)
                    if match:
                        all_video_files.append((int(match.group(1)), f))

            all_video_files.sort(key=lambda x: x[0])
            logging.info(f"All detected video files (sorted): {[f[1] for f in all_video_files]}")

            for video_num, video_name in all_video_files:
                if video_num >= 4 and video_name not in uploaded_videos:
                    video_to_upload_name = video_name
                    break
        
        if not video_to_upload_name:
            logging.info("No new video files found to upload (or all eligible files have been uploaded).")
            return True 

        video_to_upload_path = os.path.join(video_folder_path, video_to_upload_name)
        logging.info(f"Next video file to upload: {video_to_upload_path}")

        titles_list = get_titles_from_file(titles_file_path)
        if titles_list:
            title_index = (current_channel_video_number - 42) % len(titles_list)
            base_title = titles_list[title_index]
            final_video_title = f"{base_title} | #Shorts {current_channel_video_number}"
            logging.info(f"Selected base title from file: '{base_title}'")
        else:
            logging.warning("No valid titles found in titles.txt. Using a fallback default title.")
            final_video_title = f"Default Short Title | #Shorts {current_channel_video_number}"
        
        logging.info(f"Constructed video title: '{final_video_title}'")

        logging.info("Attempting to click the upload icon...")
        upload_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="upload-icon"]'))
        )
        upload_icon.click()
        logging.info("Successfully clicked the upload icon.")
        time.sleep(3)

        logging.info(f"Attempting to upload video file: {video_to_upload_path}")
        file_input_xpath = '//input[@type="file"]'

        file_input_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, file_input_xpath))
        )
        file_input_element.send_keys(os.path.abspath(video_to_upload_path))
        logging.info("Successfully sent video file path to the upload input. Upload should now be in progress.")
        time.sleep(10)

        logging.info(f"Attempting to update video title...")
        title_textbox_xpath = '//*[@id="textbox"]'
        title_element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, title_textbox_xpath))
        )
        title_element.clear()
        title_element.send_keys(final_video_title)
        logging.info(f"Successfully updated title to: '{final_video_title}'")
        time.sleep(2)

        next_button_xpath = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]/ytcp-button-shape/button"
        for i in range(3):
            logging.info(f"Attempting to click 'Next' button (attempt {i+1}/3)...")
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, next_button_xpath))
            )
            next_button.click()
            logging.info(f"Successfully clicked 'Next' button (attempt {i+1}/3).")
            time.sleep(2)

        final_button_xpath = "/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[3]/ytcp-button-shape/button"
        logging.info(f"Attempting to click the final button with XPath: {final_button_xpath}...")
        final_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, final_button_xpath))
        )
        final_button.click()
        logging.info("Successfully clicked the final button.")
        time.sleep(5)

        add_to_uploaded_log(uploaded_log_file, video_to_upload_name)
        logging.info(f"Logged '{video_to_upload_name}' as successfully processed.")

        update_channel_video_number(channel_counter_file, current_channel_video_number + 1)
        logging.info(f"Updated channel video counter to: {current_channel_video_number + 1}")
        
        increment_daily_upload_count(daily_upload_counter_file)

        email_body = (
            f"YouTube Short Upload Details:\n\n"
            f"File Name: {video_to_upload_name}\n"
            f"Channel Video Number: {current_channel_video_number}\n"
            f"Video Title: {final_video_title}\n"
            f"Status: Script-side upload process completed (monitor YouTube Studio for final status)\n"
            f"Timestamp (PKT): {get_pakistan_time().strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
        )
        send_email_notification(EMAIL_SUBJECT_SUCCESS, email_body)

        return True

    except Exception as e:
        error_message = f"An error occurred during YouTube upload process for video '{video_to_upload_name or 'N/A'}' (Channel # {current_channel_video_number or 'N/A'} - Title: '{final_video_title}'): {e}"
        logging.error(error_message)
        email_body = (
            f"YouTube Short Upload FAILED!\n\n"
            f"File Name Attempted: {video_to_upload_name or 'N/A'}\n"
            f"Channel Video Number Attempted: {current_channel_video_number or 'N/A'}\n"
            f"Video Title Attempted: {final_video_title}\n"
            f"Error: {e}\n"
            f"Timestamp (PKT): {get_pakistan_time().strftime('%Y-%m-%d %H:%M:%S %Z%z')}\n\n"
            f"This video will be retried in the next retry attempt for this slot."
        )
        send_email_notification(EMAIL_SUBJECT_FAILURE, email_body)
        return False

    finally:
        if driver:
            driver.quit()

# --- Scheduler Logic ---

def get_pakistan_time():
    """Returns the current datetime object in Pakistan Standard Time."""
    tz = pytz.timezone(PAKISTAN_TIMEZONE)
    return datetime.datetime.now(tz)

def generate_random_upload_times(start_time, end_time, num_times):
    """
    Generates a list of unique random datetime objects within a given time range.
    """
    if start_time >= end_time:
        logging.warning("Start time is not before end time. No random times generated.")
        return []

    time_diff_seconds = int((end_time - start_time).total_seconds())
    if time_diff_seconds <= 0:
        logging.warning("Time window is too small or invalid. No random times generated.")
        return []

    random_seconds = set()
    max_possible_times = min(num_times, time_diff_seconds)
    while len(random_seconds) < max_possible_times:
        random_seconds.add(random.randint(0, time_diff_seconds))

    upload_times = []
    for sec in random_seconds:
        upload_times.append(start_time + datetime.timedelta(seconds=sec))

    upload_times.sort()
    return upload_times

def can_upload_today(daily_log_file, limit):
    """Checks if the daily upload limit has been reached for the current day."""
    current_count = get_daily_upload_count(daily_log_file)
    if current_count >= limit:
        logging.info(f"Daily upload limit of {limit} reached for today ({get_pakistan_time().strftime('%Y-%m-%d')}).")
        return False
    return True

def schedule_daily_uploads():
    """
    Schedules and executes YouTube Shorts uploads daily, respecting a daily limit
    and retrying the same video until script-level success.
    """
    logging.info("Starting YouTube Shorts daily scheduler...")

    if not can_upload_today(daily_upload_counter_file, UPLOAD_TIMES_PER_DAY):
        email_body = (
            f"The daily upload limit ({UPLOAD_TIMES_PER_DAY}) for YouTube Shorts has been reached for today "
            f"({get_pakistan_time().strftime('%Y-%m-%d %Z%z')}). "
            f"No further uploads will be attempted today."
        )
        send_email_notification(EMAIL_SUBJECT_DAILY_LIMIT, email_body)
        logging.info("Daily upload limit reached. Script will exit for today.")
        return

    now_pkt = get_pakistan_time()
    end_of_day_pkt = now_pkt.replace(hour=20, minute=0, second=0, microsecond=0)

    if now_pkt >= end_of_day_pkt:
        logging.info("Current time is past 8 PM PKT. Scheduling uploads for tomorrow.")
        start_time_for_scheduling = now_pkt.replace(hour=8, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
        end_time_for_scheduling = end_of_day_pkt + datetime.timedelta(days=1)
    else:
        logging.info(f"Scheduling uploads from now ({now_pkt.strftime('%H:%M:%S')}) until 8 PM PKT today.")
        start_time_for_scheduling = now_pkt
        end_time_for_scheduling = end_of_day_pkt

    remaining_slots = UPLOAD_TIMES_PER_DAY - get_daily_upload_count(daily_upload_counter_file)
    if remaining_slots <= 0:
        logging.info("No remaining upload slots for today. Exiting scheduler.")
        return 

    scheduled_times = generate_random_upload_times(start_time_for_scheduling, end_time_for_scheduling, remaining_slots)

    if not scheduled_times:
        logging.warning("Could not generate valid upload times. Exiting scheduler for today.")
        return

    logging.info(f"Generated {len(scheduled_times)} upload times for today (PKT):")
    for s_time in scheduled_times:
        logging.info(f"- {s_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")

    uploaded_videos = get_uploaded_videos(uploaded_log_file)
    all_video_files = []
    for f in os.listdir(video_folder_path):
        if f.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
            match = re.match(r'(\d+)\.(mp4|mov|avi|webm)', f, re.IGNORECASE)
            if match:
                all_video_files.append((int(match.group(1)), f))
    all_video_files.sort(key=lambda x: x[0])

    video_to_upload_for_this_schedule = None
    for video_num, video_name in all_video_files:
        if video_num >= 4 and video_name not in uploaded_videos:
            video_to_upload_for_this_schedule = video_name
            break
    
    if not video_to_upload_for_this_schedule:
        logging.info("No new video files found to upload (or all eligible files have been uploaded). Scheduler finished.")
        return


    for i, scheduled_time in enumerate(scheduled_times):
        if not can_upload_today(daily_upload_counter_file, UPLOAD_TIMES_PER_DAY):
            logging.info("Daily upload limit reached during scheduling. Stopping further uploads for today.")
            email_body = (
                f"The daily upload limit ({UPLOAD_TIMES_PER_DAY}) for YouTube Shorts has been reached during execution for today "
                f"({get_pakistan_time().strftime('%Y-%m-%d %Z%z')}). "
                f"No further uploads will be attempted today."
            )
            send_email_notification(EMAIL_SUBJECT_DAILY_LIMIT, email_body)
            break

        now = get_pakistan_time()
        time_to_wait = (scheduled_time - now).total_seconds()

        if time_to_wait > 0:
            logging.info(f"\nWaiting until {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')} (PKT) for next upload ({i+1}/{len(scheduled_times)})...")
            time.sleep(time_to_wait)
        else:
            logging.info(f"\nScheduled time {scheduled_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')} is in the past. Attempting upload immediately ({i+1}/{len(scheduled_times)}).")

        upload_successful = False
        retry_count = 0
        while not upload_successful:
            logging.info(f"--- Starting upload attempt {retry_count + 1} for video '{video_to_upload_for_this_schedule}' (scheduled time {scheduled_time.strftime('%H:%M:%S')}) ---")
            try:
                upload_successful = upload_youtube_short(
                    profile_path, video_folder_path, uploaded_log_file, 
                    channel_counter_file, titles_file_path,
                    video_to_upload_name_param=video_to_upload_for_this_schedule
                )
                if upload_successful:
                    logging.info(f"Upload process completed successfully for '{video_to_upload_for_this_schedule}'.")
                else:
                    logging.warning(f"Upload process failed for '{video_to_upload_for_this_schedule}'. Retrying in {RETRY_DELAY_SECONDS} seconds...")
                    time.sleep(RETRY_DELAY_SECONDS)
                    retry_count += 1
            except Exception as e:
                logging.error(f"An unexpected error occurred during upload attempt {retry_count + 1} for '{video_to_upload_for_this_schedule}': {e}")
                logging.info(f"Retrying in {RETRY_DELAY_SECONDS} seconds...")
                time.sleep(RETRY_DELAY_SECONDS)
                retry_count += 1
        
        uploaded_videos = get_uploaded_videos(uploaded_log_file)
        video_to_upload_for_this_schedule = None
        for video_num, video_name in all_video_files:
            if video_num >= 4 and video_name not in uploaded_videos:
                video_to_upload_for_this_schedule = video_name
                break
        
        if not video_to_upload_for_this_schedule:
            logging.info("No more new video files to upload. Scheduler finished for today.")
            break

    logging.info("\nAll scheduled uploads for today have been attempted or daily limit reached.")

if __name__ == "__main__":
    schedule_daily_uploads()