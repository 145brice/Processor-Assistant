"""
Condition Clearer - Underwriting Condition Clearing Module
Automatically matches uploaded documents to underwriting conditions.
"""

import re
from typing import Dict, Any, List, Optional, Set
from pathlib import Path


class ConditionClearer:
    """
    Intelligent system for matching documents to underwriting conditions.
    Automatically determines if conditions are satisfied by uploaded documents.
    """

    def __init__(self):
        # Common condition keywords and their document mappings
        self.condition_mappings = {
            # Income verification conditions
            "paystub": ["paystub", "pay stub", "earnings statement", "income statement"],
            "w2": ["w2", "w-2", "wage statement", "tax form"],
            "tax return": ["tax return", "1040", "income tax", "irs"],
            "bank statement": ["bank statement", "bank stmt", "checking", "savings", "account statement"],

            # Asset verification conditions
            "asset statement": ["bank statement", "asset statement", "account balance"],
            "gift letter": ["gift letter", "gift", "donation"],
            "retirement statement": ["401k", "ira", "retirement", "pension"],

            # Credit conditions
            "credit report": ["credit report", "tri-merge", "credit score", "fico"],
            "explanation": ["explanation", "letter", "clarification", "justification"],

            # Property conditions
            "appraisal": ["appraisal", "property valuation", "1004", "1075"],
            "title report": ["title", "title report", "commitment", "preliminary title"],
            "survey": ["survey", "plat", "property survey"],
            "inspection": ["inspection", "home inspection", "property inspection"],

            # Insurance conditions
            "hazard insurance": ["hazard insurance", "homeowners insurance", "hoi"],
            "flood insurance": ["flood insurance", "flood policy"],
            "title insurance": ["title insurance", "title policy"],

            # Other common conditions
            "id": ["identification", "drivers license", "passport", "government id"],
            "divorce decree": ["divorce", "decree", "dissolution"],
            "marriage certificate": ["marriage", "certificate", "wedding"],
            "military orders": ["military", "dd214", "discharge", "orders"]
        }

        # Document type priorities (higher = more specific match)
        self.document_priorities = {
            "paystub": 10,
            "w2": 10,
            "tax return": 9,
            "bank statement": 8,
            "appraisal": 9,
            "title report": 9,
            "credit report": 8,
            "hazard insurance": 8,
            "id": 7,
            "gift letter": 9
        }

    def clear_condition(self, condition_text: str, uploaded_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Determine if a condition is cleared by uploaded documents.

        Args:
            condition_text: The underwriting condition text
            uploaded_docs: List of uploaded document info

        Returns:
            Clearing status and matching documents
        """
        condition_lower = condition_text.lower().strip()

        # Find matching document types for this condition
        matching_doc_types = self._find_matching_doc_types(condition_lower)

        if not matching_doc_types:
            return {
                "status": "❌ No matching document type",
                "confidence": 0,
                "matching_docs": [],
                "reason": "Condition requires document type not in system"
            }

        # Check if any uploaded documents match the required types
        matching_docs = []
        best_match_confidence = 0

        for doc in uploaded_docs:
            doc_name = doc.get("filename", "").lower()
            doc_type = doc.get("doc_type", "").lower()
            doc_content = doc.get("content", "").lower()

            for required_type in matching_doc_types:
                confidence = self._calculate_match_confidence(
                    required_type, doc_name, doc_type, doc_content, condition_lower
                )

                if confidence > best_match_confidence:
                    best_match_confidence = confidence

                if confidence >= 60:  # 60% confidence threshold
                    matching_docs.append({
                        "filename": doc.get("filename"),
                        "doc_type": doc.get("doc_type"),
                        "confidence": confidence,
                        "match_reason": f"Matches '{required_type}' requirement"
                    })

        # Determine overall status
        if matching_docs:
            status = "✅ Cleared" if best_match_confidence >= 80 else "⚠️ Partially Cleared"
            return {
                "status": status,
                "confidence": best_match_confidence,
                "matching_docs": matching_docs,
                "reason": f"Matched with {len(matching_docs)} document(s)"
            }
        else:
            return {
                "status": "❌ Not Cleared",
                "confidence": best_match_confidence,
                "matching_docs": [],
                "reason": f"No documents match required types: {', '.join(matching_doc_types)}"
            }

    def _find_matching_doc_types(self, condition_text: str) -> List[str]:
        """Find document types that match the condition."""
        matching_types = []

        for doc_type, keywords in self.condition_mappings.items():
            for keyword in keywords:
                if keyword in condition_text:
                    matching_types.append(doc_type)
                    break

        return list(set(matching_types))  # Remove duplicates

    def _calculate_match_confidence(self, required_type: str, doc_name: str,
                                  doc_type: str, doc_content: str, condition_text: str) -> float:
        """
        Calculate how well a document matches a required type.
        Returns confidence score 0-100.
        """
        confidence = 0

        # Exact document type match gets high confidence
        if required_type in doc_type:
            confidence += 50

        # Filename contains relevant keywords
        required_keywords = self.condition_mappings.get(required_type, [])
        filename_matches = sum(1 for keyword in required_keywords if keyword in doc_name)
        if filename_matches > 0:
            confidence += 20

        # Content contains relevant keywords (if available)
        if doc_content:
            content_matches = sum(1 for keyword in required_keywords if keyword in doc_content)
            if content_matches > 0:
                confidence += 15

        # Condition-specific keywords in document
        condition_keywords = self._extract_condition_keywords(condition_text)
        condition_matches = sum(1 for keyword in condition_keywords if keyword in doc_name or keyword in doc_content)
        if condition_matches > 0:
            confidence += 10

        # Document priority bonus
        priority = self.document_priorities.get(required_type, 5)
        confidence += priority

        return min(confidence, 100)  # Cap at 100%

    def _extract_condition_keywords(self, condition_text: str) -> List[str]:
        """Extract specific keywords from condition text."""
        keywords = []

        # Look for quoted terms
        quotes = re.findall(r'"([^"]*)"', condition_text)
        keywords.extend(quotes)

        # Look for specific terms that might indicate requirements
        specific_terms = re.findall(r'\b\d+\s+(?:day|month|year)s?\b', condition_text)
        keywords.extend(specific_terms)

        # Look for proper names or specific identifiers
        names = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', condition_text)
        keywords.extend(names)

        return keywords

    def clear_multiple_conditions(self, conditions: List[Dict[str, Any]],
                                uploaded_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clear multiple underwriting conditions at once.

        Args:
            conditions: List of condition dictionaries
            uploaded_docs: List of uploaded documents

        Returns:
            Results for all conditions
        """
        results = []

        for condition in conditions:
            condition_text = condition.get("description", condition.get("text", ""))
            result = self.clear_condition(condition_text, uploaded_docs)

            results.append({
                "condition_id": condition.get("id"),
                "condition_text": condition_text,
                "clearing_result": result
            })

        # Summary statistics
        total_conditions = len(conditions)
        cleared = sum(1 for r in results if "✅ Cleared" in r["clearing_result"]["status"])
        partial = sum(1 for r in results if "⚠️ Partially" in r["clearing_result"]["status"])
        not_cleared = sum(1 for r in results if "❌" in r["clearing_result"]["status"])

        summary = {
            "total_conditions": total_conditions,
            "cleared": cleared,
            "partially_cleared": partial,
            "not_cleared": not_cleared,
            "clearance_percentage": (cleared / total_conditions) * 100 if total_conditions > 0 else 0,
            "results": results
        }

        return summary

    def suggest_missing_documents(self, conditions: List[Dict[str, Any]],
                                uploaded_docs: List[Dict[str, Any]]) -> List[str]:
        """
        Suggest which documents should be uploaded to clear remaining conditions.

        Returns list of suggested document types.
        """
        suggestions = []

        for condition in conditions:
            condition_text = condition.get("description", condition.get("text", ""))
            result = self.clear_condition(condition_text, uploaded_docs)

            if "❌" in result["status"]:
                required_types = self._find_matching_doc_types(condition_text.lower())
                if required_types:
                    suggestions.extend(required_types)

        return list(set(suggestions))  # Remove duplicates

    def get_condition_status_report(self, clearing_results: Dict[str, Any]) -> str:
        """Generate a formatted status report for condition clearing."""
        results = clearing_results.get("results", [])

        report = []
        report.append("# Underwriting Condition Clearing Report")
        report.append("")

        # Summary
        summary = clearing_results
        report.append("## Summary")
        report.append(f"- Total Conditions: {summary['total_conditions']}")
        report.append(f"- Fully Cleared: {summary['cleared']}")
        report.append(f"- Partially Cleared: {summary['partially_cleared']}")
        report.append(f"- Not Cleared: {summary['not_cleared']}")
        report.append(".1f")
        report.append("")

        # Detailed results
        report.append("## Condition Details")
        for result in results:
            status = result["clearing_result"]["status"]
            confidence = result["clearing_result"]["confidence"]
            reason = result["clearing_result"]["reason"]

            report.append(f"### Condition: {result['condition_text'][:50]}...")
            report.append(f"**Status:** {status}")
            report.append(f"**Confidence:** {confidence}%")
            report.append(f"**Details:** {reason}")

            matching_docs = result["clearing_result"]["matching_docs"]
            if matching_docs:
                report.append("**Matching Documents:**")
                for doc in matching_docs:
                    report.append(f"  - {doc['filename']} ({doc['confidence']}% confidence)")

            report.append("")

        return "\n".join(report)