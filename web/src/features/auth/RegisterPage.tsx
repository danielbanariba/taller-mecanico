import { useNavigate, Link } from "react-router";

import { ApiError } from "../../shared/api/http";
import { getAuthErrorMessage, authCopy } from "./copy";
import { useRegister } from "./hooks";
import { RegisterForm } from "./RegisterForm";
import type { RegisterPayload } from "./api";

/** Container: wires the presentational form to the register mutation and routing. */
export function RegisterPage() {
  const navigate = useNavigate();
  const register = useRegister();

  function handleSubmit(payload: RegisterPayload) {
    register.mutate(payload, {
      onSuccess: () => navigate("/inventario", { replace: true }),
    });
  }

  const errorMessage =
    register.error instanceof ApiError ? getAuthErrorMessage(register.error.code) : undefined;

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center gap-6 px-4 py-8">
      <h1 className="text-3xl font-bold text-brand-primary">{authCopy.register.title}</h1>
      <RegisterForm
        onSubmit={handleSubmit}
        pending={register.isPending}
        errorMessage={errorMessage}
      />
      <Link to="/login" className="text-center text-base font-medium text-brand-accent">
        {authCopy.register.goToLogin}
      </Link>
    </main>
  );
}
