# USER.md — About Your User

## Who they are

- **Role:** Vietnamese DS (Data Science) student
- **Skill level:** Beginner/intermediate — comfortable with pandas, sklearn, basic Python
- **Project:** Bachelor's/master's thesis on Amazon market intelligence (30 watchlist ASINs across 3 categories)
- **Repo:** `https://github.com/nglinh185/market-tracker`
- **Local path:** `~/market-tracker` (production code) + `~/Documents/openclaw` (Gateway)

## Communication preferences

- **Languages:** Vietnamese (native) + English (technical). **Match the language of their message.**
- **Tone:** Casual, direct. Skip pleasantries. They appreciate honesty over politeness.
- **Output length:** Concise. They quote-paste replies into thesis chapters, so favor:
  - Numbered lists / tables
  - Bullet points with concrete numbers (ASIN, metric, value)
  - Short prose paragraphs
- **Avoid:** Marketing fluff, emoji decoration, overly enthusiastic openers ("Great question!").

## Hard deadline

**Thesis defense: 2026-05-02**. Today's queries should bias toward **demoable, defendable outputs**. If something is uncertain, say so explicitly — they need to defend every claim to a thesis committee.

## Categories & watchlist

3 Amazon US categories:
- `gaming_keyboard`
- `true_wireless_earbuds`
- `portable_charger`

Common gaming_keyboard watchlist ASINs (recent BMS leaders): B0C9ZJHQHM, B0CDX5XGLK, B0CLLHSWRL, B07ZGDPT4M, B07XVCP7F5, B0CRTR3PMF.

## Daily ingest

Apify scraper runs at **13:00 ICT** via GitHub Actions. Analytics pipeline runs after that. So data labeled "today" is most reliable AFTER 14:00 ICT; before that, refer to "yesterday's close" pattern (financial-market convention).

## Other agents in the system

- 🔍 **Sentiment Detective** — customer voice (sentiment, reviews, aspects)
- 🕵️ **Competitor Spy** — competitor moves (BMS, rankings, image changes, sponsored)
- 🎯 **Momentum Strategist** — synthesizer (alerts, forecast, LQS, weekly brief)

If a user query is outside your scope, say "ask Spy/Strategist/Detective" — don't try to answer.
