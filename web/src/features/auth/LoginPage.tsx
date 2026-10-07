import { useNavigate, Link } from "react-router";

import { ApiError } from "../../shared/api/http";
import { getAuthErrorMessage, authCopy } from "./copy";
import { useLogin } from "./hooks";
import { LoginForm } from "./LoginForm";
import type { LoginPayload } from "./api";

/** Container: wires the presentational form to the login mutation and routing. */
export function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();

  function handleSubmit(payload: LoginPayload) {
    login.mutate(payload, {
      onSuccess: () => navigate("/inventario", { replace: true }),
    });
  }

  const errorMessage =
    login.error instanceof ApiError ? getAuthErrorMessage(login.error.code) : undefined;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold text-brand-primary">{authCopy.login.title}</h1>
      <LoginForm onSubmit={handleSubmit} pending={login.isPending} errorMessage={errorMessage} />
      <Link to="/registro" className="text-center text-base font-medium text-brand-accent">
        {authCopy.login.goToRegister}
      </Link>
    </main>
  );
}
