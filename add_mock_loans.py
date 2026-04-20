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

    print("\n[SUCCESS] Successfully added 5 mock loans for testing!")
    print("\n[TEST SCENARIOS]:")
    print("* LN-2025-001: FHA Purchase - Processing (missing docs)")
    print("* LN-2025-002: Conventional Refinance - Underwriting")
    print("* LN-2025-003: VA Purchase - Cleared to Close")
    print("* LN-2025-004: FHA Refinance - Overdue (5 days past due)")
    print("* LN-2025-005: Conventional Purchase - Closed")

if __name__ == "__main__":
    add_mock_loans()