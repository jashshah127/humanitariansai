import { useState } from "react";
import type { FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router";
import { Button } from "../../design/components/Button.tsx";
import { Input } from "../../design/components/Input.tsx";
import { AuthLayout } from "./AuthLayout.tsx";
import { useAuth } from "./AuthContext.ts";
import { messageOf } from "./authErrors.ts";
import styles from "./auth.module.css";

export const MIN_PASSWORD = 8;

export default function SignupPage() {
  const { session, loading, signUp } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sentTo, setSentTo] = useState<string | null>(null);

  if (!loading && session) return <Navigate to="/app" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const { needsConfirmation } = await signUp(email.trim(), password);
      if (needsConfirmation) setSentTo(email.trim());
      else navigate("/app", { replace: true });
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  if (sentTo) {
    return (
      <AuthLayout title="Check your email">
        <p className={styles.lead}>
          If {sentTo} can be used, a confirmation link is on its way. Click it, then sign in.
        </p>
        <p className={styles.links}>
          <Link to="/login">Go to sign in</Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Create an account">
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
          hint={`At least ${MIN_PASSWORD} characters.`}
          type="password"
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
        />
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <Button type="submit" loading={busy}>
          {busy ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className={styles.links}>
        <Link to="/login">Already have an account? Sign in</Link>
      </p>
    </AuthLayout>
  );
}
