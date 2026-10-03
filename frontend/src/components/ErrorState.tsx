import { getApiErrorMessage } from "../lib/apiErrorMessage.ts";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-4" role="alert">
      <p className="text-sm text-rose-800">{getApiErrorMessage(error)}</p>
      {onRetry ? (
        <button
          type="button"
          className="mt-3 rounded-md border border-rose-300 bg-white px-3 py-1.5 text-sm font-medium text-rose-800"
          onClick={onRetry}
        >
          Повторить
        </button>
      ) : null}
    </div>
  );
}
