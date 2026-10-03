import { ErrorState } from "./ErrorState.tsx";
import { LoadingState } from "./LoadingState.tsx";
import { StatusBadge } from "./StatusBadge.tsx";
import { ConfirmationBadge } from "./ActiveBadge.tsx";
import { useShiftDetail } from "../hooks/useShifts.ts";
import { formatDate, formatDateTime, formatMessageReason, formatTelegramUser, messagePreview } from "../lib/format.ts";
import { formatUserRole } from "../auth/roles.ts";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="break-words">{value}</dd>
    </div>
  );
}

export function ShiftDetailView({ shiftId }: { shiftId: number }) {
  const detail = useShiftDetail(shiftId);

  if (detail.isLoading) {
    return <LoadingState />;
  }
  if (detail.isError) {
    return <ErrorState error={detail.error} onRetry={() => void detail.refetch()} />;
  }
  if (!detail.data) {
    return null;
  }

  const shift = detail.data;
  const source = shift.source_message;

  return (
    <div className="space-y-5 text-sm">
      <ConfirmationBadge manual={shift.confirmed_manually} />
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Row label="ID" value={String(shift.id)} />
        <Row label="Дата смены" value={formatDate(shift.shift_date)} />
        <Row label="Сотрудник" value={shift.employee ? `${shift.employee.full_name} · ${shift.employee.personnel_number}` : `#${shift.employee_id}`} />
        <Row label="Объект" value={shift.work_object?.name ?? `#${shift.object_id}`} />
        <Row label="Подтверждение" value={shift.confirmed_manually ? "Вручную" : "Автоматически"} />
        <Row
          label="Кем подтверждено"
          value={
            shift.confirmed_by_user
              ? `${shift.confirmed_by_user.full_name} · ${shift.confirmed_by_user.email} · ${formatUserRole(shift.confirmed_by_user.role)}`
              : "—"
          }
        />
        <Row label="Исходное сообщение" value={shift.source_message_id === null ? "—" : `#${shift.source_message_id}`} />
        <Row label="Создано" value={formatDateTime(shift.created_at)} />
        <Row label="Обновлено" value={formatDateTime(shift.updated_at)} />
      </dl>
      {source ? (
        <section>
          <h3 className="mb-2 font-semibold">Исходное сообщение</h3>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <StatusBadge status={source.status} />
            <span className="text-slate-500">{formatMessageReason(source.reason)}</span>
          </div>
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Row label="Telegram" value={formatTelegramUser(source.telegram_username, source.telegram_user_id)} />
            <Row label="Получено" value={formatDateTime(source.created_at)} />
            <div className="sm:col-span-2">
              <dt className="text-slate-500">Текст</dt>
              <dd className="whitespace-pre-wrap break-words">{messagePreview(source.text, source.caption)}</dd>
            </div>
          </dl>
        </section>
      ) : null}
    </div>
  );
}
