export function ActiveBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        active ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-600"
      }`}
    >
      {active ? "Активен" : "Неактивен"}
    </span>
  );
}

export function ConfirmationBadge({ manual }: { manual: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        manual ? "bg-amber-50 text-amber-800" : "bg-sky-50 text-sky-800"
      }`}
    >
      {manual ? "Вручную" : "Авто"}
    </span>
  );
}
