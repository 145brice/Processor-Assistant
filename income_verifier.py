"""
Income Verifier - Full Income/Employment Verification + 1003 Comparison
Compares extracted document data against 1003 loan application data.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class IncomeVerifier:
    """
    Comprehensive income and employment verification system.
    Compares document-extracted data against 1003 application data.
    """

    def __init__(self):
        self.tolerance_pct = 0.05  # 5% tolerance for income variations

    def verify_income(self, extracted: Dict[str, Any], loan_1003: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify income data from documents against 1003 application.

        Args:
            extracted: Data extracted from documents (paystubs, W-2, bank statements)
            loan_1003: Data from 1003 loan application

        Returns:
            Verification results with status and discrepancies
        """
        results = {
            "overall_status": "✅ Verified",
            "income_matches": [],
            "income_discrepancies": [],
            "employment_matches": [],
            "employment_discrepancies": [],
            "warnings": [],
            "recommendations": []
        }

        # Income verification
        income_results = self._verify_income_amounts(extracted, loan_1003)
        results["income_matches"].extend(income_results["matches"])
        results["income_discrepancies"].extend(income_results["discrepancies"])

        # Employment verification
        employment_results = self._verify_employment(extracted, loan_1003)
        results["employment_matches"].extend(employment_results["matches"])
        results["employment_discrepancies"].extend(employment_results["discrepancies"])

        # Asset verification (if available)
        if "assets" in extracted and "assets" in loan_1003:
            asset_results = self._verify_assets(extracted["assets"], loan_1003["assets"])
            results["asset_matches"] = asset_results["matches"]
            results["asset_discrepancies"] = asset_results["discrepancies"]

        # Overall status determination
        total_issues = len(results["income_discrepancies"]) + len(results["employment_discrepancies"])
        if total_issues == 0:
            results["overall_status"] = "✅ Fully Verified"
        elif total_issues <= 2:
            results["overall_status"] = "⚠️ Minor Discrepancies"
            results["recommendations"].append("Review minor income/employment discrepancies with borrower")
        else:
            results["overall_status"] = "❌ Requires Explanation"
            results["recommendations"].append("Obtain written explanation for income/employment discrepancies")
            results["recommendations"].append("May require additional documentation")

        return results

    def _verify_income_amounts(self, extracted: Dict, loan_1003: Dict) -> Dict:
        """Verify income amounts between documents and 1003."""
        results = {"matches": [], "discrepancies": []}

        income_fields = [
            ("monthly_gross_income", "Monthly Gross Income"),
            ("annual_base_salary", "Annual Base Salary"),
            ("overtime_income", "Overtime Income"),
            ("commission_income", "Commission Income"),
            ("bonus_income", "Bonus Income"),
            ("other_income", "Other Income")
        ]

        for field, display_name in income_fields:
            doc_value = extracted.get(field)
            app_value = loan_1003.get(field)

            if doc_value is not None and app_value is not None:
                diff_pct = abs(doc_value - app_value) / max(app_value, 1) * 100

                if diff_pct <= self.tolerance_pct * 100:
                    results["matches"].append(f"{display_name}: ${doc_value:,.0f} matches 1003")
                else:
                    results["discrepancies"].append({
                        "field": display_name,
                        "document_amount": doc_value,
                        "application_amount": app_value,
                        "difference_pct": diff_pct,
                        "status": "⚠️ Significant Difference" if diff_pct > 10 else "⚠️ Minor Difference"
                    })
            elif doc_value is not None and app_value is None:
                results["discrepancies"].append({
                    "field": display_name,
                    "document_amount": doc_value,
                    "application_amount": None,
                    "status": "❌ Not declared on 1003"
                })
            elif doc_value is None and app_value is not None:
                results["discrepancies"].append({
                    "field": display_name,
                    "document_amount": None,
                    "application_amount": app_value,
                    "status": "❌ No supporting documentation"
                })

        return results

    def _verify_employment(self, extracted: Dict, loan_1003: Dict) -> Dict:
        """Verify employment information."""
        results = {"matches": [], "discrepancies": []}

        employment_fields = [
            ("employer_name", "Employer Name"),
            ("job_title", "Job Title"),
            ("employment_start_date", "Employment Start Date"),
            ("years_employed", "Years Employed"),
            ("phone_number", "Employer Phone"),
            ("address", "Employer Address")
        ]

        for field, display_name in employment_fields:
            doc_value = extracted.get(field)
            app_value = loan_1003.get(field)

            if doc_value and app_value:
                if isinstance(doc_value, str) and isinstance(app_value, str):
                    # Fuzzy string matching for names/addresses
                    if self._strings_similar(doc_value, app_value):
                        results["matches"].append(f"{display_name}: Matches")
                    else:
                        results["discrepancies"].append({
                            "field": display_name,
                            "document_value": doc_value,
                            "application_value": app_value,
                            "status": "⚠️ Values don't match"
                        })
                elif doc_value == app_value:
                    results["matches"].append(f"{display_name}: Matches")
                else:
                    results["discrepancies"].append({
                        "field": display_name,
                        "document_value": doc_value,
                        "application_value": app_value,
                        "status": "⚠️ Values don't match"
                    })

        return results

    def _verify_assets(self, doc_assets: Dict, app_assets: Dict) -> Dict:
        """Verify asset information."""
        results = {"matches": [], "discrepancies": []}

        asset_types = ["checking_accounts", "savings_accounts", "investment_accounts", "retirement_accounts"]

        for asset_type in asset_types:
            doc_total = doc_assets.get(asset_type, 0)
            app_total = app_assets.get(asset_type, 0)

            if abs(doc_total - app_total) > 100:  # $100 tolerance
                results["discrepancies"].append({
                    "asset_type": asset_type.replace("_", " ").title(),
                    "document_total": doc_total,
                    "application_total": app_total,
                    "difference": abs(doc_total - app_total),
                    "status": "⚠️ Asset amounts don't match"
                })
            else:
                results["matches"].append(f"{asset_type.replace('_', ' ').title()}: Matches")

        return results

    def _strings_similar(self, str1: str, str2: str) -> bool:
        """Simple string similarity check."""
        str1_clean = re.sub(r'[^\w\s]', '', str1.lower())
        str2_clean = re.sub(r'[^\w\s]', '', str2.lower())

        # Exact match after cleaning
        if str1_clean == str2_clean:
            return True

        # Contains check for partial matches
        return str1_clean in str2_clean or str2_clean in str1_clean

    def generate_verification_report(self, verification_results: Dict) -> str:
        """Generate a formatted verification report."""
        report = []
        report.append("# Income & Employment Verification Report")
        report.append(f"**Overall Status:** {verification_results['overall_status']}")
        report.append("")

        if verification_results["income_matches"]:
            report.append("## ✅ Income Matches")
            for match in verification_results["income_matches"]:
                report.append(f"- {match}")
            report.append("")

        if verification_results["income_discrepancies"]:
            report.append("## ⚠️ Income Discrepancies")
            for disc in verification_results["income_discrepancies"]:
                if isinstance(disc, dict):
                    report.append(f"- **{disc['field']}:** {disc['status']}")
                    if 'difference_pct' in disc:
                        report.append(f"  - Document: ${disc['document_amount']:,.0f}, 1003: ${disc['application_amount']:,.0f} ({disc['difference_pct']:.1f}% difference)")
                else:
                    report.append(f"- {disc}")
            report.append("")

        if verification_results["employment_matches"]:
            report.append("## ✅ Employment Matches")
            for match in verification_results["employment_matches"]:
                report.append(f"- {match}")
            report.append("")

        if verification_results["employment_discrepancies"]:
            report.append("## ⚠️ Employment Discrepancies")
            for disc in verification_results["employment_discrepancies"]:
                if isinstance(disc, dict):
                    report.append(f"- **{disc['field']}:** {disc['status']}")
                else:
                    report.append(f"- {disc}")
            report.append("")

        if verification_results["recommendations"]:
            report.append("## 💡 Recommendations")
            for rec in verification_results["recommendations"]:
                report.append(f"- {rec}")

        return "\n".join(report)