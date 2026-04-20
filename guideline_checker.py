"""
Investor Guideline Checker (Fannie/Freddie)
Check loans against investor guidelines.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class GuidelineChecker:
    """
    Checks loans against Fannie Mae and Freddie Mac guidelines.
    Validates credit score, DTI, LTV, and other investor requirements.
    """

    # Fannie Mae guidelines (2024)
    FANNIE_GUIDELINES = {
        "credit_score_min": 620,
        "dti_max": 43,
        "ltv_max": {
            "purchase": 97,
            "refinance": 80,
            "cashout": 80
        },
        "reserves_months": 2,
        "housing_ratio_max": 28,
        "employment_length_months": 2
    }

    # Freddie Mac guidelines (2024)
    FREDDIE_GUIDELINES = {
        "credit_score_min": 620,
        "dti_max": 45,
        "ltv_max": {
            "purchase": 97,
            "refinance": 80,
            "cashout": 80
        },
        "reserves_months": 2,
        "housing_ratio_max": 28,
        "employment_length_months": 2
    }

    def __init__(self, investor: str = "fannie"):
        self.investor = investor.lower()
        self.guidelines = self.FANNIE_GUIDELINES if self.investor == "fannie" else self.FREDDIE_GUIDELINES

    def check(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check loan data against investor guidelines.

        Args:
            loan_data: Dictionary with loan information

        Returns:
            Dictionary with pass/fail status and flags
        """
        flags = []
        warnings = []
        passed = True

        # Check credit score
        credit_score = loan_data.get("credit_score", 0)
        if credit_score and credit_score < self.guidelines["credit_score_min"]:
            flags.append(f"❌ Credit score {credit_score} below {self.investor.title()} minimum {self.guidelines['credit_score_min']}")
            passed = False
        elif credit_score and credit_score < 680:
            warnings.append(f"⚠️ Credit score {credit_score} may require manual underwriter approval")

        # Check DTI
        dti = loan_data.get("dti_ratio", 0)
        if dti and dti > self.guidelines["dti_max"]:
            flags.append(f"❌ DTI {dti:.1f}% exceeds {self.investor.title()} maximum {self.guidelines['dti_max']}%")
            passed = False
        elif dti and dti > 36:
            warnings.append(f"⚠️ DTI {dti:.1f}% is high but may be acceptable with compensating factors")

        # Check LTV
        ltv = loan_data.get("ltv_ratio", 0)
        loan_type = loan_data.get("loan_type", "purchase").lower()
        ltv_max = self.guidelines["ltv_max"].get(loan_type, 80)

        if ltv and ltv > ltv_max:
            flags.append(f"❌ LTV {ltv:.1f}% exceeds {self.investor.title()} maximum {ltv_max}% for {loan_type}")
            passed = False

        # Check reserves
        reserves = loan_data.get("reserves_months", 0)
        if reserves is not None and reserves < self.guidelines["reserves_months"]:
            warnings.append(f"⚠️ Reserves {reserves} months below {self.investor.title()} minimum {self.guidelines['reserves_months']} months")

        # Check housing ratio
        housing_ratio = loan_data.get("housing_ratio", 0)
        if housing_ratio and housing_ratio > self.guidelines["housing_ratio_max"]:
            flags.append(f"❌ Housing ratio {housing_ratio:.1f}% exceeds {self.investor.title()} maximum {self.guidelines['housing_ratio_max']}%")
            passed = False

        # Employment check
        employment_months = loan_data.get("employment_length_months", 0)
        if employment_months and employment_months < self.guidelines["employment_length_months"]:
            warnings.append(f"⚠️ Employment length {employment_months} months below {self.guidelines['employment_length_months']} month minimum")

        return {
            "status": "✅ PASS" if passed else "❌ FAIL",
            "investor": self.investor.title(),
            "passed": passed,
            "flags": flags,
            "warnings": warnings,
            "guidelines_used": self.guidelines
        }

    def get_requirements_summary(self) -> str:
        """Get a summary of investor requirements."""
        g = self.guidelines
        return f"""
{self.investor.title()} Mae Guidelines:
- Credit Score: {g['credit_score_min']}+
- DTI Max: {g['dti_max']}%
- LTV Max: {g['ltv_max']}%
- Reserves: {g['reserves_months']} months
- Housing Ratio: {g['housing_ratio_max']}%
- Employment: {g['employment_length_months']}+ months
""".strip()


def check_investor_guidelines(loan_data: Dict, investor: str = "fannie") -> Dict[str, Any]:
    """Quick function to check guidelines."""
    checker = GuidelineChecker(investor)
    return checker.check(loan_data)