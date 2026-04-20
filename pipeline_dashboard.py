"""
Pipeline Dashboard with Deadline Alerts
Track loan pipeline and get alerts for important dates.
"""

import os
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class PipelineDashboard:
    """
    Dashboard for tracking loan pipeline with deadline alerts.
    Monitors loan stages, closing dates, and sends alerts.
    """

    # Loan stages in order
    STAGES = [
        "Application",
        "Pre-Qualification",
        "Processing",
        "Underwriting",
        "Conditional Approval",
        "Cleared to Close",
        "Closing",
        "Funded"
    ]

    def __init__(self):
        self.alert_thresholds = {
            "urgent": 3,      # Days until closing for urgent alert
            "warning": 7,     # Days for warning alert
            "notice": 14      # Days for notice alert
        }

    def get_alerts(self, loans: List[Dict]) -> Dict[str, Any]:
        """
        Get all alerts for a list of loans.

        Args:
            loans: List of loan dictionaries with status and dates

        Returns:
            Dictionary with categorized alerts
        """
        alerts = {
            "urgent": [],      # Closing in 3 days or less
            "warning": [],     # Closing in 7 days
            "notice": [],      # Closing in 14 days
            "stale": [],       # No activity in 30+ days
            "expired": [],     # Lock or rate expired
            "total": 0
        }

        for loan in loans:
            # Check closing date alerts
            days_to_close = loan.get("days_to_close", 999)

            if days_to_close <= self.alert_thresholds["urgent"]:
                alerts["urgent"].append({
                    "loan_id": loan.get("id"),
                    "borrower": loan.get("borrower"),
                    "days_remaining": days_to_close,
                    "message": f"🚨 URGENT: {loan.get('borrower')} closing in {days_to_close} days!"
                })
            elif days_to_close <= self.alert_thresholds["warning"]:
                alerts["warning"].append({
                    "loan_id": loan.get("id"),
                    "borrower": loan.get("borrower"),
                    "days_remaining": days_to_close,
                    "message": f"⚠️ {loan.get('borrower')} closing in {days_to_close} days"
                })
            elif days_to_close <= self.alert_thresholds["notice"]:
                alerts["notice"].append({
                    "loan_id": loan.get("id"),
                    "borrower": loan.get("borrower"),
                    "days_remaining": days_to_close,
                    "message": f"📅 {loan.get('borrower')} closing in {days_to_close} days"
                })

            # Check for stale loans (no activity)
            last_activity = loan.get("last_activity_date")
            if last_activity:
                try:
                    last_date = datetime.fromisoformat(last_activity)
                    days_inactive = (datetime.now() - last_date).days
                    if days_inactive > 30:
                        alerts["stale"].append({
                            "loan_id": loan.get("id"),
                            "borrower": loan.get("borrower"),
                            "days_inactive": days_inactive,
                            "message": f"⏰ {loan.get('borrower')} - {days_inactive} days inactive"
                        })
                except:
                    pass

            # Check for expired locks/rates
            lock_expiry = loan.get("lock_expiry_date")
            if lock_expiry:
                try:
                    expiry_date = datetime.fromisoformat(lock_expiry)
                    days_until_expiry = (expiry_date - datetime.now()).days
                    if days_until_expiry < 0:
                        alerts["expired"].append({
                            "loan_id": loan.get("id"),
                            "borrower": loan.get("borrower"),
                            "message": f"🔒 {loan.get('borrower')} - Rate/lock EXPIRED"
                        })
                    elif days_until_expiry <= 3:
                        alerts["urgent"].append({
                            "loan_id": loan.get("id"),
                            "borrower": loan.get("borrower"),
                            "message": f"🔒 {loan.get('borrower')} - Rate expires in {days_until_expiry} days!"
                        })
                except:
                    pass

        # Calculate total
        alerts["total"] = (
            len(alerts["urgent"]) +
            len(alerts["warning"]) +
            len(alerts["notice"]) +
            len(alerts["stale"]) +
            len(alerts["expired"])
        )

        return alerts

    def get_pipeline_summary(self, loans: List[Dict]) -> Dict[str, Any]:
        """Get summary statistics for the pipeline."""
        summary = {
            "total_loans": len(loans),
            "by_stage": {},
            "total_volume": 0,
            "average_days_in_pipeline": 0,
            "closing_this_week": 0,
            "closing_this_month": 0
        }

        total_days = 0

        for loan in loans:
            # Count by stage
            stage = loan.get("stage", "Unknown")
            summary["by_stage"][stage] = summary["by_stage"].get(stage, 0) + 1

            # Add to volume
            loan_amount = loan.get("loan_amount", 0)
            if loan_amount:
                summary["total_volume"] += loan_amount

            # Track days in pipeline
            created = loan.get("created_date")
            if created:
                try:
                    created_date = datetime.fromisoformat(created)
                    days = (datetime.now() - created_date).days
                    total_days += days
                except:
                    pass

            # Check closing timing
            days_to_close = loan.get("days_to_close", 999)
            if days_to_close <= 7:
                summary["closing_this_week"] += 1
            if days_to_close <= 30:
                summary["closing_this_month"] += 1

        # Calculate average
        if loans:
            summary["average_days_in_pipeline"] = total_days / len(loans)

        return summary

    def get_stage_progression(self, loans: List[Dict]) -> List[Dict]:
        """Show loans grouped by their stage progression."""
        staged_loans = {stage: [] for stage in self.STAGES}

        for loan in loans:
            stage = loan.get("stage", "Application")
            if stage in staged_loans:
                staged_loans[stage].append({
                    "loan_id": loan.get("id"),
                    "borrower": loan.get("borrower"),
                    "loan_amount": loan.get("loan_amount"),
                    "days_to_close": loan.get("days_to_close", "N/A")
                })

        return staged_loans

    def generate_alert_report(self, alerts: Dict) -> str:
        """Generate a text report of all alerts."""
        report = []
        report.append("=" * 50)
        report.append("PIPELINE ALERTS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 50)
        report.append("")

        if alerts["urgent"]:
            report.append(f"🚨 URGENT ({len(alerts['urgent'])}):")
            for alert in alerts["urgent"]:
                report.append(f"  - {alert['message']}")
            report.append("")

        if alerts["warning"]:
            report.append(f"⚠️ WARNINGS ({len(alerts['warning'])}):")
            for alert in alerts["warning"]:
                report.append(f"  - {alert['message']}")
            report.append("")

        if alerts["notice"]:
            report.append(f"📅 NOTICES ({len(alerts['notice'])}):")
            for alert in alerts["notice"]:
                report.append(f"  - {alert['message']}")
            report.append("")

        if alerts["stale"]:
            report.append(f"⏰ STALE LOANS ({len(alerts['stale'])}):")
            for alert in alerts["stale"]:
                report.append(f"  - {alert['message']}")
            report.append("")

        if alerts["expired"]:
            report.append(f"🔒 EXPIRED ({len(alerts['expired'])}):")
            for alert in alerts["expired"]:
                report.append(f"  - {alert['message']}")
            report.append("")

        report.append(f"TOTAL ALERTS: {alerts['total']}")
        report.append("=" * 50)

        return "\n".join(report)


def get_pipeline_alerts(loans: List[Dict]) -> Dict[str, Any]:
    """Quick function to get pipeline alerts."""
    dashboard = PipelineDashboard()
    return dashboard.get_alerts(loans)


def get_pipeline_summary(loans: List[Dict]) -> Dict[str, Any]:
    """Quick function to get pipeline summary."""
    dashboard = PipelineDashboard()
    return dashboard.get_pipeline_summary(loans)