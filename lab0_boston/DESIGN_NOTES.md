# The Fort Point Files — DESIGN NOTES (internal)

> INTERNAL calibration document. This is the answer key and evidence map written
> BEFORE the corpus. Do not ship to participants; do not index it. It exists so
> every question's evidence (or deliberate absence of evidence) is auditable.

The Fort Point Files is a work of fiction created for RAG education. Characters, businesses, documents, and all numbers are invented; Boston place names are used fictitiously. Inspired by the Millbrook City RAG Challenge by William Caban (used with permission).

## Cast (all invented)

| Person | Role | Key facts |
|---|---|---|
| Deirdre Fitzgerald, PE | Principal, Harborline Structural Group | MA PE #48291; City Bridge Operations Division 2009–2019; founded firm 2019; sister of Declan |
| Declan Fitzgerald | City Councilor, District 2 | Elected Nov 2025; recused on Docket #0457 (sister's firm) |
| Yolanda Peña | Owner, Gull & Anchor Bakery, 47 Sleeper St | Opened March 2011; widowed (Aurelio, no details); Spanish speaker |
| Camila Peña | Yolanda's daughter, 17 | Co-op intern at Harborline; "C. Peña" in the minutes |
| Wilner Joseph | Owner/Captain, Seaport Skiff Water Taxi | Arrived from Port-au-Prince 2010; launched May 2021; berths behind 486 Congress St; Haitian Creole |
| Grace Yuen | Owner, Golden Terrace Catering (Chinatown) | Founded 2016; deliveries detour via Seaport Blvd; Chinese/English code-switching |
| Priya Raman | Meridian Wharf Holdings LLC / Meridian Wharf Café | Owns 486 Congress St; café opened 2018; hosts the Civic Roundtable |
| Odessa Klein | Committee chair | minutes only |
| Althea Grady | Public Works Commissioner | "within two years" quote in the article |
| Marguerite Osei | Reporter, The Channel Current | byline only |

## Timeline invariants (checked before writing any date)

- Bridge: opened 1908 · closed to vehicles 1997 · closed to ALL users December 2014.
- Assessment submitted May 11, 2026 → closed-to-all elapsed = 11 yr 5 mo (~11.5). Never stated in corpus.
- Bakery opened March 2011; latest doc June/July 2026 → ~15 years. Never stated in corpus (incl. no "quince años" in the Spanish span).
- Deirdre: 2009 → 2019 = 10 years city service. Never stated.
- Inspection fail 2026-01-21, 3-day suspension, re-inspect pass 2026-01-24.
- Minutes May 19, 2026 · Roundtable June 10, 2026 · diary June 14, 2026 · article July 2, 2026.

## The two disagreeing budget figures (category 3 anchor)

- DOC 5 (budget CSV): `Northern Avenue Bridge Rehabilitation - Design & Engineering … 4200000` → **$4,200,000**
- DOC 6 (budget narrative): "commits **$3.65 million** to design and engineering"
- All OTHER numbers agree across both docs (fencing $310,000; Sleeper St $1,250,000; Harborwalk $860,000) so the single disagreement stands out.

Other planted contradictions:
- Construction duration: assessment + minutes "approximately 30 months from notice to proceed" vs article quote "within two years of breaking ground" (24 months).
- Total cost: assessment + minutes "$95 million in 2024 dollars" vs article "$110 million once escalation and contingency are folded in".

## 311 export ground truth (DOC 1) — counted by hand, verify with grep after writing

28 rows total. Columns: case_id, opened, type, queue, location, neighborhood, status, submitted_language, description.

- Rows whose location contains "Northern Avenue Bridge": **9** (rows 1–9: 3× Trespassing on Closed Structure, 2× Barrier/Fence Damage, 2× Debris in Waterway, 1× Streetlight Outage on the approach, 1× Graffiti Removal on the abutment). The string "bridge" appears in NO other row.
- submitted_language ≠ English: **7** = Spanish ×3 (rows 4, 11, 18) + Haitian Creole ×2 (rows 9, 16) + Chinese ×2 (rows 7, 22).
- Status Open: **11** (rows 3, 6, 7, 9, 11, 14, 17, 20, 21, 25, 26); Closed: **17**. (Not asked, recorded for future questions.)
- Aggregation answers: **9A = 9** · **9B = 7 (3 Spanish / 2 Haitian Creole / 2 Chinese)**.

## Question → evidence map (answer key written FIRST)

| id | Category | Question (gist) | Expected answer | Evidence carrier(s) |
|---|---|---|---|---|
| 1A | Ambiguous References | Two Fitzgeralds — who did what at committee | Deirdre presented; Declan (brother, councilor) recused | DOC 3 minutes (both names); DOC 2 bios (sibling link) |
| 1B | Ambiguous References | Which Peña ("C. Peña") spoke at committee | Camila ("C. Peña"), Yolanda's daughter; Yolanda spoke at Roundtable instead | DOC 3 ("C. Peña"); DOC 2 (daughter); DOC 7 (Yolanda at Roundtable); DOC 11 ("twice now") |
| 1C | Ambiguous References | Two Fort Point food establishments; which was inspected | Gull & Anchor (Peña) inspected Jan 21 2026; Meridian Wharf Café (Raman) not | DOC 4 (inspection names bakery only); DOC 2, DOC 8 (café) |
| 2A | Temporal | Closed-to-all elapsed + vehicle closure year | Dec 2014 → ~11.5 yr by May 2026; vehicles 1997 | DOC 10 §2 dates; DOC 9 "fenced off since December 2014". Elapsed time in NO doc |
| 2B | Temporal | How long has Yolanda run the bakery | ~15 years (March 2011 → mid-2026) | DOC 2 (March 2011); DOC 11 date June 14 2026. Duration in NO doc |
| 2C | Temporal | Harborline founded when; city years before | 2019; 2009→2019 = 10 years | DOC 2 Deirdre profile. "10" in NO doc |
| 3A | Contradictory | FY2027 D&E commitment | $4,200,000 (CSV) vs $3.65M (narrative) — both | DOC 5 row 1; DOC 6 ¶1 |
| 3B | Contradictory | Construction duration | 30 months (assessment/minutes) vs "within two years" (article) | DOC 10 §4; DOC 3; DOC 9 Grady quote |
| 3C | Contradictory | Total rehab cost | $95M 2024$ vs $110M w/ escalation+contingency | DOC 10 §4 + DOC 3; DOC 9 |
| 4A | Missing Context | Cause of cooler failure | Not stated — only coded violations (49°F walk-in), suspension, re-pass | DOC 4 carries codes; NO doc carries a cause |
| 4B | Missing Context | Wilner's work before 2021 | Not stated — arrived 2010, launched 2021, gap silent | DOC 2 Wilner profile; nothing else, deliberately |
| 4C | Missing Context | Camila's father | Aurelio deceased; no details anywhere | DOC 11 ("Since he died…"); cause/date in NO doc |
| 5A | Domain Confusion | What PE lets Deirdre do | Professional Engineer, MA #48291 — practice engineering; not phys-ed | DOC 2; DOC 10 title block |
| 5B | Domain Confusion | Chapter 91 License No. 15288 | MA Public Waterfront Act waterways license — float + gangway; not business/liquor | DOC 8 waterways block |
| 5C | Domain Confusion | Is condition rating 2 good | No — NBI 0–9, lower worse, 2 = critical | DOC 10 §3; DOC 3 ("critical … 0–9 scale") |
| 6A | Relationship | Declan ↔ assessment firm | Sister Deirdre's firm authored it; he disclosed + recused | DOC 3; DOC 2 |
| 6B | Relationship | Camila ↔ project (all links) | Daughter of affected owner; Harborline co-op intern; spoke at committee + Roundtable | DOC 2; DOC 3; DOC 7; DOC 11 |
| 6C | Relationship | Wilner → Deirdre degrees | 1 step (both at June 10 Roundtable; also his testimony at May 19 committee); longer path via Raman float/486 Congress | DOC 7; DOC 3; DOC 8 |
| 7A | Multilingual | Non-English languages + speakers | Spanish=Yolanda, Haitian Creole=Wilner, Chinese=Grace (+interpreter) | DOC 7 |
| 7B | Multilingual | Wilner's Creole content vs interpreter | Moved float TWICE since January due to falling debris; interpreter omits "twice/since January" | DOC 7 Creole span + thin interpreter note |
| 8A | Technical | Findings → committee action | rating 2; 60% section loss; fatigue cracks ×6; 1.4 m scour → ped/cyclist-only, $95M, 30 mo; committee 4–0 (1 recusal) | DOC 10 §3–4; DOC 3 |
| 8B | Technical | 311 patterns corroborating assessment | 3 trespass + 2 barrier + 2 debris rows ↔ breached fencing, unauthorized access, fender debris | DOC 1 rows 1–9; DOC 10 §3 |
| 9A | Aggregation & Counting | Rows locating at the bridge | **9** of 28 | DOC 1 rows 1–9 (count above) |
| 9B | Aggregation & Counting | Non-English submissions | **7**: 3 Spanish / 2 Haitian Creole / 2 Chinese | DOC 1 language column (count above) |

## Deliberate non-collisions

- No Millbrook names, businesses, or sentences reused (checked: no Okafor / Vasquez / Chen / Al-Rashid / Romano / Millbrook character strings in the Boston corpus).
- Invented businesses checked against prominent real Boston names: Gull & Anchor Bakery, Meridian Wharf Café, Seaport Skiff Water Taxi, Harborline Structural Group, Golden Terrace Catering, Meridian Wharf Holdings LLC, The Channel Current (outlet), Fort Point Channel Civic Roundtable (distinct from the real Fort Point Neighborhood Association).
- Street addresses (47 Sleeper St, 486 Congress St, 12 Farnsworth St) are fictitious numbers on real streets, covered by the disclaimer.
