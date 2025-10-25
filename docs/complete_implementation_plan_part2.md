
┌─ FEATURE 4: ASYNC VIDEO INTERVIEW PLATFORM ─────────────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Allows candidates to record video responses at their convenience           │
│  (like HireVue but free and self-hosted)                                    │
│                                                                              │
│  WORKFLOW:                                                                  │
│                                                                              │
│  Step 1: INVITATION                                                         │
│  • HR triggers video interview for candidate                                │
│  • System generates unique secure link: /interview/{token}                  │
│  • Email/WhatsApp sent: "Record your video interview by Oct 28"            │
│  • Link expires in 7 days                                                   │
│                                                                              │
│  Step 2: CANDIDATE EXPERIENCE                                               │
│  • Opens link in browser (Chrome/Firefox/Safari)                            │
│  • Sees 4-5 questions one by one                                            │
│  • Click "Start Recording" → browser requests camera/mic permission         │
│  • 30 seconds to prepare, then records (max 2 min per question)            │
│  • Can re-record each question once if not satisfied                        │
│  • Progress bar shows completion (Question 2 of 5)                          │
│                                                                              │
│  Step 3: RECORDING (Browser-based, No External Service)                     │
│  • Uses browser MediaRecorder API (built into Chrome/Firefox)               │
│  • Records video/audio locally                                              │
│  • Format: WebM (modern, efficient)                                         │
│  • Upload on completion (or chunk upload for reliability)                   │
│  • Auto-compression to save bandwidth                                       │
│                                                                              │
│  Step 4: PROCESSING                                                         │
│  • Video saved to Cloudflare R2 (10GB free tier)                           │
│  • FFmpeg extracts audio track                                              │
│  • Whisper transcribes audio → text                                         │
│  • Llama 3.1 analyzes transcript + metadata                                 │
│                                                                              │
│  Step 5: AI ANALYSIS                                                        │
│  For each video response:                                                   │
│  • Transcript quality check (clarity, complete sentences)                   │
│  • Content analysis (answers the question? relevant?)                       │
│  • Communication score (articulation, confidence)                           │
│  • Professional presentation (background, lighting, attire)                 │
│  • Enthusiasm indicators (tone, energy)                                     │
│                                                                              │
│  Overall video interview score:                                             │
│  • Communication clarity: 78/100                                            │
│  • Content relevance: 85/100                                                │
│  • Professional presentation: 90/100                                        │
│  • Technical competence: 72/100 (for tech questions)                        │
│  • Overall recommendation: "Strong candidate"                               │
│                                                                              │
│  Step 6: HR REVIEW DASHBOARD                                                │
│  HR can:                                                                    │
│  • Watch all video responses side-by-side                                   │
│  • Read transcripts                                                         │
│  • See AI analysis and scores                                               │
│  • Leave timestamp comments ("Good answer at 1:23")                         │
│  • Compare multiple candidates                                              │
│  • Share with hiring managers (secure link)                                 │
│                                                                              │
│  TECHNICAL IMPLEMENTATION:                                                   │
│  Frontend:                                                                  │
│  • React component with navigator.mediaDevices.getUserMedia()               │
│  • MediaRecorder API for recording                                          │
│  • Upload via fetch() with progress indicator                               │
│                                                                              │
│  Backend:                                                                   │
│  • FastAPI endpoint receives video upload                                   │
│  • FFmpeg extracts audio: ffmpeg -i video.webm -vn audio.wav               │
│  • Whisper transcribes audio                                                │
│  • Llama analyzes transcript                                                │
│  • Store video URL + analysis in database                                   │
│                                                                              │
│  COST PER INTERVIEW:                                                        │
│  • Video storage (Cloudflare R2): FREE (10GB tier = ~200 videos)           │
│  • Transcription (Whisper local): FREE                                      │
│  • Analysis (Llama local): FREE                                             │
│  • Total: $0 vs. HireVue $35/candidate                                      │
│                                                                              │
│  WHY THIS BEATS HIREVUE:                                                    │
│  • Free vs. $35 per candidate                                               │
│  • Transparent AI (no creepy facial analysis)                               │
│  • Full data ownership                                                      │
│  • Customizable questions per job                                           │
│  • India-friendly (works on 3G/4G)                                          │
│                                                                              │
│  CANDIDATE BENEFITS:                                                        │
│  • Record at their convenience (no scheduling conflicts)                    │
│  • Re-record if not happy (reduces anxiety)                                 │
│  • No app download needed (works in browser)                                │
│  • Low bandwidth (auto-compression)                                         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ FEATURE 5: HUMAN-IN-LOOP REVIEW QUEUE ─────────────────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Intelligently routes borderline candidates to human reviewers with         │
│  all context needed for fast, informed decisions                            │
│                                                                              │
│  WHEN CANDIDATES ENTER REVIEW QUEUE:                                        │
│  1. Borderline AI score (60-75 when threshold is 70)                        │
│  2. Low AI confidence (<0.75 even with high score)                          │
│  3. Conflicting signals (great resume, poor voice interview)                │
│  4. Manual escalation (HR clicks "Needs review")                            │
│  5. Diversity/compliance check (random 10% sample)                          │
│                                                                              │
│  PRIORITY LEVELS:                                                           │
│  🔴 HIGH: Score 68-72 (borderline), high-value roles, urgent hiring         │
│  🟡 MEDIUM: Score 60-68, moderate confidence issues                         │
│  🟢 LOW: Routine reviews, compliance checks                                 │
│                                                                              │
│  REVIEW DASHBOARD (HR Interface):                                           │
│                                                                              │
│  Left Panel - Queue List:                                                   │
│  ┌──────────────────────────────────────────┐                              │
│  │ 🔴 Priya Sharma - Backend Dev - 72/100   │                              │
│  │ AI: Proceed | Confidence: 65%            │                              │
│  │ Reason: Low confidence on tech skills    │                              │
│  ├──────────────────────────────────────────┤                              │
│  │ 🟡 Rahul Verma - Frontend - 68/100       │                              │
│  │ AI: Reject | Confidence: 82%             │                              │
│  │ Reason: Borderline score                 │                              │
│  ├──────────────────────────────────────────┤                              │
│  │ 🟢 Anita Desai - Product - 75/100        │                              │
│  │ AI: Proceed | Confidence: 70%            │                              │
│  │ Reason: Compliance check (random)        │                              │
│  └──────────────────────────────────────────┘                              │
│                                                                              │
│  Right Panel - Detailed View:                                               │
│  ┌───────────────────────────────────────────────────────────────┐         │
│  │ CANDIDATE: Priya Sharma                                       │         │
│  │ JOB: Senior Backend Developer                                 │         │
│  │                                                                │         │
│  │ [Resume Tab] [AI Analysis Tab] [Voice Interview] [Video]      │         │
│  │                                                                │         │
│  │ AI RECOMMENDATION: ✅ Proceed to interview                     │         │
│  │ Confidence: 65% ⚠️ (Below 75% threshold)                      │         │
│  │                                                                │         │
│  │ SCORE BREAKDOWN:                                              │         │
│  │ • Education: 85/100 (IIT Delhi, CSE)                          │         │
│  │ • Experience: 70/100 (2 years, relevant)                      │         │
│  │ • Skills: 65/100 ⚠️ (Has Python, missing AWS)                 │         │
│  │ • Communication: 75/100 (Voice interview good)                │         │
│  │                                                                │         │
│  │ STRENGTHS:                                                     │         │
│  │ • Strong educational background (IIT)                         │         │
│  │ • Good Python and Django skills                               │         │
│  │ • Clear communication in interview                            │         │
│  │                                                                │         │
│  │ CONCERNS:                                                      │         │
│  │ • No AWS experience (job requires it) ⚠️                       │         │
│  │ • Only 2 years experience (job asks for 3+)                   │         │
│  │ • No mention of Docker/Kubernetes                             │         │
│  │                                                                │         │
│  │ AI REASONING:                                                  │         │
│  │ "Candidate has strong fundamentals and IIT background          │         │
│  │  which suggests learning ability. Missing AWS is concerning    │         │
│  │  but can likely be trained. Low confidence due to experience   │         │
│  │  gap. Recommend human review to assess cultural fit."          │         │
│  │                                                                │         │
│  │ [Play Voice Interview] [View Video Responses]                  │         │
│  │                                                                │         │
│  │ YOUR DECISION:                                                 │         │
│  │ ┌─────────────────────────────────────────────────┐           │         │
│  │ │ Notes: Good candidate, AWS can be learned.      │           │         │
│  │ │ IIT background strong signal. Proceed.          │           │         │
│  │ └─────────────────────────────────────────────────┘           │         │
│  │                                                                │         │
│  │ [✅ Approve] [❌ Reject] [🔄 Escalate to Manager]             │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                                                                              │
│  AFTER HUMAN DECISION:                                                      │
│  • Application status updated (interview / rejected)                        │
│  • Feedback recorded for AI learning                                        │
│  • Candidate notified (email/WhatsApp)                                      │
│  • Next action triggered (schedule interview if approved)                   │
│                                                                              │
│  AI LEARNING LOOP:                                                          │
│  System tracks:                                                             │
│  • AI predicted: "proceed" | Human decided: "reject"                        │
│  • Reason: "Overqualified, would leave soon"                                │
│  • Learning signal: AI too optimistic on credentials                        │
│                                                                              │
│  Over time (100+ decisions):                                                │
│  • Pattern detected: AI rejects 40%, humans accept 60% → AI too strict     │
│  • Suggestion: Lower threshold from 70 to 65                                │
│  • HR approves adjustment                                                   │
│  • AI re-calibrates for this company                                        │
│                                                                              │
│  METRICS TRACKED:                                                           │
│  • Agreement rate: 82% (AI and human align)                                 │
│  • Disagreement breakdown:                                                  │
│    - AI rejects, human accepts: 12%                                         │
│    - AI accepts, human rejects: 6%                                          │
│  • Average review time: 2.3 minutes (vs. 15-20 min without AI)             │
│  • False negative rate: 4% (good candidates rejected)                       │
│  • False positive rate: 8% (bad candidates accepted)                        │
│                                                                              │
│  WHY THIS MATTERS:                                                          │
│  • Combines AI speed with human judgment                                    │
│  • Reduces bias (AI provides objective baseline)                            │
│  • Faster decisions (pre-analyzed, not starting from scratch)               │
│  • Continuous improvement (AI learns from corrections)                      │
│  • Audit trail (every decision logged with reasoning)                       │
│                                                                              │
│  COMPLIANCE FEATURES:                                                       │
│  • Random sampling (10%) for bias audits                                    │
│  • Diversity metrics tracked                                                │
│  • Appeal process (candidates can request re-review)                        │
│  • Export decisions for legal review                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ FEATURE 6: n8n INTEGRATION LAYER (700+ APPS) ──────────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Handles ALL third-party integrations through visual workflows,             │
│  replacing hundreds of lines of custom integration code                     │
│                                                                              │
│  WHY n8n vs. MANUAL CODE:                                                   │
│  Manual approach:                                                           │
│  • Write 200+ lines per integration (Slack, Calendar, Email, etc.)          │
│  • Maintain OAuth flows, API changes, rate limits                           │
│  • 10 integrations = 2,000+ lines of code                                   │
│  • Every API update breaks your code                                        │
│                                                                              │
│  n8n approach:                                                              │
│  • Visual workflow builder (drag & drop)                                    │
│  • Pre-built nodes for 700+ apps                                            │
│  • 10 integrations = 10 workflows (5 min each)                              │
│  • n8n team maintains API compatibility                                     │
│                                                                              │
│  CORE WORKFLOWS (Pre-built Templates):                                      │
│                                                                              │
│  1. NEW CANDIDATE NOTIFICATION                                              │
│     Trigger: Webhook from FastAPI (ai_score >= 75)                          │
│     ↓                                                                        │
│     Format message with candidate details                                   │
│     ↓                                                                        │
│     [Split into 3 parallel branches]                                        │
│     ↓              ↓                ↓                                       │
│     Send Slack     Send WhatsApp    Log to Sheet                            │
│     notification   to candidate     (analytics)                             │
│     ↓              ↓                ↓                                       │
│     [All merge]                                                             │
│     ↓                                                                        │
│     Update database status                                                  │
│                                                                              │
│  2. INTERVIEW SCHEDULING                                                    │
│     Trigger: Candidate approved for interview                               │
│     ↓                                                                        │
│     Query Google Calendar for interviewer availability                      │
│     ↓                                                                        │
│     Generate 3 time slot options                                            │
│     ↓                                                                        │
│     Send email to candidate with slots                                      │
│     ↓                                                                        │
│     Wait for candidate reply (webhook)                                      │
│     ↓                                                                        │
│     Book confirmed slot in calendar                                         │
│     ↓                                                                        │
│     [Parallel: Email confirmation + WhatsApp reminder + Slack notify]       │
│     ↓                                                                        │
│     Create Zoom meeting link                                                │
│     ↓                                                                        │
│     Update application record                                               │
│                                                                              │
│  3. BACKGROUND CHECK WORKFLOW (Plugin)                                      │
│     Trigger: HR clicks "Run Background Check"                               │
│     ↓                                                                        │
│     Check if customer has BGV credits                                       │
│     ↓                                                                        │
│     [IF credits available]                                                  │
│     ↓                                                                        │
│     Call SpringVerify API                                                   │
│     (employment + education + criminal)                                     │
│     ↓                                                                        │
│     Wait for webhook callback (results ready)                               │
│     ↓                                                                        │
│     Parse results, extract status                                           │
│     ↓                                                                        │
│     [IF discrepancies found]                                                │
│     ↓                                                                        │
│     Alert HR via Slack (high priority)                                      │
│     ↓                                                                        │
│     Update candidate record                                                 │
│     ↓                                                                        │
│     Deduct credit from customer account                                     │
│                                                                              │
│  4. JOB POSTING AUTOMATION                                                  │
│     Trigger: New job created in system                                      │
│     ↓                                                                        │
│     Format job description                                                  │
│     ↓                                                                        │
│     [Post to multiple platforms in parallel]                                │
│     ↓              ↓              ↓              ↓                          │
│     LinkedIn       Indeed         Naukri.com     AngelList                  │
│     ↓              ↓              ↓              ↓                          │
│     [All complete]                                                          │
│     ↓                                                                        │
│     Store posting URLs                                                      │
│     ↓                                                                        │
│     Notify recruiter via Slack                                              │
│                                                                              │
│  5. CANDIDATE NURTURE SEQUENCE                                              │
│     Trigger: Candidate rejected (but good profile for future)               │
│     ↓                                                                        │
│     Add to "Talent Pool" list                                               │
│     ↓                                                                        │
│     Wait 3 months                                                           │
│     ↓                                                                        │
│     Check if similar jobs opened                                            │
│     ↓                                                                        │
│     [IF relevant job available]                                             │
│     ↓                                                                        │
│     Send email: "Hi, we have a new role that matches your profile"         │
│     ↓                                                                        │
│     Track response                                                          │
│                                                                              │
│  INTEGRATIONS AVAILABLE (700+ Apps):                                        │
│                                                                              │
│  Communication:                                                             │
│  • Slack, Microsoft Teams, Discord                                          │
│  • Twilio (SMS, WhatsApp, Voice)                                            │
│  • SendGrid, Mailgun, Gmail                                                 │
│  • Telegram, Signal                                                         │
│                                                                              │
│  Calendar & Scheduling:                                                     │
│  • Google Calendar, Outlook Calendar                                        │
│  • Calendly, Cal.com                                                        │
│  • Zoom, Google Meet, Microsoft Teams                                       │
│                                                                              │
│  HR & Recruitment:                                                          │
│  • LinkedIn, Indeed, Glassdoor                                              │
│  • BambooHR, Workday, Greenhouse, Lever                                     │
│  • Zoho Recruit, GreytHR, Keka                                              │
│                                                                              │
│  CRM & Sales:                                                               │
│  • HubSpot, Salesforce, Pipedrive                                           │
│  • Zoho CRM, Freshsales                                                     │
│                                                                              │
│  Productivity:                                                              │
│  • Google Sheets, Airtable, Notion                                          │
│  • Trello, Asana, Jira                                                      │
│  • Dropbox, Google Drive, OneDrive                                          │
│                                                                              │
│  Analytics:                                                                 │
│  • Google Analytics, Mixpanel                                               │
│  • Segment, Amplitude                                                       │
│                                                                              │
│  Payments:                                                                  │
│  • Stripe, PayPal, Razorpay                                                 │
│                                                                              │
│  Custom:                                                                    │
│  • HTTP Request (any REST API)                                              │
│  • Webhooks (send/receive)                                                  │
│  • Code nodes (JavaScript/Python)                                           │
│                                                                              │
│  SETUP & USAGE:                                                             │
│  • Runs in Docker container (docker-compose up n8n)                         │
│  • Access at http://localhost:5678                                          │
│  • Visual workflow editor (no code)                                         │
│  • Your FastAPI sends webhooks to n8n                                       │
│  • n8n handles all external integrations                                    │
│  • Results sent back to FastAPI via webhook                                 │
│                                                                              │
│  COST COMPARISON:                                                           │
│  • n8n self-hosted: FREE (unlimited executions)                             │
│  • Zapier: $20-500/month (750-50K tasks)                                    │
│  • Make.com: $9-299/month (10K-100K operations)                             │
│  Annual savings: $1,800-6,000                                               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

[Continuing with remaining features 7-12...]
