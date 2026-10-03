import { buttonClass } from "../lib/ui.ts";

export function PaginationControls({
  offset,
  limit,
  count,
  onOffsetChange,
}: {
  offset: number;
  limit: number;
  count: number;
  onOffsetChange: (offset: number) => void;
}) {
  return (
    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-slate-600">Показано {count}</p>
      <div className="flex gap-2">
        <button
          type="button"
          className={buttonClass.secondary}
          disabled={offset === 0}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          Назад
        </button>
        <button
          type="button"
          className={buttonClass.secondary}
          disabled={count < limit}
          onClick={() => onOffsetChange(offset + limit)}
        >
          Вперёд
        </button>
      </div>
    </div>
  );
}
