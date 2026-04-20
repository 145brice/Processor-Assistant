"""
Multi-Borrower Support
Handle loans with multiple borrowers (primary + co-borrower).
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class MultiBorrowerHandler:
    """
    Handles loans with multiple borrowers (primary and co-borrower).
    Manages separate document organization and processing for each borrower.
    """

    def __init__(self):
        self.borrower_types = ["primary", "co_borrower"]

    def process(self, files: List[str], primary_borrower: str, co_borrower: str = None) -> Dict[str, Any]:
        """
        Process documents for multi-borrower loan.

        Args:
            files: List of file paths to process
            primary_borrower: Name of primary borrower
            co_borrower: Name of co-borrower (optional)

        Returns:
            Processing results for each borrower
        """
        result = {
            "primary_borrower": primary_borrower,
            "co_borrower": co_borrower,
            "borrowers_processed": 1 if not co_borrower else 2,
            "documents_assigned": {},
            "unassigned_documents": [],
            "processing_summary": ""
        }

        # Create borrower folders
        borrower_folders = self._create_borrower_folders(primary_borrower, co_borrower)

        # Assign documents to borrowers
        assignment = self._assign_documents_to_borrowers(files, primary_borrower, co_borrower)

        result["documents_assigned"] = assignment["assigned"]
        result["unassigned_documents"] = assignment["unassigned"]

        # Organize files into borrower folders
        organization = self._organize_files(files, borrower_folders, assignment)

        result["organization"] = organization

        # Generate summary
        result["processing_summary"] = self._generate_processing_summary(result)

        return result

    def _create_borrower_folders(self, primary: str, co_borrower: str = None) -> Dict[str, Path]:
        """Create organized folder structure for borrowers."""
        base_dir = Path("loan_docs") / "multi_borrower"
        base_dir.mkdir(exist_ok=True)

        folders = {}

        # Primary borrower folder
        primary_clean = primary.replace(" ", "_").replace("/", "-")
        primary_folder = base_dir / f"primary_{primary_clean}"
        primary_folder.mkdir(exist_ok=True)
        folders["primary"] = primary_folder

        # Co-borrower folder (if applicable)
        if co_borrower:
            co_clean = co_borrower.replace(" ", "_").replace("/", "-")
            co_folder = base_dir / f"co_borrower_{co_clean}"
            co_folder.mkdir(exist_ok=True)
            folders["co_borrower"] = co_folder

        # Joint documents folder
        joint_folder = base_dir / "joint_documents"
        joint_folder.mkdir(exist_ok=True)
        folders["joint"] = joint_folder

        return folders

    def _assign_documents_to_borrowers(self, files: List[str], primary: str, co_borrower: str = None) -> Dict[str, Any]:
        """Assign documents to appropriate borrowers based on naming and content."""
        assigned = {
            "primary": [],
            "co_borrower": [],
            "joint": []
        }
        unassigned = []

        primary_lower = primary.lower()
        co_lower = co_borrower.lower() if co_borrower else ""

        for file_path in files:
            filename = os.path.basename(file_path).lower()

            # Check if document belongs to primary borrower
            if any(term in filename for term in [primary_lower, "borrower1", "primary"]):
                assigned["primary"].append(file_path)
                continue

            # Check if document belongs to co-borrower
            if co_borrower and any(term in filename for term in [co_lower, "borrower2", "co", "coborrower"]):
                assigned["co_borrower"].append(file_path)
                continue

            # Check for joint documents
            if any(term in filename for term in ["joint", "both", "shared", "1003", "application", "closing disclosure"]):
                assigned["joint"].append(file_path)
                continue

            # If no clear assignment, mark as unassigned
            unassigned.append(file_path)

        return {
            "assigned": assigned,
            "unassigned": unassigned
        }

    def _organize_files(self, files: List[str], folders: Dict[str, Path], assignment: Dict[str, Any]) -> Dict[str, Any]:
        """Copy files into appropriate borrower folders."""
        organization = {
            "primary_files": len(assignment["assigned"]["primary"]),
            "co_borrower_files": len(assignment["assigned"]["co_borrower"]),
            "joint_files": len(assignment["assigned"]["joint"]),
            "folders_created": len(folders),
            "errors": []
        }

        # Copy assigned files
        for borrower_type, file_list in assignment["assigned"].items():
            if borrower_type in folders:
                folder = folders[borrower_type]
                for file_path in file_list:
                    try:
                        if os.path.exists(file_path):
                            shutil.copy2(file_path, folder / os.path.basename(file_path))
                    except Exception as e:
                        organization["errors"].append(f"Failed to copy {file_path}: {str(e)}")

        return organization

    def _generate_processing_summary(self, result: Dict[str, Any]) -> str:
        """Generate a summary of the multi-borrower processing."""
        summary = []
        summary.append("MULTI-BORROWER PROCESSING SUMMARY")
        summary.append("=" * 40)
        summary.append(f"Primary Borrower: {result['primary_borrower']}")

        if result['co_borrower']:
            summary.append(f"Co-Borrower: {result['co_borrower']}")

        summary.append(f"Borrowers Processed: {result['borrowers_processed']}")
        summary.append("")

        assigned = result['documents_assigned']
        summary.append("DOCUMENT ASSIGNMENT:")
        summary.append(f"  Primary Borrower: {len(assigned['primary'])} documents")
        summary.append(f"  Co-Borrower: {len(assigned['co_borrower'])} documents")
        summary.append(f"  Joint Documents: {len(assigned['joint'])} documents")

        if result['unassigned_documents']:
            summary.append(f"  Unassigned: {len(result['unassigned_documents'])} documents")

        if result.get('organization', {}).get('errors'):
            summary.append("")
            summary.append("ERRORS:")
            for error in result['organization']['errors']:
                summary.append(f"  - {error}")

        return "\n".join(summary)

    def validate_multi_borrower_setup(self, primary_data: Dict, co_borrower_data: Dict = None) -> List[str]:
        """Validate that multi-borrower setup is complete."""
        issues = []

        # Check primary borrower data completeness
        required_fields = ["name", "ssn", "income", "credit_score"]
        for field in required_fields:
            if not primary_data.get(field):
                issues.append(f"Missing {field} for primary borrower")

        # Check co-borrower data if present
        if co_borrower_data:
            for field in required_fields:
                if not co_borrower_data.get(field):
                    issues.append(f"Missing {field} for co-borrower")

            # Check for consistency between borrowers
            if primary_data.get("loan_amount") and co_borrower_data.get("loan_amount"):
                if primary_data["loan_amount"] != co_borrower_data["loan_amount"]:
                    issues.append("Loan amounts don't match between borrowers")

        return issues

    def merge_borrower_financials(self, primary_data: Dict, co_borrower_data: Dict = None) -> Dict[str, Any]:
        """Merge financial data from multiple borrowers for qualification."""
        merged = primary_data.copy()

        if co_borrower_data:
            # Combine incomes
            primary_income = primary_data.get("monthly_income", 0)
            co_income = co_borrower_data.get("monthly_income", 0)
            merged["combined_monthly_income"] = primary_income + co_income

            # Combine debts
            primary_debt = primary_data.get("monthly_debt", 0)
            co_debt = co_borrower_data.get("monthly_debt", 0)
            merged["combined_monthly_debt"] = primary_debt + co_debt

            # Use better credit score
            primary_score = primary_data.get("credit_score", 0)
            co_score = co_borrower_data.get("credit_score", 0)
            merged["best_credit_score"] = max(primary_score, co_score)

            # Calculate combined DTI
            if merged["combined_monthly_income"] > 0:
                merged["combined_dti"] = (merged["combined_monthly_debt"] / merged["combined_monthly_income"]) * 100

        return merged

    def generate_borrower_comparison_report(self, primary_data: Dict, co_borrower_data: Dict = None) -> str:
        """Generate a comparison report between borrowers."""
        report = []
        report.append("BORROWER COMPARISON REPORT")
        report.append("=" * 40)
        report.append(f"Primary Borrower: {primary_data.get('name', 'N/A')}")
        report.append(f"Co-Borrower: {co_borrower_data.get('name', 'N/A') if co_borrower_data else 'None'}")
        report.append("")

        if co_borrower_data:
            comparison_fields = [
                ("Monthly Income", "monthly_income"),
                ("Credit Score", "credit_score"),
                ("Monthly Debt", "monthly_debt"),
                ("Loan Amount", "loan_amount")
            ]

            report.append("INDIVIDUAL BORROWER COMPARISON:")
            for label, field in comparison_fields:
                primary_val = primary_data.get(field, "N/A")
                co_val = co_borrower_data.get(field, "N/A")
                report.append("30")

            report.append("")
            merged = self.merge_borrower_financials(primary_data, co_borrower_data)
            report.append("COMBINED QUALIFICATION DATA:")
            report.append(f"  Combined Monthly Income: ${merged.get('combined_monthly_income', 0):,.2f}")
            report.append(f"  Combined Monthly Debt: ${merged.get('combined_monthly_debt', 0):,.2f}")
            report.append(".1f")
            report.append(f"  Best Credit Score: {merged.get('best_credit_score', 'N/A')}")

        return "\n".join(report)


def process_multi_borrower_loan(files: List[str], primary: str, co_borrower: str = None) -> Dict[str, Any]:
    """Quick function to process multi-borrower loan."""
    handler = MultiBorrowerHandler()
    return handler.process(files, primary, co_borrower)