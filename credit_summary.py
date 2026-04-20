"""
Credit Summary - Basic Credit Report Import & Summary
Imports credit reports and generates summary analysis.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class CreditSummary:
    """
    Basic credit report import and summary analysis.
    Extracts key information from credit reports and provides risk assessment.
    """

    def __init__(self):
        self.risk_thresholds = {
            "excellent": 750,
            "good": 700,
            "fair": 650,
            "poor": 550
        }

    def summarize(self, credit_text: str) -> Dict[str, Any]:
        """
        Analyze credit report text and generate summary.

        Args:
            credit_text: Raw text from credit report

        Returns:
            Credit summary with scores, flags, and analysis
        """
        summary = {
            "credit_score": None,
            "score_range": None,
            "risk_level": "Unknown",
            "flags": [],
            "tradelines": [],
            "total_accounts": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
            "delinquent_accounts": 0,
            "collections": 0,
            "inquiries": 0,
            "recommendations": [],
            "analysis": ""
        }

        # Extract credit score
        summary["credit_score"] = self._extract_credit_score(credit_text)

        # Determine score range and risk level
        if summary["credit_score"]:
            summary["score_range"] = self._get_score_range(summary["credit_score"])
            summary["risk_level"] = self._assess_risk_level(summary["credit_score"])

        # Extract account information
        account_info = self._extract_account_info(credit_text)
        summary.update(account_info)

        # Check for red flags
        summary["flags"] = self._check_red_flags(credit_text)

        # Extract recent inquiries
        summary["inquiries"] = self._count_recent_inquiries(credit_text)

        # Generate recommendations
        summary["recommendations"] = self._generate_recommendations(summary)

        # Generate overall analysis
        summary["analysis"] = self._generate_analysis(summary)

        return summary

    def _extract_credit_score(self, text: str) -> Optional[int]:
        """Extract credit score from text."""
        # Look for common credit score patterns
        score_patterns = [
            r'credit\s+score[:\s]+(\d{3})',
            r'score[:\s]+(\d{3})',
            r'(\d{3})\s+(?:fico|credit|score)',
            r'fico[:\s]+(\d{3})',
            r'vantage[:\s]+(\d{3})'
        ]

        for pattern in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                if 300 <= score <= 900:  # Valid credit score range
                    return score

        return None

    def _get_score_range(self, score: int) -> str:
        """Get credit score range description."""
        if score >= 800:
            return "Exceptional (800+)"
        elif score >= 740:
            return "Very Good (740-799)"
        elif score >= 670:
            return "Good (670-739)"
        elif score >= 580:
            return "Fair (580-669)"
        else:
            return "Poor (300-579)"

    def _assess_risk_level(self, score: int) -> str:
        """Assess overall risk level based on credit score."""
        if score >= self.risk_thresholds["excellent"]:
            return "Low Risk"
        elif score >= self.risk_thresholds["good"]:
            return "Low-Moderate Risk"
        elif score >= self.risk_thresholds["fair"]:
            return "Moderate Risk"
        elif score >= self.risk_thresholds["poor"]:
            return "High Risk"
        else:
            return "Very High Risk"

    def _extract_account_info(self, text: str) -> Dict[str, Any]:
        """Extract account information from credit report."""
        info = {
            "total_accounts": 0,
            "open_accounts": 0,
            "closed_accounts": 0,
            "delinquent_accounts": 0,
            "tradelines": []
        }

        # Count different account types
        open_keywords = ["open", "current", "active"]
        closed_keywords = ["closed", "paid", "satisfied"]

        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()

            # Count accounts
            if any(keyword in line_lower for keyword in ["account", "tradeline", "card", "loan"]):
                info["total_accounts"] += 1

                if any(keyword in line_lower for keyword in open_keywords):
                    info["open_accounts"] += 1
                elif any(keyword in line_lower for keyword in closed_keywords):
                    info["closed_accounts"] += 1

                # Check for delinquency
                if any(term in line_lower for term in ["late", "delinquent", "past due", "charge-off", "collection"]):
                    info["delinquent_accounts"] += 1

                # Extract tradeline info (simplified)
                tradeline = self._extract_tradeline_info(line)
                if tradeline:
                    info["tradelines"].append(tradeline)

        return info

    def _extract_tradeline_info(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract information from a single tradeline."""
        # This is a simplified extraction - real implementation would be more sophisticated
        tradeline = {}

        # Try to extract creditor name
        creditor_match = re.search(r'([A-Z\s&]+)', line)
        if creditor_match:
            tradeline["creditor"] = creditor_match.group(1).strip()

        # Try to extract balance
        balance_match = re.search(r'\$?([\d,]+\.?\d*)', line)
        if balance_match:
            try:
                tradeline["balance"] = float(balance_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # Check status
        if "current" in line.lower():
            tradeline["status"] = "Current"
        elif "late" in line.lower():
            tradeline["status"] = "Late"
        elif "paid" in line.lower():
            tradeline["status"] = "Paid"

        return tradeline if tradeline else None

    def _check_red_flags(self, text: str) -> List[str]:
        """Check for credit red flags."""
        flags = []
        text_lower = text.lower()

        # Bankruptcy
        if any(term in text_lower for term in ["bankruptcy", "chapter 7", "chapter 13"]):
            flags.append("⚠️ Bankruptcy on record")

        # Foreclosure
        if "foreclosure" in text_lower:
            flags.append("⚠️ Foreclosure on record")

        # High credit utilization
        utilization_match = re.search(r'utilization[:\s]+(\d+)%', text_lower)
        if utilization_match:
            util = int(utilization_match.group(1))
            if util > 30:
                flags.append(f"⚠️ High credit utilization ({util}%)")

        # Multiple late payments
        late_count = len(re.findall(r'\b(?:30|60|90|120)\s+days?\s+(?:past\s+)?due\b', text_lower))
        if late_count > 3:
            flags.append(f"⚠️ Multiple late payments ({late_count} instances)")

        # Recent derogatory marks
        if any(term in text_lower for term in ["charge-off", "repossession", "collections"]):
            flags.append("⚠️ Derogatory marks on record")

        # Too many hard inquiries
        inquiry_count = len(re.findall(r'\b(?:hard\s+)?inquiry\b', text_lower))
        if inquiry_count > 6:
            flags.append(f"⚠️ Excessive hard inquiries ({inquiry_count})")

        return flags

    def _count_recent_inquiries(self, text: str) -> int:
        """Count recent credit inquiries."""
        # Look for inquiry sections
        inquiry_section = re.search(r'inquir(?:y|ies).*?(?=\n\n|\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if inquiry_section:
            inquiry_text = inquiry_section.group(0)
            return len(re.findall(r'\b\d{2}/\d{2}/\d{4}\b', inquiry_text))
        return 0

    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate credit recommendations based on analysis."""
        recommendations = []

        score = summary.get("credit_score")
        if score:
            if score < 620:
                recommendations.append("Consider credit counseling or repair services")
            elif score < 700:
                recommendations.append("Focus on paying down high-interest debt")
            else:
                recommendations.append("Maintain current good credit practices")

        if summary.get("delinquent_accounts", 0) > 0:
            recommendations.append("Address any delinquent accounts immediately")

        if len(summary.get("flags", [])) > 2:
            recommendations.append("Consult with credit counselor for risk mitigation")

        inquiries = summary.get("inquiries", 0)
        if inquiries > 3:
            recommendations.append("Limit new credit applications to avoid score impact")

        return recommendations

    def _generate_analysis(self, summary: Dict[str, Any]) -> str:
        """Generate overall credit analysis."""
        score = summary.get("credit_score")
        risk_level = summary.get("risk_level", "Unknown")
        flags = summary.get("flags", [])

        analysis = f"Credit Score: {score or 'Not found'} ({risk_level}). "

        if flags:
            analysis += f"Found {len(flags)} red flag(s): "
            analysis += ", ".join([flag.replace("⚠️ ", "") for flag in flags[:3]])
            if len(flags) > 3:
                analysis += f" (+{len(flags)-3} more)"
        else:
            analysis += "No major red flags detected."

        return analysis

    def compare_credit_reports(self, report1: Dict, report2: Dict) -> Dict[str, Any]:
        """
        Compare two credit reports (e.g., from different bureaus).

        Returns differences and recommendations.
        """
        comparison = {
            "score_difference": None,
            "score_variance_pct": 0,
            "discrepancies": [],
            "recommendations": []
        }

        score1 = report1.get("credit_score")
        score2 = report2.get("credit_score")

        if score1 and score2:
            comparison["score_difference"] = abs(score1 - score2)
            comparison["score_variance_pct"] = (comparison["score_difference"] / ((score1 + score2) / 2)) * 100

            if comparison["score_variance_pct"] > 50:
                comparison["discrepancies"].append("Significant score difference between reports")
                comparison["recommendations"].append("Order credit reports from all three bureaus")

        # Compare flags
        flags1 = set(report1.get("flags", []))
        flags2 = set(report2.get("flags", []))
        unique_flags = (flags1 - flags2) | (flags2 - flags1)

        if unique_flags:
            comparison["discrepancies"].append(f"Different red flags between reports: {list(unique_flags)}")

        return comparison