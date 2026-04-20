"""
Automated Red Flag / Fraud Detector
Scans documents for common fraud indicators.
"""

import re
from typing import Dict, Any, List, Optional


class FraudDetector:
    """
    Scans documents for common fraud indicators and red flags.
    Checks for suspicious patterns that may indicate fraudulent activity.
    """

    def __init__(self):
        self.fraud_indicators = {
            # Income fraud indicators
            "large_deposit": ["large deposit", "unexplained deposit", "suspicious deposit"],
            "income_drop": ["income decrease", "salary drop", "pay cut"],
            "employment_gap": ["unemployed", "gap in employment", "no employment"],

            # Identity fraud indicators
            "ssn_inconsistency": ["different ssn", "multiple ssn", "ssn mismatch"],
            "name_variation": ["name difference", "different name", "alias"],

            # Asset fraud indicators
            "asset_inflation": ["inflated assets", "asset padding", "overstated assets"],
            "recent_account": ["new account", "recently opened", "just opened"],

            # Document fraud indicators
            "altered_document": ["altered", "modified", "tampered", "forged"],
            "inconsistent_dates": ["date mismatch", "different dates", "inconsistent dates"],

            # Application fraud indicators
            "rushed_application": ["rushed", "hurried", "quick close"],
            "high_ltv": ["high ltv", "high ratio", "low down payment"],
        }

    def scan(self, extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan extracted document data for fraud indicators.

        Args:
            extracted_data: Dictionary with extracted document information

        Returns:
            List of fraud flags found
        """
        flags = []

        # Check for large unexplained deposits
        deposits = extracted_data.get("deposits", [])
        for deposit in deposits:
            if isinstance(deposit, dict):
                amount = deposit.get("amount", 0)
                description = deposit.get("description", "").lower()

                # Flag deposits over $5,000 that are unexplained
                if amount > 5000 and not any(term in description for term in ["salary", "payroll", "pay", "income", "refund", "tax"]):
                    flags.append({
                        "type": "large_deposit",
                        "severity": "high",
                        "description": f"Large unexplained deposit: ${amount:,.2f}",
                        "recommendation": "Verify source of funds with borrower"
                    })

        # Check for income inconsistencies
        incomes = extracted_data.get("incomes", [])
        if len(incomes) > 1:
            amounts = [inc.get("amount", 0) for inc in incomes if isinstance(inc, dict)]
            if amounts:
                avg_income = sum(amounts) / len(amounts)
                max_income = max(amounts)
                min_income = min(amounts)

                # Flag if income varies by more than 20%
                if max_income > min_income * 1.2:
                    flags.append({
                        "type": "income_variation",
                        "severity": "medium",
                        "description": f"Income varies significantly (${min_income:,.0f} to ${max_income:,.0f})",
                        "recommendation": "Verify income stability and source"
                    })

        # Check for employment gaps
        employment = extracted_data.get("employment", [])
        if len(employment) > 1:
            # Sort by start date and check for gaps
            try:
                sorted_emp = sorted(employment, key=lambda x: x.get("start_date", "1900-01-01"))
                for i in range(len(sorted_emp) - 1):
                    current_end = sorted_emp[i].get("end_date")
                    next_start = sorted_emp[i + 1].get("start_date")

                    if current_end and next_start:
                        # Calculate gap in months
                        # This is simplified - real implementation would parse dates properly
                        gap_indicator = "gap" in str(current_end).lower() or "gap" in str(next_start).lower()
                        if gap_indicator:
                            flags.append({
                                "type": "employment_gap",
                                "severity": "medium",
                                "description": "Potential employment gap detected",
                                "recommendation": "Verify continuous employment history"
                            })
            except:
                pass

        # Check for asset inconsistencies
        assets = extracted_data.get("assets", [])
        if len(assets) > 1:
            balances = [asset.get("balance", 0) for asset in assets if isinstance(asset, dict)]
            if balances:
                total_assets = sum(balances)

                # Flag if total assets seem unusually high for stated income
                monthly_income = extracted_data.get("monthly_income", 0)
                if monthly_income > 0:
                    asset_to_income_ratio = total_assets / (monthly_income * 12)
                    if asset_to_income_ratio > 10:  # Assets > 10 years of income
                        flags.append({
                            "type": "asset_inflation",
                            "severity": "high",
                            "description": f"Unusually high assets relative to income (ratio: {asset_to_income_ratio:.1f})",
                            "recommendation": "Verify asset sources and documentation"
                        })

        # Check for document tampering indicators
        documents = extracted_data.get("documents", [])
        for doc in documents:
            if isinstance(doc, dict):
                filename = doc.get("filename", "").lower()
                content = doc.get("content", "").lower()

                # Check for signs of alteration
                if any(term in filename or term in content for term in ["copy", "duplicate", "modified", "edited"]):
                    flags.append({
                        "type": "document_alteration",
                        "severity": "high",
                        "description": f"Potential document alteration in {filename}",
                        "recommendation": "Request original documents from source"
                    })

        # Check for identity inconsistencies
        identities = extracted_data.get("identities", [])
        if len(identities) > 1:
            names = [id.get("name", "") for id in identities if isinstance(id, dict)]
            ssns = [id.get("ssn", "") for id in identities if isinstance(id, dict)]

            # Check for different SSNs
            unique_ssns = set(ssns)
            if len(unique_ssns) > 1:
                flags.append({
                    "type": "ssn_inconsistency",
                    "severity": "critical",
                    "description": f"Multiple SSNs found: {', '.join(unique_ssns)}",
                    "recommendation": "Verify identity and SSN with multiple sources"
                })

            # Check for name variations
            unique_names = set(names)
            if len(unique_names) > 1:
                flags.append({
                    "type": "name_variation",
                    "severity": "medium",
                    "description": f"Name variations found: {', '.join(unique_names)}",
                    "recommendation": "Verify identity consistency across documents"
                })

        return flags

    def get_risk_score(self, flags: List[Dict]) -> Dict[str, Any]:
        """Calculate overall fraud risk score from flags."""
        if not flags:
            return {
                "risk_level": "Low",
                "score": 0,
                "description": "No fraud indicators detected"
            }

        # Calculate score based on severity
        score = 0
        severity_weights = {
            "low": 1,
            "medium": 3,
            "high": 5,
            "critical": 10
        }

        for flag in flags:
            severity = flag.get("severity", "low")
            score += severity_weights.get(severity, 1)

        # Determine risk level
        if score >= 15:
            risk_level = "Critical"
            description = "High risk of fraud - additional verification required"
        elif score >= 8:
            risk_level = "High"
            description = "Elevated fraud risk - manual review recommended"
        elif score >= 4:
            risk_level = "Medium"
            description = "Moderate fraud concerns - verify key items"
        else:
            risk_level = "Low"
            description = "Minor concerns - standard verification sufficient"

        return {
            "risk_level": risk_level,
            "score": score,
            "description": description,
            "flag_count": len(flags)
        }

    def generate_fraud_report(self, flags: List[Dict]) -> str:
        """Generate a fraud assessment report."""
        risk_assessment = self.get_risk_score(flags)

        report = []
        report.append("=" * 60)
        report.append("FRAUD RISK ASSESSMENT REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)
        report.append("")

        report.append(f"Overall Risk Level: {risk_assessment['risk_level']}")
        report.append(f"Risk Score: {risk_assessment['score']}")
        report.append(f"Assessment: {risk_assessment['description']}")
        report.append(f"Red Flags Found: {risk_assessment['flag_count']}")
        report.append("")

        if flags:
            report.append("DETAILED FINDINGS:")
            report.append("-" * 40)

            for flag in flags:
                severity = flag.get("severity", "low").upper()
                report.append(f"[{severity}] {flag.get('type', 'Unknown').replace('_', ' ').title()}")
                report.append(f"  Description: {flag.get('description', 'N/A')}")
                report.append(f"  Recommendation: {flag.get('recommendation', 'N/A')}")
                report.append("")
        else:
            report.append("No fraud indicators detected.")
            report.append("Standard verification procedures recommended.")

        report.append("=" * 60)

        return "\n".join(report)


def scan_for_fraud(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Quick function to scan for fraud indicators."""
    detector = FraudDetector()
    return detector.scan(extracted_data)