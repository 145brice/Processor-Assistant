"""
Financial Data Extractor - Pulls key numbers from scanned documents for DTI calculations
Integrates with ai_engine.py results to provide clean financial data for calculators.
"""

from typing import Dict, Any, Optional


class FinancialDataExtractor:
    """
    Extracts and aggregates financial data from scanned documents for DTI and closing cost calculations.
    Provides clean, ready-to-use financial data from AI engine results.
    """

    def __init__(self):
        self.required_fields = {
            "monthly_income": ["monthly_gross_income", "gross_monthly_income", "monthly_income"],
            "annual_income": ["annual_salary", "annual_income", "salary"],
            "monthly_debt": ["monthly_debt", "monthly_debt_payments", "total_monthly_debt"],
            "loan_amount": ["loan_amount", "requested_amount", "loan_amt"],
            "property_value": ["property_value", "appraised_value", "avm_value"],
            "credit_score": ["credit_score", "fico_score"],
            "down_payment": ["down_payment", "down_payment_amount"]
        }

    def extract_for_dti(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract financial data needed for DTI calculations.

        Args:
            scan_results: Results from AI engine scanning

        Returns:
            Clean financial data for DTI calculator
        """
        extracted_data = scan_results.get("extracted_data", {}) if scan_results else {}

        # Extract key DTI inputs
        monthly_income = self._extract_field(extracted_data, "monthly_income")
        annual_income = self._extract_field(extracted_data, "annual_income")
        monthly_debt = self._extract_field(extracted_data, "monthly_debt")

        # If we have annual income but no monthly, convert
        if not monthly_income and annual_income:
            monthly_income = annual_income / 12

        # Extract credit score for loan type recommendations
        credit_score = self._extract_field(extracted_data, "credit_score")

        result = {
            "monthly_gross_income": monthly_income or 0,
            "monthly_debt_payments": monthly_debt or 0,
            "credit_score": credit_score or 700,  # Default to good credit
            "source": "scanned_documents" if extracted_data else "manual",
            "confidence": self._calculate_confidence(extracted_data)
        }

        return result

    def extract_for_closing_costs(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract financial data needed for closing cost calculations.

        Args:
            scan_results: Results from AI engine scanning

        Returns:
            Clean financial data for closing cost calculator
        """
        extracted_data = scan_results.get("extracted_data", {}) if scan_results else {}

        # Extract key closing cost inputs
        loan_amount = self._extract_field(extracted_data, "loan_amount")
        property_value = self._extract_field(extracted_data, "property_value")
        down_payment = self._extract_field(extracted_data, "down_payment")

        # Infer loan type from credit score or other indicators
        credit_score = self._extract_field(extracted_data, "credit_score")
        loan_type = self._infer_loan_type(credit_score, loan_amount, property_value)

        result = {
            "loan_amount": loan_amount or 0,
            "property_value": property_value or 0,
            "down_payment": down_payment or 0,
            "loan_type": loan_type,
            "source": "scanned_documents" if extracted_data else "manual",
            "confidence": self._calculate_confidence(extracted_data)
        }

        return result

    def _extract_field(self, extracted_data: Dict[str, Any], field_name: str) -> Optional[float]:
        """Extract a specific field from extracted data, trying multiple variations."""
        if not extracted_data:
            return None

        field_variations = self.required_fields.get(field_name, [field_name])

        for variation in field_variations:
            value = extracted_data.get(variation)
            if value is not None:
                # Convert to float if it's a number
                try:
                    if isinstance(value, str):
                        # Remove currency symbols and commas
                        clean_value = value.replace("$", "").replace(",", "").strip()
                        return float(clean_value)
                    elif isinstance(value, (int, float)):
                        return float(value)
                except (ValueError, TypeError):
                    continue

        return None

    def _infer_loan_type(self, credit_score: Optional[int], loan_amount: Optional[float],
                        property_value: Optional[float]) -> str:
        """Infer the most likely loan type based on available data."""
        # Default to conventional
        loan_type = "conventional"

        # FHA typically for lower credit scores
        if credit_score and credit_score < 640:
            loan_type = "fha"

        # VA for military (we can't detect this directly, so stick with conventional)

        # Check LTV for refinance vs purchase hints
        if loan_amount and property_value and property_value > 0:
            ltv = (loan_amount / property_value) * 100
            if ltv < 80:  # Low LTV often indicates refinance
                loan_type = "refinance"
            else:  # High LTV often indicates purchase
                loan_type = "purchase"

        return loan_type

    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> str:
        """Calculate confidence level of extracted data."""
        if not extracted_data:
            return "low"

        # Count how many key fields we have
        key_fields = ["monthly_income", "loan_amount", "property_value", "credit_score"]
        found_fields = 0

        for field in key_fields:
            if self._extract_field(extracted_data, field) is not None:
                found_fields += 1

        confidence_ratio = found_fields / len(key_fields)

        if confidence_ratio >= 0.75:
            return "high"
        elif confidence_ratio >= 0.5:
            return "medium"
        else:
            return "low"

    def get_data_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of all extractable financial data.

        Args:
            scan_results: Results from AI engine scanning

        Returns:
            Summary of available financial data
        """
        dti_data = self.extract_for_dti(scan_results)
        closing_data = self.extract_for_closing_costs(scan_results)

        return {
            "dti_ready": dti_data["monthly_gross_income"] > 0,
            "closing_ready": closing_data["loan_amount"] > 0 and closing_data["property_value"] > 0,
            "dti_data": dti_data,
            "closing_data": closing_data,
            "overall_confidence": max(dti_data["confidence"], closing_data["confidence"],
                                    key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x, 0))
        }


def extract_financial_data(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to extract financial data from scan results."""
    extractor = FinancialDataExtractor()
    return extractor.get_data_summary(scan_results)