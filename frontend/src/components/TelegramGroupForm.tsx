import { useState, type FormEvent } from "react";

import { Field, SelectInput, TextInput } from "./Field.tsx";
import { buttonClass } from "../lib/ui.ts";
import type { WorkObject } from "../types/directory.ts";
import type { TelegramGroup, TelegramGroupWrite } from "../types/telegramGroup.ts";

function parseChatId(value: string): number | "invalid" {
  const trimmed = value.trim();
  if (!/^-?\d+$/.test(trimmed)) {
    return "invalid";
  }
  const parsed = Number(trimmed);
  return Number.isSafeInteger(parsed) ? parsed : "invalid";
}

export function TelegramGroupForm({
  group,
  workObjects,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  group: TelegramGroup | null;
  workObjects: WorkObject[];
  pending: boolean;
  error: string | null;
  onSubmit: (data: TelegramGroupWrite) => void;
  onCancel: () => void;
}) {
  const [chatId, setChatId] = useState(group ? String(group.telegram_chat_id) : "");
  const [name, setName] = useState(group?.name ?? "");
  const [objectId, setObjectId] = useState(group ? String(group.object_id) : "");
  const [isActive, setIsActive] = useState(group?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);
  const knownObject = group !== null && workObjects.some((item) => item.id === group.object_id);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedChatId = parseChatId(chatId);
    if (name.trim() === "" || objectId === "") {
      setFormError("Укажите название, chat ID и объект");
      return;
    }
    if (parsedChatId === "invalid") {
      setFormError("Telegram chat ID должен быть целым числом");
      return;
    }
    setFormError(null);
    onSubmit({
      telegram_chat_id: parsedChatId,
      name: name.trim(),
      object_id: Number(objectId),
      ...(group ? {} : { is_active: isActive }),
    });
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Название" htmlFor="group-name">
          <TextInput id="group-name" value={name} disabled={pending} onChange={(event) => setName(event.target.value)} />
        </Field>
        <Field label="Telegram chat ID" htmlFor="group-chat">
          <TextInput id="group-chat" inputMode="numeric" value={chatId} disabled={pending} onChange={(event) => setChatId(event.target.value)} />
        </Field>
        <Field label="Объект" htmlFor="group-object">
          <SelectInput id="group-object" value={objectId} disabled={pending} onChange={(event) => setObjectId(event.target.value)}>
            <option value="">Не выбран</option>
            {group && !knownObject ? <option value={group.object_id}>Объект #{group.object_id}</option> : null}
            {workObjects.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </SelectInput>
        </Field>
        {group ? null : (
          <label className="flex items-center gap-2 self-end text-sm text-slate-700">
            <input type="checkbox" checked={isActive} disabled={pending} onChange={(event) => setIsActive(event.target.checked)} />
            Активна
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
