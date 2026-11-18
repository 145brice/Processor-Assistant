// Sidebar structure. Mirrors show_sidebar() in app.py (see APP_INVENTORY.md "Sidebar").
export interface NavItem { label: string; href: string }
export interface NavGroup { label: string; items: NavItem[] }

const tool = (label: string, key: string): NavItem => ({ label, href: `/tools/${key}` });

export const PRIMARY_NAV: NavItem[] = [
  { label: "Scanner", href: "/scanner" },
  { label: "Pipeline - saved scans", href: "/pipeline" },
  { label: "Overview", href: "/overview" },
];

/** Shown inside the collapsed "More Tools" group when me.features.more_tools is true. */
export const MORE_TOOLS: NavGroup[] = [
  {
    label: "Workspace",
    items: [tool("Team", "team"), { label: "Usage", href: "/settings/usage" }, { label: "History", href: "/history" }],
  },
  {
    label: "Quick Tools",
    items: [
      tool("Loan Snapshot", "snapshot"), tool("Report Issue", "report_issue"),
      tool("Missing Docs", "missing_docs"), tool("Doc Expiry", "doc_expiry"),
      tool("Spanish Reply", "spanish_reply"),
    ],
  },
  {
    label: "Advanced Tools",
    items: [
      tool("Income Verifier", "income_verifier"), tool("Auto Data Entry", "auto_data_entry"),
      tool("Credit Summary", "credit_summary"), tool("DTI Calculator", "dti_calculator"),
      tool("Condition Clearer", "condition_clearer"), tool("Compliance Checker", "compliance_checker"),
    ],
  },
  {
    label: "Pipeline Advanced",
    items: [
      tool("Closing Package", "closing_package"), tool("Guideline Checker", "guideline_checker"),
      tool("Fraud Detector", "fraud_detector"), tool("Multi-Borrower", "multi_borrower"),
      tool("LOS Export", "los_export"),
    ],
  },
  {
    label: "Advanced Automation",
    items: [
      tool("Rate Lock Monitor", "rate_lock_monitor"), tool("Underwriting Tracker", "underwriting_tracker"),
      tool("Document Classifier", "document_classifier"), tool("Escrow Calculator", "escrow_calculator"),
    ],
  },
];

export const SETTINGS_NAV: NavItem[] = [
  { label: "Beta offer", href: "/pricing" },
  { label: "Usage / Billing", href: "/settings/usage" },
  { label: "AI Settings", href: "/settings/ai" },
];

/** Route key -> task that builds the tool page. Same table as backend routers/tools.py. */
export const TOOL_TASKS: Record<string, string> = {
  snapshot: "T-30", report_issue: "T-30", missing_docs: "T-30", doc_expiry: "T-30", spanish_reply: "T-30",
  income_verifier: "T-31", auto_data_entry: "T-31", credit_summary: "T-31", dti_calculator: "T-31",
  condition_clearer: "T-31", compliance_checker: "T-31",
  closing_package: "T-32", pipeline_dashboard: "T-32", guideline_checker: "T-32", fraud_detector: "T-32",
  multi_borrower: "T-32", los_export: "T-32", rate_lock_monitor: "T-32", underwriting_tracker: "T-32",
  document_classifier: "T-32", escrow_calculator: "T-32",
  team: "T-33",
};
