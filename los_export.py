"""
Basic LOS Export (PDF + CSV)
Export loan data for import into Loan Origination Systems.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


class LOSExport:
    """
    Export loan data in formats compatible with Loan Origination Systems.
    Supports CSV and PDF export formats.
    """

    def __init__(self):
        # Common LOS field mappings
        self.los_field_mappings = {
            # Borrower Information
            "borrower_name": ["BorrowerName", "ApplicantName", "FullName"],
            "borrower_ssn": ["SSN", "SocialSecurityNumber", "TaxID"],
            "borrower_dob": ["DOB", "DateOfBirth", "BirthDate"],
            "borrower_phone": ["Phone", "HomePhone", "Telephone"],
            "borrower_email": ["Email", "EmailAddress"],
            "borrower_address": ["Address", "HomeAddress", "ResidentialAddress"],

            # Loan Information
            "loan_amount": ["LoanAmount", "RequestedAmount", "LoanAmt"],
            "loan_type": ["LoanType", "LoanPurpose", "Purpose"],
            "loan_program": ["LoanProgram", "Program", "Product"],
            "interest_rate": ["InterestRate", "Rate", "NoteRate"],
            "loan_term": ["LoanTerm", "Term", "Years"],

            # Property Information
            "property_address": ["PropertyAddress", "SubjectProperty"],
            "property_value": ["PropertyValue", "AppraisedValue", "AVMValue"],
            "ltv_ratio": ["LTV", "LoanToValueRatio"],
            "cltv_ratio": ["CLTV", "CombinedLTV"],

            # Financial Information
            "monthly_income": ["MonthlyIncome", "GrossMonthlyIncome"],
            "monthly_debt": ["MonthlyDebt", "TotalMonthlyDebt"],
            "dti_ratio": ["DTI", "DebtToIncomeRatio"],
            "credit_score": ["CreditScore", "FICOScore"],

            # Employment Information
            "employer_name": ["Employer", "EmployerName", "Company"],
            "job_title": ["JobTitle", "Position", "Occupation"],
            "years_employed": ["YearsEmployed", "Tenure", "EmploymentLength"],

            # Asset Information
            "checking_balance": ["CheckingBalance", "CheckingAccount"],
            "savings_balance": ["SavingsBalance", "SavingsAccount"],
            "total_assets": ["TotalAssets", "AssetTotal"]
        }

    def export(self, loan_data: Dict[str, Any], export_path: str, format_type: str = "csv") -> Dict[str, Any]:
        """
        Export loan data to specified format.

        Args:
            loan_data: Dictionary with complete loan information
            export_path: Directory path for exports
            format_type: "csv", "json", or "pdf"

        Returns:
            Export results with file paths and status
        """
        export_dir = Path(export_path)
        export_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        loan_id = loan_data.get("loan_id", "unknown").replace("/", "-")

        result = {
            "success": True,
            "export_format": format_type,
            "timestamp": timestamp,
            "files_created": [],
            "errors": []
        }

        try:
            if format_type.lower() == "csv":
                csv_file = export_dir / f"los_export_{loan_id}_{timestamp}.csv"
                self._export_to_csv(loan_data, csv_file)
                result["files_created"].append(str(csv_file))

            elif format_type.lower() == "json":
                json_file = export_dir / f"los_export_{loan_id}_{timestamp}.json"
                self._export_to_json(loan_data, json_file)
                result["files_created"].append(str(json_file))

            elif format_type.lower() == "pdf":
                if HAS_PDF:
                    pdf_file = export_dir / f"los_export_{loan_id}_{timestamp}.pdf"
                    self._export_to_pdf(loan_data, pdf_file)
                    result["files_created"].append(str(pdf_file))
                else:
                    result["errors"].append("PDF export requires pypdf library")

            # Create summary report
            summary_file = export_dir / f"export_summary_{loan_id}_{timestamp}.txt"
            self._create_export_summary(loan_data, result, summary_file)
            result["files_created"].append(str(summary_file))

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Export failed: {str(e)}")

        return result

    def _export_to_csv(self, loan_data: Dict[str, Any], csv_path: Path):
        """Export loan data to CSV format."""
        # Flatten the nested dictionary
        flat_data = self._flatten_loan_data(loan_data)

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            # Write headers
            writer.writerow(["Field", "Value"])

            # Write data
            for key, value in flat_data.items():
                writer.writerow([key, str(value) if value is not None else ""])

    def _export_to_json(self, loan_data: Dict[str, Any], json_path: Path):
        """Export loan data to JSON format."""
        # Add metadata
        export_data = {
            "export_metadata": {
                "exported_at": datetime.now().isoformat(),
                "format": "LOS Compatible JSON",
                "version": "1.0"
            },
            "loan_data": loan_data
        }

        with open(json_path, "w", encoding="utf-8") as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

    def _export_to_pdf(self, loan_data: Dict[str, Any], pdf_path: Path):
        """Export loan data to PDF format."""
        if not HAS_PDF:
            raise ImportError("PDF export requires pypdf library")

        # This is a simplified PDF export - real implementation would format nicely
        writer = PdfWriter()

        # Create a simple text-based PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "LOS EXPORT - LOAN DATA")

        # Add loan information
        c.setFont("Helvetica", 12)
        y_position = 720

        flat_data = self._flatten_loan_data(loan_data)
        for key, value in list(flat_data.items())[:50]:  # Limit to first 50 fields for PDF
            if y_position < 50:  # Start new page if needed
                c.showPage()
                y_position = 750

            c.drawString(50, y_position, f"{key}: {str(value) if value is not None else ''}")
            y_position -= 15

        c.save()
        buffer.seek(0)

        # Save to file
        with open(pdf_path, "wb") as f:
            f.write(buffer.getvalue())

    def _flatten_loan_data(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested loan data for export."""
        flat = {}

        def flatten_dict(d: Dict, prefix: str = ""):
            for key, value in d.items():
                new_key = f"{prefix}{key}" if prefix else key

                if isinstance(value, dict):
                    flatten_dict(value, f"{new_key}.")
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            flatten_dict(item, f"{new_key}[{i}].")
                        else:
                            flat[f"{new_key}[{i}]"] = item
                else:
                    flat[new_key] = value

        flatten_dict(loan_data)
        return flat

    def _create_export_summary(self, loan_data: Dict, export_result: Dict, summary_path: Path):
        """Create a summary of the export."""
        summary = []
        summary.append("LOS EXPORT SUMMARY")
        summary.append("=" * 40)
        summary.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        summary.append(f"Loan ID: {loan_data.get('loan_id', 'Unknown')}")
        summary.append(f"Export Format: {export_result['export_format'].upper()}")
        summary.append(f"Status: {'SUCCESS' if export_result['success'] else 'FAILED'}")
        summary.append("")

        if export_result["files_created"]:
            summary.append("FILES CREATED:")
            for file_path in export_result["files_created"]:
                summary.append(f"  - {Path(file_path).name}")
            summary.append("")

        if export_result.get("errors"):
            summary.append("ERRORS:")
            for error in export_result["errors"]:
                summary.append(f"  - {error}")

        summary.append("")
        summary.append("LOAN SUMMARY:")
        summary.append(f"  Borrower: {loan_data.get('borrower_name', 'Unknown')}")
        summary.append(f"  Loan Amount: ${loan_data.get('loan_amount', 0):,.2f}")
        summary.append(f"  Property Value: ${loan_data.get('property_value', 0):,.2f}")
        summary.append(f"  LTV: {loan_data.get('ltv_ratio', 0):.1f}%")

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("\n".join(summary))

    def validate_los_compatibility(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that loan data is compatible with LOS import."""
        validation = {
            "compatible": True,
            "warnings": [],
            "errors": [],
            "missing_fields": [],
            "data_quality_score": 100
        }

        # Check for required fields
        required_fields = [
            "borrower_name", "loan_amount", "loan_type",
            "property_address", "monthly_income", "credit_score"
        ]

        for field in required_fields:
            if not loan_data.get(field):
                validation["missing_fields"].append(field)
                validation["data_quality_score"] -= 10

        # Check data quality
        if len(validation["missing_fields"]) > 2:
            validation["errors"].append("Too many missing required fields for LOS import")
            validation["compatible"] = False

        # Check for data consistency
        loan_amount = loan_data.get("loan_amount", 0)
        property_value = loan_data.get("property_value", 0)

        if property_value > 0 and loan_amount > property_value:
            validation["warnings"].append("Loan amount exceeds property value")
            validation["data_quality_score"] -= 5

        # Check credit score range
        credit_score = loan_data.get("credit_score", 0)
        if credit_score and (credit_score < 300 or credit_score > 900):
            validation["warnings"].append("Credit score outside valid range")
            validation["data_quality_score"] -= 5

        return validation

    def get_supported_los_systems(self) -> List[str]:
        """Get list of supported LOS systems."""
        return [
            "Encompass",
            "Calyx Point",
            "Byte",
            "Mortgage Builder",
            "Black Knight MSP",
            "Fiserv",
            "ICE Mortgage Technology",
            "Mortgage Cadence",
            "Perpetual",
            "Generic CSV Import"
        ]


def export_to_los(loan_data: Dict[str, Any], export_path: str, format_type: str = "csv") -> Dict[str, Any]:
    """Quick function to export loan data to LOS format."""
    exporter = LOSExport()
    return exporter.export(loan_data, export_path, format_type)