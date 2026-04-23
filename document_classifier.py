"""
Automated Document Classifier - AI-powered document classification and routing
Uses pattern matching and content analysis to classify and route documents automatically.
"""

import re
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class AutomatedDocumentClassifier:
    """
    Automatically classifies documents and routes them to appropriate loan folders.
    Uses filename patterns, content analysis, and metadata to determine document types.
    """

    def __init__(self):
        # Document type patterns with keywords and routing rules
        self.document_patterns = {
            "paystub": {
                "keywords": ["paystub", "pay stub", "paystub", "earnings", "salary", "wage", "payroll"],
                "filename_patterns": [r"paystub", r"pay.*stub", r"earnings", r"salary"],
                "folder": "income_documents",
                "priority": 9
            },
            "w2": {
                "keywords": ["w-2", "w2", "w 2", "wage and tax", "tax form", "irs"],
                "filename_patterns": [r"w.?2", r"tax.*form", r"irs"],
                "folder": "tax_documents",
                "priority": 9
            },
            "tax_return": {
                "keywords": ["tax return", "1040", "income tax", "irs", "transcript"],
                "filename_patterns": [r"1040", r"tax.*return", r"transcript"],
                "folder": "tax_documents",
                "priority": 8
            },
            "bank_statement": {
                "keywords": ["bank statement", "statement", "checking", "savings", "account"],
                "filename_patterns": [r"bank.*stmt", r"statement", r"checking", r"savings"],
                "folder": "asset_documents",
                "priority": 8
            },
            "appraisal": {
                "keywords": ["appraisal", "property valuation", "1004", "1075", "avm"],
                "filename_patterns": [r"appraisal", r"1004", r"1075", r"valuation"],
                "folder": "property_documents",
                "priority": 9
            },
            "title_report": {
                "keywords": ["title", "title report", "commitment", "preliminary", "owners policy"],
                "filename_patterns": [r"title.*report", r"commitment", r"prelim"],
                "folder": "property_documents",
                "priority": 8
            },
            "credit_report": {
                "keywords": ["credit report", "tri-merge", "credit score", "fico", "experian", "equifax", "transunion"],
                "filename_patterns": [r"credit.*report", r"tri.*merge", r"fico"],
                "folder": "credit_documents",
                "priority": 9
            },
            "closing_disclosure": {
                "keywords": ["closing disclosure", "cd", "closing", "disclosure"],
                "filename_patterns": [r"closing.*disclosure", r"cd"],
                "folder": "closing_documents",
                "priority": 10
            },
            "loan_estimate": {
                "keywords": ["loan estimate", "le", "estimate"],
                "filename_patterns": [r"loan.*estimate", r"le"],
                "folder": "closing_documents",
                "priority": 10
            },
            "identification": {
                "keywords": ["drivers license", "passport", "id", "identification", "government id"],
                "filename_patterns": [r"license", r"passport", r"gov.*id"],
                "folder": "identification",
                "priority": 7
            },
            "gift_letter": {
                "keywords": ["gift letter", "gift", "donation"],
                "filename_patterns": [r"gift.*letter", r"gift"],
                "folder": "asset_documents",
                "priority": 8
            },
            "flood_insurance": {
                "keywords": ["flood insurance", "flood policy", "flood certification"],
                "filename_patterns": [r"flood.*insurance", r"flood.*policy"],
                "folder": "insurance_documents",
                "priority": 7
            },
            "hazard_insurance": {
                "keywords": ["hazard insurance", "homeowners insurance", "hoi", "home insurance"],
                "filename_patterns": [r"hazard", r"homeowners", r"hoi"],
                "folder": "insurance_documents",
                "priority": 7
            },
            "survey": {
                "keywords": ["survey", "plat", "property survey"],
                "filename_patterns": [r"survey", r"plat"],
                "folder": "property_documents",
                "priority": 6
            },
            "inspection_report": {
                "keywords": ["inspection", "home inspection", "property inspection"],
                "filename_patterns": [r"inspection.*report", r"home.*inspection"],
                "folder": "property_documents",
                "priority": 6
            },
            "divorce_decree": {
                "keywords": ["divorce", "decree", "dissolution", "marital settlement"],
                "filename_patterns": [r"divorce", r"decree", r"dissolution"],
                "folder": "legal_documents",
                "priority": 8
            },
            "marriage_certificate": {
                "keywords": ["marriage", "certificate", "wedding", "marriage license"],
                "filename_patterns": [r"marriage", r"certificate", r"wedding"],
                "folder": "legal_documents",
                "priority": 7
            },
            "application_1003": {
                "keywords": ["1003", "uniform residential loan application", "urla", "loan application"],
                "filename_patterns": [r"1003", r"urla", r"application"],
                "folder": "application_documents",
                "priority": 10
            }
        }

    def classify_document(self, file_path: str, content_preview: str = "") -> Dict[str, Any]:
        """
        Classify a single document based on filename and content.

        Args:
            file_path: Path to the document file
            content_preview: Optional text content preview

        Returns:
            Classification results with confidence scores
        """
        filename = os.path.basename(file_path).lower()
        content = content_preview.lower()

        # Initialize results
        results = {
            "filename": os.path.basename(file_path),
            "primary_classification": None,
            "secondary_classifications": [],
            "confidence": 0,
            "routing_folder": None,
            "priority": 0,
            "matched_keywords": [],
            "recommendations": []
        }

        # Score each document type
        type_scores = {}
        for doc_type, patterns in self.document_patterns.items():
            score = self._calculate_document_score(filename, content, patterns)
            if score > 0:
                type_scores[doc_type] = {
                    "score": score,
                    "folder": patterns["folder"],
                    "priority": patterns["priority"]
                }

        if not type_scores:
            results["recommendations"].append("Document type not recognized - manual classification needed")
            return results

        # Sort by score and select primary classification
        sorted_types = sorted(type_scores.items(), key=lambda x: x[1]["score"], reverse=True)

        primary_type = sorted_types[0][0]
        primary_data = sorted_types[0][1]

        results["primary_classification"] = primary_type
        results["confidence"] = min(primary_data["score"], 100)
        results["routing_folder"] = primary_data["folder"]
        results["priority"] = primary_data["priority"]

        # Add secondary classifications (if score > 30)
        if len(sorted_types) > 1:
            secondary = [t for t, d in sorted_types[1:] if d["score"] > 30]
            results["secondary_classifications"] = secondary[:3]  # Top 3 secondary

        # Generate recommendations
        results["recommendations"] = self._generate_classification_recommendations(results)

        return results

    def _calculate_document_score(self, filename: str, content: str, patterns: Dict) -> int:
        """Calculate classification score for a document type."""
        score = 0

        # Filename pattern matching (high weight)
        for pattern in patterns["filename_patterns"]:
            if re.search(pattern, filename, re.IGNORECASE):
                score += 40
                break

        # Keyword matching in filename (medium weight)
        filename_words = re.findall(r'\b\w+\b', filename)
        for keyword in patterns["keywords"]:
            if keyword.lower() in filename:
                score += 25
                break

        # Content keyword matching (lower weight)
        if content:
            for keyword in patterns["keywords"]:
                if keyword.lower() in content:
                    score += 15
                    break

        # Exact filename matches get bonus points
        for keyword in patterns["keywords"]:
            if keyword.lower() == filename.split('.')[0].lower():
                score += 20
                break

        return score

    def _generate_classification_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on classification results."""
        recommendations = []

        if results["confidence"] < 50:
            recommendations.append("Low confidence classification - verify document type manually")

        if results["secondary_classifications"]:
            recommendations.append(f"Could also be: {', '.join(results['secondary_classifications'][:2])}")

        if not results["routing_folder"]:
            recommendations.append("No routing folder assigned - document needs manual placement")

        if results["priority"] >= 9:
            recommendations.append("High-priority document - review promptly")
        elif results["priority"] <= 5:
            recommendations.append("Low-priority document - can be reviewed later")

        return recommendations

    def batch_classify_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Classify multiple documents in batch.

        Args:
            file_paths: List of file paths to classify

        Returns:
            Batch classification results
        """
        results = {
            "total_documents": len(file_paths),
            "classified_documents": 0,
            "unclassified_documents": 0,
            "routing_summary": {},
            "high_priority_count": 0,
            "low_confidence_count": 0,
            "document_results": []
        }

        for file_path in file_paths:
            if os.path.exists(file_path):
                classification = self.classify_document(file_path)
                results["document_results"].append(classification)

                if classification["primary_classification"]:
                    results["classified_documents"] += 1

                    # Update routing summary
                    folder = classification["routing_folder"]
                    results["routing_summary"][folder] = results["routing_summary"].get(folder, 0) + 1

                    # Count priorities and confidence levels
                    if classification["priority"] >= 8:
                        results["high_priority_count"] += 1
                    if classification["confidence"] < 60:
                        results["low_confidence_count"] += 1
                else:
                    results["unclassified_documents"] += 1
            else:
                results["document_results"].append({
                    "filename": os.path.basename(file_path),
                    "error": "File not found"
                })

        return results

    def route_document(self, file_path: str, loan_folder: str, classification: Dict = None) -> Dict[str, Any]:
        """
        Route a classified document to the appropriate loan subfolder.

        Args:
            file_path: Source file path
            loan_folder: Destination loan folder
            classification: Pre-computed classification (optional)

        Returns:
            Routing results
        """
        if not classification:
            classification = self.classify_document(file_path)

        if not classification["routing_folder"]:
            return {"success": False, "error": "No routing folder determined"}

        # Create destination path
        loan_path = Path(loan_folder)
        routing_folder = classification["routing_folder"]
        dest_folder = loan_path / routing_folder
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Create destination filename
        original_name = os.path.basename(file_path)
        dest_path = dest_folder / original_name

        # Handle duplicate names
        counter = 1
        while dest_path.exists():
            name_parts = original_name.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_name = f"{original_name}_{counter}"
            dest_path = dest_folder / new_name
            counter += 1

        try:
            # Copy file to destination
            import shutil
            shutil.copy2(file_path, dest_path)

            return {
                "success": True,
                "original_path": file_path,
                "destination_path": str(dest_path),
                "routing_folder": routing_folder,
                "classification": classification["primary_classification"],
                "confidence": classification["confidence"]
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to copy file: {str(e)}"}

    def generate_routing_report(self, batch_results: Dict) -> str:
        """Generate a comprehensive routing report."""
        results = batch_results

        report = []
        report.append("DOCUMENT CLASSIFICATION & ROUTING REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {os.environ.get('USERNAME', 'System')} at {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        report.append("SUMMARY:")
        report.append(f"  Total Documents Processed: {results['total_documents']}")
        report.append(f"  Successfully Classified: {results['classified_documents']}")
        report.append(f"  Unclassified: {results['unclassified_documents']}")
        report.append(f"  High Priority Documents: {results['high_priority_count']}")
        report.append(f"  Low Confidence Classifications: {results['low_confidence_count']}")
        report.append("")

        if results["routing_summary"]:
            report.append("ROUTING SUMMARY:")
            for folder, count in sorted(results["routing_summary"].items()):
                report.append(f"  {folder.replace('_', ' ').title()}: {count} documents")
            report.append("")

        # Detailed results for problematic documents
        problematic = []
        for doc_result in results["document_results"]:
            if (doc_result.get("confidence", 100) < 60 or
                not doc_result.get("primary_classification") or
                doc_result.get("error")):
                problematic.append(doc_result)

        if problematic:
            report.append("DOCUMENTS NEEDING ATTENTION:")
            report.append("-" * 40)
            for doc in problematic[:10]:  # Show first 10
                filename = doc.get("filename", "Unknown")
                if doc.get("error"):
                    report.append(f"  ❌ {filename}: {doc['error']}")
                elif not doc.get("primary_classification"):
                    report.append(f"  ❓ {filename}: Not classified")
                else:
                    confidence = doc.get("confidence", 0)
                    report.append(f"  ⚠️ {filename}: Low confidence ({confidence}%)")
            if len(problematic) > 10:
                report.append(f"  ... and {len(problematic) - 10} more")
            report.append("")

        report.append("RECOMMENDATIONS:")
        if results["unclassified_documents"] > 0:
            report.append(f"• Manually classify {results['unclassified_documents']} unclassified documents")
        if results["low_confidence_count"] > 0:
            report.append(f"• Review {results['low_confidence_count']} low-confidence classifications")
        if results["high_priority_count"] > 0:
            report.append(f"• Prioritize review of {results['high_priority_count']} high-priority documents")

        success_rate = (results["classified_documents"] / results["total_documents"]) * 100 if results["total_documents"] > 0 else 0
        report.append(f"Overall Success Rate: {success_rate:.1f}%")

        return "\n".join(report)


def classify_document(file_path: str) -> Dict[str, Any]:
    """Quick function to classify a single document."""
    classifier = AutomatedDocumentClassifier()
    return classifier.classify_document(file_path)