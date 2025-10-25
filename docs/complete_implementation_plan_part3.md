
┌─ FEATURE 7: CANDIDATE PIPELINE MANAGEMENT DASHBOARD ────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Visual Kanban-style board for tracking all candidates through hiring       │
│  stages with drag-drop, filters, and real-time updates                     │
│                                                                              │
│  PIPELINE STAGES (Customizable):                                            │
│  ┌────────┬────────┬──────────┬─────────┬──────────┬─────────┐            │
│  │  NEW   │SCREENING│INTERVIEW │OFFER    │ONBOARDING│  HIRED  │            │
│  │  (45)  │  (23)   │   (8)    │  (2)    │   (1)    │  (15)   │            │
│  ├────────┼────────┼──────────┼─────────┼──────────┼─────────┤            │
│  │┌──────┐│┌──────┐│┌────────┐│┌───────┐│┌────────┐│┌───────┐│            │
│  ││Priya ││││Rahul││││Anita   ││││Amit  ││││Neha   ││││Kiran ││            │
│  ││85/100││││72   ││││Voice In││││Final ││││Docs   ││││✓     ││            │
│  ││2h ago│││Today ││││Tomorrow││││Review││││Pending││││Oct 15││            │
│  │└──────┘│└──────┘│└────────┘│└───────┘│└────────┘│└───────┘│            │
│  │ ...    │ ...    │ ...      │ ...     │ ...      │ ...     │            │
│  └────────┴────────┴──────────┴─────────┴──────────┴─────────┘            │
│                                                                              │
│  CARD DETAILS (Click to expand):                                            │
│  ┌──────────────────────────────────────┐                                  │
│  │ 👤 Priya Sharma                      │                                  │
│  │ 📧 priya@example.com                 │                                  │
│  │ 📱 +91-9876543210                    │                                  │
│  │                                      │                                  │
│  │ 🎯 Applied: Backend Developer        │                                  │
│  │ 📅 2 hours ago                       │                                  │
│  │ 📍 Source: LinkedIn                  │                                  │
│  │                                      │                                  │
│  │ 🤖 AI Score: 85/100 ⭐               │                                  │
│  │ └─ Education: 90                     │                                  │
│  │ └─ Experience: 80                    │                                  │
│  │ └─ Skills: 85                        │                                  │
│  │                                      │                                  │
│  │ 📊 Status: Screening Passed          │                                  │
│  │                                      │                                  │
│  │ 🎬 Actions:                          │                                  │
│  │ [📞 Call] [📧 Email] [📅 Schedule]  │                                  │
│  │ [👁️ View Profile] [❌ Reject]       │                                  │
│  └──────────────────────────────────────┘                                  │
│                                                                              │
│  FILTERS & SEARCH:                                                          │
│  • By job: [Backend Developer ▼]                                            │
│  • By score: [70-100]                                                       │
│  • By source: [LinkedIn] [Indeed] [Referral]                               │
│  • By date: [Last 7 days ▼]                                                │
│  • Search: "Python developers with 3+ years"                                │
│                                                                              │
│  BULK ACTIONS:                                                              │
│  • Select multiple candidates                                               │
│  • Move to stage (e.g., 10 candidates to Interview)                        │
│  • Send bulk email (custom template)                                        │
│  • Export to CSV (for reports)                                              │
│  • Archive old applications                                                 │
│                                                                              │
│  REAL-TIME UPDATES:                                                         │
│  • New candidate appears in "NEW" instantly                                 │
│  • AI score updates in real-time                                            │
│  • Stage changes reflected immediately                                      │
│  • Notifications: "5 new candidates in last hour"                           │
│                                                                              │
│  ANALYTICS WIDGETS (Top of page):                                           │
│  ┌─────────────┬────────────┬──────────────┬─────────────┐                │
│  │   TODAY     │  THIS WEEK │  TIME-TO-HIRE│  ACCEPTANCE │                │
│  │ 12 new      │ 45 new     │   8.5 days   │     78%     │                │
│  │ 8 screened  │ 23 hired   │   ↓ 2.3 days │   ↑ 5%     │                │
│  └─────────────┴────────────┴──────────────┴─────────────┘                │
│                                                                              │
│  DRAG & DROP:                                                               │
│  • Grab candidate card, drag to new stage                                   │
│  • Auto-triggers: Email to candidate, status update, next action           │
│  • Confirmation: "Move Priya to Interview? [Yes] [No]"                     │
│                                                                              │
│  CUSTOMIZATION:                                                             │
│  • Add custom stages ("Technical Test", "Culture Fit Interview")           │
│  • Custom fields per company (Visa status, Notice period)                  │
│  • Color coding by priority/urgency                                         │
│  • Custom card layout                                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ FEATURE 8: SMART SCHEDULING AUTOMATION ────────────────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Automatically finds interview slots, sends invites, handles confirmations, │
│  reschedules, and manages the entire interview calendar                     │
│                                                                              │
│  WORKFLOW (Zero Manual Work):                                               │
│                                                                              │
│  Step 1: TRIGGER                                                            │
│  • Candidate approved for interview                                         │
│  • HR clicks "Schedule Interview" button                                    │
│  • System initiates auto-scheduling                                         │
│                                                                              │
│  Step 2: AVAILABILITY DETECTION                                             │
│  • Query Google Calendar API for interviewer availability                   │
│  • Check next 7 days, 9 AM - 5 PM, weekdays only                           │
│  • Exclude: Existing meetings, buffer time, lunch hours                     │
│  • Find 30-minute slots with 15-min buffer                                  │
│                                                                              │
│  Step 3: CANDIDATE COMMUNICATION                                            │
│  • Email sent with 3 slot options:                                          │
│    "Please select your preferred slot:                                      │
│     1. Oct 25, 2025 at 10:00 AM                                             │
│     2. Oct 25, 2025 at 2:00 PM                                              │
│     3. Oct 26, 2025 at 11:00 AM"                                            │
│  • WhatsApp message with same options                                       │
│  • Unique booking link (one-click confirm)                                  │
│                                                                              │
│  Step 4: CANDIDATE SELECTS SLOT                                             │
│  • Clicks preferred time in email                                           │
│  • System books that slot immediately                                       │
│  • Other slots released back to pool                                        │
│                                                                              │
│  Step 5: CALENDAR CREATION                                                  │
│  • Create Google Calendar event                                             │
│  • Add interviewer + candidate as attendees                                 │
│  • Generate Zoom/Meet link automatically                                    │
│  • Add agenda: "Interview for [Job Title]"                                  │
│  • Set reminders: 1 hour before, 15 min before                             │
│                                                                              │
│  Step 6: CONFIRMATIONS                                                      │
│  Interviewer receives:                                                      │
│  • Google Calendar invite (auto-syncs)                                      │
│  • Slack message: "Interview scheduled with Priya - Oct 25 at 10 AM"       │
│  • Candidate profile link                                                   │
│                                                                              │
│  Candidate receives:                                                        │
│  • Email confirmation with:                                                 │
│    - Date, time, timezone                                                   │
│    - Zoom/Meet link                                                         │
│    - Interviewer name and title                                             │
│    - Company address (if in-person)                                         │
│    - What to prepare                                                        │
│  • WhatsApp reminder                                                        │
│  • Calendar invite (.ics file)                                              │
│                                                                              │
│  Step 7: AUTOMATED REMINDERS                                                │
│  24 hours before:                                                           │
│  • Email: "Reminder: Interview tomorrow at 10 AM"                           │
│  • WhatsApp: Quick reminder message                                         │
│                                                                              │
│  1 hour before:                                                             │
│  • WhatsApp: "Your interview starts in 1 hour. Meeting link: [Zoom]"       │
│  • SMS fallback if WhatsApp fails                                           │
│                                                                              │
│  15 min before:                                                             │
│  • Push notification (if mobile app)                                        │
│  • Final WhatsApp ping                                                      │
│                                                                              │
│  Step 8: NO-SHOW HANDLING                                                   │
│  • If candidate doesn't join 10 min after start                            │
│  • Auto-send: "We missed you. Reschedule at [link]"                        │
│  • Mark in system: "No-show"                                                │
│  • Notify HR via Slack                                                      │
│                                                                              │
│  Step 9: RESCHEDULING                                                       │
│  • Candidate clicks "Reschedule" link in email                             │
│  • Shows new available slots                                                │
│  • Cancels old meeting, books new one                                       │
│  • All parties notified automatically                                       │
│                                                                              │
│  MULTI-ROUND INTERVIEWS:                                                    │
│  • Round 1: Technical (30 min, Engineer)                                    │
│  • Round 2: Managerial (45 min, Hiring Manager)                            │
│  • Round 3: Cultural fit (30 min, HR)                                       │
│  • System schedules all sequentially                                        │
│  • Each round auto-triggers next upon completion                            │
│                                                                              │
│  CONFLICT RESOLUTION:                                                       │
│  • If interviewer suddenly busy, system:                                    │
│    1. Detects calendar conflict                                             │
│    2. Finds alternative slot                                                │
│    3. Proposes to candidate automatically                                   │
│    4. Updates all parties                                                   │
│                                                                              │
│  TIME ZONE HANDLING:                                                        │
│  • Auto-detects candidate timezone                                          │
│  • Displays slots in their local time                                       │
│  • Stores in UTC, shows localized                                           │
│  • "Oct 25, 10 AM IST (7:30 PM PST)"                                        │
│                                                                              │
│  ANALYTICS:                                                                 │
│  • Average time from approval to scheduled: 6 hours                         │
│  • No-show rate: 8%                                                         │
│  • Reschedule rate: 12%                                                     │
│  • Interviewer utilization: 85%                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ FEATURE 9: COMPREHENSIVE ANALYTICS & REPORTING ────────────────────────────┐
│                                                                              │
│  WHAT IT DOES:                                                              │
│  Real-time dashboards showing recruitment KPIs, AI performance,             │
│  diversity metrics, and ROI calculations                                    │
│                                                                              │
│  DASHBOARD SECTIONS:                                                        │
│                                                                              │
│  1. RECRUITMENT FUNNEL                                                      │
│     ┌─────────────────────────────────────┐                                │
│     │ Applications: 1,250                 │                                │
│     │    ↓ 78% passed screening           │                                │
│     │ Screened: 975                       │                                │
│     │    ↓ 45% invited to interview       │                                │
│     │ Interviewed: 439                    │                                │
│     │    ↓ 28% received offers            │                                │
│     │ Offers: 123                         │                                │
│     │    ↓ 82% accepted (industry: 75%)   │                                │
│     │ Hired: 101                          │                                │
│     └─────────────────────────────────────┘                                │
│                                                                              │
│  2. TIME METRICS                                                            │
│     • Time-to-hire: 8.5 days (target: 10 days) ✅                          │
│     • Time-to-screen: 4.2 hours (industry avg: 3 days)                     │
│     • Time-to-interview: 2.3 days                                           │
│     • Time-to-offer: 1.8 days                                               │
│     • Offer-to-acceptance: 5.2 days                                         │
│                                                                              │
│  3. COST ANALYSIS                                                           │
│     • Cost per hire: ₹12,450                                                │
│       - Platform cost: ₹2,500 (subscription)                                │
│       - Voice interviews: ₹350 (Twilio)                                     │
│       - HR time: ₹9,600 (8 hours @ ₹1,200/hr)                              │
│     • ROI vs. manual: 68% cost reduction                                    │
│     • Savings this month: ₹2.8 lakhs                                        │
│                                                                              │
│  4. AI PERFORMANCE                                                          │
│     • Screening accuracy: 84%                                               │
│     • Human-AI agreement: 79%                                               │
│     • False negatives: 6% (good candidates rejected)                        │
│     • False positives: 10% (bad candidates approved)                        │
│     • Avg confidence score: 0.81                                            │
│     • Improvement over last month: +3.2%                                    │
│                                                                              │
│  5. SOURCE EFFECTIVENESS                                                    │
│     ┌─────────────┬──────────┬─────────┬──────────┐                        │
│     │   Source    │ Applied  │  Hired  │   Rate   │                        │
│     ├─────────────┼──────────┼─────────┼──────────┤                        │
│     │ LinkedIn    │   580    │   48    │   8.3%   │                        │
│     │ Referral    │   220    │   32    │  14.5% ⭐│                        │
│     │ Indeed      │   310    │   15    │   4.8%   │                        │
│     │ Naukri      │   140    │    6    │   4.3%   │                        │
│     └─────────────┴──────────┴─────────┴──────────┘                        │
│     Insight: Referrals 3x more effective - incentivize!                     │
│                                                                              │
│  6. DIVERSITY METRICS                                                       │
│     Gender distribution:                                                    │
│     • Male: 68% (applications) → 65% (hired)                                │
│     • Female: 30% → 33% ✅ (improving representation)                       │
│     • Non-binary/Other: 2% → 2%                                             │
│                                                                              │
│     Education background:                                                   │
│     • Tier 1 (IIT/NIT): 22%                                                 │
│     • Tier 2: 45%                                                           │
│     • Tier 3: 28%                                                           │
│     • Non-traditional: 5%                                                   │
│                                                                              │
│     AI bias check: ⚠️                                                       │
│     • Female candidates scored 2.3 points lower on avg                      │
│     • Action: Investigating skill extraction bias                           │
│                                                                              │
│  7. INTERVIEW PERFORMANCE                                                   │
│     Voice interviews:                                                       │
│     • Conducted: 439                                                        │
│     • Avg duration: 8.2 minutes                                             │
│     • Completion rate: 94%                                                  │
│     • Candidate satisfaction: 4.2/5                                         │
│                                                                              │
│     Video interviews:                                                       │
│     • Requested: 123                                                        │
│     • Completed: 108 (88%)                                                  │
│     • Avg completion time: 18 minutes                                       │
│                                                                              │
│  8. HIRING MANAGER SATISFACTION                                             │
│     Survey results (monthly):                                               │
│     • Candidate quality: 4.5/5 ⭐                                           │
│     • Time savings: 4.8/5 ⭐                                                │
│     • Platform ease-of-use: 4.3/5                                           │
│     • Would recommend: 92%                                                  │
│                                                                              │
│  9. PREDICTIVE ANALYTICS                                                    │
│     Based on current trends:                                                │
│     • Forecast: 142 hires next month                                        │
│     • Bottleneck: Interview availability (need 2 more interviewers)        │
│     • Attrition risk: 8 recent hires (low engagement signals)              │
│                                                                              │
│  EXPORT & SHARING:                                                          │
│  • PDF reports (monthly/quarterly)                                          │
│  • CSV exports for external analysis                                        │
│  • Share dashboards with leadership (read-only)                             │
│  • API access for custom reporting                                          │
│                                                                              │
│  COMPLIANCE REPORTS:                                                        │
│  • EEO-1 Report (US)                                                        │
│  • Diversity audit trail                                                    │
│  • AI decision logs (all 1,250 decisions)                                   │
│  • Right-to-explanation records                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

[Features 10-12 and implementation guide coming next...]
