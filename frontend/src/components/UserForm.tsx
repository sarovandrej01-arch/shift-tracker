import { useState, type FormEvent } from "react";

import { formatUserRole } from "../auth/roles.ts";
import { Field, SelectInput, TextInput } from "./Field.tsx";
import { buttonClass } from "../lib/ui.ts";
import type { User, UserRole, UserWrite } from "../types/user.ts";

const ROLES: UserRole[] = ["admin", "moderator"];

export function UserForm({
  account,
  currentUserId,
  pending,
  error,
  onSubmit,
  onCancel,
}: {
  account: User | null;
  currentUserId: number | null;
  pending: boolean;
  error: string | null;
  onSubmit: (data: UserWrite) => void;
  onCancel: () => void;
}) {
  const editingSelf = account !== null && account.id === currentUserId;
  const [fullName, setFullName] = useState(account?.full_name ?? "");
  const [email, setEmail] = useState(account?.email ?? "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState<UserRole>(account?.role ?? "moderator");
  const [isActive, setIsActive] = useState(account?.is_active ?? true);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (fullName.trim() === "" || email.trim() === "") {
      setFormError("Укажите имя и email");
      return;
    }
    if (!account && password.length < 8) {
      setFormError("Пароль должен быть не короче 8 символов");
      return;
    }
    if (account && password !== "" && password.length < 8) {
      setFormError("Пароль должен быть не короче 8 символов");
      return;
    }
    setFormError(null);
    const payload: UserWrite = {
      full_name: fullName.trim(),
      email: email.trim(),
      role: editingSelf ? "admin" : role,
      ...(account ? {} : { is_active: isActive }),
    };
    if (password !== "") {
      payload.password = password;
    }
    setPassword("");
    onSubmit(payload);
  }

  return (
    <form className="space-y-3" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="Имя" htmlFor="user-name">
          <TextInput id="user-name" value={fullName} disabled={pending} onChange={(event) => setFullName(event.target.value)} />
        </Field>
        <Field label="Email" htmlFor="user-email">
          <TextInput id="user-email" type="email" autoComplete="off" value={email} disabled={pending} onChange={(event) => setEmail(event.target.value)} />
        </Field>
        <Field label={account ? "Новый пароль" : "Пароль"} htmlFor="user-password">
          <TextInput
            id="user-password"
            type={showPassword ? "text" : "password"}
            autoComplete="new-password"
            value={password}
            disabled={pending}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>
        <div className="flex items-end">
          <button type="button" className={`${buttonClass.secondary} w-full`} onClick={() => setShowPassword((value) => !value)}>
            {showPassword ? "Скрыть пароль" : "Показать пароль"}
          </button>
        </div>
        <Field label="Роль" htmlFor="user-role">
          <SelectInput
            id="user-role"
            value={editingSelf ? "admin" : role}
            disabled={pending || editingSelf}
            onChange={(event) => setRole(event.target.value as UserRole)}
          >
            {ROLES.map((item) => (
              <option key={item} value={item}>
                {formatUserRole(item)}
              </option>
            ))}
          </SelectInput>
        </Field>
        {account ? null : (
          <label className="flex items-center gap-2 self-end text-sm text-slate-700">
            <input type="checkbox" checked={isActive} disabled={pending} onChange={(event) => setIsActive(event.target.checked)} />
            Активен
          </label>
        )}
      </div>
      {editingSelf ? <p className="text-sm text-slate-500">Свою роль администратора здесь изменить нельзя.</p> : null}
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
