"""
Auto Data Entry - Automatically fill forms from extracted document data
Uses AI-extracted information to populate loan application forms.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime


class AutoDataEntry:
    """
    Automatically fills loan application forms using extracted document data.
    Maps document fields to form fields with intelligent matching.
    """

    def __init__(self):
        # Field mapping between document extraction and form fields
        self.field_mapping = {
            # Borrower Information
            "borrower_name": ["borrower_full_name", "applicant_name", "full_name"],
            "borrower_ssn": ["social_security_number", "ssn", "tax_id"],
            "borrower_dob": ["date_of_birth", "birth_date", "dob"],
            "borrower_phone": ["home_phone", "phone_number", "telephone"],
            "borrower_email": ["email_address", "email"],
            "borrower_address": ["home_address", "residential_address", "current_address"],

            # Employment Information
            "employer_name": ["employer", "company_name", "employer_name"],
            "job_title": ["position", "title", "occupation"],
            "employment_start_date": ["start_date", "employed_since", "hire_date"],
            "years_employed": ["years_at_job", "tenure"],
            "monthly_income": ["gross_monthly_income", "monthly_gross"],
            "annual_income": ["annual_salary", "annual_income"],

            # Asset Information
            "bank_name": ["financial_institution", "bank"],
            "account_number": ["acct_number", "account_num"],
            "account_balance": ["balance", "current_balance"],
            "account_type": ["acct_type", "type"],

            # Income Information
            "pay_period": ["pay_frequency", "pay_cycle"],
            "ytd_income": ["year_to_date", "ytd_earnings"],
            "net_pay": ["take_home", "net_amount"],

            # Property Information (if applicable)
            "property_address": ["property_addr", "subject_property"],
            "property_value": ["appraised_value", "property_value"],
            "loan_amount": ["loan_amt", "requested_amount"],
        }

    def fill_form(self, extracted_data: Dict[str, Any], form_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fill a form template using extracted document data.

        Args:
            extracted_data: Data extracted from documents
            form_template: Empty form template with field names

        Returns:
            Filled form with populated fields
        """
        filled_form = form_template.copy()

        # Direct field mapping
        for doc_field, form_fields in self.field_mapping.items():
            if doc_field in extracted_data and extracted_data[doc_field] is not None:
                value = extracted_data[doc_field]

                # Try to fill matching form fields
                for form_field in form_fields:
                    if form_field in filled_form and not filled_form[form_field]:
                        filled_form[form_field] = self._format_value(value, form_field)
                        break

        # Intelligent field filling for unmapped fields
        self._intelligent_fill(extracted_data, filled_form)

        # Calculate derived fields
        self._calculate_derived_fields(filled_form)

        return filled_form

    def _format_value(self, value: Any, field_name: str) -> Any:
        """Format extracted values appropriately for form fields."""
        if value is None:
            return None

        # Currency formatting
        if "amount" in field_name.lower() or "income" in field_name.lower() or "salary" in field_name.lower():
            if isinstance(value, (int, float)):
                return f"${value:,.2f}"

        # Date formatting
        if "date" in field_name.lower() and isinstance(value, str):
            try:
                # Try to parse and reformat date
                parsed_date = self._parse_date(value)
                if parsed_date:
                    return parsed_date.strftime("%m/%d/%Y")
            except:
                pass

        # Phone number formatting
        if "phone" in field_name.lower() and isinstance(value, str):
            return self._format_phone(value)

        # SSN formatting
        if "ssn" in field_name.lower() or "social" in field_name.lower():
            return self._format_ssn(value)

        return value

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object."""
        date_patterns = [
            r"(\d{1,2})/(\d{1,2})/(\d{4})",  # MM/DD/YYYY
            r"(\d{1,2})-(\d{1,2})-(\d{4})",  # MM-DD-YYYY
            r"(\d{4})/(\d{1,2})/(\d{1,2})",  # YYYY/MM/DD
            r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if len(match.groups()) == 3:
                        month, day, year = map(int, match.groups())
                        if year > 1900 and year < 2100:
                            return datetime(year, month, day)
                except ValueError:
                    continue

        return None

    def _format_phone(self, phone_str: str) -> str:
        """Format phone number."""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone_str)

        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

        return phone_str  # Return original if can't format

    def _format_ssn(self, ssn_str: str) -> str:
        """Format SSN."""
        digits = re.sub(r'\D', '', str(ssn_str))

        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"

        return str(ssn_str)

    def _intelligent_fill(self, extracted_data: Dict, filled_form: Dict):
        """Use intelligent matching for unmapped fields."""
        unmapped_fields = [k for k, v in filled_form.items() if not v]

        for form_field in unmapped_fields:
            # Try fuzzy matching with extracted data keys
            best_match = self._find_best_match(form_field, list(extracted_data.keys()))
            if best_match and extracted_data[best_match] is not None:
                filled_form[form_field] = self._format_value(extracted_data[best_match], form_field)

    def _find_best_match(self, form_field: str, doc_fields: List[str]) -> Optional[str]:
        """Find the best matching document field for a form field."""
        form_clean = re.sub(r'[^a-zA-Z]', '', form_field.lower())

        best_match = None
        best_score = 0

        for doc_field in doc_fields:
            doc_clean = re.sub(r'[^a-zA-Z]', '', doc_field.lower())

            # Exact substring match gets high score
            if form_clean in doc_clean or doc_clean in form_clean:
                score = len(set(form_clean) & set(doc_clean)) / len(set(form_clean) | set(doc_clean))
                if score > best_score:
                    best_score = score
                    best_match = doc_field

        return best_match if best_score > 0.3 else None

    def _calculate_derived_fields(self, filled_form: Dict):
        """Calculate derived fields based on filled data."""
        # Calculate debt-to-income if monthly income and debts are available
        if (filled_form.get("monthly_gross_income") and
            filled_form.get("monthly_debt_payments")):

            try:
                income = self._parse_currency(filled_form["monthly_gross_income"])
                debt = self._parse_currency(filled_form["monthly_debt_payments"])

                if income and income > 0:
                    dti = (debt / income) * 100
                    filled_form["debt_to_income_ratio"] = f"{dti:.1f}%"
            except:
                pass

        # Calculate loan-to-value if available
        if (filled_form.get("loan_amount") and
            filled_form.get("appraised_value")):

            try:
                loan_amt = self._parse_currency(filled_form["loan_amount"])
                appraised = self._parse_currency(filled_form["appraised_value"])

                if appraised and appraised > 0:
                    ltv = (loan_amt / appraised) * 100
                    filled_form["loan_to_value_ratio"] = f"{ltv:.1f}%"
            except:
                pass

    def _parse_currency(self, currency_str: str) -> Optional[float]:
        """Parse currency string to float."""
        if isinstance(currency_str, (int, float)):
            return float(currency_str)

        if isinstance(currency_str, str):
            # Remove currency symbols and commas
            clean = re.sub(r'[$,]', '', currency_str.strip())
            try:
                return float(clean)
            except ValueError:
                return None

        return None

    def get_fill_statistics(self, original_form: Dict, filled_form: Dict) -> Dict[str, Any]:
        """Get statistics about form filling completion."""
        total_fields = len(original_form)
        filled_fields = sum(1 for v in filled_form.values() if v is not None and str(v).strip())

        return {
            "total_fields": total_fields,
            "filled_fields": filled_fields,
            "completion_percentage": (filled_fields / total_fields) * 100 if total_fields > 0 else 0,
            "unfilled_fields": [k for k, v in filled_form.items() if not v]
        }

    def validate_filled_form(self, filled_form: Dict) -> List[str]:
        """Validate filled form for completeness and consistency."""
        errors = []

        # Required field checks
        required_fields = ["borrower_name", "borrower_ssn", "monthly_income"]
        for field in required_fields:
            if not filled_form.get(field):
                errors.append(f"Missing required field: {field}")

        # SSN format validation
        ssn = filled_form.get("borrower_ssn", "")
        if ssn and not re.match(r'^\d{3}-\d{2}-\d{4}$', str(ssn)):
            errors.append("SSN format should be XXX-XX-XXXX")

        # Phone format validation
        phone = filled_form.get("borrower_phone", "")
        if phone and not re.match(r'^\(\d{3}\) \d{3}-\d{4}$', str(phone)):
            errors.append("Phone format should be (XXX) XXX-XXXX")

        # Income validation
        monthly_income = filled_form.get("monthly_gross_income")
        if monthly_income:
            try:
                income_val = self._parse_currency(monthly_income)
                if income_val and income_val < 1000:
                    errors.append("Monthly income seems unusually low")
            except:
                errors.append("Invalid monthly income format")

        return errors