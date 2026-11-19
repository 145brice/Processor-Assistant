// Sidebar structure. Mirrors show_sidebar() in app.py (see APP_INVENTORY.md "Sidebar").
export interface NavItem { label: string; href: string }
export interface NavGroup { label: string; items: NavItem[] }

const tool = (label: string, key: string): NavItem => ({ label, href: `/tools/${key}` });

export const PRIMARY_NAV: NavItem[] = [
  { label: "Scanner", href: "/scanner" },
  { label: "Pipeline", href: "/pipeline" },
  { label: "Overview", href: "/overview" },
];

/** Shown inside the collapsed "More Tools" group when me.features.more_tools is true. */
export const MORE_TOOLS: NavGroup[] = [
  {
    label: "Workspace",
    items: [{ label: "Usage", href: "/settings/usage" }, { label: "History", href: "/history" }],
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
      tool("Credit Summary", "credit_summary"), tool("DTI Calculator", "dti_calculator"),
      tool("Condition Clearer", "condition_clearer"), tool("Compliance Checker", "compliance_checker"),
    ],
  },
  {
    label: "Pipeline Advanced",
    items: [
      tool("Pipeline Dashboard", "pipeline_dashboard"), tool("Closing Package", "closing_package"),
      tool("Guideline Checker", "guideline_checker"),
      tool("Multi-Borrower", "multi_borrower"),
      tool("LOS Export", "los_export"),
    ],
  },
  {
    label: "Advanced Automation",
    items: [
      tool("Rate Lock Monitor", "rate_lock_monitor"),
      tool("Document Classifier", "document_classifier"), tool("Escrow Calculator", "escrow_calculator"),
    ],
  },
];

export const SETTINGS_NAV: NavItem[] = [
  { label: "Beta offer", href: "/pricing" },
  { label: "Usage / Billing", href: "/settings/usage" },
  { label: "AI Settings", href: "/settings/ai" },
];
