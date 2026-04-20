"""
Escrow Calculator - Closing costs and escrow analysis
Calculates estimated closing costs, escrow requirements, and cash needed to close.
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class EscrowCalculator:
    """
    Comprehensive escrow and closing cost calculator.
    Calculates all closing costs, escrow requirements, and cash to close.
    """

    def __init__(self):
        # Base closing cost estimates (as % of loan amount)
        self.closing_cost_rates = {
            "lender_fees": 0.75,      # Origination fee, processing, etc.
            "appraisal": 0.50,        # Appraisal fee
            "credit_report": 0.05,    # Credit report
            "flood_cert": 0.15,       # Flood certification
            "tax_service": 0.05,      # Tax service
            "recording_fees": 0.25,   # Recording fees
            "title_fees": 0.75,       # Title insurance and search
            "transfer_taxes": 0.75,   # Transfer taxes
            "survey": 0.25,          # Survey fee
            "inspection": 0.50,       # Home inspection
            "home_warranty": 0.35,    # Home warranty (optional)
            "prepaid_interest": 0.25, # Interest from closing to 1st payment
            "prepaid_taxes": 0.50,    # Property taxes (typically 2 months)
            "prepaid_insurance": 0.35,# Hazard insurance (typically 1 year)
            "escrow_reserves": 2.0,   # 2 months escrow reserves
        }

        # Regional cost adjustments
        self.regional_adjustments = {
            "high_cost": 1.25,   # High-cost areas (CA, NY, etc.)
            "standard": 1.0,     # Standard cost areas
            "low_cost": 0.85     # Low-cost rural areas
        }

        # FHA vs Conventional adjustments
        self.program_adjustments = {
            "conventional": 1.0,
            "fha": 1.1,          # FHA typically has higher costs
            "va": 0.9,           # VA often has lower costs
            "usda": 0.95
        }

    def calculate_closing_costs(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive closing costs.

        Args:
            loan_data: Dictionary with loan and property information

        Returns:
            Detailed closing cost breakdown
        """
        loan_amount = loan_data.get("loan_amount", 0)
        property_value = loan_data.get("property_value", 0)
        loan_type = loan_data.get("loan_type", "conventional").lower()
        location = loan_data.get("location", "standard")
        include_home_warranty = loan_data.get("include_home_warranty", False)

        if loan_amount <= 0:
            return {"error": "Invalid loan amount"}

        # Apply program and location adjustments
        program_mult = self.program_adjustments.get(loan_type, 1.0)
        location_mult = self.regional_adjustments.get(location, 1.0)
        total_mult = program_mult * location_mult

        # Calculate each cost component
        breakdown = {}
        total_closing_costs = 0

        for cost_type, rate in self.closing_cost_rates.items():
            # Skip optional items unless specified
            if cost_type == "home_warranty" and not include_home_warranty:
                continue

            amount = loan_amount * (rate / 100) * total_mult
            breakdown[cost_type] = round(amount, 2)
            total_closing_costs += amount

        # Calculate escrow reserves separately (monthly amount × months)
        monthly_payment = self._calculate_monthly_payment(loan_data)
        escrow_months = loan_data.get("escrow_months", 2)

        # Estimate escrow amount (property taxes + insurance)
        monthly_property_tax = loan_data.get("annual_property_tax", property_value * 0.01) / 12
        monthly_hazard_insurance = loan_data.get("annual_hazard_insurance", property_value * 0.0035) / 12
        monthly_escrow = monthly_property_tax + monthly_hazard_insurance

        escrow_reserves = monthly_escrow * escrow_months
        breakdown["escrow_reserves"] = round(escrow_reserves, 2)
        total_closing_costs += escrow_reserves

        # Calculate total cash needed
        down_payment = 0
        if loan_type != "refinance":
            # Purchase transaction
            down_payment_pct = loan_data.get("down_payment_pct", 20.0)
            down_payment = (property_value * down_payment_pct / 100)

        total_cash_needed = down_payment + total_closing_costs

        # Calculate cash-on-cash return metrics
        ltv = (loan_amount / property_value * 100) if property_value > 0 else 0
        cltv = ((loan_amount + total_cash_needed) / property_value * 100) if property_value > 0 else 0

        result = {
            "loan_amount": loan_amount,
            "property_value": property_value,
            "loan_type": loan_type,
            "location": location,
            "down_payment": round(down_payment, 2),
            "down_payment_pct": loan_data.get("down_payment_pct", 20.0),
            "breakdown": breakdown,
            "total_closing_costs": round(total_closing_costs, 2),
            "total_cash_needed": round(total_cash_needed, 2),
            "ltv_ratio": round(ltv, 2),
            "cltv_ratio": round(cltv, 2),
            "cost_to_loan_ratio": round((total_closing_costs / loan_amount) * 100, 2) if loan_amount > 0 else 0,
            "monthly_payment": round(monthly_payment, 2),
            "monthly_escrow": round(monthly_escrow, 2),
            "escrow_months": escrow_months
        }

        return result

    def _calculate_monthly_payment(self, loan_data: Dict) -> float:
        """Calculate estimated monthly mortgage payment."""
        loan_amount = loan_data.get("loan_amount", 0)
        interest_rate = loan_data.get("interest_rate", 6.5) / 100  # Convert to decimal
        loan_term_years = loan_data.get("loan_term_years", 30)

        if loan_amount <= 0 or interest_rate < 0:
            return 0

        # Monthly interest rate
        monthly_rate = interest_rate / 12

        # Number of payments
        num_payments = loan_term_years * 12

        # Mortgage payment formula: M = P[r(1+r)^n]/[(1+r)^n-1]
        if monthly_rate > 0:
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        else:
            # Interest-free loan
            monthly_payment = loan_amount / num_payments

        # Add estimated taxes and insurance (PITI)
        property_value = loan_data.get("property_value", 0)
        if property_value > 0:
            # Property tax estimate (1% of property value annually)
            annual_tax = property_value * 0.01
            monthly_tax = annual_tax / 12

            # Hazard insurance estimate (0.35% of property value annually)
            annual_insurance = property_value * 0.0035
            monthly_insurance = annual_insurance / 12

            monthly_payment += monthly_tax + monthly_insurance

        return monthly_payment

    def calculate_affordability(self, borrower_data: Dict[str, Any], loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate what loan amount a borrower can afford.

        Args:
            borrower_data: Borrower financial information
            loan_data: Loan parameters

        Returns:
            Affordability analysis
        """
        monthly_gross_income = borrower_data.get("monthly_gross_income", 0)
        monthly_debt = borrower_data.get("monthly_debt", 0)
        credit_score = borrower_data.get("credit_score", 700)

        if monthly_gross_income <= 0:
            return {"error": "Invalid income amount"}

        # Determine DTI limits based on credit score and loan type
        loan_type = loan_data.get("loan_type", "conventional").lower()
        dti_limit = self._get_dti_limit(credit_score, loan_type)

        # Calculate maximum housing payment
        max_housing_payment = monthly_gross_income * (dti_limit / 100) - monthly_debt
        max_housing_payment = max(max_housing_payment, 0)

        # Estimate loan amount based on housing payment
        interest_rate = loan_data.get("interest_rate", 6.5) / 100
        loan_term_years = loan_data.get("loan_term_years", 30)

        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12

        if monthly_rate > 0:
            max_loan_amount = max_housing_payment * ((1 - (1 + monthly_rate) ** (-num_payments)) / monthly_rate)
        else:
            max_loan_amount = max_housing_payment * num_payments

        # Estimate property value (assuming 20% down payment)
        estimated_property_value = max_loan_amount / 0.80

        # Calculate estimated closing costs
        closing_costs = self.calculate_closing_costs({
            "loan_amount": max_loan_amount,
            "property_value": estimated_property_value,
            "loan_type": loan_type,
            "location": loan_data.get("location", "standard")
        })

        total_cash_needed = closing_costs.get("total_cash_needed", 0)

        result = {
            "monthly_gross_income": monthly_gross_income,
            "monthly_debt": monthly_debt,
            "credit_score": credit_score,
            "dti_limit": dti_limit,
            "max_monthly_housing_payment": round(max_housing_payment, 2),
            "max_loan_amount": round(max_loan_amount, 2),
            "estimated_property_value": round(estimated_property_value, 2),
            "estimated_closing_costs": closing_costs.get("total_closing_costs", 0),
            "total_cash_needed": round(total_cash_needed, 2),
            "ltv_ratio": round((max_loan_amount / estimated_property_value) * 100, 2) if estimated_property_value > 0 else 0,
            "loan_type": loan_type
        }

        return result

    def _get_dti_limit(self, credit_score: int, loan_type: str) -> float:
        """Get DTI limit based on credit score and loan type."""
        base_limits = {
            "conventional": 43,
            "fha": 43,
            "va": 41,
            "usda": 41
        }

        base_limit = base_limits.get(loan_type, 43)

        # Adjust based on credit score
        if credit_score >= 760:
            return base_limit + 5  # Exceptional credit gets higher limits
        elif credit_score >= 700:
            return base_limit + 2  # Good credit gets slight increase
        elif credit_score >= 620:
            return base_limit  # Standard limits
        else:
            return base_limit - 5  # Poor credit gets lower limits

    def compare_loan_scenarios(self, scenarios: List[Dict]) -> Dict[str, Any]:
        """
        Compare multiple loan scenarios for cost analysis.

        Args:
            scenarios: List of loan scenario dictionaries

        Returns:
            Scenario comparison results
        """
        results = []

        for i, scenario in enumerate(scenarios):
            costs = self.calculate_closing_costs(scenario)

            results.append({
                "scenario": i + 1,
                "scenario_name": scenario.get("name", f"Scenario {i+1}"),
                "loan_amount": scenario.get("loan_amount", 0),
                "total_closing_costs": costs.get("total_closing_costs", 0),
                "total_cash_needed": costs.get("total_cash_needed", 0),
                "cost_to_loan_ratio": costs.get("cost_to_loan_ratio", 0),
                "monthly_payment": costs.get("monthly_payment", 0)
            })

        # Find best value scenario
        if results:
            best_value = min(results, key=lambda x: x["cost_to_loan_ratio"])
            lowest_cost = min(results, key=lambda x: x["total_closing_costs"])
            lowest_cash = min(results, key=lambda x: x["total_cash_needed"])

            comparison = {
                "scenarios": results,
                "best_value_ratio": best_value["scenario"],
                "lowest_closing_costs": lowest_cost["scenario"],
                "lowest_cash_needed": lowest_cash["scenario"],
                "total_scenarios": len(scenarios)
            }
        else:
            comparison = {"scenarios": [], "error": "No valid scenarios provided"}

        return comparison

    def generate_cost_estimate_report(self, calculation_results: Dict) -> str:
        """Generate a detailed closing cost estimate report."""
        results = calculation_results

        report = []
        report.append("CLOSING COST ESTIMATE REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        # Loan summary
        report.append("LOAN SUMMARY:")
        report.append(f"  Loan Amount: ${results.get('loan_amount', 0):,.2f}")
        report.append(f"  Property Value: ${results.get('property_value', 0):,.2f}")
        report.append(f"  LTV Ratio: {results.get('ltv_ratio', 0):.1f}%")
        report.append(f"  Loan Type: {results.get('loan_type', 'Unknown').title()}")
        report.append(f"  Location: {results.get('location', 'Unknown').title()}")
        report.append("")

        # Cost breakdown
        report.append("CLOSING COST BREAKDOWN:")
        breakdown = results.get("breakdown", {})
        for cost_type, amount in breakdown.items():
            display_name = cost_type.replace("_", " ").title()
            report.append("30")
        report.append("")

        # Totals
        report.append("TOTALS:")
        report.append(f"  Total Closing Costs: ${results.get('total_closing_costs', 0):,.2f}")
        report.append(f"  Down Payment: ${results.get('down_payment', 0):,.2f}")
        report.append(f"  Total Cash Needed: ${results.get('total_cash_needed', 0):,.2f}")
        report.append(f"  Cost-to-Loan Ratio: {results.get('cost_to_loan_ratio', 0):.1f}%")
        report.append("")

        # Monthly payments
        report.append("ESTIMATED MONTHLY PAYMENTS:")
        report.append(f"  Principal & Interest: ${results.get('monthly_payment', 0):,.2f}")
        report.append(f"  Escrow (Taxes & Insurance): ${results.get('monthly_escrow', 0):,.2f}")
        report.append("")

        report.append("NOTES:")
        report.append("• All estimates are approximate and may vary by lender")
        report.append("• Actual costs depend on specific property and location")
        report.append("• Additional fees may apply for special circumstances")
        report.append("• Consult with your lender for final closing cost estimates")

        return "\n".join(report)


def calculate_closing_costs(loan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to calculate closing costs."""
    calculator = EscrowCalculator()
    return calculator.calculate_closing_costs(loan_data)