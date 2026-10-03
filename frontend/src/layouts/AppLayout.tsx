import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { canAccessAdmin } from "../auth/roles.ts";
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

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || canAccessAdmin(user));

  function handleLogout() {
    logout();
    void navigate("/login", { replace: true });
  }

  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-900">
      <aside className="flex min-h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-5 text-sm font-semibold">
          Shift Tracker
        </div>
        <nav className="flex flex-col gap-1 p-3" aria-label="Main">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "rounded-md px-3 py-2 text-sm font-medium",
                  isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-100",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6">
          <span className="font-semibold">Shift Tracker</span>
          <div className="flex items-center gap-4">
            <span className="max-w-xs truncate text-sm text-slate-600">
              {user?.full_name ?? "Пользователь"}
            </span>
            <button
              type="button"
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700"
              onClick={handleLogout}
            >
              Выйти
            </button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <div className="rounded-lg border border-slate-200 bg-white p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
