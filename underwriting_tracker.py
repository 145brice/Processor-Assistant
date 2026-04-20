"""
Underwriting Condition Tracker - Automate condition clearing and tracking
Tracks underwriting conditions, matches documents, and monitors completion status.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class UnderwritingConditionTracker:
    """
    Tracks and automates underwriting condition clearing.
    Matches submitted documents to conditions and monitors progress.
    """

    def __init__(self):
        self.condition_types = {
            # Document conditions
            "paystub": ["paystub", "pay stub", "earnings statement", "income verification"],
            "w2": ["w2", "w-2", "wage statement", "tax form"],
            "tax_return": ["tax return", "1040", "income tax", "irs transcript"],
            "bank_statement": ["bank statement", "bank stmt", "checking", "savings", "account statement"],
            "appraisal": ["appraisal", "property valuation", "1004", "1075"],
            "title_report": ["title", "title report", "commitment", "preliminary title"],
            "credit_report": ["credit report", "tri-merge", "credit score", "fico"],
            "id_verification": ["identification", "drivers license", "passport", "government id"],

            # Verification conditions
            "income_verification": ["income verification", "employment verification", "vvoe"],
            "asset_verification": ["asset verification", "deposit verification", "avo"],
            "employment_verification": ["employment verification", "vvoe"],

            # Property conditions
            "flood_certification": ["flood", "flood certification", "flood insurance"],
            "survey": ["survey", "plat", "property survey"],
            "inspection_report": ["inspection", "home inspection", "property inspection"],

            # Legal conditions
            "divorce_decree": ["divorce", "decree", "dissolution"],
            "marriage_certificate": ["marriage", "certificate", "wedding"],
            "power_of_attorney": ["power of attorney", "poa", "attorney"],
            "trust_documents": ["trust", "trust documents", "revocable trust"],

            # Other common conditions
            "gift_letter": ["gift letter", "gift", "donation"],
            "repair_completion": ["repair", "repairs completed", "work completion"],
            "rent_roll": ["rent roll", "rental income", "lease agreements"]
        }

    def track_conditions(self, loan_id: str, conditions: List[Dict], submitted_docs: List[Dict]) -> Dict[str, Any]:
        """
        Track progress on underwriting conditions for a loan.

        Args:
            loan_id: Loan identifier
            conditions: List of condition dictionaries
            submitted_docs: List of submitted document dictionaries

        Returns:
            Tracking results with status updates
        """
        results = {
            "loan_id": loan_id,
            "total_conditions": len(conditions),
            "cleared_conditions": 0,
            "pending_conditions": 0,
            "overdue_conditions": 0,
            "condition_status": [],
            "overall_progress": 0,
            "estimated_completion_date": None
        }

        for condition in conditions:
            condition_result = self._evaluate_condition(condition, submitted_docs)
            results["condition_status"].append(condition_result)

            if condition_result["status"] == "cleared":
                results["cleared_conditions"] += 1
            elif condition_result["status"] == "overdue":
                results["overdue_conditions"] += 1
                results["pending_conditions"] += 1
            else:
                results["pending_conditions"] += 1

        # Calculate overall progress
        if results["total_conditions"] > 0:
            results["overall_progress"] = (results["cleared_conditions"] / results["total_conditions"]) * 100

        # Estimate completion date
        pending_conditions = [c for c in results["condition_status"] if c["status"] == "pending"]
        if pending_conditions:
            avg_days_to_clear = 7  # Assume 7 days average to clear a condition
            results["estimated_completion_date"] = datetime.now() + timedelta(days=len(pending_conditions) * avg_days_to_clear)

        return results

    def _evaluate_condition(self, condition: Dict, submitted_docs: List[Dict]) -> Dict[str, Any]:
        """Evaluate a single condition against submitted documents."""
        condition_text = condition.get("description", "").lower()
        due_date = condition.get("due_date")
        submitted_date = condition.get("submitted_date")

        # Check if already submitted
        if submitted_date:
            status = "cleared"
            days_overdue = 0
        else:
            # Check if overdue
            if due_date:
                try:
                    due_datetime = datetime.fromisoformat(due_date)
                    days_overdue = (datetime.now() - due_datetime).days
                    if days_overdue > 0:
                        status = "overdue"
                    else:
                        status = "pending"
                except:
                    status = "pending"
                    days_overdue = 0
            else:
                status = "pending"
                days_overdue = 0

        # Check for matching documents
        matching_docs = self._find_matching_documents(condition_text, submitted_docs)

        # Determine confidence level
        confidence = len(matching_docs) * 25  # 25% confidence per matching document
        confidence = min(confidence, 100)

        result = {
            "condition_id": condition.get("id"),
            "description": condition.get("description"),
            "status": status,
            "due_date": due_date,
            "days_overdue": days_overdue,
            "matching_documents": len(matching_docs),
            "confidence": confidence,
            "document_details": matching_docs,
            "recommendations": []
        }

        # Generate recommendations
        result["recommendations"] = self._generate_condition_recommendations(result)

        return result

    def _find_matching_documents(self, condition_text: str, submitted_docs: List[Dict]) -> List[Dict]:
        """Find documents that match a condition."""
        matching_docs = []

        for doc in submitted_docs:
            doc_name = doc.get("filename", "").lower()
            doc_type = doc.get("doc_type", "").lower()

            # Check if document type matches condition requirements
            for condition_type, keywords in self.condition_types.items():
                if any(keyword in condition_text for keyword in keywords):
                    # Check if document matches this type
                    if any(keyword in doc_name or keyword in doc_type for keyword in keywords):
                        matching_docs.append({
                            "filename": doc.get("filename"),
                            "doc_type": doc.get("doc_type"),
                            "submitted_date": doc.get("submitted_date"),
                            "match_type": condition_type
                        })
                        break

        return matching_docs

    def _generate_condition_recommendations(self, condition_result: Dict) -> List[str]:
        """Generate recommendations for a condition."""
        recommendations = []

        if condition_result["status"] == "overdue":
            days = condition_result["days_overdue"]
            if days > 7:
                recommendations.append(f"Overdue by {days} days - escalate to borrower immediately")
            else:
                recommendations.append(f"Due in {abs(condition_result.get('days_overdue', 0))} days - follow up with borrower")

        if condition_result["matching_documents"] == 0:
            recommendations.append("No matching documents found - request specific document from borrower")
        elif condition_result["confidence"] < 50:
            recommendations.append("Document match confidence is low - verify document authenticity")

        if condition_result["status"] == "pending":
            recommendations.append("Send reminder email to borrower with specific requirements")

        return recommendations

    def generate_condition_report(self, tracking_results: Dict) -> str:
        """Generate a comprehensive condition tracking report."""
        results = tracking_results

        report = []
        report.append("UNDERWRITING CONDITION TRACKING REPORT")
        report.append("=" * 60)
        report.append(f"Loan ID: {results['loan_id']}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        report.append("SUMMARY:")
        report.append(f"  Total Conditions: {results['total_conditions']}")
        report.append(f"  Cleared: {results['cleared_conditions']}")
        report.append(f"  Pending: {results['pending_conditions']}")
        report.append(f"  Overdue: {results['overdue_conditions']}")
        report.append(".1f")
        report.append("")

        if results.get("estimated_completion_date"):
            report.append(f"Estimated Completion: {results['estimated_completion_date'].strftime('%Y-%m-%d')}")
            report.append("")

        # Detailed condition status
        if results["condition_status"]:
            report.append("CONDITION DETAILS:")
            report.append("-" * 40)

            for condition in results["condition_status"]:
                status_icon = {"cleared": "✅", "pending": "⏳", "overdue": "🚨"}.get(condition["status"], "❓")
                report.append(f"{status_icon} {condition['description'][:60]}...")
                report.append(f"   Status: {condition['status'].title()}")
                report.append(f"   Confidence: {condition['confidence']}%")
                report.append(f"   Matching Docs: {condition['matching_documents']}")

                if condition["recommendations"]:
                    report.append("   Recommendations:")
                    for rec in condition["recommendations"]:
                        report.append(f"     • {rec}")

                report.append("")

        # Overall recommendations
        report.append("OVERALL RECOMMENDATIONS:")
        if results["overdue_conditions"] > 0:
            report.append(f"• Address {results['overdue_conditions']} overdue conditions immediately")
        if results["pending_conditions"] > 0:
            report.append(f"• Follow up on {results['pending_conditions']} pending conditions")
        if results["overall_progress"] >= 80:
            report.append("• Loan is nearly ready for final approval")
        elif results["overall_progress"] < 50:
            report.append("• Significant work remains - prioritize critical conditions")

        return "\n".join(report)

    def prioritize_conditions(self, conditions: List[Dict]) -> List[Dict]:
        """Prioritize conditions by urgency and importance."""
        prioritized = []

        for condition in conditions:
            priority_score = 0

            # Due date priority
            if condition.get("due_date"):
                try:
                    due_date = datetime.fromisoformat(condition["due_date"])
                    days_until_due = (due_date - datetime.now()).days

                    if days_until_due < 0:
                        priority_score += 100  # Overdue
                    elif days_until_due <= 3:
                        priority_score += 80   # Due soon
                    elif days_until_due <= 7:
                        priority_score += 60   # This week
                    elif days_until_due <= 14:
                        priority_score += 40   # This month
                except:
                    pass

            # Condition type priority
            condition_text = condition.get("description", "").lower()
            if any(word in condition_text for word in ["credit", "income", "appraisal"]):
                priority_score += 30  # Core underwriting conditions
            elif any(word in condition_text for word in ["title", "flood", "survey"]):
                priority_score += 20  # Property-related
            elif any(word in condition_text for word in ["id", "gift", "divorce"]):
                priority_score += 10  # Supporting documents

            condition["priority_score"] = priority_score
            prioritized.append(condition)

        # Sort by priority score (highest first)
        prioritized.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return prioritized


def track_loan_conditions(loan_id: str, conditions: List[Dict], submitted_docs: List[Dict]) -> Dict[str, Any]:
    """Quick function to track underwriting conditions."""
    tracker = UnderwritingConditionTracker()
    return tracker.track_conditions(loan_id, conditions, submitted_docs)