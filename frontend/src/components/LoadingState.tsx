export function LoadingState({ variant = "list" }: { variant?: "list" | "cards" | "table" }) {
  if (variant === "cards") {
    return (
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4" aria-busy="true" aria-label="Загрузка">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-lg bg-slate-100" />
        ))}
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className="space-y-2" aria-busy="true" aria-label="Загрузка">
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className="h-10 animate-pulse rounded-md bg-slate-100" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3" aria-busy="true" aria-label="Загрузка">
      {Array.from({ length: 4 }, (_, index) => (
        <div key={index} className="h-20 animate-pulse rounded-lg bg-slate-100" />
      ))}
    </div>
  );
}
