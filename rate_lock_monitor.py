"""
Rate Lock Monitor - Track interest rate locks and expiration alerts
Monitors rate locks, calculates float-down options, and alerts on expirations.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class RateLockMonitor:
    """
    Monitors interest rate locks, expiration dates, and float-down opportunities.
    Provides alerts and recommendations for rate lock management.
    """

    def __init__(self):
        self.lock_types = {
            "mandatory": {"days": 30, "description": "Standard mandatory lock"},
            "best_efforts": {"days": 45, "description": "Best efforts lock"},
            "extended": {"days": 60, "description": "Extended lock period"}
        }

        self.alert_thresholds = {
            "critical": 3,   # Days until lock expires
            "warning": 7,    # Days for warning
            "notice": 14     # Days for notice
        }

    def monitor_lock(self, loan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor a rate lock for expiration and opportunities.

        Args:
            loan_data: Dictionary with lock information

        Returns:
            Lock status and recommendations
        """
        lock_date = loan_data.get("lock_date")
        lock_expiry = loan_data.get("lock_expiry_date")
        locked_rate = loan_data.get("locked_rate", 0)
        lock_days = loan_data.get("lock_days", 30)

        if not lock_expiry:
            return {"status": "No lock information", "alerts": []}

        # Calculate days until expiry
        try:
            expiry_date = datetime.fromisoformat(lock_expiry)
            days_until_expiry = (expiry_date - datetime.now()).days
        except:
            return {"status": "Invalid expiry date", "alerts": []}

        # Determine status
        if days_until_expiry < 0:
            status = "EXPIRED"
            alerts = [{"type": "critical", "message": f"🔴 RATE LOCK EXPIRED {abs(days_until_expiry)} days ago!"}]
        elif days_until_expiry <= self.alert_thresholds["critical"]:
            status = "CRITICAL"
            alerts = [{"type": "critical", "message": f"🚨 Rate lock expires in {days_until_expiry} days!"}]
        elif days_until_expiry <= self.alert_thresholds["warning"]:
            status = "WARNING"
            alerts = [{"type": "warning", "message": f"⚠️ Rate lock expires in {days_until_expiry} days"}]
        elif days_until_expiry <= self.alert_thresholds["notice"]:
            status = "NOTICE"
            alerts = [{"type": "notice", "message": f"📅 Rate lock expires in {days_until_expiry} days"}]
        else:
            status = "ACTIVE"
            alerts = []

        # Check for float-down opportunities
        current_market_rate = loan_data.get("current_market_rate", locked_rate)
        float_down_available = current_market_rate < locked_rate

        if float_down_available:
            rate_diff = locked_rate - current_market_rate
            alerts.append({
                "type": "opportunity",
                "message": f"💰 Float-down opportunity: {rate_diff:.3f}% lower rate available"
            })

        # Recommendations
        recommendations = self._generate_lock_recommendations(days_until_expiry, float_down_available)

        return {
            "status": status,
            "days_until_expiry": days_until_expiry,
            "locked_rate": locked_rate,
            "alerts": alerts,
            "float_down_available": float_down_available,
            "recommendations": recommendations
        }

    def _generate_lock_recommendations(self, days_left: int, float_down_available: bool) -> List[str]:
        """Generate recommendations based on lock status."""
        recommendations = []

        if days_left < 0:
            recommendations.append("Contact lender immediately to re-lock rate")
            recommendations.append("Document any rate increase and inform borrower")
        elif days_left <= 3:
            recommendations.append("Prepare rate extension or re-lock options")
            recommendations.append("Notify borrower of impending lock expiry")
        elif days_left <= 7:
            recommendations.append("Review current market rates for potential float-down")
            recommendations.append("Prepare lock extension paperwork if needed")

        if float_down_available:
            recommendations.append("Evaluate float-down option with borrower")
            recommendations.append("Calculate cost-benefit of rate reduction vs. extension")

        if days_left > 30:
            recommendations.append("Monitor market conditions for optimal lock timing")

        return recommendations

    def calculate_lock_costs(self, loan_amount: float, lock_days: int, lock_type: str = "mandatory") -> Dict[str, Any]:
        """Calculate estimated costs for different lock periods."""
        # Simplified cost calculation (real costs vary by lender)
        base_fee = 500  # Base lock fee
        daily_rate = 0.5  # Cost per day for extended locks

        if lock_type == "extended":
            additional_days = max(0, lock_days - 30)
            total_fee = base_fee + (additional_days * daily_rate)
        else:
            total_fee = base_fee

        # Per thousand cost
        cost_per_thousand = (total_fee / loan_amount) * 1000

        return {
            "lock_days": lock_days,
            "total_fee": round(total_fee, 2),
            "cost_per_thousand": round(cost_per_thousand, 2),
            "breakdown": {
                "base_fee": base_fee,
                "additional_days": max(0, lock_days - 30),
                "daily_rate": daily_rate
            }
        }

    def batch_monitor_locks(self, loans: List[Dict]) -> Dict[str, Any]:
        """Monitor rate locks for multiple loans."""
        results = {
            "total_loans": len(loans),
            "expired_locks": 0,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "float_down_opportunities": 0,
            "loan_results": []
        }

        for loan in loans:
            lock_result = self.monitor_lock(loan)
            results["loan_results"].append({
                "loan_id": loan.get("loan_id"),
                "borrower": loan.get("borrower_name"),
                "lock_status": lock_result["status"],
                "days_left": lock_result.get("days_until_expiry", 0),
                "alerts": lock_result["alerts"]
            })

            if lock_result["status"] == "EXPIRED":
                results["expired_locks"] += 1
            elif lock_result["status"] == "CRITICAL":
                results["critical_alerts"] += 1
            elif lock_result["status"] == "WARNING":
                results["warning_alerts"] += 1

            if lock_result.get("float_down_available", False):
                results["float_down_opportunities"] += 1

        return results

    def generate_lock_report(self, monitoring_results: Dict) -> str:
        """Generate a comprehensive rate lock monitoring report."""
        report = []
        report.append("RATE LOCK MONITORING REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")

        summary = monitoring_results
        report.append("SUMMARY:")
        report.append(f"  Total Loans Monitored: {summary['total_loans']}")
        report.append(f"  Expired Locks: {summary['expired_locks']}")
        report.append(f"  Critical Alerts: {summary['critical_alerts']}")
        report.append(f"  Warning Alerts: {summary['warning_alerts']}")
        report.append(f"  Float-Down Opportunities: {summary['float_down_opportunities']}")
        report.append("")

        if summary["expired_locks"] > 0 or summary["critical_alerts"] > 0:
            report.append("CRITICAL ISSUES:")
            for loan in summary["loan_results"]:
                if loan["lock_status"] in ["EXPIRED", "CRITICAL"]:
                    report.append(f"  🚨 {loan['borrower']} ({loan['loan_id']}): {loan['lock_status']} - {loan['days_left']} days")
            report.append("")

        if summary["float_down_opportunities"] > 0:
            report.append("FLOAT-DOWN OPPORTUNITIES:")
            for loan in summary["loan_results"]:
                alerts = [a for a in loan["alerts"] if a.get("type") == "opportunity"]
                if alerts:
                    report.append(f"  💰 {loan['borrower']} ({loan['loan_id']}): {alerts[0]['message']}")
            report.append("")

        report.append("RECOMMENDATIONS:")
        if summary["expired_locks"] > 0:
            report.append("  • Contact lenders immediately for expired locks")
        if summary["critical_alerts"] > 0:
            report.append("  • Prepare lock extensions for critical alerts")
        if summary["float_down_opportunities"] > 0:
            report.append("  • Evaluate float-down options with borrowers")
        if summary["expired_locks"] == 0 and summary["critical_alerts"] == 0:
            report.append("  • All rate locks are in good standing")

        return "\n".join(report)


def monitor_rate_lock(loan_data: Dict) -> Dict[str, Any]:
    """Quick function to monitor a single rate lock."""
    monitor = RateLockMonitor()
    return monitor.monitor_lock(loan_data)