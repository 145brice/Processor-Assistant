// Definitions for the More Tools pages. One entry per tool route key; the shared runner page
// (web/src/app/(app)/tools/[tool]) renders the form from `fields` and shows the API's output
// blocks. The matching backend handler is in backend/pa_api/tools/.
import {
  Bug,
  CalendarClock,
  Camera,
  FileWarning,
  Languages,
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
};
