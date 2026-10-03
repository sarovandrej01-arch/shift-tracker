import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { canAccessAdmin, formatUserRole } from "../auth/roles.ts";
import { useAuth } from "../hooks/useAuth.ts";

type NavItem = {
  to: string;
  label: string;
  adminOnly?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/reviews", label: "Reviews" },
  { to: "/messages", label: "Messages" },
  { to: "/shifts", label: "Shifts" },
  { to: "/employees", label: "Employees" },
  { to: "/work-objects", label: "Work Objects" },
  { to: "/telegram-groups", label: "Telegram Groups" },
  { to: "/users", label: "Users", adminOnly: true },
];

function navClassName(isActive: boolean): string {
  return [
    "rounded-md px-3 py-2 text-sm font-medium",
    isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100",
  ].join(" ");
}

function SidebarNav({
  items,
  onNavigate,
}: {
  items: NavItem[];
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex flex-col gap-1 p-3" aria-label="Main">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          className={({ isActive }) => navClassName(isActive)}
          onClick={onNavigate}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [navOpen, setNavOpen] = useState(false);
  const [navPath, setNavPath] = useState(location.pathname);
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || canAccessAdmin(user));

  if (navPath !== location.pathname) {
    setNavPath(location.pathname);
    setNavOpen(false);
  }

  useEffect(() => {
    if (!navOpen) {
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setNavOpen(false);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen]);

  return (
    <div className="flex min-h-screen overflow-x-hidden bg-slate-100 text-slate-900">
      <aside className="hidden min-h-screen w-52 shrink-0 flex-col border-r border-slate-200 bg-white md:flex lg:w-60">
        <div className="border-b border-slate-200 px-4 py-5 text-sm font-semibold">Shift Tracker</div>
        <SidebarNav items={items} />
      </aside>
      {navOpen ? (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-900/40"
            aria-label="Закрыть меню"
            onClick={() => setNavOpen(false)}
          />
          <div id="app-navigation" className="relative flex h-full w-72 max-w-[85vw] flex-col bg-white">
            <div className="border-b border-slate-200 px-4 py-4 text-sm font-semibold">Shift Tracker</div>
            <SidebarNav items={items} onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      ) : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex min-h-14 items-center justify-between gap-3 border-b border-slate-200 bg-white px-3 py-2 sm:px-6 sm:py-3">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              className="rounded-md border border-slate-300 px-2.5 py-1.5 text-sm font-medium md:hidden"
              aria-expanded={navOpen}
              aria-controls="app-navigation"
              onClick={() => setNavOpen(true)}
            >
              Меню
            </button>
            <span className="truncate text-sm font-semibold sm:text-base">Shift Tracker</span>
          </div>
          <div className="flex min-w-0 items-center gap-2 sm:gap-4">
            {user ? (
              <div className="min-w-0 text-right">
                <p className="max-w-28 truncate text-sm font-medium sm:max-w-xs">{user.full_name}</p>
                <p className="hidden truncate text-xs text-slate-500 sm:block">{user.email}</p>
                <p className="hidden text-xs text-slate-500 sm:block">{formatUserRole(user.role)}</p>
              </div>
            ) : null}
            <button
              type="button"
              className="shrink-0 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700"
              onClick={logout}
            >
              Выйти
            </button>
          </div>
        </header>
        <main className="min-w-0 flex-1 p-3 sm:p-6">
          <div className="min-w-0 rounded-lg border border-slate-200 bg-white p-3 sm:p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
