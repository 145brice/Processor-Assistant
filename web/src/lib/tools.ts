// Definitions for the More Tools pages. One entry per tool route key; the shared runner page
// (web/src/app/(app)/tools/[tool]) renders the form from `fields` and shows the API's output
// blocks. The matching backend handler is in backend/pa_api/tools/.
import {
  Bug,
  Calculator,
  CalendarClock,
  Camera,
  CreditCard,
  FileWarning,
  Languages,
  ListChecks,
  ShieldCheck,
  TextCursorInput,
  Wallet,
  type LucideIcon,
} from "lucide-react";

export type FieldType = "text" | "textarea" | "loan" | "number" | "select" | "date";

export interface ToolField {
  name: string;
  label: string;
  type: FieldType;
  placeholder?: string;
  help?: string;
  required?: boolean;
  rows?: number;
  options?: string[];
}

export interface ToolAction {
  id: string;
  label: string;
  primary?: boolean;
}

export interface ToolDef {
  key: string;
  title: string;
  description: string;
  icon: LucideIcon;
  fields: ToolField[];
  /** Several buttons, each sent as `action`. Without it, one run button is shown. */
  actions?: ToolAction[];
  runLabel?: string;
}

// ---------- what the API returns (see "Tool output blocks" in API_CONTRACT.md) ----------
export type Tone = "good" | "warn" | "bad" | "info" | "neutral";

export type ToolBlock =
  | { type: "stats"; items: { label: string; value: string | number; tone: Tone }[] }
  | { type: "list"; title: string; tone: Tone; items: string[] }
  | { type: "checklist"; title: string; rows: { label: string; ok: boolean }[] }
  | { type: "kv"; title: string; rows: { label: string; value: string }[] }
  | { type: "text"; title: string; text: string }
  | { type: "notice"; tone: Tone; text: string; href: string; link_label: string }
  | { type: "table"; title: string; columns: string[]; rows: string[][] }
  | { type: "link"; label: string; href: string };

const loan: ToolField = {
  name: "loan_id",
  label: "Loan",
  type: "loan",
  required: true,
};

export const TOOLS: Record<string, ToolDef> = {
  snapshot: {
    key: "snapshot",
    title: "Loan Snapshot",
    description: "See which required documents a loan has and which are still missing.",
    icon: Camera,
    fields: [loan],
    runLabel: "Show snapshot",
  },
  missing_docs: {
    key: "missing_docs",
    title: "Missing Documents",
    description: "Check a loan against the list of required documents.",
    icon: FileWarning,
    fields: [loan],
    runLabel: "Check documents",
  },
  doc_expiry: {
    key: "doc_expiry",
    title: "Document Expiry",
    description: "Find insurance, appraisal, credit, title and VOE documents that have expired or are about to.",
    icon: CalendarClock,
    fields: [loan],
    runLabel: "Check expiry",
  },
  report_issue: {
    key: "report_issue",
    title: "Report an Issue",
    description: "Describe a problem. Social Security and bank account numbers are masked to the last 4 digits.",
    icon: Bug,
    fields: [
      {
        name: "text",
        label: "Describe the problem",
        type: "textarea",
        rows: 6,
        required: true,
        placeholder: "What happened, and what did you expect?",
      },
      {
        name: "loan_id",
        label: "Loan (optional)",
        type: "loan",
        help: "Adds the loan number to the report.",
      },
    ],
    runLabel: "Prepare report",
  },
  spanish_reply: {
    key: "spanish_reply",
    title: "Spanish Reply",
    description: "Detect a Spanish email, translate it, and draft your reply in Spanish.",
    icon: Languages,
    fields: [
      {
        name: "email_text",
        label: "Borrower email",
        type: "textarea",
        rows: 5,
        placeholder: "Paste the email here to detect its language and translate it.",
        help: "Names, numbers and addresses are removed before anything is translated.",
      },
      {
        name: "reply_en",
        label: "Your reply in English",
        type: "textarea",
        rows: 4,
        placeholder: "Thank you for your email. We need your bank statements and pay stubs.",
      },
      {
        name: "conditions",
        label: "Conditions for a template email",
        type: "textarea",
        rows: 4,
        placeholder: "1. Government-issued photo ID\n2. Recent bank statements\n3. Recent pay stubs",
      },
    ],
    actions: [
      { id: "detect", label: "Detect language and translate", primary: true },
      { id: "reply", label: "Translate my reply to Spanish" },
      { id: "templates", label: "Generate email templates" },
    ],
  },

  // ---------- T-31 Advanced Tools ----------
  income_verifier: {
    key: "income_verifier",
    title: "Income Verifier",
    description: "Compare the income and employment found on a loan's scanned documents with the loan itself.",
    icon: Wallet,
    fields: [loan],
    runLabel: "Verify income",
  },
  auto_data_entry: {
    key: "auto_data_entry",
    title: "Auto Data Entry",
    description: "Fill the loan application fields from the data found on a loan's scanned documents.",
    icon: TextCursorInput,
    fields: [loan],
    runLabel: "Fill fields",
  },
  credit_summary: {
    key: "credit_summary",
    title: "Credit Summary",
    description: "Paste a credit report to see the score, risk level, red flags and recommendations.",
    icon: CreditCard,
    fields: [
      {
        name: "credit_text",
        label: "Credit report text",
        type: "textarea",
        rows: 10,
        required: true,
        placeholder: "Paste the credit report text here.",
        help: "It is read here and not saved. Only the summary is shown.",
      },
    ],
    runLabel: "Analyze credit report",
  },
  dti_calculator: {
    key: "dti_calculator",
    title: "DTI and Closing Costs",
    description: "Check debt-to-income against loan limits, or estimate closing costs and cash needed.",
    icon: Calculator,
    fields: [
      { name: "income", label: "Monthly gross income ($)", type: "number" },
      { name: "debt", label: "Monthly debt payments ($)", type: "number" },
      { name: "housing", label: "Proposed housing payment ($)", type: "number" },
      { name: "loan_type", label: "Loan type", type: "select", options: ["conventional", "fha", "va"] },
      { name: "loan_amount", label: "Loan amount ($)", type: "number", help: "Used for closing costs." },
      { name: "property_value", label: "Property value ($)", type: "number", help: "Used for closing costs." },
      { name: "transaction", label: "Transaction type", type: "select", options: ["purchase", "refinance"] },
    ],
    actions: [
      { id: "dti", label: "Calculate DTI", primary: true },
      { id: "closing", label: "Calculate closing costs" },
    ],
  },
  condition_clearer: {
    key: "condition_clearer",
    title: "Condition Clearer",
    description: "Check whether the documents scanned into a loan clear an underwriting condition.",
    icon: ListChecks,
    fields: [
      loan,
      {
        name: "condition",
        label: "Underwriting condition",
        type: "textarea",
        rows: 3,
        required: true,
        placeholder: "Example: Provide paystub for the last 30 days",
      },
    ],
    runLabel: "Check condition",
  },
  compliance_checker: {
    key: "compliance_checker",
    title: "Compliance Checker",
    description: "Run a loan's key numbers through the compliance checklist.",
    icon: ShieldCheck,
    fields: [
      { name: "loan_type", label: "Loan type", type: "select", options: ["conventional", "fha", "va", "usda"] },
      { name: "dti", label: "DTI ratio (%)", type: "number" },
      { name: "ltv", label: "LTV ratio (%)", type: "number" },
      { name: "credit_score", label: "Credit score", type: "number" },
      { name: "loan_amount", label: "Loan amount ($)", type: "number" },
    ],
    runLabel: "Run compliance check",
  },
};
