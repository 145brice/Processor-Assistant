"""
Compliance Checker - Compliance Checklist + Flagging System
Checks loan files for regulatory compliance and flags issues.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class ComplianceChecker:
    """
    Comprehensive compliance checking system for mortgage loans.
    Validates regulatory requirements and flags potential issues.
    """

    def __init__(self):
        # Regulatory requirements by loan type
        self.regulatory_requirements = {
            "conventional": {
                "dti_limit": 43,
                "ltv_limit": 97,
                "credit_score_min": 620,
                "reserves_required": 2,
                "seasoning_required": 60,  # days
                "documentation": ["income", "assets", "credit", "property"]
            },
            "fha": {
                "dti_limit": 43,
                "ltv_limit": 96.5,
                "credit_score_min": 580,
                "reserves_required": 3,
                "seasoning_required": 60,
                "documentation": ["income", "assets", "credit", "property", "mortgage_history"]
            },
            "va": {
                "dti_limit": 41,
                "ltv_limit": 100,
                "credit_score_min": None,  # No minimum
                "reserves_required": 2,
                "seasoning_required": 60,
                "documentation": ["income", "assets", "credit", "property", "eligibility"]
            },
            "usda": {
                "dti_limit": 41,
                "ltv_limit": 100,
                "credit_score_min": 640,
                "reserves_required": 2,
                "seasoning_required": 60,
                "documentation": ["income", "assets", "credit", "property", "rural_eligibility"]
            }
        }

        # TRID compliance requirements
        self.trid_requirements = {
            "closing_disclosure": True,
            "loan_estimate": True,
            "good_faith_comparison": True,
            "tolerance_cure": True,
            "redisclosure_triggers": ["changed_circumstance", "apr_increase", "closing_date_change"]
        }

        # HMDA reporting requirements
        self.hmda_thresholds = {
            "loan_amount": 111000,  # 2024 threshold
            "home_improvement": 85000
        }

    def check_compliance(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive compliance check on loan data.

        Args:
            loan_data: Complete loan application data

        Returns:
            Compliance check results with flags and recommendations
        """
        results = {
            "overall_status": "✅ Compliant",
            "compliance_score": 100,
            "flags": [],
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "check_categories": {}
        }

        # Extract loan type and basic info
        loan_type = loan_data.get("loan_type", "conventional").lower()
        requirements = self.regulatory_requirements.get(loan_type, self.regulatory_requirements["conventional"])

        # Perform all compliance checks
        results["check_categories"] = {
            "regulatory": self._check_regulatory_compliance(loan_data, requirements),
            "trid": self._check_trid_compliance(loan_data),
            "hmda": self._check_hmda_reporting(loan_data),
            "fair_lending": self._check_fair_lending(loan_data),
            "documentation": self._check_documentation_compliance(loan_data),
            "underwriting": self._check_underwriting_compliance(loan_data, requirements)
        }

        # Aggregate results
        self._aggregate_results(results)

        return results

    def _check_regulatory_compliance(self, loan_data: Dict, requirements: Dict) -> Dict[str, Any]:
        """Check basic regulatory compliance."""
        checks = {"status": "✅ Compliant", "flags": [], "score": 100}

        # DTI Check
        dti = loan_data.get("dti_ratio", 0)
        dti_limit = requirements["dti_limit"]
        if dti > dti_limit:
            checks["flags"].append(f"⚠️ DTI ratio {dti:.1f}% exceeds {dti_limit}% limit")
            checks["score"] -= 20

        # LTV Check
        ltv = loan_data.get("ltv_ratio", 0)
        ltv_limit = requirements["ltv_limit"]
        if ltv > ltv_limit:
            checks["flags"].append(f"⚠️ LTV ratio {ltv:.1f}% exceeds {ltv_limit}% limit")
            checks["score"] -= 15

        # Credit Score Check
        credit_score = loan_data.get("credit_score")
        min_score = requirements.get("credit_score_min")
        if min_score and credit_score and credit_score < min_score:
            checks["flags"].append(f"❌ Credit score {credit_score} below minimum {min_score}")
            checks["score"] -= 25

        # Reserves Check
        reserves_months = loan_data.get("reserves_months", 0)
        required_reserves = requirements["reserves_required"]
        if reserves_months < required_reserves:
            checks["flags"].append(f"⚠️ Reserves {reserves_months} months below required {required_reserves}")
            checks["score"] -= 10

        if checks["flags"]:
            checks["status"] = "⚠️ Review Required" if checks["score"] > 70 else "❌ Non-Compliant"

        return checks

    def _check_trid_compliance(self, loan_data: Dict) -> Dict[str, Any]:
        """Check TRID (TILA-RESPA) compliance."""
        checks = {"status": "✅ Compliant", "flags": [], "score": 100}

        # Check for required disclosures
        disclosures = loan_data.get("disclosures_provided", [])
        required = ["closing_disclosure", "loan_estimate"]

        for req in required:
            if req not in disclosures:
                checks["flags"].append(f"❌ Missing required disclosure: {req.replace('_', ' ').title()}")
                checks["score"] -= 30

        # Check tolerance compliance
        if loan_data.get("tolerance_violation", False):
            checks["flags"].append("❌ Tolerance violation - redisclosure required")
            checks["score"] -= 25

        # Check timing requirements
        application_date = loan_data.get("application_date")
        cd_provided_date = loan_data.get("closing_disclosure_date")

        if application_date and cd_provided_date:
            days_diff = (cd_provided_date - application_date).days
            if days_diff < 3:
                checks["flags"].append("⚠️ Closing Disclosure provided too early (minimum 3 days)")
                checks["score"] -= 10

        if checks["flags"]:
            checks["status"] = "⚠️ Review Required" if checks["score"] > 70 else "❌ Non-Compliant"

        return checks

    def _check_hmda_reporting(self, loan_data: Dict) -> Dict[str, Any]:
        """Check HMDA reporting requirements."""
        checks = {"status": "✅ Not Required", "flags": [], "score": 100}

        loan_amount = loan_data.get("loan_amount", 0)
        loan_purpose = loan_data.get("loan_purpose", "").lower()

        # Check if HMDA reporting is required
        if loan_amount >= self.hmda_thresholds["loan_amount"]:
            checks["status"] = "📋 HMDA Required"

            # Check for required HMDA data points
            hmda_fields = [
                "applicant_race", "applicant_ethnicity", "applicant_sex",
                "co_applicant_race", "co_applicant_ethnicity", "co_applicant_sex",
                "loan_purpose", "property_type", "occupancy_type"
            ]

            missing_fields = []
            for field in hmda_fields:
                if not loan_data.get(field):
                    missing_fields.append(field.replace("_", " ").title())

            if missing_fields:
                checks["flags"].append(f"⚠️ Missing HMDA data: {', '.join(missing_fields[:3])}")
                checks["score"] -= len(missing_fields) * 5

        return checks

    def _check_fair_lending(self, loan_data: Dict) -> Dict[str, Any]:
        """Check for potential fair lending violations."""
        checks = {"status": "✅ Compliant", "flags": [], "score": 100}

        # Check for pricing disparities
        applicant_rate = loan_data.get("interest_rate", 0)
        similar_loans_avg = loan_data.get("market_rate_average", applicant_rate)

        if abs(applicant_rate - similar_loans_avg) > 0.5:  # 0.5% threshold
            checks["flags"].append("⚠️ Interest rate variance from market average")
            checks["score"] -= 15

        # Check for prohibited discrimination
        protected_classes = ["race", "color", "religion", "national_origin", "sex", "disability", "familial_status"]
        for protected_class in protected_classes:
            if loan_data.get(f"discrimination_{protected_class}", False):
                checks["flags"].append(f"❌ Potential discrimination based on {protected_class}")
                checks["score"] -= 50

        if checks["flags"]:
            checks["status"] = "⚠️ Review Required" if checks["score"] > 50 else "❌ Violation Suspected"

        return checks

    def _check_documentation_compliance(self, loan_data: Dict) -> Dict[str, Any]:
        """Check documentation completeness and compliance."""
        checks = {"status": "✅ Complete", "flags": [], "score": 100}

        loan_type = loan_data.get("loan_type", "conventional").lower()
        required_docs = self.regulatory_requirements.get(loan_type, {}).get("documentation", [])

        provided_docs = loan_data.get("documents_provided", [])

        missing_docs = []
        for req_doc in required_docs:
            if req_doc not in provided_docs:
                missing_docs.append(req_doc.replace("_", " ").title())

        if missing_docs:
            checks["flags"].append(f"❌ Missing required documents: {', '.join(missing_docs)}")
            checks["score"] -= len(missing_docs) * 10

        # Check document authenticity
        if loan_data.get("suspicious_documents", False):
            checks["flags"].append("❌ Suspicious document indicators detected")
            checks["score"] -= 30

        # Check document timeliness
        stale_docs = loan_data.get("stale_documents", [])
        if stale_docs:
            checks["flags"].append(f"⚠️ Outdated documents: {len(stale_docs)} items need refresh")
            checks["score"] -= len(stale_docs) * 5

        if checks["flags"]:
            checks["status"] = "⚠️ Incomplete" if checks["score"] > 60 else "❌ Major Gaps"

        return checks

    def _check_underwriting_compliance(self, loan_data: Dict, requirements: Dict) -> Dict[str, Any]:
        """Check underwriting-specific compliance."""
        checks = {"status": "✅ Compliant", "flags": [], "score": 100}

        # Ability to repay (ATR) check
        monthly_income = loan_data.get("monthly_income", 0)
        monthly_debt = loan_data.get("monthly_debt", 0)
        housing_payment = loan_data.get("housing_payment", 0)

        residual_income = monthly_income - monthly_debt - housing_payment

        # FHA residual income requirements (simplified)
        if loan_data.get("loan_type", "").upper() == "FHA":
            family_size = loan_data.get("family_size", 1)
            required_residual = self._get_fha_residual_income(family_size)

            if residual_income < required_residual:
                shortfall = required_residual - residual_income
                checks["flags"].append(f"⚠️ FHA residual income shortfall: ${shortfall:.0f} per month")
                checks["score"] -= 15

        # Asset verification
        required_reserves = requirements["reserves_required"]
        actual_reserves = loan_data.get("reserves_months", 0)

        if actual_reserves < required_reserves:
            checks["flags"].append(f"⚠️ Insufficient reserves: {actual_reserves} vs {required_reserves} months required")
            checks["score"] -= 10

        if checks["flags"]:
            checks["status"] = "⚠️ Review Required"

        return checks

    def _get_fha_residual_income(self, family_size: int) -> float:
        """Get FHA minimum residual income requirements."""
        requirements = {
            1: 386,   # 1 person
            2: 557,   # 2 persons
            3: 675,   # 3 persons
            4: 793,   # 4 persons
            5: 851    # 5+ persons
        }
        return requirements.get(min(family_size, 5), 851)

    def _aggregate_results(self, results: Dict[str, Any]):
        """Aggregate all category results into overall status."""
        categories = results["check_categories"]
        total_score = 0
        all_flags = []

        for category_name, category_results in categories.items():
            total_score += category_results.get("score", 100)
            all_flags.extend(category_results.get("flags", []))

        # Average score across categories
        avg_score = total_score / len(categories) if categories else 100
        results["compliance_score"] = round(avg_score, 1)

        # Categorize all flags
        errors = [f for f in all_flags if "❌" in f]
        warnings = [f for f in all_flags if "⚠️" in f]

        results["errors"] = errors
        results["warnings"] = warnings
        results["flags"] = all_flags

        # Determine overall status
        if errors:
            results["overall_status"] = "❌ Non-Compliant"
            results["recommendations"].append("Address critical compliance errors before proceeding")
        elif warnings and avg_score < 80:
            results["overall_status"] = "⚠️ Review Required"
            results["recommendations"].append("Review and resolve warning items")
        elif avg_score >= 90:
            results["overall_status"] = "✅ Fully Compliant"
            results["recommendations"].append("All compliance checks passed")
        else:
            results["overall_status"] = "⚠️ Minor Issues"
            results["recommendations"].append("Address minor compliance items")

    def get_compliance_report(self, compliance_results: Dict[str, Any]) -> str:
        """Generate a comprehensive compliance report."""
        report = []
        report.append("# Loan Compliance Check Report")
        report.append(f"**Overall Status:** {compliance_results['overall_status']}")
        report.append(f"**Compliance Score:** {compliance_results['compliance_score']}%")
        report.append("")

        # Category breakdown
        report.append("## Compliance Categories")
        for category_name, category_results in compliance_results["check_categories"].items():
            status = category_results["status"]
            score = category_results["score"]
            flags = category_results.get("flags", [])

            report.append(f"### {category_name.title()}")
            report.append(f"**Status:** {status}")
            report.append(f"**Score:** {score}%")

            if flags:
                report.append("**Issues:**")
                for flag in flags:
                    report.append(f"- {flag}")
            else:
                report.append("*No issues detected*")
            report.append("")

        # Recommendations
        if compliance_results.get("recommendations"):
            report.append("## Recommendations")
            for rec in compliance_results["recommendations"]:
                report.append(f"- {rec}")
            report.append("")

        # Critical issues
        errors = compliance_results.get("errors", [])
        if errors:
            report.append("## Critical Issues (Must Fix)")
            for error in errors:
                report.append(f"- {error}")
            report.append("")

        # Warnings
        warnings = compliance_results.get("warnings", [])
        if warnings:
            report.append("## Warnings (Should Review)")
            for warning in warnings:
                report.append(f"- {warning}")

        return "\n".join(report)