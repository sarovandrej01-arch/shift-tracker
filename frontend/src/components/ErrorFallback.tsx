export function ErrorFallback() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-100 px-6 text-slate-900">
      <h1 className="text-2xl font-semibold">Что-то пошло не так</h1>
      <button
        type="button"
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white"
        onClick={() => window.location.reload()}
      >
        Перезагрузить
      </button>
    </div>
  );
}
