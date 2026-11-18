"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { MORE_TOOLS, PRIMARY_NAV, SETTINGS_NAV, type NavItem } from "@/lib/nav";

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate: () => void }) {
  const active = usePathname() === item.href;
  return <Link href={item.href} onClick={onNavigate} className={"block rounded px-3 py-2 text-sm " + (active ? "bg-white/15 font-semibold" : "hover:bg-white/10")}>{item.label}</Link>;
}

function Group({ label, children, small = false, storageKey }: { label: string; children: React.ReactNode; small?: boolean; storageKey: string }) {
  const [open, setOpen] = useState(false);
  useEffect(() => { setOpen(window.localStorage.getItem(storageKey) === "open"); }, [storageKey]);
  const toggle = () => setOpen((value) => { const next = !value; window.localStorage.setItem(storageKey, next ? "open" : "closed"); return next; });
  return <div className={small ? "ml-2" : "mt-4 border-t border-white/15 pt-3"}>
    <button type="button" onClick={toggle} aria-expanded={open} className="w-full px-3 py-1 text-left text-xs font-bold uppercase tracking-wide">{open ? "−" : "+"} {label}</button>
    {open && <div className="mt-1">{children}</div>}
  </div>;
}

export default function Sidebar() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [drawerOpen, setDrawerOpen] = useState(false);
  useEffect(() => { const saved = window.localStorage.getItem("pa_theme"); if (saved === "dark" || saved === "light") setTheme(saved); }, []);
  useEffect(() => { document.documentElement.dataset.theme = theme; window.localStorage.setItem("pa_theme", theme); }, [theme]);
  const closeDrawer = () => setDrawerOpen(false);
  return <>
    <button type="button" className="fixed left-3 top-3 z-30 rounded bg-[#1a2840] px-3 py-2 text-white md:hidden" onClick={() => setDrawerOpen(true)} aria-label="Open navigation">☰</button>
    {drawerOpen && <button type="button" className="fixed inset-0 z-30 bg-black/40 md:hidden" onClick={closeDrawer} aria-label="Close navigation" />}
    <nav className={(drawerOpen ? "translate-x-0" : "-translate-x-full") + " fixed inset-y-0 left-0 z-40 flex w-72 shrink-0 flex-col bg-[#1a2840] p-3 text-white transition-transform md:static md:translate-x-0 md:w-60"}>
      <div className="mb-3 flex items-center justify-between px-3"><span className="text-lg font-extrabold">Processor Assistant</span><button type="button" className="text-xl md:hidden" onClick={closeDrawer} aria-label="Close navigation">×</button></div>
      <button type="button" className="mb-3 rounded px-3 py-2 text-left text-sm hover:bg-white/10" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>{theme === "light" ? "☾ Dark mode" : "☀ Light mode"}</button>
      <div className="mb-2 px-3 text-xs text-slate-300">Sandbox mode</div>
      {PRIMARY_NAV.map((item) => <NavLink key={item.href} item={item} onNavigate={closeDrawer} />)}
      <Group label="More Tools" storageKey="pa_group_more_tools">{MORE_TOOLS.map((group) => <Group key={group.label} label={group.label} small storageKey={"pa_group_tool_" + group.label}>{group.items.map((item) => <NavLink key={item.href + item.label} item={item} onNavigate={closeDrawer} />)}</Group>)}</Group>
      <Group label="Settings" storageKey="pa_group_settings">{SETTINGS_NAV.map((item) => <NavLink key={item.href + item.label} item={item} onNavigate={closeDrawer} />)}</Group>
      <div className="mt-auto border-t border-white/15 pt-3 text-xs text-slate-300"><Link href="/privacy">Privacy</Link> · <Link href="/terms">Terms</Link></div>
    </nav>
  </>;
}
