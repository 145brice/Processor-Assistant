"""
DTI Calculator - Debt-to-Income & Closing Cost Calculator
Calculates DTI ratios and estimates closing costs for loan qualification.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP


class DTICalculator:
    """
    Comprehensive DTI (Debt-to-Income) and closing cost calculator.
    Calculates qualification ratios and total cash needed to close.
    """

    def __init__(self):
        # FHA/Housing debt ratios
        self.fha_front_end_limit = 31.0  # %
        self.fha_back_end_limit = 43.0   # %
        self.conventional_front_end_limit = 28.0  # %
        self.conventional_back_end_limit = 36.0   # %
        self.va_limit = 41.0  # %

        # Closing cost estimates (as % of loan amount)
        self.closing_cost_percentages = {
            "purchase": {
                "lender_fees": 0.75,
                "title_fees": 0.75,
                "appraisal": 0.50,
                "credit_report": 0.05,
                "flood_cert": 0.15,
                "tax_service": 0.05,
                "recording_fees": 0.25,
                "transfer_taxes": 0.75,
                "home_inspection": 0.50,
                "survey": 0.25,
                "prepaid_interest": 0.25,
                "homeowners_insurance": 0.35,
                "property_taxes": 0.50
            },
            "refinance": {
                "lender_fees": 0.75,
                "title_fees": 0.50,
                "appraisal": 0.50,
                "credit_report": 0.05,
                "flood_cert": 0.15,
                "recording_fees": 0.25,
                "prepaid_interest": 0.25,
                "homeowners_insurance": 0.35,
                "property_taxes": 0.50
            }
        }

    def calculate_dti(self, monthly_gross_income: float, monthly_debt_payments: float,
                     housing_payment: float = 0, loan_type: str = "conventional") -> Dict[str, Any]:
        """
        Calculate debt-to-income ratios.

        Args:
            monthly_gross_income: Total monthly gross income
            monthly_debt_payments: Monthly payments for all debts (excluding housing)
            housing_payment: Proposed monthly housing payment (PITI)
            loan_type: Type of loan (conventional, fha, va)

        Returns:
            DTI calculation results
        """
        if monthly_gross_income <= 0:
            return {"error": "Invalid income amount"}

        # Calculate front-end DTI (housing only)
        front_end_dti = (housing_payment / monthly_gross_income) * 100

        # Calculate back-end DTI (housing + all other debts)
        total_debt = monthly_debt_payments + housing_payment
        back_end_dti = (total_debt / monthly_gross_income) * 100

        # Get loan type limits
        limits = self._get_dti_limits(loan_type)

        # Determine qualification status
        front_end_status = "✅ Qualified" if front_end_dti <= limits["front_end"] else "❌ Exceeds limit"
        back_end_status = "✅ Qualified" if back_end_dti <= limits["back_end"] else "❌ Exceeds limit"

        overall_qualified = front_end_dti <= limits["front_end"] and back_end_dti <= limits["back_end"]

        result = {
            "monthly_gross_income": monthly_gross_income,
            "monthly_debt_payments": monthly_debt_payments,
            "housing_payment": housing_payment,
            "total_monthly_debt": total_debt,
            "front_end_dti": round(front_end_dti, 2),
            "back_end_dti": round(back_end_dti, 2),
            "front_end_limit": limits["front_end"],
            "back_end_limit": limits["back_end"],
            "front_end_status": front_end_status,
            "back_end_status": back_end_status,
            "overall_qualified": overall_qualified,
            "loan_type": loan_type,
            "recommendations": []
        }

        # Generate recommendations
        result["recommendations"] = self._generate_dti_recommendations(result)

        return result

    def _get_dti_limits(self, loan_type: str) -> Dict[str, float]:
        """Get DTI limits for loan type."""
        limits = {
            "conventional": {"front_end": self.conventional_front_end_limit, "back_end": self.conventional_back_end_limit},
            "fha": {"front_end": self.fha_front_end_limit, "back_end": self.fha_back_end_limit},
            "va": {"front_end": self.va_limit, "back_end": self.va_limit},
            "usda": {"front_end": 29.0, "back_end": 41.0},
            "portfolio": {"front_end": 33.0, "back_end": 45.0}
        }
        return limits.get(loan_type.lower(), limits["conventional"])

    def _generate_dti_recommendations(self, result: Dict) -> List[str]:
        """Generate DTI-based recommendations."""
        recommendations = []

        front_end_dti = result["front_end_dti"]
        back_end_dti = result["back_end_dti"]
        front_end_limit = result["front_end_limit"]
        back_end_limit = result["back_end_limit"]

        if front_end_dti > front_end_limit:
            excess = front_end_dti - front_end_limit
            recommendations.append(f"Front-end DTI exceeds limit by {excess:.1f}%. Consider lower loan amount or higher down payment.")

        if back_end_dti > back_end_limit:
            excess = back_end_dti - back_end_limit
            recommendations.append(f"Back-end DTI exceeds limit by {excess:.1f}%. Consider debt consolidation or higher income verification.")

        if not result["overall_qualified"]:
            recommendations.append("Loan may not qualify based on current DTI ratios. Consider lender overlays or exceptions.")

        # Additional recommendations
        if back_end_dti > 40:
            recommendations.append("High DTI may require lender approval or additional documentation.")

        if front_end_dti < 20:
            recommendations.append("Very low front-end DTI may indicate room for higher loan amount.")

        return recommendations

    def calculate_closing_costs(self, loan_amount: float, property_value: float,
                              loan_type: str = "purchase", location: str = "standard") -> Dict[str, Any]:
        """
        Calculate estimated closing costs.

        Args:
            loan_amount: Loan amount
            property_value: Property value/appraised value
            loan_type: "purchase" or "refinance"
            location: Location for tax adjustments

        Returns:
            Detailed closing cost breakdown
        """
        if loan_amount <= 0:
            return {"error": "Invalid loan amount"}

        costs = self.closing_cost_percentages.get(loan_type.lower(), self.closing_cost_percentages["purchase"])

        # Calculate each cost component
        breakdown = {}
        total_costs = 0

        for cost_type, percentage in costs.items():
            amount = loan_amount * (percentage / 100)
            breakdown[cost_type] = round(amount, 2)
            total_costs += amount

        # Adjust for location-specific costs
        total_costs = self._adjust_for_location(total_costs, location)

        # Calculate total cash needed to close
        down_payment = 0
        if loan_type.lower() == "purchase":
            # Assume 20% down payment for calculation
            down_payment = property_value * 0.20

        total_cash_needed = down_payment + total_costs

        # Calculate cash-on-cash return metrics
        if property_value > 0:
            ltv = (loan_amount / property_value) * 100
            cltv = ((loan_amount + total_costs) / property_value) * 100
        else:
            ltv = cltv = 0

        result = {
            "loan_amount": loan_amount,
            "property_value": property_value,
            "loan_type": loan_type,
            "location": location,
            "breakdown": breakdown,
            "total_closing_costs": round(total_costs, 2),
            "down_payment": round(down_payment, 2),
            "total_cash_needed": round(total_cash_needed, 2),
            "ltv_ratio": round(ltv, 2),
            "cltv_ratio": round(cltv, 2),
            "cost_to_loan_ratio": round((total_costs / loan_amount) * 100, 2)
        }

        return result

    def _adjust_for_location(self, total_costs: float, location: str) -> float:
        """Adjust closing costs based on location."""
        adjustments = {
            "high_cost": 1.25,  # 25% higher in high-cost areas
            "low_cost": 0.85,   # 15% lower in low-cost areas
            "standard": 1.0     # No adjustment
        }

        multiplier = adjustments.get(location.lower(), 1.0)
        return total_costs * multiplier

    def calculate_affordability(self, monthly_gross_income: float, monthly_debt: float,
                              interest_rate: float, loan_term_years: int = 30,
                              loan_type: str = "conventional") -> Dict[str, Any]:
        """
        Calculate maximum loan amount borrower can afford.

        Args:
            monthly_gross_income: Monthly gross income
            monthly_debt: Existing monthly debt payments
            interest_rate: Annual interest rate (as decimal)
            loan_term_years: Loan term in years
            loan_type: Type of loan

        Returns:
            Affordability analysis
        """
        if monthly_gross_income <= 0:
            return {"error": "Invalid income"}

        limits = self._get_dti_limits(loan_type)

        # Calculate maximum housing payment based on back-end DTI
        max_total_debt = monthly_gross_income * (limits["back_end"] / 100)
        max_housing_payment = max_total_debt - monthly_debt

        # Ensure housing payment is reasonable
        max_housing_payment = max(max_housing_payment, 0)

        # Calculate maximum loan amount based on housing payment
        # Using simple mortgage formula: M = P[r(1+r)^n]/[(1+r)^n-1]
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12

        if monthly_rate > 0:
            max_loan_amount = max_housing_payment * ((1 - (1 + monthly_rate) ** (-num_payments)) / monthly_rate)
        else:
            max_loan_amount = max_housing_payment * num_payments

        # Estimate property value (assuming 80% LTV)
        estimated_property_value = max_loan_amount / 0.80

        result = {
            "monthly_gross_income": monthly_gross_income,
            "monthly_debt": monthly_debt,
            "available_for_housing": max_housing_payment,
            "back_end_dti_limit": limits["back_end"],
            "max_loan_amount": round(max_loan_amount, 2),
            "estimated_property_value": round(estimated_property_value, 2),
            "interest_rate": interest_rate,
            "loan_term_years": loan_term_years,
            "loan_type": loan_type
        }

        return result

    def compare_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare multiple DTI scenarios.

        Args:
            scenarios: List of scenario dictionaries with income, debt, housing data

        Returns:
            Comparison analysis
        """
        results = []
        best_scenario = None
        best_dti = float('inf')

        for i, scenario in enumerate(scenarios):
            result = self.calculate_dti(
                scenario.get("monthly_gross_income", 0),
                scenario.get("monthly_debt_payments", 0),
                scenario.get("housing_payment", 0),
                scenario.get("loan_type", "conventional")
            )

            results.append({
                "scenario": i + 1,
                "data": scenario,
                "results": result
            })

            # Find best qualified scenario
            if result.get("overall_qualified", False):
                total_dti = result.get("back_end_dti", 100)
                if total_dti < best_dti:
                    best_dti = total_dti
                    best_scenario = i + 1

        return {
            "scenarios": results,
            "best_qualified_scenario": best_scenario,
            "total_scenarios": len(scenarios),
            "qualified_scenarios": sum(1 for r in results if r["results"].get("overall_qualified", False))
        }

    def get_lender_requirements(self, lender_name: str = "standard") -> Dict[str, Any]:
        """Get specific lender DTI requirements."""
        lenders = {
            "standard": {
                "conventional": {"front_end": 28, "back_end": 36},
                "fha": {"front_end": 31, "back_end": 43},
                "va": {"front_end": 41, "back_end": 41}
            },
            "portfolio": {
                "conventional": {"front_end": 33, "back_end": 45},
                "fha": {"front_end": 35, "back_end": 50},
                "va": {"front_end": 45, "back_end": 50}
            },
            "hard_money": {
                "conventional": {"front_end": 50, "back_end": 65}
            }
        }

        return lenders.get(lender_name.lower(), lenders["standard"])