"""
Income Comparator - Compare income on documents vs 1003 and flag differences
Analyzes paystubs, W-2s, bank statements to compare against loan application.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class IncomeComparison:
    """Result of income comparison."""
    status: str
    difference_pct: Optional[float]
    doc_income: Optional[float]
    app_income: Optional[float]
    variance: Optional[float]
    details: list


def parse_dollar_amount(text: str) -> Optional[float]:
    """Extract dollar amount from text."""
    patterns = [
        r'\$\s*([\d,]+\.?\d*)',
        r'([\d,]+\.\d{2})\s*(?:/|\ per| annually| monthly| hr|p/hr)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                continue
    return None


def extract_ytd_income(text: str) -> Optional[float]:
    """Extract YTD income from paystub/W-2 text."""
    patterns = [
        r'(?i)YTD[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?i)YEAR[\s-]?TO[\s-]?DATE[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?i)TOTAL[\s]*(?:EARNINGS|INCOME)[:\s]*\$?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            val = parse_dollar_amount(match.group(1))
            if val and val > 1000:
                return val
    return None


def extract_gross_income(text: str) -> Optional[float]:
    """Extract gross income from paystub."""
    patterns = [
        r'(?i)GROSS[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?i)TOTAL[\s]*(?:PAY|GROSS)[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?i)EARNINGS[:\s]*\$?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            val = parse_dollar_amount(match.group(1))
            if val and val > 100:
                return val
    return None


def annualize_income(amount: float, pay_period: str) -> float:
    """Annualize based on pay period."""
    period_lower = pay_period.lower()
    
    if "biweekly" in period_lower or "every 2" in period_lower:
        return amount * 26
    elif "weekly" in period_lower:
        return amount * 52
    elif "semi-monthly" in period_lower:
        return amount * 24
    elif "monthly" in period_lower:
        return amount * 12
    elif "quarterly" in period_lower:
        return amount * 4
    else:
        return amount


def extract_base_salary(text: str) -> Optional[float]:
    """Extract annual salary."""
    patterns = [
        r'(?i)(?:annual|base|salary)[:\s]*\$?\s*([\d,]+\.?\d*)',
        r'(?i)SALARY[:\s]*\$?\s*([\d,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            val = parse_dollar_amount(match.group(1))
            if val and val > 10000:
                return val
    return None


def calculate_monthly_income(annual: float) -> float:
    """Convert annual to monthly."""
    return annual / 12


def compare_income(
    extracted_income: float,
    loan_application_income: float,
    tolerance: float = 0.10,
    use_monthly: bool = True
) -> IncomeComparison:
    """
    Compare extracted income vs 1003 income.
    
    Args:
        extracted_income: Income extracted from document
        loan_application_income: Income from 1003
        tolerance: Allowable difference (default 10%)
        use_monthly: Compare monthly vs annual
    
    Returns:
        IncomeComparison with status and variance
    """
    if use_monthly:
        doc_monthly = calculate_monthly_income(extracted_income)
        app_monthly = calculate_monthly_income(loan_application_income)
        diff = abs(doc_monthly - app_monthly)
        variance = diff / app_monthly if app_monthly else 0
    else:
        diff = abs(extracted_income - loan_application_income)
        variance = diff / loan_application_income if loan_application_income else 0
    
    details = []
    
    if variance <= tolerance:
        return IncomeComparison(
            status="✅ Matches",
            difference_pct=variance * 100,
            doc_income=extracted_income,
            app_income=loan_application_income,
            variance=variance * 100,
            details=["Income within tolerance range"]
        )
    
    if extracted_income > loan_application_income:
        status = "⚠️ Higher on Document"
        details.append(f"Document shows ${extracted_income:,.0f} vs ${loan_application_income:,.0f} on 1003")
    else:
        status = "⚠️ Lower on Document"
        details.append(f"Document shows ${extracted_income:,.0f} vs ${loan_application_income:,.0f} on 1003")
    
    if variance > 0.25:
        details.append("⚠️ Difference exceeds 25% - requires explanation letter")
    
    return IncomeComparison(
        status=status,
        difference_pct=variance * 100,
        doc_income=extracted_income,
        app_income=loan_application_income,
        variance=variance * 100,
        details=details
    )


def parse_1003_income(text: str) -> dict:
    """Parse income from 1003 text."""
    result = {
        "base_employment": None,
        "overtime": None,
        "bonuses": None,
        "commissions": None,
        "other": None,
    }
    
    base_match = re.search(r'(?i)EMPLOYMENT[\s]*[:\-]?\s*\$?\s*([\d,]+\.?\d*)', text)
    if base_match:
        result["base_employment"] = parse_dollar_amount(base_match.group(1))
    
    ot_match = ref = re.search(r'(?i)OVERTIME[:\s]*\$?\s*([\d,]+\.?\d*)', text)
    if ot_match:
        result["overtime"] = parse_dollar_amount(ot_match.group(1))
    
    bonus_match = re.search(r'(?i)BONUS(?:ES)?[:\s]*\$?\s*([\d,]+\.?\d*)', text)
    if bonus_match:
        result["bonuses"] = parse_dollar_amount(bonus_match.group(1))
    
    comm_match = re.search(r'(?i)COMMISSION(?:S)?[:\s]*\$?\s*([\d,]+\.?\d*)', text)
    if comm_match:
        result["commissions"] = parse_dollar_amount(comm_match.group(1))
    
    return result


def analyze_from_paystub(paystub_text: str, pay_period: str = "biweekly") -> dict:
    """Analyze paystub and calculate annualized income."""
    result = {
        "ytd_income": None,
        "base_income": None,
        "annualized": None,
    }
    
    result["ytd_income"] = extract_ytd_income(paystub_text)
    result["base_income"] = extract_gross_income(paystub_text) or extract_base_salary(paystub_text)
    
    if result["base_income"]:
        result["annualized"] = annualize_income(result["base_income"], pay_period)
    elif result["ytd_income"]:
        result["annualized"] = result["ytd_income"]
    
    return result


def analyze_from_w2(w2_text: str) -> dict:
    """Analyze W-2 and extract wages."""
    result = {
        "wages": None,
        "state_tax": None,
    }
    
    wage_match = re.search(r'(?i)WAGES[:\s]*\$?\s*([\d,]+\.?\d*)', w2_text)
    if wage_match:
        result["wages"] = parse_dollar_amount(wage_match.group(1))
    
    return result


def analyze_from_bank_statement(stmt_text: str) -> dict:
    """Analyze bank statement for recurring deposits."""
    result = {
        "average_monthly_income": None,
        "direct_deposits": [],
    }
    
    deposit_matches = re.findall(
        r'(?i)(?:DIRECT DEPOSIT|DEPOSIT|PAYROLL|ACH CREDIT)[\s]*\$?\s*([\d,]+\.?\d*)',
        stmt_text
    )
    
    amounts = []
    for dm in deposit_matches:
        amt = parse_dollar_amount(dm)
        if amt and amt > 50:
            amounts.append(amt)
    
    if amounts:
        avg = sum(amounts) / len(amounts)
        result["average_monthly_income"] = avg * 2
        result["direct_deposits"] = amounts
    
    return result


def full_comparison(
    paystub_text: str = None,
    w2_text: str = None,
    bank_text: str = None,
    loan_1003_text: str = None,
    app_monthly_income: float = None,
    tolerance: float = 0.10
) -> dict:
    """
    Full income comparison from multiple documents.
    Compares against monthly income from 1003 or provided value.
    """
    doc_incomes = []
    sources = []
    
    if paystub_text:
        paystub_result = analyze_from_paystub(paystub_text)
        if paystub_result.get("annualized"):
            doc_incomes.append(paystub_result["annualized"])
            sources.append("paystub")
    
    if w2_text:
        w2_result = analyze_from_w2(w2_text)
        if w2_result.get("wages"):
            doc_incomes.append(w2_result["wages"])
            sources.append("W-2")
    
    if bank_text:
        bank_result = analyze_from_bank_statement(bank_text)
        if bank_result.get("average_monthly_income"):
            monthly_from_bank = bank_result["average_monthly_income"]
            doc_incomes.append(monthly_from_bank * 12)
            sources.append("bank_statement")
    
    if not doc_incomes or not app_monthly_income:
        return {
            "error": "Missing document text or application income",
            "doc_incomes": doc_incomes,
            "app_income": app_monthly_income,
        }
    
    annual_app_income = app_monthly_income * 12
    
    doc_annual = max(doc_incomes) if doc_incomes else None
    
    if doc_annual:
        comparison = compare_income(doc_annual, annual_app_income, tolerance)
        
        return {
            "comparison": comparison,
            "sources": sources,
            "doc_annual": doc_annual,
            "app_annual": annual_app_income,
            "doc_monthly": doc_annual / 12,
            "app_monthly": app_monthly_income,
        }
    
    return {"error": "Could not extract income from documents"}