import { formatMessageStatus } from "../lib/format.ts";
import type { MessageStatus } from "../types/message.ts";

const STATUS_CLASS: Record<MessageStatus, string> = {
  new: "bg-slate-100 text-slate-700",
  processing: "bg-sky-50 text-sky-800",
  accepted: "bg-emerald-50 text-emerald-800",
  review: "bg-amber-50 text-amber-800",
  rejected: "bg-rose-50 text-rose-800",
  duplicate: "bg-violet-50 text-violet-800",
  error: "bg-red-50 text-red-800",
};

export function StatusBadge({ status }: { status: MessageStatus }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[status]}`}>
      {formatMessageStatus(status)}
    </span>
  );
}
