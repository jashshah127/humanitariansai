import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router";
import { Button } from "../../design/components/Button.tsx";
import { Input } from "../../design/components/Input.tsx";
import { AuthLayout } from "./AuthLayout.tsx";
import { useAuth } from "./AuthContext.ts";
import { messageOf } from "./authErrors.ts";
import styles from "./auth.module.css";

export default function LoginPage() {
  const { session, loading, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (!loading && session) return <Navigate to={from} replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await signIn(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(messageOf(err));
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Sign in">
      {params.get("reason") === "expired" && (
        <p className={styles.note}>Your session ended. Sign in again to keep going.</p>
      )}
      <form className={styles.form} onSubmit={submit}>
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <Button type="submit" loading={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      <p className={styles.links}>
        <Link to="/reset-password">Forgot your password?</Link>
        <Link to="/signup">Create an account</Link>
      </p>
    </AuthLayout>
  );
}
