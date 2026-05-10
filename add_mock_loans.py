#!/usr/bin/env python3
"""
Add Mock Loans - Create sample loans for testing snapshot functionality
"""

import sys
import os
from datetime import datetime, timedelta

# Add the current directory to path so we can import crm
sys.path.append(os.path.dirname(__file__))

from crm import add_loan

def add_mock_loans():
    """Add sample loans with realistic data for testing."""

    # Calculate some realistic dates
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)
    two_months = today + timedelta(days=60)

    print("Adding mock loans for testing...")

    # Mock Loan 1: Carlos & Diana Reyes - FHA Purchase
    loan1 = add_loan(
        loan_num="LN-2025-001",
        borrower="Carlos & Diana Reyes",
        status="Processing",
        due_date=tomorrow.strftime("%Y-%m-%d"),
        missing_docs="Bank statements (last 60 days), Pay stubs (last 30 days), W-2 forms",
        folder_path="loan_docs/LN-2025-001",
        created_by="test_processor",
        assigned_to="John Processor",
        lock_expiry=next_week.strftime("%Y-%m-%d"),
        closing_date=next_week.strftime("%Y-%m-%d"),
        commitment_date=today.strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Provide paystub for last 30 days", "status": "pending", "due_date": tomorrow.strftime("%Y-%m-%d")},
            {"description": "Provide bank statements for last 60 days", "status": "pending", "due_date": next_week.strftime("%Y-%m-%d")},
            {"description": "Provide W-2 forms for last 2 years", "status": "cleared", "due_date": today.strftime("%Y-%m-%d")}
        ],
        contacts={
            "borrower": {"name": "Carlos Reyes", "phone": "555-123-4567", "email": "carlos@email.com"},
            "co_borrower": {"name": "Diana Reyes", "phone": "555-123-4568", "email": "diana@email.com"},
            "loan_officer": {"name": "Sarah Johnson", "phone": "555-999-0001", "email": "sarah@broker.com"}
        }
    )
    print(f"[+] Added loan: {loan1['borrower']} ({loan1['loan_num']})")

    # Mock Loan 2: Michael Chen - Conventional Refinance
    loan2 = add_loan(
        loan_num="LN-2025-002",
        borrower="Michael Chen",
        status="Underwriting",
        due_date=next_week.strftime("%Y-%m-%d"),
        missing_docs="Tax returns (2023), Credit report authorization",
        folder_path="loan_docs/LN-2025-002",
        created_by="test_processor",
        assigned_to="Jane Underwriter",
        lock_expiry=next_month.strftime("%Y-%m-%d"),
        closing_date=next_month.strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=3)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Provide 2023 tax returns", "status": "pending", "due_date": next_week.strftime("%Y-%m-%d")},
            {"description": "Sign credit report authorization", "status": "pending", "due_date": tomorrow.strftime("%Y-%m-%d")},
            {"description": "Provide divorce decree (if applicable)", "status": "cleared", "due_date": today.strftime("%Y-%m-%d")}
        ],
        contacts={
            "borrower": {"name": "Michael Chen", "phone": "555-234-5678", "email": "michael@email.com"},
            "loan_officer": {"name": "David Smith", "phone": "555-999-0002", "email": "david@broker.com"}
        }
    )
    print(f"[+] Added loan: {loan2['borrower']} ({loan2['loan_num']})")

    # Mock Loan 3: Jennifer & Robert Martinez - VA Purchase
    loan3 = add_loan(
        loan_num="LN-2025-003",
        borrower="Jennifer & Robert Martinez",
        status="Cleared to Close",
        due_date=next_month.strftime("%Y-%m-%d"),
        missing_docs="HOI policy, Survey",
        folder_path="loan_docs/LN-2025-003",
        created_by="test_processor",
        assigned_to="Bob Closer",
        lock_expiry=two_months.strftime("%Y-%m-%d"),
        closing_date=next_month.strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=7)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Provide homeowners insurance policy", "status": "pending", "due_date": next_week.strftime("%Y-%m-%d")},
            {"description": "Order and provide property survey", "status": "pending", "due_date": next_month.strftime("%Y-%m-%d")},
            {"description": "VA Certificate of Eligibility", "status": "cleared", "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d")}
        ],
        contacts={
            "borrower": {"name": "Jennifer Martinez", "phone": "555-345-6789", "email": "jennifer@email.com"},
            "co_borrower": {"name": "Robert Martinez", "phone": "555-345-6790", "email": "robert@email.com"},
            "loan_officer": {"name": "Maria Rodriguez", "phone": "555-999-0003", "email": "maria@broker.com"}
        }
    )
    print(f"[+] Added loan: {loan3['borrower']} ({loan3['loan_num']})")

    # Mock Loan 4: Lisa Thompson - FHA Refinance (Overdue)
    loan4 = add_loan(
        loan_num="LN-2025-004",
        borrower="Lisa Thompson",
        status="Pending",
        due_date=(today - timedelta(days=5)).strftime("%Y-%m-%d"),  # 5 days overdue
        missing_docs="Pay stubs, Bank statements, Gift letter",
        folder_path="loan_docs/LN-2025-004",
        created_by="test_processor",
        assigned_to="John Processor",
        lock_expiry=next_month.strftime("%Y-%m-%d"),
        closing_date=next_month.strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=10)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Provide pay stubs for last 30 days", "status": "overdue", "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d")},
            {"description": "Provide bank statements for last 60 days", "status": "pending", "due_date": tomorrow.strftime("%Y-%m-%d")},
            {"description": "Provide gift letter from parents", "status": "pending", "due_date": next_week.strftime("%Y-%m-%d")}
        ],
        contacts={
            "borrower": {"name": "Lisa Thompson", "phone": "555-456-7890", "email": "lisa@email.com"},
            "loan_officer": {"name": "Tom Wilson", "phone": "555-999-0004", "email": "tom@broker.com"}
        }
    )
    print(f"[+] Added loan: {loan4['borrower']} ({loan4['loan_num']})")

    # Mock Loan 5: David & Sarah Kim - Conventional Purchase
    loan5 = add_loan(
        loan_num="LN-2025-005",
        borrower="David & Sarah Kim",
        status="Closed",
        due_date=(today - timedelta(days=15)).strftime("%Y-%m-%d"),
        missing_docs="",
        folder_path="loan_docs/LN-2025-005",
        created_by="test_processor",
        assigned_to="Jane Closer",
        lock_expiry=(today - timedelta(days=10)).strftime("%Y-%m-%d"),
        closing_date=(today - timedelta(days=15)).strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=20)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "All conditions cleared - loan funded", "status": "cleared", "due_date": (today - timedelta(days=15)).strftime("%Y-%m-%d")}
        ],
        contacts={
            "borrower": {"name": "David Kim", "phone": "555-567-8901", "email": "david@email.com"},
            "co_borrower": {"name": "Sarah Kim", "phone": "555-567-8902", "email": "sarah@email.com"},
            "loan_officer": {"name": "Chris Lee", "phone": "555-999-0005", "email": "chris@broker.com"}
        }
    )
    print(f"[+] Added loan: {loan5['borrower']} ({loan5['loan_num']})")

    # Mock Loan 6: Priya & Anand Patel - Conventional Purchase
    loan6 = add_loan(
        loan_num="LN-2026-006",
        borrower="Priya & Anand Patel",
        status="Pending",
        due_date=(today + timedelta(days=3)).strftime("%Y-%m-%d"),
        missing_docs="Gift letter, Explanation letter for large deposit",
        folder_path="loan_docs/LN-2026-006",
        created_by="test_processor",
        assigned_to="John Processor",
        lock_expiry=(today + timedelta(days=21)).strftime("%Y-%m-%d"),
        closing_date=(today + timedelta(days=18)).strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=2)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Gift letter from borrower's parents", "status": "Pending", "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
            {"description": "Letter of explanation for $12,000 deposit on 04/15", "status": "Pending", "due_date": (today + timedelta(days=3)).strftime("%Y-%m-%d")},
            {"description": "Copy of earnest money check and proof of funds", "status": "Cleared", "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"description": "Homeowners insurance binder", "status": "Requested", "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")},
        ],
        contacts={
            "borrower": {"name": "Priya Patel", "phone": "615-201-4433", "email": "priya.patel@gmail.com"},
            "co_borrower": {"name": "Anand Patel", "phone": "615-201-4434", "email": "anand.patel@gmail.com"},
            "loan_officer": {"name": "Rachel Monroe", "phone": "615-800-1122", "email": "rmonroe@firsthome.com"},
            "realtor": {"name": "Greg Schultz", "phone": "615-555-7788", "email": "greg@nashvillerealty.com"},
        }
    )
    print(f"[+] Added loan: {loan6['borrower']} ({loan6['loan_num']})")

    # Mock Loan 7: Marcus Johnson - FHA Purchase (first-time buyer)
    loan7 = add_loan(
        loan_num="LN-2026-007",
        borrower="Marcus Johnson",
        status="Requested",
        due_date=(today + timedelta(days=10)).strftime("%Y-%m-%d"),
        missing_docs="VOE from employer, 12-month rental history",
        folder_path="loan_docs/LN-2026-007",
        created_by="test_processor",
        assigned_to="Jane Underwriter",
        lock_expiry=(today + timedelta(days=35)).strftime("%Y-%m-%d"),
        closing_date=(today + timedelta(days=32)).strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "Verbal verification of employment", "status": "Requested", "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
            {"description": "12-month rental history from landlord", "status": "Requested", "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")},
            {"description": "Most recent 30-day pay stubs", "status": "Cleared", "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d")},
            {"description": "2023 and 2024 W-2s", "status": "Cleared", "due_date": (today - timedelta(days=4)).strftime("%Y-%m-%d")},
            {"description": "60-day bank statements", "status": "Pending", "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d")},
        ],
        contacts={
            "borrower": {"name": "Marcus Johnson", "phone": "901-338-2291", "email": "marcusj@outlook.com"},
            "loan_officer": {"name": "Tanya Brooks", "phone": "901-800-5533", "email": "tbrooks@mortgagepro.com"},
            "realtor": {"name": "Denise Carr", "phone": "901-555-4411", "email": "denise@midsouthrealty.com"},
        }
    )
    print(f"[+] Added loan: {loan7['borrower']} ({loan7['loan_num']})")

    # Mock Loan 8: Helen & Frank Kowalski - Conventional Refi (rate & term)
    loan8 = add_loan(
        loan_num="LN-2026-008",
        borrower="Helen & Frank Kowalski",
        status="Overdue",
        due_date=(today - timedelta(days=3)).strftime("%Y-%m-%d"),
        missing_docs="2024 tax returns (still outstanding)",
        folder_path="loan_docs/LN-2026-008",
        created_by="test_processor",
        assigned_to="John Processor",
        lock_expiry=(today + timedelta(days=12)).strftime("%Y-%m-%d"),
        closing_date=(today + timedelta(days=14)).strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=8)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "2024 federal tax returns (both borrowers)", "status": "Overdue", "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d")},
            {"description": "Signed 4506-C for 2023 and 2024", "status": "Overdue", "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d")},
            {"description": "Current mortgage statement", "status": "Cleared", "due_date": (today - timedelta(days=6)).strftime("%Y-%m-%d")},
            {"description": "HOI renewal declaration page", "status": "Requested", "due_date": (today + timedelta(days=3)).strftime("%Y-%m-%d")},
        ],
        contacts={
            "borrower": {"name": "Helen Kowalski", "phone": "414-772-0093", "email": "helen.k@yahoo.com"},
            "co_borrower": {"name": "Frank Kowalski", "phone": "414-772-0094", "email": "frank.k@yahoo.com"},
            "loan_officer": {"name": "Steve Paulson", "phone": "414-800-3344", "email": "spaulson@refiplus.com"},
        }
    )
    print(f"[+] Added loan: {loan8['borrower']} ({loan8['loan_num']})")

    # Mock Loan 9: Aaliyah Washington - USDA Rural Purchase
    loan9 = add_loan(
        loan_num="LN-2026-009",
        borrower="Aaliyah Washington",
        status="Cleared",
        due_date=(today + timedelta(days=4)).strftime("%Y-%m-%d"),
        missing_docs="",
        folder_path="loan_docs/LN-2026-009",
        created_by="test_processor",
        assigned_to="Bob Closer",
        lock_expiry=(today + timedelta(days=8)).strftime("%Y-%m-%d"),
        closing_date=(today + timedelta(days=6)).strftime("%Y-%m-%d"),
        commitment_date=(today - timedelta(days=12)).strftime("%Y-%m-%d"),
        conditions=[
            {"description": "USDA Conditional Commitment received", "status": "Cleared", "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d")},
            {"description": "Final inspection certificate", "status": "Cleared", "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d")},
            {"description": "Homeowners insurance binder", "status": "Cleared", "due_date": (today - timedelta(days=3)).strftime("%Y-%m-%d")},
            {"description": "Title commitment", "status": "Cleared", "due_date": (today - timedelta(days=7)).strftime("%Y-%m-%d")},
        ],
        contacts={
            "borrower": {"name": "Aaliyah Washington", "phone": "731-445-8820", "email": "aaliyah.w@gmail.com"},
            "loan_officer": {"name": "Kim Tran", "phone": "731-800-6677", "email": "ktran@ruralloans.com"},
            "realtor": {"name": "Paul Gibbs", "phone": "731-555-9901", "email": "pgibbs@homesteadrealty.com"},
            "title": {"name": "First American Title", "phone": "731-555-2200", "email": "closing@firstam.com"},
        }
    )
    print(f"[+] Added loan: {loan9['borrower']} ({loan9['loan_num']})")

    # Mock Loan 10: Derek & Monica Ruiz - Jumbo Purchase
    loan10 = add_loan(
        loan_num="LN-2026-010",
        borrower="Derek & Monica Ruiz",
        status="Pending",
        due_date=(today + timedelta(days=14)).strftime("%Y-%m-%d"),
        missing_docs="CPA-prepared P&L, Business bank statements (12 mo), Self-employment docs",
        folder_path="loan_docs/LN-2026-010",
        created_by="test_processor",
        assigned_to="Jane Underwriter",
        lock_expiry=(today + timedelta(days=45)).strftime("%Y-%m-%d"),
        closing_date=(today + timedelta(days=42)).strftime("%Y-%m-%d"),
        commitment_date=today.strftime("%Y-%m-%d"),
        conditions=[
            {"description": "CPA-prepared profit & loss statement (YTD)", "status": "Pending", "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d")},
            {"description": "12 months business bank statements", "status": "Pending", "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d")},
            {"description": "Business license / articles of incorporation", "status": "Requested", "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d")},
            {"description": "2022, 2023, 2024 personal tax returns", "status": "Cleared", "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d")},
            {"description": "Asset statements (investment + reserve accounts)", "status": "Cleared", "due_date": (today - timedelta(days=2)).strftime("%Y-%m-%d")},
            {"description": "Signed purchase contract with all addenda", "status": "Cleared", "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d")},
        ],
        contacts={
            "borrower": {"name": "Derek Ruiz", "phone": "512-881-6640", "email": "derek.ruiz@ruizventures.com"},
            "co_borrower": {"name": "Monica Ruiz", "phone": "512-881-6641", "email": "monica.ruiz@gmail.com"},
            "loan_officer": {"name": "Amanda Pierce", "phone": "512-800-9988", "email": "apierce@jumbohome.com"},
            "realtor": {"name": "Carlos Vega", "phone": "512-555-3310", "email": "cvega@luxerealty.com"},
            "title": {"name": "Lone Star Title", "phone": "512-555-7700", "email": "escrow@lonestartitle.com"},
        }
    )
    print(f"[+] Added loan: {loan10['borrower']} ({loan10['loan_num']})")

    print("\n[SUCCESS] Successfully added 10 mock loans for testing!")
    print("\n[TEST SCENARIOS]:")
    print("* LN-2025-001: FHA Purchase - Processing (missing docs)")
    print("* LN-2025-002: Conventional Refinance - Underwriting")
    print("* LN-2025-003: VA Purchase - Cleared to Close")
    print("* LN-2025-004: FHA Refinance - Overdue (5 days past due)")
    print("* LN-2025-005: Conventional Purchase - Closed")
    print("* LN-2026-006: Conventional Purchase - Pending (gift letter + deposit LOE)")
    print("* LN-2026-007: FHA Purchase - Requested (VOE + rental history)")
    print("* LN-2026-008: Conventional Refi - Overdue (tax returns missing)")
    print("* LN-2026-009: USDA Rural Purchase - Cleared to Close")
    print("* LN-2026-010: Jumbo Purchase - Pending (self-employed borrower)")

if __name__ == "__main__":
    add_mock_loans()