"use client";
// Skeleton sidebar: structure and collapse behaviour only. Styling, theme toggle, user
// name and the More Tools switch from /api/me are task T-10 / T-13.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { MORE_TOOLS, PRIMARY_NAV, SETTINGS_NAV, type NavItem } from "@/lib/nav";

function NavLink({ item }: { item: NavItem }) {
  const active = usePathname() === item.href;
  return (
    <Link
      href={item.href}
      className={`block rounded px-3 py-2 text-sm ${active ? "bg-white/15 font-semibold" : "hover:bg-white/10"}`}
    >
      {item.label}
    </Link>
  );
}

function Group({ label, children, small = false }: { label: string; children: React.ReactNode; small?: boolean }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={small ? "ml-2" : "mt-4 border-t border-white/15 pt-3"}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="w-full px-3 py-1 text-left text-xs font-bold uppercase tracking-wide"
      >
        {open ? "−" : "+"} {label}
      </button>
      {open && <div className="mt-1">{children}</div>}
    </div>
  );
}

export default function Sidebar() {
  return (
    <nav className="flex w-60 shrink-0 flex-col bg-[#1a2840] p-3 text-white">
      <div className="mb-4 px-3 text-lg font-extrabold">Processor Assistant</div>
      {PRIMARY_NAV.map((item) => <NavLink key={item.href} item={item} />)}
      <Group label="More Tools">
        {MORE_TOOLS.map((group) => (
          <Group key={group.label} label={group.label} small>
            {group.items.map((item) => <NavLink key={item.href + item.label} item={item} />)}
          </Group>
        ))}
      </Group>
      <Group label="Settings">
        {SETTINGS_NAV.map((item) => <NavLink key={item.href + item.label} item={item} />)}
      </Group>
    </nav>
  );
}
