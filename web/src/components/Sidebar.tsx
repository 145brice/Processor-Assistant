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

function NavLink({ item, onNavigate, nested = false }: { item: NavItem; onNavigate: () => void; nested?: boolean }) {
  const active = usePathname() === item.href;
  const Icon = ITEM_ICONS[item.href];
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={
        "group relative flex items-center gap-3 rounded-lg px-3 text-sm transition-colors " +
        (nested ? "py-1.5 pl-9 " : "py-2 ") +
        (active ? "bg-sidebar-active font-medium text-white" : "text-sidebar-text hover:bg-sidebar-hover hover:text-white")
      }
    >
      {active && <span className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-brand" />}
      {Icon && !nested && <Icon className={"size-4 shrink-0 " + (active ? "text-white" : "text-sidebar-muted group-hover:text-white")} />}
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

function Group({ label, children, storageKey, icon: Icon, sub = false }: {
  label: string; children: React.ReactNode; storageKey: string; icon?: LucideIcon; sub?: boolean;
}) {
  const [open, setOpen] = useState(false);
  useEffect(() => { setOpen(window.localStorage.getItem(storageKey) === "open"); }, [storageKey]);
  const toggle = () => setOpen((value) => {
    const next = !value;
    window.localStorage.setItem(storageKey, next ? "open" : "closed");
    return next;
  });
  return (
    <div className={sub ? "" : "mt-5"}>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={open}
        className={
          sub
            ? "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm text-sidebar-text transition-colors hover:bg-sidebar-hover hover:text-white"
            : "flex w-full items-center gap-2 px-3 pb-1.5 text-left text-[11px] font-semibold uppercase tracking-[0.08em] text-sidebar-muted transition-colors hover:text-sidebar-text"
        }
      >
        {Icon && <Icon className="size-4 shrink-0 text-sidebar-muted" />}
        <span className="flex-1 truncate">{label}</span>
        <ChevronRight className={"size-3.5 shrink-0 transition-transform " + (open ? "rotate-90" : "")} />
      </button>
      {open && <div className={"space-y-0.5 " + (sub ? "pb-1" : "")}>{children}</div>}
    </div>
  );
}

export default function Sidebar() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const router = useRouter();
  useEffect(() => {
    const saved = window.localStorage.getItem("pa_theme");
    if (saved === "dark" || saved === "light") setTheme(saved);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("pa_theme", theme);
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
        className="fixed left-3 top-3 z-30 grid size-10 place-items-center rounded-lg bg-sidebar text-white shadow-lg md:hidden"
        onClick={() => setDrawerOpen(true)}
        aria-label="Open navigation"
      >
        <Menu className="size-5" />
      </button>
      {drawerOpen && (
        <button type="button" className="fixed inset-0 z-30 bg-slate-950/50 backdrop-blur-sm md:hidden" onClick={closeDrawer} aria-label="Close navigation" />
      )}
      <nav
        className={
          (drawerOpen ? "translate-x-0" : "-translate-x-full") +
          " fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col bg-sidebar text-white transition-transform duration-200 md:sticky md:top-0 md:h-screen md:w-64 md:translate-x-0"
        }
      >
        <div className="flex items-center gap-3 px-5 pb-4 pt-5">
          <div className="grid size-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-[#2f4c8f] shadow-md shadow-black/20">
            <ScanLine className="size-5 text-white" />
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-[15px] font-semibold tracking-tight">Processor Assistant</div>
            <div className="text-xs text-sidebar-muted">Mortgage processing</div>
          </div>
          <button type="button" className="grid size-8 place-items-center rounded-lg text-sidebar-text hover:bg-sidebar-hover md:hidden" onClick={closeDrawer} aria-label="Close navigation">
            <X className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-4">
          <div className="space-y-0.5">
            {PRIMARY_NAV.map((item) => <NavLink key={item.href} item={item} onNavigate={closeDrawer} />)}
          </div>

          <Group label="More tools" storageKey="pa_group_more_tools">
            {MORE_TOOLS.map((group) => (
              <Group key={group.label} label={group.label} sub icon={GROUP_ICONS[group.label]} storageKey={"pa_group_tool_" + group.label}>
                {group.items.map((item) => <NavLink key={item.href + item.label} item={item} nested onNavigate={closeDrawer} />)}
              </Group>
            ))}
          </Group>

          <Group label="Settings" storageKey="pa_group_settings">
            {SETTINGS_NAV.map((item) => <NavLink key={item.href + item.label} item={item} onNavigate={closeDrawer} />)}
          </Group>
        </div>

        <div className="border-t border-white/5 px-3 py-3">
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="flex flex-1 items-center gap-3 rounded-lg px-3 py-2 text-sm text-sidebar-text transition-colors hover:bg-sidebar-hover hover:text-white"
            >
              {theme === "light" ? <Moon className="size-4 text-sidebar-muted" /> : <Sun className="size-4 text-sidebar-muted" />}
              {theme === "light" ? "Dark mode" : "Light mode"}
            </button>
            <button
              type="button"
              onClick={() => void logout()}
              title="Log out"
              aria-label="Log out"
              className="grid size-9 place-items-center rounded-lg text-sidebar-text transition-colors hover:bg-sidebar-hover hover:text-white"
            >
              <LogOut className="size-4" />
            </button>
          </div>
          <div className="mt-2 flex items-center gap-3 px-3 text-xs text-sidebar-muted">
            <Link href="/privacy" className="hover:text-sidebar-text">Privacy</Link>
            <span aria-hidden>·</span>
            <Link href="/terms" className="hover:text-sidebar-text">Terms</Link>
          </div>
        </div>
      </nav>
    </>
  );
}
