"""
AI Service module for Government Job Guide – AI Career Assistant.
Integrates with the official Google Gen AI Python SDK (google-genai).
Includes input validation, safe error handling, retry logic with bounded backoff,
and fallback guidance when API keys are unconfigured.
"""

import os
import re
import time
import logging
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger('ai_service')
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Official System Instruction as mandated by specifications
SYSTEM_INSTRUCTION = (
    "You are Government Job Guide, an Indian government career-guidance assistant. "
    "Help students and job seekers understand government career options according to their education, "
    "branch, age, state, and interests.\n\n"
    "Answer the actual question directly. Use simple English or Hindi/Hinglish based on the user's language. "
    "Give practical and relevant guidance rather than repeating the same generic list.\n\n"
    "For each suitable career option, explain:\n"
    "- Recruiting organization or department\n"
    "- Basic educational eligibility\n"
    "- Typical selection stages\n"
    "- Relevant examination or preparation topics\n"
    "- Whether the opportunity is technical or general graduate-level\n"
    "- Important eligibility conditions that require official verification\n\n"
    "Distinguish students who are currently studying from graduates. For engineering students, "
    "discuss relevant technical opportunities while explaining that branch and degree requirements "
    "vary by recruitment.\n\n"
    "Do not invent vacancies, application dates, examination dates, salary amounts, official links, "
    "or eligibility requirements. Never claim to have checked live vacancies unless live data has "
    "actually been retrieved from a reliable source.\n\n"
    "When exact current recruitment details are requested, explain the limitation and direct the "
    "user to the relevant official recruitment body's website. If official-source browsing is implemented, "
    "cite the actual sources retrieved.\n\n"
    "Never guarantee employment or selection. Ask only one useful follow-up question when additional "
    "details are needed."
)

MAX_MESSAGE_LENGTH = 2500
MAX_HISTORY_ITEMS = 20


def get_gemini_config() -> Tuple[str, str]:
    """Retrieve Gemini API key and model from environment variables."""
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    model_id = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite').strip()
    if not model_id:
        model_id = 'gemini-3.5-flash-lite'
    return api_key, model_id


def is_placeholder_key(key: str) -> bool:
    """Check if the API key is empty or a placeholder."""
    if not key:
        return True
    placeholders = ['your_gemini_api_key_here', 'placeholder', 'none', 'null', 'api_key_here']
    return key.lower() in placeholders


def validate_chat_input(data: Any) -> Tuple[bool, str, str, List[Dict[str, str]]]:
    """
    Validate incoming JSON data for the chat endpoint.
    Returns: (is_valid, error_message, cleaned_message, cleaned_history)
    """
    if not isinstance(data, dict):
        return False, "Invalid request format: JSON object expected.", "", []

    message = data.get('message')
    if message is None or not isinstance(message, str):
        return False, "Message field is required and must be text.", "", []

    message_clean = message.strip()
    if not message_clean:
        return False, "Message cannot be empty.", "", []

    if len(message_clean) > MAX_MESSAGE_LENGTH:
        return False, f"Message exceeds maximum allowed length of {MAX_MESSAGE_LENGTH} characters.", "", []

    history_raw = data.get('history', [])
    if not isinstance(history_raw, list):
        return False, "History field must be a list if provided.", "", []

    # Limit history items
    history_trimmed = history_raw[-MAX_HISTORY_ITEMS:]
    cleaned_history: List[Dict[str, str]] = []

    for item in history_trimmed:
        if not isinstance(item, dict):
            continue
        role = item.get('role', '').lower().strip()
        # Accept 'user', 'assistant', 'model'
        if role in ('assistant', 'model'):
            role = 'model'
        elif role == 'user':
            role = 'user'
        else:
            continue

        text = item.get('text') or item.get('content') or ''
        if not isinstance(text, str):
            continue
        text_clean = text.strip()
        if text_clean:
            cleaned_history.append({'role': role, 'text': text_clean[:3000]})

    return True, "", message_clean, cleaned_history


def build_fallback_response(user_query: str) -> str:
    """
    High-quality offline knowledge base for instant career guidance when GEMINI_API_KEY
    is not yet configured in .env. Ensures the platform is fully responsive and testable immediately.
    """
    q = user_query.lower()

    notice = (
        "> [!NOTE]\n"
        "> **Demo Guidance Mode Active**: Your `GEMINI_API_KEY` is not yet configured in `.env`. "
        "Showing built-in career guidance. Configure your key in `.env` for live, real-time Gemini reasoning.\n\n"
    )

    if "12th" in q:
        return notice + (
            "### Government Career Opportunities After 12th Standard\n\n"
            "Passing 10+2 opens several high-repute central and state government paths across defense, clerical, and technical services:\n\n"
            "#### 1. SSC Combined Higher Secondary Level (CHSL)\n"
            "- **Recruiting Body:** Staff Selection Commission (SSC)\n"
            "- **Basic Eligibility:** 10+2 from a recognized board; age typically 18–27 years.\n"
            "- **Roles:** Lower Division Clerk (LDC), Junior Secretariat Assistant (JSA), Data Entry Operator (DEO).\n"
            "- **Selection Stages:** Tier-I (Computer Based Test: General Intelligence, English, Quantitative Aptitude, General Awareness) + Tier-II (Skill Test / Typing Test).\n"
            "- **Nature:** General administrative / clerical.\n\n"
            "#### 2. National Defence Academy (NDA) & Naval Academy\n"
            "- **Recruiting Body:** Union Public Service Commission (UPSC)\n"
            "- **Basic Eligibility:** 12th Pass (Physics & Math mandatory for Air Force/Navy; any stream for Army); age roughly 16.5–19.5 years; unmarried male/female.\n"
            "- **Selection Stages:** Written Examination (Mathematics & General Ability Test) followed by 5-day Services Selection Board (SSB) Interview and Medicals.\n"
            "- **Nature:** Defense officer-cadet training.\n\n"
            "#### 3. Railway Recruitment Board (RRB NTPC Undergraduate Posts)\n"
            "- **Recruiting Body:** Railway Recruitment Boards (RRBs)\n"
            "- **Basic Eligibility:** 12th pass; age 18–30/33 years depending on notification.\n"
            "- **Roles:** Junior Clerk cum Typist, Accounts Clerk cum Typist, Trains Clerk, Commercial cum Ticket Clerk.\n"
            "- **Selection Stages:** CBT-1, CBT-2, Typing Skill Test (if applicable), and Document Verification.\n\n"
            "#### 4. State Police Constable & Forest Guard\n"
            "- **Recruiting Body:** State Police Recruitment Boards (e.g., Maharashtra Police, UP Police, Delhi Police).\n"
            "- **Basic Eligibility:** 12th pass, physical fitness standards (height, chest measurements, running tests).\n"
            "- **Selection Stages:** Written Exam, Physical Endurance & Measurement Test (PET/PMT), Medical Exam.\n\n"
            "**Official Verification Reminder:** Age relaxations for OBC/SC/ST/EWS and exact cut-off dates require reference to the respective official recruitment notifications on [ssc.gov.in](https://ssc.gov.in) or [upsc.gov.in](https://upsc.gov.in).\n\n"
            "**Follow-up Question:** Would you prefer defense services (NDA, Police) or civil administrative roles (SSC, Railways)?"
        )

    if "b.tech" in q or "cse" in q or "engineering" in q or "b.e" in q or "computer" in q:
        return notice + (
            "### Government Career Paths for B.Tech / B.E. (Computer Science & Engineering)\n\n"
            "Engineers, particularly CSE/IT graduates, have both specialized technical and prestigious general administrative options:\n\n"
            "#### 1. Public Sector Undertakings (PSUs) via GATE & Direct Exams\n"
            "- **Recruiting Bodies:** IOCL, ONGC, NTPC, BEL, BHEL, PowerGrid, BARC, ISRO.\n"
            "- **Basic Eligibility:** B.Tech/B.E. in CSE/IT with first-class marks (typically 60–65%+ aggregate).\n"
            "- **Selection Stages:** GATE (CS paper) percentile score shortlisting followed by Technical Interview & Group Discussion; or independent computer-based technical tests (e.g., ISRO ICRB, NIELIT, CDAC).\n"
            "- **Nature:** Core technical (Software development, network infrastructure, cybersecurity, cloud).\n\n"
            "#### 2. Specialist Officers in Banking (IBPS SO IT Officer - Scale I)\n"
            "- **Recruiting Body:** Institute of Banking Personnel Selection (IBPS) & SBI.\n"
            "- **Basic Eligibility:** 4-year Engineering Degree in Computer Science, IT, Computer Applications, Electronics & Telecommunications; age 20–30 years.\n"
            "- **Selection Stages:** Prelims (Reasoning, English, Quant/GA) -> Mains (Professional IT Knowledge) -> Interview.\n"
            "- **Nature:** Technical banking operations (Core Banking System, security, databases).\n\n"
            "#### 3. Intelligence & National Security (NIC / IB / CERT-In / DRDO)\n"
            "- **Recruiting Bodies:** National Informatics Centre (NIC - Scientist B / Scientific Officer), Intelligence Bureau (ACIO Technical), DRDO (RAC Scientist B).\n"
            "- **Basic Eligibility:** B.Tech CSE/IT with valid GATE score or dedicated competitive examination.\n"
            "- **Selection Stages:** Written exam covering Data Structures, Algorithms, OS, DBMS, Networks, Cyber Security followed by Interview.\n\n"
            "#### 4. Civil Services (UPSC CSE & State PSC)\n"
            "- **Nature:** General graduate level. Any engineering degree is fully recognized for IAS, IPS, IRS, etc.\n\n"
            "**Important Verification:** Degree completion criteria (appearing vs passed) varies. Most technical recruitment mandates degree completion prior to document verification.\n\n"
            "**Follow-up Question:** Are you interested in core technical software/cybersecurity roles (PSUs/NIC) or general administrative services (UPSC/Banking PO)?"
        )

    if "ssc" in q:
        return notice + (
            "### Staff Selection Commission (SSC) Job Opportunities\n\n"
            "SSC is one of India's largest recruitment agencies for non-gazetted group 'B' and 'C' positions in Central Ministries and Departments:\n\n"
            "#### 1. SSC CGL (Combined Graduate Level)\n"
            "- **Eligibility:** Graduation in any discipline from a recognized University; Age 18–30/32 years (post-dependent).\n"
            "- **Prominent Posts:** Assistant Section Officer (CSS, MEA, IB), Inspector of Central Excise (GST), Income Tax Inspector, Sub-Inspector (CBI), Auditor (CAG).\n"
            "- **Stages:** Tier-I (Qualifying CBT) -> Tier-II (Objective CBT: Math, Reasoning, English, General Awareness, Computer Knowledge, Data Entry Speed Test).\n\n"
            "#### 2. SSC CHSL (Combined Higher Secondary Level)\n"
            "- **Eligibility:** 10+2 Pass; Age 18–27 years.\n"
            "- **Posts:** Lower Division Clerk (LDC), Junior Secretariat Assistant (JSA), Data Entry Operator (DEO).\n\n"
            "#### 3. SSC CPO (Central Police Organisation)\n"
            "- **Eligibility:** Bachelor's degree + Physical Endurance standards; Age 20–25 years.\n"
            "- **Posts:** Sub-Inspector in Delhi Police and Central Armed Police Forces (BSF, CISF, CRPF, ITBP, SSB).\n\n"
            "#### 4. SSC JE (Junior Engineer)\n"
            "- **Eligibility:** Diploma or B.Tech in Civil, Electrical, or Mechanical Engineering; Age up to 30/32 years.\n\n"
            "**Preparation Core:** Quantitative Aptitude, Reasoning Ability, English Comprehension, and Current Affairs.\n\n"
            "**Official Source:** Detailed schemes and official notifications are released on [ssc.gov.in](https://ssc.gov.in).\n\n"
            "**Follow-up Question:** What is your highest qualification so I can recommend the most suitable SSC examination?"
        )

    if "railway" in q or "rrb" in q:
        return notice + (
            "### Indian Railways Recruitment Opportunities (RRB & RRC)\n\n"
            "Indian Railways conducts large-scale recruitments through Railway Recruitment Boards (RRBs) across four key categories:\n\n"
            "#### 1. RRB NTPC (Non-Technical Popular Categories)\n"
            "- **Undergraduate (12th Pass):** Junior Clerk cum Typist, Accounts Clerk cum Typist, Commercial cum Ticket Clerk (Age 18–30).\n"
            "- **Graduate Level:** Station Master, Goods Train Manager (Goods Guard), Senior Commercial cum Ticket Clerk, Traffic Assistant (Age 18–33/36).\n"
            "- **Selection:** CBT 1 -> CBT 2 -> CBAT (Aptitude Test for Station Master) / Typing Skill Test -> Document Verification & Medical.\n\n"
            "#### 2. RRB Assistant Loco Pilot (ALP) & Technicians\n"
            "- **Eligibility:** Matriculation / 10th + ITI in recognized trades, or Diploma / B.Tech in Mechanical/Electrical/Electronics.\n"
            "- **Selection:** CBT 1, CBT 2 (Part A: General, Part B: Trade syllabus), Computer-Based Aptitude Test (for ALP), and Strict A-1 Medical Fitness.\n\n"
            "#### 3. RRB Junior Engineer (JE)\n"
            "- **Eligibility:** Diploma or B.E./B.Tech in relevant engineering discipline.\n"
            "- **Posts:** JE (Civil, Electrical, Mechanical, Signal & Telecommunication), Chemical & Metallurgical Assistant (CMA).\n\n"
            "#### 4. RRC Level 1 (Group D)\n"
            "- **Eligibility:** 10th Pass or ITI from NCVT/SCVT; Age 18–33 years.\n\n"
            "**Official Source:** Candidate notices are released on regional RRB websites (e.g., [rrbcdg.gov.in](https://rrbcdg.gov.in)).\n\n"
            "**Follow-up Question:** Do you have a technical qualification (ITI/Diploma/B.Tech) or are you seeking general non-technical posts?"
        )

    if "diploma" in q or "iti" in q:
        return notice + (
            "### Government Jobs for Diploma & ITI Holders\n\n"
            "Technical diplomas and ITI trade certificates offer direct, specialized entry points into engineering and technical divisions:\n\n"
            "#### 1. Junior Engineer (SSC JE & State Irrigation/PWD/Electricity Boards)\n"
            "- **Eligibility:** 3-year Diploma in Civil, Mechanical, or Electrical Engineering.\n"
            "- **Key Organizations:** CPWD, MES, Border Roads Organisation (BRO), Central Water Commission.\n"
            "- **Selection:** Paper-I (Objective CBT: General Intelligence, General Awareness, Engineering Discipline) + Paper-II (In-depth Technical CBT).\n\n"
            "#### 2. Railway Technician & Junior Engineer (RRB)\n"
            "- **Eligibility:** ITI in relevant trade (Fitter, Electrician, Machinist, Welder) for Technician; 3-year Diploma for RRB JE.\n\n"
            "#### 3. PSU Apprenticeships & Technician Trainees\n"
            "- **Recruiting Bodies:** DRDO, ISRO, BHEL, IOCL, ONGC, SAIL, NTPC, NPCIL, BARC.\n"
            "- **Roles:** Technician Grade-C, Scientific Assistant, Stipendiary Trainee Category-I/II.\n"
            "- **Selection:** Written test on trade/diploma engineering fundamentals + Skill/Trade test.\n\n"
            "**Important Verification:** Distance education diplomas are often ineligible for central engineering cadres. Always check specific state/central norms.\n\n"
            "**Follow-up Question:** Which branch or ITI trade do you specialize in?"
        )

    if "upsc" in q or "civil services" in q:
        return notice + (
            "### UPSC & Civil Services Career Guidance\n\n"
            "The Union Public Service Commission conducts prestigious examinations for All India Services and Central Group 'A' & 'B' cadres:\n\n"
            "#### 1. Civil Services Examination (CSE)\n"
            "- **Target Roles:** IAS (Indian Administrative Service), IPS (Indian Police Service), IFS (Indian Foreign Service), IRS, IA&AS.\n"
            "- **Eligibility:** Bachelor's degree in any discipline from a recognized university; Age 21–32 years (general category, relaxable for reserved categories).\n"
            "- **Three Stages:**\n"
            "  1. **Preliminary Examination:** General Studies Paper-I (100 questions, marks determine merit) & CSAT Paper-II (80 questions, 33% qualifying).\n"
            "  2. **Mains Examination (Descriptive):** 9 Papers (2 Qualifying language papers, 1 Essay, 4 General Studies papers, 2 Optional subject papers).\n"
            "  3. **Personality Test (Interview):** Board interview assessing mental alertness, critical judgment, and public administration aptitude.\n\n"
            "#### 2. Other UPSC Opportunities\n"
            "- **Engineering Services Examination (ESE/IES):** For Civil, Mechanical, Electrical, and Electronics engineers.\n"
            "- **Combined Defence Services (CDS):** For entry into IMA, OTA, INA, and AFA.\n"
            "- **Central Armed Police Forces (CAPF AC):** For Assistant Commandant posts in BSF, CRPF, CISF, ITBP, SSB.\n\n"
            "**Preparation Core:** Daily newspaper analysis (The Hindu / Indian Express), NCERT textbooks (Class 6-12), and consistent answer writing practice.\n\n"
            "**Official Source:** Candidate calendar and notifications are published on [upsc.gov.in](https://upsc.gov.in).\n\n"
            "**Follow-up Question:** Are you currently in college or a working graduate preparing for your first attempt?"
        )

    if "defence" in q or "defense" in q or "army" in q or "navy" in q or "air force" in q:
        return notice + (
            "### Defence Forces Career Pathways (Indian Armed Forces)\n\n"
            "The Armed Forces offer officer and non-officer entries across Army, Navy, and Air Force:\n\n"
            "#### 1. Officer Entries\n"
            "- **After 12th:** NDA & NA Exam (UPSC), Technical Entry Scheme (TES - 10+2 PCM via JEE Main ranks).\n"
            "- **After Graduation:** Combined Defence Services (CDS - UPSC), Air Force Common Admission Test (AFCAT), Navy Direct Technical Entries.\n"
            "- **For Engineers:** TGC (Technical Graduate Course - Army), SSC-Tech, SSC-Naval Armament.\n"
            "- **Selection Process:** Written test (if applicable) -> 5-Day SSB (Services Selection Board) Interview assessing Officer Like Qualities (OLQ) -> Comprehensive Medical Board.\n\n"
            "#### 2. Non-Officer (Soldier / Airman / Sailor) Entries\n"
            "- **Agniveer Scheme:** 4-year service scheme in Army, Navy, and Air Force for 10th/12th candidates (age 17.5–21 years).\n"
            "- **Selection:** Online CEE (Common Entrance Examination) -> Physical Fitness Test -> Medical Examination.\n\n"
            "**Official Portals:** [joinindianarmy.nic.in](https://joinindianarmy.nic.in), [joinindiannavy.gov.in](https://joinindiannavy.gov.in), [careerindianairforce.cdac.in](https://careerindianairforce.cdac.in).\n\n"
            "**Follow-up Question:** Are you seeking an Officer commission entry (NDA/CDS/SSB) or Agniveer entry?"
        )

    if "maharashtra" in q or "mpsc" in q:
        return notice + (
            "### Maharashtra State Government Job Opportunities\n\n"
            "Maharashtra public recruitment is conducted primarily through MPSC and State Recruitment Committees:\n\n"
            "#### 1. Maharashtra Public Service Commission (MPSC)\n"
            "- **MPSC State Services (Rajyaseva):** Deputy Collector, DySP, Tehsildar, Block Development Officer (BDO). Requires Bachelor's degree; Prelims -> Mains (Descriptive) -> Interview.\n"
            "- **MPSC Subordinate Services (Group B Combined):** Police Sub-Inspector (PSI), State Tax Inspector (STI), Assistant Section Officer (ASO).\n"
            "- **MPSC Group C Combined:** Tax Assistant, Clerk-Typist, Industry Inspector.\n\n"
            "#### 2. Maharashtra Police Recruitment\n"
            "- **Posts:** Police Constable, SRPF, Driver Police Constable.\n"
            "- **Eligibility:** 12th pass; Physical Test (50 marks) and Written Exam (100 marks).\n\n"
            "#### 3. Zilla Parishad & Talathi Bharti\n"
            "- **Posts:** Talathi (Revenue Assistant), Junior Engineer, Health Worker, Gram Sevak.\n"
            "- **Eligibility:** Graduation for Talathi; MS-CIT computer certificate and Marathi language proficiency generally required.\n\n"
            "**Mandatory State Requirement:** Domicile of Maharashtra and proficiency in Marathi (Reading, Writing, Speaking).\n\n"
            "**Official Source:** [mpsc.gov.in](https://mpsc.gov.in) and [mahasarkar.co.in](https://mahasarkar.co.in).\n\n"
            "**Follow-up Question:** Do you hold a Maharashtra domicile and are you fluent in Marathi?"
        )

    # General / Default response
    return notice + (
        f"### Government Career Exploration Guidance\n\n"
        f"Regarding your query on **\"{user_query}\"**, here is a structured breakdown of how government recruitment operates:\n\n"
        "#### 1. Primary Recruitment Sectors\n"
        "- **Central Civil Administration:** SSC (CGL, CHSL, MTS) for ministries, departments, and subordinate offices.\n"
        "- **Technical & Engineering:** PSU recruitment via GATE, SSC JE, RRB JE, and State Electricity Boards.\n"
        "- **Banking & Insurance:** IBPS PO/Clerk/SO, SBI PO/Clerk, RBI Grade B, and LIC AAO.\n"
        "- **State Public Services:** State PSCs (Administrative officers, revenue inspectors, municipal officers).\n"
        "- **Uniformed Services:** Defence (Army, Navy, Air Force) and State Police forces.\n\n"
        "#### 2. Key Pillars of Every Examination\n"
        "Most government exams evaluate candidates across four standard sections:\n"
        "1. **Quantitative Aptitude:** Arithmetic, Algebra, Geometry, Data Interpretation.\n"
        "2. **Reasoning Ability:** Verbal, Non-verbal, Logical deductions, Puzzles.\n"
        "3. **General Awareness:** History, Geography, Indian Polity, Economy, Current Affairs (past 6–12 months).\n"
        "4. **English Language:** Grammar rules, Vocabulary, Reading comprehension.\n\n"
        "**Important Verification Notice:** Government notifications strictly enforce cut-off dates for age, educational certificates, and category reservations. Always consult the official recruitment gazette.\n\n"
        "**Follow-up Question:** What is your highest qualification and target department so I can provide customized, exact exam paths?"
    )


def call_gemini_api(cleaned_message: str, cleaned_history: List[Dict[str, str]]) -> str:
    """
    Calls the official Google Gen AI Python SDK with system instruction,
    bounded backoff retry for transient rate limits, and safe error parsing.
    """
    api_key, model_id = get_gemini_config()

    if is_placeholder_key(api_key):
        logger.info("Using built-in fallback knowledge (GEMINI_API_KEY is not configured).")
        return build_fallback_response(cleaned_message)

    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
    except ImportError as e:
        logger.error(f"Google Gen AI SDK import failed: {e}")
        return build_fallback_response(cleaned_message)

    client = genai.Client(api_key=api_key)

    # Convert cleaned history to SDK types
    contents = []
    for h in cleaned_history:
        role = 'user' if h['role'] == 'user' else 'model'
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=h['text'])]
        ))

    # Append current user message
    contents.append(types.Content(
        role='user',
        parts=[types.Part.from_text(text=cleaned_message)]
    ))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=2048,
    )

    # Retry with bounded backoff (max 2 retries for 429/503)
    max_retries = 2
    backoff_seconds = 1.0

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Calling Gemini model '{model_id}' (attempt {attempt + 1})...")
            response = client.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )

            # Safely extract response text
            if response and response.text:
                return response.text.strip()
            else:
                return "I received your query, but no response text was generated. Please try rephrasing your question."

        except APIError as api_err:
            error_code = getattr(api_err, 'code', None) or getattr(api_err, 'status_code', None)
            err_msg = str(api_err)
            logger.warning(f"Gemini API error (attempt {attempt + 1}): code={error_code}, msg={err_msg}")

            # Check if retryable (rate limit 429 or server unavailable 503)
            is_rate_limit = error_code == 429 or "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg
            is_unavailable = error_code == 503 or "503" in err_msg or "UNAVAILABLE" in err_msg

            if (is_rate_limit or is_unavailable) and attempt < max_retries:
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue

            # Non-retryable or retries exhausted
            if is_rate_limit:
                raise RuntimeError("API quota limit reached (429). Please try again shortly or inspect your quota at Google AI Studio.")
            elif error_code in (401, 403) or "API_KEY_INVALID" in err_msg or "PERMISSION_DENIED" in err_msg:
                raise RuntimeError("Invalid or unauthorized Gemini API key (401/403). Please verify your GEMINI_API_KEY in the .env file.")
            elif error_code == 404 or "NOT_FOUND" in err_msg:
                raise RuntimeError(f"Configured Gemini model '{model_id}' was not found (404). Recommended models: 'gemini-2.5-flash' or 'gemini-2.0-flash'.")
            else:
                raise RuntimeError(f"Gemini API service error: {err_msg[:200]}")

        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {e}")
            if attempt < max_retries:
                time.sleep(backoff_seconds)
                backoff_seconds *= 2
                continue
            raise RuntimeError(f"An unexpected error occurred while communicating with the AI service: {str(e)[:200]}")


def generate_eligibility_report(criteria: Dict[str, Any]) -> str:
    """
    Constructs an in-depth, structured eligibility prompt and runs it through the AI engine.
    """
    qualification = criteria.get('qualification', 'Not specified')
    study_status = criteria.get('study_status', 'Completed')
    branch = criteria.get('branch', 'Not applicable')
    age = criteria.get('age', 'Not specified')
    state = criteria.get('state', 'All India')
    dept = criteria.get('department', 'Any')
    pref = criteria.get('career_preference', 'Both Technical and Non-Technical')

    prompt = (
        f"Perform a comprehensive Government Career Eligibility Assessment for this candidate profile:\n"
        f"- Highest Qualification: {qualification}\n"
        f"- Current Study Status: {study_status}\n"
        f"- Engineering/Specialization Branch: {branch}\n"
        f"- Age: {age} years\n"
        f"- Domicile State: {state}\n"
        f"- Preferred Department / Sector: {dept}\n"
        f"- Career Preference: {pref}\n\n"
        f"Please provide a structured report with:\n"
        f"1. **Summary Profile Overview**: Candidate status and category match.\n"
        f"2. **Top Recommended Government Examinations**: 3-4 distinct exams with recruiting organization, exact eligibility criteria, age limits, and post roles.\n"
        f"3. **Selection Stages & Exam Pattern**: Specific stages (Prelims/Mains/Interview/PET) for the top recommendation.\n"
        f"4. **Key Syllabus & Preparation Focus**: Core topics to prepare right now.\n"
        f"5. **Important Verification & Constraints**: Notice regarding cut-off dates, category relaxations, and official gazette verification.\n"
        f"6. **Actionable Next Steps**: One or two immediate preparation actions."
    )

    return call_gemini_api(prompt, [])
