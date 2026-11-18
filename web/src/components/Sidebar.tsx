"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart3, Bot, Briefcase, ChevronRight, FileStack, KeyRound, LayoutDashboard, LogOut, Menu, Moon,
  ScanLine, Sparkles, Sun, Workflow, Wrench, X, Zap, type LucideIcon,
} from "lucide-react";
import { MORE_TOOLS, PRIMARY_NAV, SETTINGS_NAV, type NavItem } from "@/lib/nav";
import { supabase } from "@/lib/supabase";

const ITEM_ICONS: Record<string, LucideIcon> = {
  "/scanner": ScanLine,
  "/pipeline": FileStack,
  "/overview": LayoutDashboard,
  "/pricing": Sparkles,
  "/settings/usage": BarChart3,
  "/settings/ai": KeyRound,
};

const GROUP_ICONS: Record<string, LucideIcon> = {
  Workspace: Briefcase,
  "Quick Tools": Zap,
  "Advanced Tools": Wrench,
  "Pipeline Advanced": Workflow,
  "Advanced Automation": Bot,
};

const TOOL_COUNT = MORE_TOOLS.reduce((n, g) => n + g.items.length, 0);

function useStoredOpen(storageKey: string): [boolean, () => void] {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    try { setOpen(window.localStorage.getItem(storageKey) === "open"); } catch { /* storage blocked */ }
  }, [storageKey]);
  const toggle = () => setOpen((value) => {
    const next = !value;
    try { window.localStorage.setItem(storageKey, next ? "open" : "closed"); } catch { /* storage blocked */ }
    return next;
  });
  return [open, toggle];
}

function NavLink({ item, onNavigate, nested = false }: { item: NavItem; onNavigate: () => void; nested?: boolean }) {
  const active = usePathname() === item.href;
  const Icon = ITEM_ICONS[item.href];
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={
        "group relative flex h-8 items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors duration-150 " +
        (active
          ? "bg-white/[0.08] font-medium text-white shadow-[inset_0_0_0_1px_rgba(255,255,255,0.06)]"
          : "text-sidebar-text hover:bg-white/[0.04] hover:text-white")
      }
    >
      {nested ? (
        <span className={"size-1 shrink-0 rounded-full transition-colors " + (active ? "bg-[#8fb0f2]" : "bg-sidebar-muted/60 group-hover:bg-sidebar-text")} />
      ) : (
        Icon && <Icon strokeWidth={1.75} className={"size-4 shrink-0 transition-colors " + (active ? "text-[#8fb0f2]" : "text-sidebar-muted group-hover:text-sidebar-text")} />
      )}
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

function Section({ label, count, storageKey, children }: { label: string; count?: number; storageKey: string; children: React.ReactNode }) {
  const [open, toggle] = useStoredOpen(storageKey);
  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="group flex h-6 w-full items-center gap-1.5 px-2.5 text-left text-[10.5px] font-semibold uppercase tracking-[0.12em] text-sidebar-muted transition-colors hover:text-sidebar-text"
      >
        <span className="flex-1">{label}</span>
        {count !== undefined && !open && (
          <span className="rounded bg-white/[0.06] px-1.5 py-px text-[10px] font-medium tracking-normal text-sidebar-muted">{count}</span>
        )}
        <ChevronRight strokeWidth={2} className={"size-3 shrink-0 transition-transform duration-200 " + (open ? "rotate-90" : "")} />
      </button>
      {open && <div className="animate-fade-up mt-1 space-y-px">{children}</div>}
    </div>
  );
}

function ToolGroup({ label, storageKey, icon: Icon, children }: { label: string; storageKey: string; icon?: LucideIcon; children: React.ReactNode }) {
  const [open, toggle] = useStoredOpen(storageKey);
  return (
    <div>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className="group flex h-8 w-full items-center gap-2.5 rounded-md px-2.5 text-left text-[13px] text-sidebar-text transition-colors hover:bg-white/[0.04] hover:text-white"
      >
        {Icon && <Icon strokeWidth={1.75} className="size-4 shrink-0 text-sidebar-muted transition-colors group-hover:text-sidebar-text" />}
        <span className="flex-1 truncate">{label}</span>
        <ChevronRight strokeWidth={2} className={"size-3 shrink-0 text-sidebar-muted transition-transform duration-200 " + (open ? "rotate-90" : "opacity-0 group-hover:opacity-100")} />
      </button>
      {open && (
        <div className="animate-fade-up relative ml-[17px] space-y-px border-l border-white/[0.08] py-0.5 pl-2">
          {children}
        </div>
      )}
    </div>
  );
}

export default function Sidebar() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem("pa_theme");
      if (saved === "dark" || saved === "light") setTheme(saved);
    } catch { /* storage blocked */ }
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { window.localStorage.setItem("pa_theme", theme); } catch { /* storage blocked */ }
  }, [theme]);
  const closeDrawer = () => setDrawerOpen(false);
  const logout = async () => {
    await supabase.auth.signOut();
    document.cookie = "pa_sandbox=; Path=/; Max-Age=0; SameSite=Lax";
    router.push("/login");
  };

  return (
    <>
      <button
        type="button"
        className="fixed left-3 top-3 z-30 grid size-9 place-items-center rounded-lg bg-sidebar text-white shadow-lg ring-1 ring-white/10 md:hidden"
        onClick={() => setDrawerOpen(true)}
        aria-label="Open navigation"
      >
        <Menu className="size-4" />
      </button>
      {drawerOpen && (
        <button type="button" className="fixed inset-0 z-30 bg-slate-950/50 backdrop-blur-sm md:hidden" onClick={closeDrawer} aria-label="Close navigation" />
      )}
      <nav
        className={
          (drawerOpen ? "translate-x-0" : "-translate-x-full") +
          " fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col border-r border-white/[0.06] bg-sidebar text-white transition-transform duration-200 md:sticky md:top-0 md:h-screen md:w-[248px] md:translate-x-0"
        }
      >
        {/* soft top light, keeps the navy from looking flat */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-40 bg-gradient-to-b from-white/[0.04] to-transparent" />

        <div className="relative flex h-14 items-center gap-2.5 px-4">
          <div className="grid size-7 place-items-center rounded-lg bg-gradient-to-b from-[#5b7fd0] to-brand-strong shadow-sm shadow-black/40 ring-1 ring-inset ring-white/20">
            <ScanLine strokeWidth={2} className="size-4 text-white" />
          </div>
          <div className="min-w-0 flex-1 leading-none">
            <div className="truncate text-[13.5px] font-semibold tracking-[-0.01em]">Processor Assistant</div>
            <div className="mt-1 text-[11px] text-sidebar-muted">Mortgage processing</div>
          </div>
          <button type="button" className="grid size-7 place-items-center rounded-md text-sidebar-text hover:bg-white/[0.06] md:hidden" onClick={closeDrawer} aria-label="Close navigation">
            <X className="size-4" />
          </button>
        </div>

        <div className="relative flex-1 overflow-y-auto px-2.5 pb-4 pt-2 [scrollbar-width:thin]">
          <div className="space-y-px">
            {PRIMARY_NAV.map((item) => <NavLink key={item.href} item={item} onNavigate={closeDrawer} />)}
          </div>

          <Section label="More tools" count={TOOL_COUNT} storageKey="pa_group_more_tools">
            {MORE_TOOLS.map((group) => (
              <ToolGroup key={group.label} label={group.label} icon={GROUP_ICONS[group.label]} storageKey={"pa_group_tool_" + group.label}>
                {group.items.map((item) => <NavLink key={item.href + item.label} item={item} nested onNavigate={closeDrawer} />)}
              </ToolGroup>
            ))}
          </Section>

          <Section label="Settings" storageKey="pa_group_settings">
            {SETTINGS_NAV.map((item) => <NavLink key={item.href + item.label} item={item} onNavigate={closeDrawer} />)}
          </Section>
        </div>

        {/* T-13: the signed-in user block (avatar, name, role / Sandbox badge) goes above this footer. */}
        <div className="relative border-t border-white/[0.06] p-2.5">
          <div className="flex items-center gap-2">
            <div role="radiogroup" aria-label="Theme" className="flex flex-1 rounded-lg bg-white/[0.04] p-0.5 ring-1 ring-inset ring-white/[0.06]">
              {([["light", Sun, "Light"], ["dark", Moon, "Dark"]] as const).map(([value, Icon, label]) => (
                <button
                  key={value}
                  type="button"
                  role="radio"
                  aria-checked={theme === value}
                  onClick={() => setTheme(value)}
                  className={
                    "flex h-7 flex-1 items-center justify-center gap-1.5 rounded-md text-[12px] font-medium transition " +
                    (theme === value ? "bg-white/[0.1] text-white shadow-sm" : "text-sidebar-muted hover:text-sidebar-text")
                  }
                >
                  <Icon strokeWidth={1.75} className="size-3.5" /> {label}
                </button>
              ))}
            </div>
            <button
              type="button"
              onClick={() => void logout()}
              title="Log out"
              aria-label="Log out"
              className="grid size-8 place-items-center rounded-lg text-sidebar-muted ring-1 ring-inset ring-white/[0.06] transition hover:bg-white/[0.06] hover:text-white"
            >
              <LogOut strokeWidth={1.75} className="size-4" />
            </button>
          </div>
          <div className="mt-2.5 flex items-center gap-2 px-1 text-[11px] text-sidebar-muted">
            <Link href="/privacy" className="hover:text-sidebar-text">Privacy</Link>
            <span aria-hidden className="opacity-50">·</span>
            <Link href="/terms" className="hover:text-sidebar-text">Terms</Link>
          </div>
        </div>
      </nav>
    </>
  );
}
