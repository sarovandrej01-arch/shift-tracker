import { useEffect, type ReactNode } from "react";
import { createPortal } from "react-dom";

import { buttonClass } from "../lib/ui.ts";

export function Modal({
  title,
  open,
  onClose,
  children,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) {
      return;
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-end md:items-center md:justify-center md:p-6">
      <button type="button" className="absolute inset-0 bg-slate-900/40" aria-label="Закрыть окно" onClick={onClose} />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        className="relative z-10 max-h-[100dvh] w-full overflow-y-auto bg-white p-4 md:max-h-[90vh] md:max-w-3xl md:rounded-lg md:p-6"
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 id="dialog-title" className="text-lg font-semibold">
            {title}
          </h2>
          <button type="button" className={buttonClass.secondary} onClick={onClose}>
            Закрыть
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
