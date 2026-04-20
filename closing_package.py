"""
Closing Package Generator - Create and organize closing packages
Compiles all required documents for loan closing.
"""

import os
import io
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False


class ClosingPackageGenerator:
    """
    Generates complete closing packages from loan documents.
    Organizes and combines all required closing documents.
    """

    def __init__(self):
        self.required_closing_docs = [
            "Closing Disclosure (CD)",
            "Loan Estimate (LE)",
            "Note",
            "Deed of Trust",
            "Title Policy",
            "Hazard Insurance",
            "Survey",
            "Repair Addendum",
            "Lead Paint Disclosure",
            "Occupancy Affidavit",
            "Cash to Close Statement"
        ]

    def generate(self, loan_folder: str, borrower_name: str) -> Dict[str, Any]:
        """Generate a complete closing package from loan folder documents."""
        folder = Path(loan_folder)
        if not folder.exists():
            return {"success": False, "error": "Loan folder not found"}

        package_folder = folder / "Closing_Package"
        package_folder.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_name = borrower_name.replace(" ", "_").replace("/", "-")

        existing_docs = self._scan_loan_documents(folder)
        missing_docs = self._check_missing_documents(existing_docs)
        
        manifest = self._create_manifest(existing_docs, borrower_name, timestamp)
        organized = self._organize_documents(folder, package_folder, existing_docs, safe_name)

        with open(package_folder / "MANIFEST.txt", "w") as f:
            f.write(manifest)

        return {
            "success": True,
            "borrower_name": borrower_name,
            "package_folder": str(package_folder),
            "timestamp": timestamp,
            "documents_found": len(existing_docs),
            "documents_included": organized["included_count"],
            "missing_documents": missing_docs,
            "manifest": manifest
        }

    def _scan_loan_documents(self, folder: Path) -> Dict[str, List[Dict]]:
        """Scan loan folder and categorize documents."""
        documents = {}
        for file in folder.rglob("*"):
            if not file.is_file() or file.name.startswith("."):
                continue
            doc_type = self._identify_document_type(file.name.lower())
            if doc_type not in documents:
                documents[doc_type] = []
            documents[doc_type].append({"name": file.name, "path": str(file)})
        return documents

    def _identify_document_type(self, filename: str) -> str:
        """Identify document type from filename."""
        if "cd" in filename and "closing" in filename:
            return "Closing Disclosure (CD)"
        elif "closing disclosure" in filename:
            return "Closing Disclosure (CD)"
        elif "le" in filename and "loan estimate" in filename:
            return "Loan Estimate (LE)"
        elif "loan estimate" in filename:
            return "Loan Estimate (LE)"
        elif "note" in filename:
            return "Note"
        elif "deed" in filename or "trust" in filename:
            return "Deed of Trust"
        elif "title" in filename:
            return "Title Policy"
        elif "insurance" in filename or "hoi" in filename or "hazard" in filename:
            return "Hazard Insurance"
        elif "survey" in filename:
            return "Survey"
        elif "repair" in filename:
            return "Repair Addendum"
        elif "lead" in filename:
            return "Lead Paint Disclosure"
        elif "occupancy" in filename:
            return "Occupancy Affidavit"
        elif "cash" in filename or "close" in filename:
            return "Cash to Close Statement"
        else:
            return "Other Document"

    def _check_missing_documents(self, existing_docs: Dict) -> List[str]:
        """Check which required closing documents are missing."""
        existing_types = set(existing_docs.keys())
        required_types = set(self.required_closing_docs)
        return list(required_types - existing_types)

    def _create_manifest(self, documents: Dict, borrower_name: str, timestamp: str) -> str:
        """Create a manifest listing all documents."""
        lines = ["CLOSING PACKAGE MANIFEST", "=" * 40, f"Borrower: {borrower_name}", f"Generated: {timestamp}", "", "DOCUMENTS:"]
        for doc_type, docs in sorted(documents.items()):
            lines.append(f"\n{doc_type}:")
            for doc in docs:
                lines.append(f"  - {doc['name']}")
        return "\n".join(lines)

    def _organize_documents(self, source: Path, dest: Path, documents: Dict, safe_name: str) -> Dict:
        """Copy and organize documents into closing package."""
        included_count = 0
        for doc_type, docs in documents.items():
            doc_folder = dest / doc_type.replace(" ", "_")
            doc_folder.mkdir(exist_ok=True)
            for doc in docs:
                src_path = Path(doc["path"])
                if src_path.exists():
                    try:
                        shutil.copy2(src_path, doc_folder / src_path.name)
                        included_count += 1
                    except:
                        pass
        return {"included_count": included_count, "path": str(dest)}


def create_closing_package(loan_folder: str, borrower_name: str) -> Dict[str, Any]:
    """Quick function to generate closing package."""
    generator = ClosingPackageGenerator()
    return generator.generate(loan_folder, borrower_name)