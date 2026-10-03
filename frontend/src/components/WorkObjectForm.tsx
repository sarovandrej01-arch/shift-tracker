import { useState, type FormEvent } from "react";

import { Field, TextInput } from "./Field.tsx";
import { toApiTime, toTimeInput } from "../lib/format.ts";
import { buttonClass } from "../lib/ui.ts";
import type { WorkObject, WorkObjectWrite } from "../types/directory.ts";

function parseMinutes(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) {
    return null;
  }
  return Number(value.trim());
}

export function WorkObjectForm({
  workObject,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  workObject: WorkObject | null;
  pending: boolean;
  error: string | null;
  onSubmit: (data: WorkObjectWrite) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(workObject?.name ?? "");
  const [startTime, setStartTime] = useState(workObject ? toTimeInput(workObject.shift_start_time) : "");
  const [beforeMinutes, setBeforeMinutes] = useState(workObject ? String(workObject.checkin_before_minutes) : "0");
  const [afterMinutes, setAfterMinutes] = useState(workObject ? String(workObject.checkin_after_minutes) : "0");
  const [timezone, setTimezone] = useState(workObject?.timezone ?? "Europe/Moscow");
  const [isActive, setIsActive] = useState(workObject?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const before = parseMinutes(beforeMinutes);
    const after = parseMinutes(afterMinutes);
    if (name.trim() === "" || startTime === "" || timezone.trim() === "") {
      setFormError("Укажите название, начало смены и часовой пояс");
      return;
    }
    if (before === null || after === null) {
      setFormError("Допуск должен быть целым числом от 0");
      return;
    }
    setFormError(null);
    onSubmit({
      name: name.trim(),
      shift_start_time: toApiTime(startTime),
      checkin_before_minutes: before,
      checkin_after_minutes: after,
      timezone: timezone.trim(),
      ...(workObject ? {} : { is_active: isActive }),
    });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Название" htmlFor="object-name">
          <TextInput id="object-name" value={name} disabled={pending} onChange={(event) => setName(event.target.value)} />
        </Field>
        <Field label="Начало смены" htmlFor="object-start">
          <TextInput id="object-start" type="time" value={startTime} disabled={pending} onChange={(event) => setStartTime(event.target.value)} />
        </Field>
        <Field label="Допуск до, мин" htmlFor="object-before">
          <TextInput
            id="object-before"
            inputMode="numeric"
            value={beforeMinutes}
            disabled={pending}
            onChange={(event) => setBeforeMinutes(event.target.value)}
          />
        </Field>
        <Field label="Допуск после, мин" htmlFor="object-after">
          <TextInput
            id="object-after"
            inputMode="numeric"
            value={afterMinutes}
            disabled={pending}
            onChange={(event) => setAfterMinutes(event.target.value)}
          />
        </Field>
        <Field label="Часовой пояс" htmlFor="object-timezone">
          <TextInput id="object-timezone" value={timezone} disabled={pending} onChange={(event) => setTimezone(event.target.value)} />
        </Field>
        {workObject ? null : (
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
