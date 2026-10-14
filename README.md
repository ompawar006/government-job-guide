# Government Job Guide – AI Career Assistant

A complete, production-grade, full-stack web application designed for Indian students and job seekers. It provides intelligent, unbiased guidance on central and state government career pathways based on education, age, state, and department preferences.

---

## 🌟 Key Features

1. **AI Career Advisor (Gemini Integration):**
   - Direct interactive consultation powered by Google Gemini AI (`gemini-2.5-flash`).
   - Grounded system instructions following official recruitment guidelines for 10th, 12th, ITI, Diploma, B.Tech (including CSE/IT), and general graduates.
   - Built-in fallback guidance mode if API key is not yet configured, ensuring zero crashes.

2. **Full Voice Interaction (Web Speech API):**
   - **Speech-to-Text (STT):** Dictate questions directly into the input bar using your microphone.
   - **Text-to-Speech (TTS):** Listen to AI responses read aloud with dedicated play and stop controls.
   - Graceful fallback for browsers without Web Speech support.

3. **Qualification & Eligibility Auditor:**
   - Evaluates applicant criteria (degree, study status, engineering branch, age, domicile state, preference).
   - Dynamic branch selection for engineering/polytechnic degrees.
   - Returns structured recommendations with selection stages, preparation focus, and cut-off disclaimers.

4. **Comprehensive Job Categories Directory:**
   - 9 major government sectors: SSC, Indian Railways (RRB), Banking (IBPS/SBI/RBI), UPSC & Civil Services, Maharashtra State (MPSC), Police & CAPF, Defence Forces, Teaching (CTET/KVS/NET), and PSUs/Technical.
   - Real-time search filter and in-depth modals with official commission links.

5. **Preparation Blueprint Hub:**
   - Organized study guidance across 7 core subjects: Quantitative Aptitude, Reasoning, English, General Studies, Current Affairs, Technical Engineering, and Interview/SSB.
   - Verified links to free official NCERT digital textbooks and previous exam resources.

6. **User Accounts & Saved Roadmaps:**
   - Secure registration & login with Werkzeug password hashing and protected session cookies.
   - Save customized AI roadmaps directly to your account with full-screen reading modal and deletion controls.
   - Profile preferences to store your educational qualification, age, and state for one-click evaluations.

---

## 📂 Project Structure

```
government-job-guide/
│
├── app.py                     # Main Flask application with routes and REST APIs
├── database.py                # SQLite database management, migrations, and CRUD
├── ai_service.py              # Google GenAI SDK integration, validation, retry & fallback logic
├── requirements.txt           # Python dependencies
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore for venv, env files, and databases
├── README.md                  # Comprehensive documentation and setup guide
│
├── instance/
│   └── database.db            # SQLite database (auto-generated on startup)
│
├── static/
│   ├── css/
│   │   └── style.css          # Navy-blue and cyan modern design system
│   └── js/
│       ├── main.js            # Toast notifications, clipboard helpers, global UI
│       ├── auth.js            # Client-side validation and password match checks
│       ├── chat.js            # AI chat controller, marked.js rendering, auto-scroll
│       ├── voice.js           # Web Speech API (STT dictation & TTS narration)
│       └── eligibility.js     # Qualification assessment form handler
│
├── templates/
│   ├── base.html              # Master layout with responsive navbar, alerts, footer
│   ├── index.html             # Landing page with hero, how-it-works, FAQs
│   ├── login.html             # User login with quick demo-fill helper
│   ├── register.html          # Registration form with validation
│   ├── dashboard.html         # Candidate dashboard with quick actions and next steps
│   ├── chat.html              # AI Chatbot interface with prompt chips
│   ├── jobs.html              # 9 Government sectors directory with modals
│   ├── eligibility.html       # Interactive eligibility evaluation tool
│   ├── preparation.html       # Study hub across 7 core examination subjects
│   ├── saved.html             # Saved guidance library with reader modal
│   └── profile.html           # Candidate profile and password management
│
└── tests/
    └── test_app.py            # Automated test suite (Auth, APIs, Isolation, Validation)
```

---

## 🚀 Quick Setup & Run (Windows PowerShell)

Follow these exact commands to run the project locally on Windows:

### 1. Check Python Installation
Open Windows PowerShell and verify Python 3.10+ is available:
```powershell
python --version
python -m pip --version
```

### 2. Navigate to Project Directory
```powershell
cd "C:\Users\DELL\.gemini\antigravity\scratch\government-job-guide"
```

### 3. Create & Activate Virtual Environment
```powershell
# Create virtual environment
python -m venv .venv

# If PowerShell blocks script execution, run this once:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the template configuration file:
```powershell
Copy-Item .env.example .env
```
Open `.env` in VS Code or Notepad:
```powershell
notepad .env
```
Set your Google Gemini API key:
```env
SECRET_KEY=change_this_to_any_random_string_for_sessions
PORT=5000
FLASK_ENV=development

# Get your free Gemini API key from https://aistudio.google.com/
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*(Note: If you do not have a Gemini API key immediately, the application will automatically run in high-quality **Demo Guidance Mode** with built-in career roadmaps.)*

### 6. Run Automated Tests
Execute the automated test suite to verify everything works:
```powershell
python -m pytest tests/test_app.py -v
```
*(All 8 tests should pass with green checkmarks.)*

### 7. Launch the Application
Start the Flask development server:
```powershell
python app.py
```

### 8. Open in Your Browser
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Recommended Gemini Models

The application uses the official `google-genai` SDK (`from google import genai`). Supported models:
- `gemini-2.5-flash` (Recommended: fast, high quality, balanced quotas)
- `gemini-2.0-flash`
- `gemini-1.5-flash`

---

## 🛠️ Troubleshooting Common Issues

### Issue 1: `Activate.ps1 cannot be loaded because running scripts is disabled`
**Cause:** Windows PowerShell script execution policy is restricted by default.  
**Fix:** Run this command in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 2: `429 Resource Exhausted / Quota Limit Exceeded`
**Cause:** Gemini API free-tier per-minute quota reached.  
**Fix:** The backend has built-in retry logic with exponential backoff. If your key has hit its daily limit, switch to `gemini-2.5-flash` or wait for quota reset at Google AI Studio.

### Issue 3: `401 Unauthorized / Invalid API Key`
**Cause:** Misconfigured or expired `GEMINI_API_KEY` in `.env`.  
**Fix:** Verify your key at [Google AI Studio](https://aistudio.google.com/). Ensure there are no trailing spaces or quotes around the key in your `.env` file.

### Issue 4: Microphone Voice Recognition Not Responding
**Cause:** Browser permissions or unsupported browser.  
**Fix:** Click the lock icon in your browser address bar (Chrome, Edge, or Safari) and toggle **Microphone** permission to **Allow**.

---

## 🔒 Security Practices Implemented

- Passwords hashed using Werkzeug's `pbkdf2:sha256` salted hashing algorithm.
- No plain text passwords stored or printed in logs.
- API keys kept exclusively on the Python backend; never exposed to frontend JavaScript.
- Strict input sanitization with length limits to prevent denial-of-service.
- HTML output sanitized with `DOMPurify` to prevent cross-site scripting (XSS).
- Session cookies configured with `HttpOnly` and `SameSite='Lax'`.

---

## 📄 License
Educational Open-Source Project. Created for Indian civil, engineering, and government career aspirants.
