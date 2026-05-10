#!/usr/bin/env python3
"""Populate realistic scanned-in contacts for all sandbox loans.
Also removes duplicate loans (keeps lowest ID per loan_num).
"""
import sys, os
sys.path.append(os.path.dirname(__file__))
from crm import get_all_loans, update_loan, _load, _save

# ── Full contact sets per loan_num ────────────────────────────────────────────
CONTACTS = {
    "LN-2025-001": {
        "borrower":       {"name": "Carlos Reyes",       "phone": "615-482-3301", "email": "carlos.reyes@gmail.com"},
        "co_borrower":    {"name": "Diana Reyes",         "phone": "615-482-3302", "email": "diana.reyes@gmail.com"},
        "loan_officer":   {"name": "Sarah Johnson",       "phone": "615-800-1001", "email": "sjohnson@firsthomemtg.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Jake Whitfield",      "phone": "615-555-2211", "email": "jake@nashvillehomes.com"},
        "insurance":      {"name": "Diane Pruitt",        "phone": "615-448-7700", "email": "dpruitt@statefarm.com",        "company": "State Farm Insurance"},
        "title":          {"name": "Linda Carmichael",    "phone": "615-321-4400", "email": "lcarmichael@titleworks.com",   "company": "TitleWorks of Tennessee"},
        "appraiser":      {"name": "Greg Holden",         "phone": "615-555-8833", "email": "gholden@midstateappraisal.com","company": "Mid-State Appraisal Group"},
        "employer":       {"name": "HR Dept – Amazon",    "phone": "888-280-4331", "email": "hr-verify@amazon.com",         "company": "Amazon Logistics"},
    },
    "LN-2025-002": {
        "borrower":       {"name": "Marcus Johnson",      "phone": "901-772-5540", "email": "marcusj82@yahoo.com"},
        "co_borrower":    {"name": "Tina Johnson",        "phone": "901-772-5541", "email": "tinaj82@yahoo.com"},
        "loan_officer":   {"name": "David Smith",         "phone": "901-800-2002", "email": "dsmith@memphismortgage.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Carol Simmons",       "phone": "901-555-4422", "email": "csimmons@bluffcityrealty.com"},
        "insurance":      {"name": "Tony Ferrara",        "phone": "901-334-9900", "email": "tferrara@allstate.com",        "company": "Allstate Insurance"},
        "title":          {"name": "Paula Reeves",        "phone": "901-210-5500", "email": "preeves@shelbyco-title.com",   "company": "Shelby County Title Co."},
        "appraiser":      {"name": "Kevin Marsh",         "phone": "901-555-7744", "email": "kmarsh@tristateval.com",       "company": "Tri-State Valuation"},
        "employer":       {"name": "HR – FedEx Corp",     "phone": "800-463-3339", "email": "employment@fedex.com",         "company": "FedEx Corporation"},
    },
    "LN-2025-003": {
        "borrower":       {"name": "Aisha Patel",         "phone": "404-881-6610", "email": "aisha.patel@outlook.com"},
        "loan_officer":   {"name": "Maria Rodriguez",     "phone": "404-800-3003", "email": "mrodriguez@atlantamtg.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Brandon Holt",        "phone": "404-555-6633", "email": "bholt@peachstaterealty.com"},
        "insurance":      {"name": "Sandra Yates",        "phone": "404-229-8800", "email": "syates@progressiveins.com",   "company": "Progressive Insurance"},
        "title":          {"name": "James Wilder",        "phone": "404-510-3300", "email": "jwilder@fulcotitle.com",      "company": "Fulco Title & Escrow"},
        "appraiser":      {"name": "Rhonda Price",        "phone": "404-555-9900", "email": "rprice@atlantaappraisals.com","company": "Atlanta Appraisal Assoc."},
        "employer":       {"name": "HR – Emory Healthcare","phone": "404-778-7777","email": "employment@emoryhealthcare.org","company": "Emory Healthcare"},
    },
    "LN-2025-004": {
        "borrower":       {"name": "Robert Kim",          "phone": "206-554-3310", "email": "robertkim@gmail.com"},
        "co_borrower":    {"name": "Sandra Kim",          "phone": "206-554-3311", "email": "sandrakim@gmail.com"},
        "loan_officer":   {"name": "Tom Wilson",          "phone": "206-800-4004", "email": "twilson@pugetsoundmtg.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Amy Thornton",        "phone": "206-555-8811", "email": "athornton@emeraldcityrealty.com"},
        "insurance":      {"name": "Mark Dugan",          "phone": "206-441-5500", "email": "mdugan@nationwideins.com",    "company": "Nationwide Insurance"},
        "title":          {"name": "Rachel Stern",        "phone": "206-382-4400", "email": "rstern@pnwtitle.com",         "company": "Pacific NW Title Co."},
        "appraiser":      {"name": "Daniel Foss",         "phone": "206-555-7722", "email": "dfoss@seattleappraisers.com","company": "Seattle Appraisal Group"},
        "employer":       {"name": "HR – Boeing",         "phone": "425-965-1234", "email": "employment@boeing.com",       "company": "The Boeing Company"},
    },
    "LN-2024-088": {
        "borrower":       {"name": "Jennifer Morales",    "phone": "602-334-4420", "email": "jmorales@hotmail.com"},
        "loan_officer":   {"name": "Chris Lee",           "phone": "602-800-5005", "email": "clee@desertmtg.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Steven Nunez",        "phone": "602-555-3344", "email": "snunez@arizonarealty.com"},
        "insurance":      {"name": "Carla Webb",          "phone": "602-771-3300", "email": "cwebb@libertymutual.com",    "company": "Liberty Mutual Insurance"},
        "title":          {"name": "Oscar Delaney",       "phone": "602-252-7700", "email": "odelaney@arizonatitle.com",  "company": "Arizona Title Agency"},
        "appraiser":      {"name": "Faye Huang",          "phone": "602-555-6611", "email": "fhuang@valleyvalu.com",      "company": "Valley Valuation LLC"},
        "employer":       {"name": "HR – Banner Health",  "phone": "602-747-4000", "email": "hr@bannerhealth.com",        "company": "Banner Health"},
    },
    "LN-2026-006": {
        "borrower":       {"name": "Priya Patel",         "phone": "615-201-4433", "email": "priya.patel@gmail.com"},
        "co_borrower":    {"name": "Anand Patel",         "phone": "615-201-4434", "email": "anand.patel@gmail.com"},
        "loan_officer":   {"name": "Rachel Monroe",       "phone": "615-800-1122", "email": "rmonroe@firsthome.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Greg Schultz",        "phone": "615-555-7788", "email": "greg@nashvillerealty.com"},
        "insurance":      {"name": "Pam Hollingsworth",   "phone": "615-383-9900", "email": "phollingsworth@farmersins.com","company": "Farmers Insurance"},
        "title":          {"name": "Nancy Booker",        "phone": "615-244-5500", "email": "nbooker@volunteerstatetitle.com","company": "Volunteer State Title"},
        "appraiser":      {"name": "Marcus Webb",         "phone": "615-555-4466", "email": "mwebb@nashappraisals.com",   "company": "Nashville Appraisal Group"},
        "employer":       {"name": "HR – Vanderbilt Univ","phone": "615-322-7311", "email": "hr@vanderbilt.edu",          "company": "Vanderbilt University"},
    },
    "LN-2026-007": {
        "borrower":       {"name": "Marcus Johnson",      "phone": "901-338-2291", "email": "marcusj@outlook.com"},
        "loan_officer":   {"name": "Tanya Brooks",        "phone": "901-800-5533", "email": "tbrooks@mortgagepro.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Denise Carr",         "phone": "901-555-4411", "email": "denise@midsouthrealty.com"},
        "insurance":      {"name": "Victor Okafor",       "phone": "901-522-7700", "email": "vokafor@travelerins.com",    "company": "Travelers Insurance"},
        "title":          {"name": "Beth Cranford",       "phone": "901-525-3300", "email": "bcranford@midtownsettle.com","company": "Midtown Settlement Services"},
        "appraiser":      {"name": "Lee Atkinson",        "phone": "901-555-8833", "email": "latkinson@midsouthappr.com", "company": "Mid-South Appraisers"},
        "employer":       {"name": "HR – Methodist Hospital","phone":"901-516-8274","email": "hr@methodisthealth.org",    "company": "Methodist Le Bonheur Healthcare"},
    },
    "LN-2026-008": {
        "borrower":       {"name": "Helen Kowalski",      "phone": "414-772-0093", "email": "helen.k@yahoo.com"},
        "co_borrower":    {"name": "Frank Kowalski",      "phone": "414-772-0094", "email": "frank.k@yahoo.com"},
        "loan_officer":   {"name": "Steve Paulson",       "phone": "414-800-3344", "email": "spaulson@refiplus.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "insurance":      {"name": "Gail Hoffman",        "phone": "414-276-5500", "email": "ghoffman@ericksonnins.com",  "company": "Erickson Insurance Group"},
        "title":          {"name": "Tom Czerwinski",      "phone": "414-224-6600", "email": "tczerwinski@milwaukeetitle.com","company": "Milwaukee Title LLC"},
        "appraiser":      {"name": "Janet Kopp",          "phone": "414-555-2277", "email": "jkopp@greatlakesval.com",   "company": "Great Lakes Valuation"},
        "employer":       {"name": "HR – Johnson Controls","phone":"414-524-1200", "email": "hr@johnsoncontrols.com",    "company": "Johnson Controls"},
    },
    "LN-2026-009": {
        "borrower":       {"name": "Aaliyah Washington",  "phone": "731-445-8820", "email": "aaliyah.w@gmail.com"},
        "loan_officer":   {"name": "Kim Tran",            "phone": "731-800-6677", "email": "ktran@ruralloans.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Paul Gibbs",          "phone": "731-555-9901", "email": "pgibbs@homesteadrealty.com"},
        "insurance":      {"name": "Donna Treadwell",     "phone": "731-668-4400", "email": "dtreadwell@countryins.com", "company": "Country Insurance & Financial"},
        "title":          {"name": "First American Title – Jackson","phone":"731-424-5500","email":"closing@firstamjackson.com","company":"First American Title"},
        "appraiser":      {"name": "Clint Harper",        "phone": "731-555-3366", "email": "charper@westtnappraiser.com","company": "West TN Appraisal Services"},
        "employer":       {"name": "HR – Jackson-Madison County School","phone":"731-664-2510","email":"hr@jmcss.org","company":"Jackson-Madison County Schools"},
    },
    "LN-2026-010": {
        "borrower":       {"name": "Derek Ruiz",          "phone": "512-881-6640", "email": "derek.ruiz@ruizventures.com"},
        "co_borrower":    {"name": "Monica Ruiz",         "phone": "512-881-6641", "email": "monica.ruiz@gmail.com"},
        "loan_officer":   {"name": "Amanda Pierce",       "phone": "512-800-9988", "email": "apierce@jumbohome.com"},
        "loan_processor": {"name": "Brice Leasure",       "phone": "615-555-0100", "email": "brice@processorassistant.com"},
        "realtor":        {"name": "Carlos Vega",         "phone": "512-555-3310", "email": "cvega@luxerealty.com"},
        "insurance":      {"name": "Patricia Nguyen",     "phone": "512-474-8800", "email": "pnguyen@chubbrealty.com",  "company": "Chubb Insurance"},
        "title":          {"name": "Lone Star Title – Austin","phone":"512-555-7700","email":"escrow@lonestartitle.com","company":"Lone Star Title Company"},
        "appraiser":      {"name": "Harold Quinn",        "phone": "512-555-5544", "email": "hquinn@texashighappr.com", "company": "Texas High-End Appraisals"},
        "employer":       {"name": "Ruiz Ventures LLC (self)","phone":"512-881-6640","email":"derek.ruiz@ruizventures.com","company":"Ruiz Ventures LLC"},
        "cpa":            {"name": "Sylvia Moreno CPA",   "phone": "512-476-3300", "email": "smoreno@austincpa.com",   "company": "Moreno & Associates CPA"},
    },
}

def run():
    loans = _load()

    # Dedupe: keep only the lowest ID per loan_num
    seen = {}
    keep_ids = set()
    for loan in sorted(loans, key=lambda l: l.get("id", 9999)):
        num = loan.get("loan_num", "")
        if num not in seen:
            seen[num] = loan["id"]
            keep_ids.add(loan["id"])

    before = len(loans)
    loans = [l for l in loans if l["id"] in keep_ids]
    after = len(loans)
    print(f"Removed {before - after} duplicate loans. Keeping {after} unique loans.")

    # Apply contacts
    updated = 0
    for loan in loans:
        num = loan.get("loan_num", "")
        if num in CONTACTS:
            loan["contacts"] = CONTACTS[num]
            updated += 1

    _save(loans)
    print(f"Updated contacts on {updated} loans.")
    for loan in loans:
        print(f"  [{loan['id']}] {loan['loan_num']} – {loan['borrower']}")

if __name__ == "__main__":
    run()
