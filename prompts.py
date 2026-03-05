"""
AI Prompt Templates for Processor Traien
All prompts for mortgage document analysis.
Uses $variable style for Python substitution to avoid conflicts with curly braces in AI instructions.
"""

SYSTEM_PROMPT = """You are an expert mortgage loan processor with 20+ years of experience.
You analyze mortgage documents with extreme attention to detail.
You output structured, actionable results.
Never include raw PII (SSNs, full account numbers) in your output - reference them only as "present" or "missing".
Always be specific about what you found and what's missing."""

CONDITION_EXTRACTION_PROMPT = """Analyze this $doc_type document and extract ALL conditions that need to be satisfied.

Output each condition as a separate numbered item using this EXACT markdown table format:

| # | Condition | Responsible | Status |
|---|-----------|-------------|--------|
| 1 | [Clear description of what is needed] | [Borrower / Title / Underwriter / Other] | [Needed / Received / Pending / Not Required] |
| 2 | [Next condition] | [Party] | [Status] |

Continue numbering for ALL conditions found in the document.

After the table, if there are any important notes or observations about the conditions, list them as:

**Notes:**
- [Any relevant observation]

Do NOT include risk flags here. If the document is unclear or you cannot extract meaningful data, say so clearly rather than guessing.

DOCUMENT TEXT:
$text"""

BANK_STATEMENT_RULES_PROMPT = """Analyze this bank statement against the following 50 compliance rules.
For EACH rule, output: **Rule #[number]:** [FOUND / MISSING / PARTIAL / N/A] – [brief reason]

RULES:
1. Balance ≥ reserves needed (check if ending balance covers typical 2-3 month reserve requirement)
2. Statement covers at least 60-day span
3. No overdraft occurrences
4. Deposits reasonably match stated income
5. No large unexplained deposits (>50% of monthly income in single deposit)
6. ACH/direct deposit labels present for income
7. No account freeze or hold indicators
8. All pages appear present (check page numbering)
9. Account holder name present and consistent
10. No negative balance days
11. Statement date within 30-60 days of current date
12. Account number present (do NOT output the full number)
13. Borrower name matches throughout
14. Financial institution name and info present
15. No NSF (Non-Sufficient Funds) fees
16. Average daily balance appears reasonable
17. No unexplained wire transfers
18. No cash advance transactions
19. Rent/housing payment pattern visible (if renter)
20. Payroll deposits consistent in timing and amount
21. No gambling-related transactions
22. No cryptocurrency exchange transactions
23. Tax refund deposits (if applicable/seasonal)
24. Child support payments consistent (if applicable)
25. Pension/retirement deposits (if applicable)
26. Dividend/investment income (if applicable)
27. Interest earned entries present
28. No foreign currency transactions (or explained)
29. Account type clearly identified (checking/savings)
30. Joint account holders match application (if joint)
31. Opening balance positive
32. Closing balance positive
33. No charge-off notices
34. No returned deposit items
35. No stop payment orders
36. Statement period dates clearly shown
37. Page count appears complete (no gaps)
38. No handwritten alterations
39. Digital/official formatting appears authentic
40. No redacted or blacked-out information
41. Currency is USD
42. No high-risk merchant transactions
43. Income sources consistent month to month
44. Expense patterns appear normal (no sudden spikes)
45. No unexplained loan payments to unknown entities
46. Savings rate appears reasonable vs income
47. No bankruptcy-related transactions (trustee payments, etc.)
48. Account appears established (not newly opened)
49. No extended dormant periods followed by sudden activity
50. Balance trend stable or upward

After completing all 50 rules, provide:
**SUMMARY:** [X] Found / [Y] Missing / [Z] Partial / [W] N/A
**TOP CONCERNS:** List the top 3 most critical issues found (if any)

BANK STATEMENT TEXT:
$text"""

RISK_FLAG_PROMPT = """Analyze this mortgage document for risk indicators.
Look specifically for:

1. **DTI (Debt-to-Income):** Any mention of DTI ratio. Flag if >43% (QM limit) or >45% (high risk)
2. **Credit Score:** Any FICO or credit score mentioned. Flag if <620 (subprime), warn if <680
3. **LTV (Loan-to-Value):** Any LTV ratio. Flag if >95%, warn if >90%
4. **Income Red Flags:** Gaps in employment, declining income, mismatched amounts
5. **Asset Red Flags:** Insufficient reserves, large undocumented deposits, borrowed funds
6. **Property Red Flags:** Appraisal concerns, title issues, flood zone
7. **Compliance Red Flags:** Missing disclosures, timing violations, TRID issues

For each flag found:
⚠️ **[Category]:** [What was found] – **Severity:** [HIGH / MEDIUM / LOW] – [Recommended action]

If the document is clean, state: ✅ No significant risk flags detected.

DOCUMENT TEXT:
$text"""

EMAIL_DRAFT_PROMPT = """Based on these mortgage conditions, draft a professional email.

RECIPIENT TYPE: $recipient_type
LANGUAGE: $language

CONDITIONS:
$conditions

GUIDELINES:
- For BORROWER emails: Be friendly but clear. List exactly what they need to provide. Give deadlines if apparent.
- For TITLE COMPANY emails: Be professional and specific. Reference file/loan numbers if found.
- For UNDERWRITER emails: Be concise and technical. Reference specific conditions by number.

If language is Spanish, provide the email in Spanish with professional mortgage terminology.

Draft the email with Subject line, greeting, body, and closing. Keep it concise."""

AUTO_EMAIL_PROMPT = """Based on these extracted mortgage conditions, generate ALL necessary emails automatically.

CONDITIONS:
$conditions

For each responsible party that has conditions assigned to them, draft a separate email. Group conditions by responsible party.

Output each email in this format:

---
**TO: [Borrower / Title Company / Underwriter / Other]**

**Subject:** [Professional subject line]

[Email body - professional, clear, listing the specific conditions they are responsible for]

[Professional closing]
---

ALSO provide a Spanish version of the Borrower email if there are borrower conditions.

Label it: **TO: Borrower (Spanish)**

Only draft emails for parties that actually have conditions. If a party has no conditions, skip them."""

WEB_RESEARCH_PROMPT = """Analyze these mortgage conditions and identify which ones require online verification or research.

CONDITIONS:
$conditions

For each condition that could be verified or partially fulfilled through online research, output:

| # | Condition | What to Search | Search URL/Site |
|---|-----------|---------------|-----------------|
| 1 | [condition description] | [what to look up] | [specific URL or site to check] |

Common things to search for:
- **Business licenses / Good standing**: State Secretary of State websites
  - TX: https://mycpa.cpa.state.tx.us/coa/
  - CA: https://bizfileonline.sos.ca.gov/search/business
  - FL: https://search.sunbiz.org/
  - NY: https://appext20.dos.ny.gov/corp_public/CORPSEARCH.ENTITY_SEARCH_ENTRY
  - IL: https://www.ilsos.gov/corporatellc/
- **Property records / Tax assessor**: County assessor websites
- **Flood zone lookup**: https://msc.fema.gov/portal/search
- **FHA case number lookup**: https://entp.hud.gov/clas/
- **NMLS license verification**: https://www.nmlsconsumeraccess.org/
- **Homeowner insurance verification**: Check carrier website
- **HOA verification**: Property management company websites
- **Employment verification**: Company website / LinkedIn
- **Title company verification**: State department of insurance

If no conditions require online research, state: "No conditions require online verification."

Be specific about what to search and where."""

CONTACTS_EXTRACT_PROMPT = """Extract ALL names, contact information, and key parties from this mortgage document.

Output in this EXACT format:

**BORROWER(S):**
| Name | Role | Phone | Email | Address |
|------|------|-------|-------|---------|
| [name] | Primary Borrower | [if found] | [if found] | [if found] |
| [name] | Co-Borrower | [if found] | [if found] | [if found] |

**LOAN DETAILS:**
- Loan Number: [if found]
- Loan Amount: [if found]
- Property Address: [if found]
- Loan Type: [FHA/VA/Conv/USDA if found]
- Interest Rate: [if found]
- Loan Term: [if found]

**OTHER PARTIES:**
| Name / Company | Role | Phone | Email |
|----------------|------|-------|-------|
| [name] | Loan Officer | [if found] | [if found] |
| [name] | Real Estate Agent | [if found] | [if found] |
| [company] | Title Company | [if found] | [if found] |
| [company] | Insurance | [if found] | [if found] |
| [name] | Appraiser | [if found] | [if found] |

If information is not found in the document, write "Not found". Do NOT guess or fabricate contact info.
Do NOT include full SSNs or full account numbers - only indicate "present" or "not found".

DOCUMENT TEXT:
$text"""

STACKING_ORDER_PROMPT = """Based on this mortgage document, generate a complete loan file stacking order checklist.
Determine the loan type (FHA, VA, Conventional, USDA) from the document if possible.

Output a checklist in this EXACT format. Mark each item based on what you can determine from the document:
- [x] = Document appears present or referenced
- [ ] = Document needed / not found
- [~] = Partially present or unclear

**LOAN FILE STACKING ORDER**

**Section 1: Application & Disclosures**
- [ ] Uniform Residential Loan Application (1003)
- [ ] Loan Estimate (LE) - initial
- [ ] Loan Estimate (LE) - revised (if applicable)
- [ ] Closing Disclosure (CD)
- [ ] Intent to Proceed
- [ ] Right to Receive Appraisal
- [ ] Servicing Disclosure
- [ ] ECOA Notice
- [ ] Privacy Policy
- [ ] Patriot Act Disclosure

**Section 2: Credit & Income**
- [ ] Credit Report (tri-merge)
- [ ] Pay stubs (most recent 30 days)
- [ ] W-2s (2 years)
- [ ] Tax Returns (2 years) / 4506-C
- [ ] VOE (Verification of Employment)
- [ ] Self-employment docs (if applicable)
- [ ] Retirement/pension/SS award letters (if applicable)

**Section 3: Assets**
- [ ] Bank Statements (2 months, all pages)
- [ ] Investment/retirement account statements
- [ ] Gift letter + donor bank statement (if applicable)
- [ ] Earnest money deposit verification

**Section 4: Property**
- [ ] Purchase Agreement / Sales Contract
- [ ] Appraisal Report
- [ ] Title Commitment / Preliminary Title Report
- [ ] Survey (if required)
- [ ] Homeowner's Insurance Binder
- [ ] Flood Certification
- [ ] HOA Docs (if applicable)
- [ ] Termite/pest inspection (if required)

**Section 5: Government / Program Specific**
- [ ] FHA Case Number Assignment
- [ ] VA Certificate of Eligibility (COE)
- [ ] USDA Eligibility (if applicable)
- [ ] MI Certificate (if applicable)

**Section 6: Closing**
- [ ] Approval / Commitment Letter
- [ ] Conditions list (prior to docs / prior to funding)
- [ ] Clear to Close (CTC)
- [ ] Closing Instructions
- [ ] Final CD
- [ ] Note
- [ ] Deed of Trust / Mortgage
- [ ] Settlement Statement

Mark items based on what is referenced or present in the document text below. Add notes for anything unusual.

DOCUMENT TEXT:
$text"""

MEGA_CHECKLIST_PROMPT = """You are analyzing a mortgage document. First, auto-detect the document type from the text. Then run through EVERY item on the master checklist below and mark each one.

For EACH item, output a row in this EXACT markdown table format:

| # | Category | Item | Applies? | Status | Note |
|---|----------|------|----------|--------|------|

Where:
- **Applies?** = Yes / No / N/A (does this item pertain to this document at all?)
- **Status** = Found / Missing / Partial / N/A / Unable to Determine
- **Note** = Brief explanation of what was found or why it's missing

At the TOP of your response, output:
**Auto-Detected Document Type:** [what you think this document is]
**Confidence:** [High / Medium / Low]

Then output the full table. Here is the master checklist:

**SECTION 1: LOAN TYPE & PROGRAM (1-15)**
1. Conventional loan indicators
2. FHA loan indicators (case number, MIP, FHA addendums)
3. VA loan indicators (COE, VA funding fee, VA addendums)
4. USDA loan indicators (guarantee fee, rural eligibility)
5. Jumbo / non-conforming loan indicators
6. Fixed rate mortgage
7. Adjustable rate mortgage (ARM) - initial rate, caps, index, margin
8. Interest-only period
9. Balloon payment terms
10. Construction-to-permanent loan
11. Reverse mortgage / HECM
12. Home equity / HELOC
13. Renovation loan (203k / HomeStyle)
14. Down payment assistance (DPA) program
15. State or local housing program (bond program, MCC)

**SECTION 2: PROPERTY TYPE (16-30)**
16. Single family residence (SFR)
17. Condo / condominium
18. Condo - warrantable status
19. Condo - non-warrantable flags
20. Condo - HOA questionnaire / condo cert (Form 1073/1076)
21. PUD (Planned Unit Development)
22. Co-op
23. 2-4 unit / multi-family
24. Manufactured / mobile home (HUD tag, foundation cert)
25. Modular home
26. Mixed-use property
27. Investment property
28. Second home / vacation
29. Primary residence confirmation
30. New construction

**SECTION 3: HOA & CONDO DOCS (31-45)**
31. HOA dues amount and frequency
32. HOA contact info / management company
33. HOA financial statements / budget
34. HOA insurance (master policy)
35. HOA litigation pending
36. HOA delinquency rate (>15% concern)
37. HOA special assessments
38. Condo project approval (Fannie/Freddie/FHA)
39. Condo owner-occupancy ratio
40. Condo commercial space percentage
41. Condo single-entity ownership concentration
42. HOA transfer fee
43. HOA reserves adequacy
44. Condo bylaws / CC&Rs referenced
45. HOA dues included in DTI / escrow

**SECTION 4: INSURANCE (46-70)**
46. Homeowner's / hazard insurance binder
47. Hazard insurance coverage amount (≥ loan amount or replacement cost)
48. Insurance agent / company info
49. Insurance effective date / expiration
50. Flood zone determination (Zone A, AE, V, X, etc.)
51. Flood insurance required (if in flood zone)
52. Flood insurance policy / binder
53. Flood insurance coverage amount
54. NFIP vs private flood insurance
55. Earthquake insurance (if CA, WA, or seismic area)
56. Wind / hurricane insurance (if coastal FL, TX, etc.)
57. Windstorm separate deductible
58. Named storm deductible
59. Volcanic / lava insurance (if HI)
60. Mine subsidence insurance (if applicable)
61. PMI / private mortgage insurance (if LTV > 80% conventional)
62. PMI company and certificate number
63. PMI monthly premium amount
64. MIP / FHA mortgage insurance premium (upfront + monthly)
65. VA funding fee (amount and financed?)
66. USDA guarantee fee
67. Title insurance - lender's policy
68. Title insurance - owner's policy
69. Insurance declarations page present
70. Liability coverage amount

**SECTION 5: TITLE & LEGAL (71-95)**
71. Title commitment / preliminary title report
72. Title company name and contact
73. Title effective date
74. Title exceptions / Schedule B items
75. Liens / judgments found on title
76. Tax liens
77. Mechanic's liens
78. HOA lien
79. Prior mortgage satisfaction / payoff
80. Chain of title clear
81. Legal description present
82. Lot and block / metes and bounds
83. Easements identified
84. Encroachments
85. Survey required / provided
86. Deed type (warranty, quitclaim, special warranty)
87. Vesting / how title is held
88. Power of Attorney (POA) used
89. Trust - property held in trust
90. Trust review / certification needed
91. Estate / probate issues
92. Divorce decree / property settlement
93. Prenuptial / postnuptial agreement
94. Life estate
95. Deed restrictions / covenants

**SECTION 6: BORROWER PROFILE (96-125)**
96. Primary borrower name
97. Co-borrower name(s)
98. SSN present (do NOT output - just mark present/missing)
99. Date of birth
100. Citizenship status (US citizen, permanent resident, non-permanent)
101. First-time homebuyer
102. Marital status
103. Dependents / number
104. Current address / 2-year history
105. Years at current address
106. Phone number
107. Email address
108. Credit score - primary borrower
109. Credit score - co-borrower
110. Credit report date
111. Number of tradelines
112. Derogatory credit items (lates, collections, charge-offs)
113. Bankruptcy history (Ch 7, Ch 13) and discharge date
114. Foreclosure history and date
115. Short sale history
116. Deed-in-lieu history
117. Credit disputes active
118. Authorized user accounts
119. Credit inquiries (last 120 days)
120. Debt-to-income ratio (DTI) - front end
121. Debt-to-income ratio (DTI) - back end
122. Housing payment history (12+ months)
123. Rent verification / VOR
124. Alimony / child support obligations
125. Student loan payment (IBR vs actual)

**SECTION 7: INCOME & EMPLOYMENT (126-155)**
126. Employer name - primary
127. Employer name - co-borrower
128. Job title / position
129. Employment start date
130. Years in same line of work
131. W-2 employee vs self-employed
132. Base income amount
133. Overtime income (2-year average)
134. Bonus income (2-year average)
135. Commission income (2-year average)
136. Self-employment income (2-year average from tax returns)
137. Partnership / S-Corp / sole proprietor
138. 1099 contractor income
139. Rental income (from Schedule E or leases)
140. Social Security / SSI income
141. Pension / retirement income
142. Disability income
143. VA benefits income
144. Alimony / child support income (if used to qualify)
145. Interest / dividend income
146. Trust income
147. Notes receivable income
148. Part-time / second job income
149. Seasonal employment
150. Employment gap > 30 days (explanation needed)
151. VOE (Verification of Employment) present
152. WVOE (Written VOE) present
153. Pay stubs (most recent 30 days)
154. W-2s (2 years)
155. Tax returns / 1040s (2 years)

**SECTION 8: ASSETS & RESERVES (156-175)**
156. Checking account(s) balance
157. Savings account(s) balance
158. Money market balance
159. CD (Certificate of Deposit)
160. 401(k) / IRA / retirement accounts
161. Stocks / bonds / mutual funds
162. Cash value of life insurance
163. Gift funds - gift letter present
164. Gift funds - donor bank statement
165. Gift funds - transfer documentation
166. Seller concessions / credits
167. Earnest money deposit verification
168. Down payment source documented
169. Reserves - 2 months PITI verified
170. Reserves - 6 months (if investment property or multi-unit)
171. Large deposits explained (>50% of monthly income)
172. Business funds used (if self-employed)
173. Proceeds from sale of current home
174. Bridge loan / swing loan
175. Borrowed funds against assets (margin loans)

**SECTION 9: APPRAISAL (176-205)**
176. Appraisal report present
177. Appraisal form type (1004, 1073, 1025, 2055, 1004D)
178. Appraised value
179. Appraiser name and license number
180. Appraisal date
181. Appraisal effective date
182. Subject property condition (C1-C6 rating)
183. Subject property quality (Q1-Q6 rating)
184. Comparable sales (3+ comps)
185. Comparable adjustment net/gross within limits
186. Comp distance from subject (< 1 mile ideal)
187. Comp sale dates (< 6 months ideal)
188. Value reconciliation reasonable
189. GLA (Gross Living Area) matches records
190. Room count / bedroom / bath count
191. Lot size
192. Year built
193. Functional obsolescence
194. External obsolescence
195. Deferred maintenance
196. Health and safety issues
197. Well / septic (if applicable)
198. Environmental hazards noted
199. Access to public road
200. Utilities confirmed (electric, water, sewer/septic)
201. Zoning compliance
202. Highest and best use
203. Declining market indicated
204. Appraisal conditions / requirements
205. Appraisal rebuttal or reconsideration of value (if applicable)

**SECTION 10: APPLICATION & DISCLOSURES (206-230)**
206. Uniform Residential Loan Application (1003) complete
207. Loan Estimate (LE) - initial issued within 3 business days
208. Loan Estimate (LE) - revised (if COC)
209. Closing Disclosure (CD) present
210. CD delivered 3+ business days before closing
211. Intent to Proceed received
212. Right to Receive Appraisal copy
213. Servicing Disclosure
214. ECOA / Adverse Action notice
215. Privacy Policy notice
216. Patriot Act / CIP disclosure
217. HMDA data collected
218. Anti-steering disclosure (if broker)
219. Affiliated Business Arrangement (AfBA) disclosure
220. Credit Score Disclosure notice
221. Fair Lending notice
222. Right of Rescission (if refinance)
223. Occupancy affidavit
224. 4506-C / tax transcript authorization
225. SSA-89 (Social Security verification)
226. Borrower authorization / consent forms
227. Signature and date on all disclosures
228. E-sign consent (if applicable)
229. TRID compliance timing check
230. Change of Circumstance (COC) documentation

**SECTION 11: CLOSING & FUNDING (231-250)**
231. Approval / commitment letter present
232. Conditions list - prior to docs (PTD)
233. Conditions list - prior to funding (PTF)
234. Clear to Close (CTC) issued
235. Closing instructions to title
236. Closing date scheduled
237. Note (promissory note)
238. Deed of Trust / Mortgage
239. Settlement Statement / ALTA
240. Final Closing Disclosure vs initial LE comparison
241. Cash to close amount
242. Wire instructions
243. Funding authorization
244. Trailing documents list
245. Bailee letter (if applicable)
246. Warehouse line / investor delivery
247. Post-closing audit items
248. Compliance review complete
249. QC (Quality Control) pre-funding
250. Investor / agency stacking order complete

DOCUMENT TEXT:
$text"""

# Document type descriptions for the AI
DOC_TYPE_CONTEXT = {
    "Approval Letter": "This is a mortgage approval/commitment letter from a lender or underwriter. It contains conditions that must be satisfied before closing.",
    "Closing Disclosure (CD)": "This is a Closing Disclosure form showing final loan terms, closing costs, and transaction details.",
    "Loan Estimate (LE)": "This is a Loan Estimate showing estimated loan terms, projected payments, and closing costs.",
    "1003 Application": "This is a Uniform Residential Loan Application (1003/Fannie Mae Form) with borrower information, employment, assets, and declarations.",
    "Credit Report": "This is a credit report showing credit scores, trade lines, payment history, and inquiries.",
    "Bank Statement": "This is a bank statement showing account activity, balances, deposits, and withdrawals.",
    "Change of Circumstance (COC)": "This is a Change of Circumstance notice indicating changes to loan terms or fees.",
    "Broker Package (BP)": "This is a broker package containing broker disclosures, fee agreements, and compensation details.",
}
