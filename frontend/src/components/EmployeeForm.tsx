import { useState, type FormEvent } from "react";

import { Field, TextInput } from "./Field.tsx";
import { buttonClass } from "../lib/ui.ts";
import type { Employee, EmployeeWrite } from "../types/directory.ts";

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed === "" ? null : trimmed;
}

function optionalUserId(value: string): number | null | "invalid" {
  const trimmed = value.trim();
  if (trimmed === "") {
    return null;
  }
  if (!/^\d+$/.test(trimmed)) {
    return "invalid";
  }
  return Number(trimmed);
}

export function EmployeeForm({
  employee,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  employee: Employee | null;
  pending: boolean;
  error: string | null;
  onSubmit: (data: EmployeeWrite) => void;
  onCancel: () => void;
}) {
  const [fullName, setFullName] = useState(employee?.full_name ?? "");
  const [personnelNumber, setPersonnelNumber] = useState(employee?.personnel_number ?? "");
  const [telegramUserId, setTelegramUserId] = useState(employee?.telegram_user_id?.toString() ?? "");
  const [telegramUsername, setTelegramUsername] = useState(employee?.telegram_username ?? "");
  const [callsign, setCallsign] = useState(employee?.callsign ?? "");
  const [isActive, setIsActive] = useState(employee?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (fullName.trim() === "" || personnelNumber.trim() === "") {
      setFormError("Укажите ФИО и табельный номер");
      return;
    }
    const userId = optionalUserId(telegramUserId);
    if (userId === "invalid") {
      setFormError("Telegram ID должен быть целым числом");
      return;
    }
    setFormError(null);
    onSubmit({
      full_name: fullName.trim(),
      personnel_number: personnelNumber.trim(),
      telegram_user_id: userId,
      telegram_username: optionalText(telegramUsername),
      callsign: optionalText(callsign),
      ...(employee ? {} : { is_active: isActive }),
    });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="ФИО" htmlFor="employee-name">
          <TextInput id="employee-name" value={fullName} disabled={pending} onChange={(event) => setFullName(event.target.value)} />
        </Field>
        <Field label="Табельный номер" htmlFor="employee-number">
          <TextInput
            id="employee-number"
            value={personnelNumber}
            disabled={pending}
            onChange={(event) => setPersonnelNumber(event.target.value)}
          />
        </Field>
        <Field label="Позывной" htmlFor="employee-callsign">
          <TextInput id="employee-callsign" value={callsign} disabled={pending} onChange={(event) => setCallsign(event.target.value)} />
        </Field>
        <Field label="Telegram username" htmlFor="employee-username">
          <TextInput
            id="employee-username"
            value={telegramUsername}
            disabled={pending}
            onChange={(event) => setTelegramUsername(event.target.value)}
          />
        </Field>
        <Field label="Telegram ID" htmlFor="employee-telegram-id">
          <TextInput
            id="employee-telegram-id"
            inputMode="numeric"
            value={telegramUserId}
            disabled={pending}
            onChange={(event) => setTelegramUserId(event.target.value)}
          />
        </Field>
        {employee ? null : (
          <label className="flex items-center gap-2 self-end text-sm text-slate-700">
            <input type="checkbox" checked={isActive} disabled={pending} onChange={(event) => setIsActive(event.target.checked)} />
            Активен
          </label>
        )}
      </div>
      {formError || error ? (
        <p className="text-sm text-rose-700" role="alert">
          {formError ?? error}
        </p>
      ) : null}
      <div className="flex flex-col gap-2 sm:flex-row">
        <button type="submit" className={`${buttonClass.primary} w-full sm:w-auto`} disabled={pending}>
          {pending ? "Сохранение…" : "Сохранить"}
        </button>
        <button type="button" className={`${buttonClass.secondary} w-full sm:w-auto`} disabled={pending} onClick={onCancel}>
          Отмена
        </button>
      </div>
    </form>
  );
}
