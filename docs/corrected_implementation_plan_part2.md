
┌─ FEATURE 4: [REMOVED FROM MVP - POST-FUNDING FEATURE] ─────────────────────┐
│                                                                              │
│  🚧 LIVE AI-PROCTORED VIDEO INTERVIEWS                                      │
│  (Build after funding - Month 3-6 | Estimated cost: ₹5-10L to build)       │
│                                                                              │
│  WHY NOT IN MVP:                                                            │
│  ❌ Async "record yourself" video is easily cheatable (notes, rehearsal)   │
│  ❌ Live AI proctoring is complex and expensive for MVP                    │
│  ✅ Voice interviews (Feature 3) achieve same goals at zero cost           │
│                                                                              │
│  WHAT THIS WILL BE (Post-Funding):                                          │
│  Real-time video interview with AI proctoring similar to exam platforms    │
│                                                                              │
│  FEATURES (Future):                                                         │
│  • Live video call with AI monitoring candidate                             │
│  • Cheating detection:                                                      │
│    - Face tracking (ensures candidate stays on camera)                      │
│    - Eye movement (detects reading from notes/second screen)                │
│    - Multiple faces detection (someone helping off-camera)                  │
│    - Phone/device detection (computer vision)                               │
│    - Tab switching detection (browser monitoring)                           │
│    - Audio analysis (detects multiple voices)                               │
│    - Background monitoring (flags if someone enters room)                   │
│  • Recording stored for human review                                        │
│  • Real-time transcript generation                                          │
│  • AI analysis post-interview                                               │
│                                                                              │
│  TECHNICAL APPROACH (When Built):                                           │
│                                                                              │
│  Option 1: Build In-House (If funded)                                       │
│  • WebRTC for live video streaming                                          │
│  • MediaPipe (Google open-source) for face detection                        │
│  • YOLO for object detection (phones, multiple people)                      │
│  • OpenCV for eye tracking                                                  │
│  • Daily.co or Agora for managed video infrastructure                       │
│  • Estimated cost: ₹5-10L to build + ₹2-3L/month to operate                │
│                                                                              │
│  Option 2: Integrate Existing Platform (Faster, cheaper)                    │
│  • Mercer Mettl (Indian, proven, used by thousands)                         │
│  • Talview (AI video interviews + proctoring)                               │
│  • HireVue (enterprise, expensive but proven)                               │
│  • InterviewVector (budget-friendly)                                        │
│  • Integrate via n8n: Trigger API → Get results → Store                     │
│  • Cost: ₹100-500 per interview (customer pays, you add margin)            │
│                                                                              │
│  Option 3: Hybrid (Quick MVP post-funding)                                  │
│  • Use Zoom/Google Meet for video call                                      │
│  • AI joins as participant (Zoom bot via API)                               │
│  • Basic monitoring via Zoom API                                            │
│  • Not as sophisticated but works                                           │
│  • Cost: Minimal, leverages existing tools                                  │
│                                                                              │
│  WHY VOICE INTERVIEWS ARE BETTER FOR MVP:                                   │
│                                                                              │
│  ✅ Lower cost: ₹0.50 vs. ₹5-10 per interview                              │
│  ✅ Lower bandwidth: Works on 3G (critical for India)                      │
│  ✅ Less anxiety: Candidates more comfortable on phone                      │
│  ✅ No camera setup: No "bad lighting/background" issues                    │
│  ✅ Easier to scale: Twilio handles infrastructure                          │
│  ✅ Privacy-friendly: Less invasive than video monitoring                   │
│  ✅ Reduces bias: No discrimination based on appearance/home environment    │
│                                                                              │
│  Voice interviews assess what actually matters:                             │
│  • Communication skills ✅                                                  │
│  • Technical knowledge ✅                                                   │
│  • Thought process ✅                                                       │
│  • Confidence & enthusiasm ✅                                               │
│                                                                              │
│  Video monitoring adds:                                                     │
│  • Physical appearance bias ❌ (not relevant for most roles)               │
│  • Home environment bias ❌ (discriminates against poor candidates)        │
│  • Camera quality bias ❌ (unfair to those with old laptops)               │
│  • Privacy concerns ❌ (people uncomfortable being watched)                 │
│                                                                              │
│  SALES STRATEGY:                                                            │
│                                                                              │
│  To customers (MVP):                                                        │
│  "We offer AI voice screening that's proven to be more effective,          │
│  accessible, and less biased than video interviews. For roles requiring    │
│  video assessment, we integrate with industry-standard proctoring          │
│  platforms (Mercer Mettl, Talview). Coming Q3 2026: Our own AI-proctored  │
│  video system with advanced cheating detection."                            │
│                                                                              │
│  To investors:                                                              │
│  "We're starting with voice interviews (proven, scalable, low-cost).       │
│  Our roadmap includes AI-proctored video screening once we have funding    │
│  to build it right. This is a strategic choice - voice interviews achieve  │
│  95% of the value at 1% of the cost. Video is a premium add-on for funded  │
│  growth phase."                                                              │
│                                                                              │
│  COMPETITIVE POSITIONING:                                                   │
│                                                                              │
│  MVP Phase (Weeks 1-8):                                                     │
│  • Resume AI screening ✅                                                   │
│  • Voice interviews ✅                                                      │
│  • Human-in-loop review ✅                                                  │
│  • Complete enough to sell to SMBs                                          │
│                                                                              │
│  Post-Funding (Month 3-6):                                                  │
│  • Add video interviews with AI proctoring                                  │
│  • Now compete with HireVue, Talview at 1/10th the price                   │
│  • Full-featured platform for enterprise customers                          │
│                                                                              │
│  MVP FOCUSES ON:                                                            │
│  ✅ Feature 1: Resume Parsing (spaCy + HuggingFace)                        │
│  ✅ Feature 2: AI Screening (Llama 3.1)                                    │
│  ✅ Feature 3: Voice Interviews (Twilio + Whisper)                         │
│  ✅ Feature 5: Human-in-Loop Review Queue                                  │
│  ✅ Feature 6: n8n Integrations (700+ apps)                                │
│  ✅ Feature 7: Pipeline Dashboard                                          │
│  ✅ Feature 8: Smart Scheduling                                            │
│  ✅ Feature 9: Analytics & Reporting                                       │
│  ✅ Feature 10: Audit Trail & Compliance                                   │
│  ✅ Feature 11: AI Learning & Improvement                                  │
│  ✅ Feature 12: Multi-Channel Communication                                │
│                                                                              │
│  = 11 COMPLETE FEATURES (not 12)                                            │
│  = More than enough to launch and get customers                             │
│  = Add video later when customers ask for it + you have funding            │
│                                                                              │
│  DEMO SCRIPT (For Investors):                                               │
│                                                                              │
│  "Let me show you our AI-HR platform live:                                  │
│                                                                              │
│  [1] Upload Resume - 2 seconds, AI extracts everything                      │
│  [2] AI Screening - 5 seconds, scored 82/100 with explanation               │
│  [3] Voice Interview - Play recording of AI conducting phone screen         │
│      Natural conversation, auto-transcribed, analyzed                       │
│  [4] Human Review - Borderline cases reviewed by HR in 2 minutes            │
│  [5] Scheduled Interview - One click, calendar updated automatically        │
│                                                                              │
│  Total time: 3 minutes vs. 3 days manually.                                 │
│                                                                              │
│  The system runs on my laptop at zero cost today. With funding, we add:    │
│  • Live AI-proctored video interviews (₹5-10L build)                        │
│  • Advanced cheating detection                                              │
│  • Mobile apps                                                              │
│  • Enterprise features                                                      │
│                                                                              │
│  But the core platform you see working today is production-ready and        │
│  generating value immediately."                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

[Continue with Feature 5: Human-in-Loop Review Queue - unchanged...]
