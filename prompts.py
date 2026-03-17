"""
Prompt Templates for Processor Traien (Offline Mode)
These are no longer sent to an AI API - they are kept here as reference
for the regex patterns and document type context used in ai_engine.py.
"""

# Document type descriptions (still used by ai_engine.py for context)
DOC_TYPE_CONTEXT = {
    "Approval Letter": "Mortgage approval/commitment letter with conditions to satisfy before closing.",
    "Closing Disclosure (CD)": "Final loan terms, closing costs, and transaction details.",
    "Loan Estimate (LE)": "Estimated loan terms, projected payments, and closing costs.",
    "1003 Application": "Uniform Residential Loan Application with borrower info, employment, assets.",
    "Credit Report": "Credit scores, trade lines, payment history, and inquiries.",
    "Bank Statement": "Account activity, balances, deposits, and withdrawals.",
    "Change of Circumstance (COC)": "Changes to loan terms or fees.",
    "Broker Package (BP)": "Broker disclosures, fee agreements, and compensation details.",
}
