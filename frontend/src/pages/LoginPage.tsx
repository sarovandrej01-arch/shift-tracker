import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { getLoginErrorMessage } from "../auth/loginError.ts";
import { LoadingScreen } from "../components/LoadingScreen.tsx";
import { useAuth } from "../hooks/useAuth.ts";

export function LoginPage() {
  const { isAuthenticated, isLoading, authError, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextEmailError = email.trim() === "" ? "Введите email" : null;
    const nextPasswordError = password === "" ? "Введите пароль" : null;
    setEmailError(nextEmailError);
    setPasswordError(nextPasswordError);
    setSubmitError(null);

    if (nextEmailError || nextPasswordError) {
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      setPassword("");
      void navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmitError(getLoginErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  const formError = submitError ?? authError;

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8">
        <p className="text-sm font-semibold text-slate-900">Shift Tracker</p>
        <h1 className="mt-2 text-2xl font-semibold">Вход в систему</h1>
        <p className="mt-2 text-sm text-slate-600">Введите данные учетной записи</p>
        <form className="mt-6 space-y-4" noValidate onSubmit={(event) => void handleSubmit(event)}>
          <div>
            <label className="block text-sm font-medium text-slate-700" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              disabled={isSubmitting}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setEmail(event.target.value)}
            />
            {emailError ? <p className="mt-1 text-sm text-red-700">{emailError}</p> : null}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700" htmlFor="password">
              Пароль
            </label>
            <input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              disabled={isSubmitting}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setPassword(event.target.value)}
            />
            {passwordError ? <p className="mt-1 text-sm text-red-700">{passwordError}</p> : null}
          </div>
          {formError ? (
            <p className="text-sm text-red-700" role="alert">
              {formError}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
          >
            {isSubmitting ? "Вход…" : "Войти"}
          </button>
        </form>
      </div>
    </div>
  );
}
