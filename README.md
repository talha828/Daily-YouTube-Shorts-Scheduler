# Daily-YouTube-Shorts-Scheduler 🚀

![Python Version](https://img.shields.io/badge/Python-3.x-blue.svg)
![Selenium Version](https://img.shields.io/badge/Selenium-WebAutomation-green.svg)
![Headless Browser](https://img.shields.io/badge/Headless-Supported-lightgrey.svg)

**Automate your daily YouTube Shorts uploads with dynamic titles, scheduled timings, and robust retry logic.**

---

## ✨ Features

* **Automated Uploads:** Uploads video files (`.mp4`, `.mov`, etc.) from a specified folder.
* **Sequential Video Selection:** Automatically picks the next un-uploaded video (starting from `4.mp4`).
* **Dynamic Titles:** Uses titles from `titles.txt` and appends the sequential short number (e.g., "My Title | #Shorts 42").
* **Daily Scheduling:** Configurable number of uploads per day with random timings.
* **Daily Limit Enforcement:** Stops uploading once the daily video limit is reached.
* **Persistent Retries:** Continuously retries a failed upload for the *same video* until successful.
* **Headless Mode:** Runs the browser in the background without a visible window.
* **Secure Credentials:** Loads email password from a `.env` file for security.
* **Detailed Logging & Email Alerts:** Provides logs and email notifications for successes, failures, and daily limit reached.

---

## 🛠️ Setup & Installation

### Prerequisites

* **Python 3.x**
* **Firefox Browser**
* **GeckoDriver:** Download from [GitHub Releases](https://github.com/mozilla/geckodriver/releases) and place in your system's PATH (e.g., `/usr/local/bin/`).
* **Firefox Profile:** A dedicated Firefox profile where you are already logged into your YouTube account (`about:profiles` in Firefox to find/manage).

### Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/yourusername/Daily-YouTube-Shorts-Scheduler.git](https://github.com/yourusername/Daily-YouTube-Shorts-Scheduler.git)
    cd Daily-YouTube-Shorts-Scheduler
    ```
2.  **Install Python dependencies:**
    ```bash
    pip install selenium pytz python-dotenv
    ```
    *(Or create a `requirements.txt` with these and run `pip install -r requirements.txt`)*
3.  **Create `titles.txt`:** In the project root, create `titles.txt` with one title per line.
    ```
    # Example titles.txt
    My Awesome Short
    Daily Inspiration
    Quick Tip
    ```
4.  **Create `.env` file:** In the project root, create a `.env` file for your email password.
    ```
    SENDER_PASSWORD="your_email_app_password"
    ```
    **Important:** Add `/.env` to your `.gitignore` file to prevent committing sensitive data.

---

## ⚙️ Configuration

Open `your_script_name.py` and update the following variables:

* `profile_path`: Your Firefox profile directory path.
* `video_folder_path`: Path to your folder containing video files.
* `SENDER_EMAIL`: Your email for sending notifications.
* `RECEIVER_EMAIL`: Email to receive notifications.
* `UPLOAD_TIMES_PER_DAY`: Set your desired daily upload limit (e.g., `5`).
* `RETRY_DELAY_SECONDS`: Delay between retries (e.g., `300` for 5 minutes).
* `PAKISTAN_TIMEZONE`: Adjust if your timezone is different.

---

## 🚀 Usage

Run the script from your terminal:

```bash
python3 main.py
````

For continuous operation, consider using `cron` (Linux) to schedule the script to run periodically.

-----

## 📂 Project Structure

```
Daily-YouTube-Shorts-Scheduler/
├── your_script_name.py    # Main script
├── .env                   # Secure credentials (Git ignored)
├── titles.txt             # Custom video titles
├── uploaded_videos.log    # Log of uploaded video filenames
├── channel_video_counter.txt # Tracks next channel video number
├── daily_upload_counter.log  # Tracks daily upload count
├── youtube_automation.log # Comprehensive script logs
└── README.md              # This file
```

-----

## ⚠️ Important Notes

  * **XPath Stability:** The script relies on specific XPaths for YouTube Studio elements. YouTube's UI can change, which may break the script. Regular verification of XPaths might be necessary.
  * **"Success" Definition:** The script considers an upload "successful" if all Selenium interactions complete. It does not verify YouTube's internal video processing or publishing status (e.g., copyright checks). Monitor your YouTube Studio dashboard.

-----

## 📞 Contact

For questions or issues, feel free to reach out:

  * GitHub: [talha828](https://github.com/talha828)
  * Email: [talha.developer.01@gmail.com](mailto:talha.developer.01@gmail.com)

-----
