import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "../../design/components/Button.tsx";
import { Input } from "../../design/components/Input.tsx";
import { AuthLayout } from "./AuthLayout.tsx";
import { useAuth } from "./AuthContext.ts";
import { messageOf } from "./authErrors.ts";
import { MIN_PASSWORD } from "./SignupPage.tsx";
import styles from "./auth.module.css";

/**
 * Two jobs on one page:
 *  1. no reset link -> ask for an email and send the link;
 *  2. arrived from the link (Supabase has signed the user in) -> choose a new password.
 */
export default function ResetPasswordPage() {
  const { recoveryLink, linkError, session, loading } = useAuth();

  if (recoveryLink && loading) {
    return (
      <AuthLayout title="Reset your password">
        <p className={styles.note}>Checking your reset link…</p>
      </AuthLayout>
    );
  }
  if (recoveryLink && session) return <NewPasswordForm />;

  const linkFailed = linkError !== null || recoveryLink; // link given but no session came of it
  return <RequestLinkForm linkFailed={linkFailed} />;
}

function RequestLinkForm({ linkFailed }: { linkFailed: boolean }) {
  const { requestReset } = useAuth();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await requestReset(email.trim());
      setSent(true);
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <AuthLayout title="Check your email">
        <p className={styles.lead}>
          If an account exists for {email.trim()}, a reset link is on its way. It can take a few
          minutes.
        </p>
        <p className={styles.links}>
          <Link to="/login">Back to sign in</Link>
        </p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset your password">
      {linkFailed && (
        <p className={styles.error} role="alert">
          That reset link has expired or was already used. Ask for a new one below.
        </p>
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
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <Button type="submit" loading={busy}>
          {busy ? "Sending…" : "Send reset link"}
        </Button>
      </form>
      <p className={styles.links}>
        <Link to="/login">Back to sign in</Link>
      </p>
    </AuthLayout>
  );
}

function NewPasswordForm() {
  const { updatePassword } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await updatePassword(password);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(messageOf(err));
      setBusy(false);
    }
  }

  return (
    <AuthLayout title="Choose a new password">
      <form className={styles.form} onSubmit={submit}>
        <Input
          label="New password"
          hint={`At least ${MIN_PASSWORD} characters.`}
          type="password"
          autoComplete="new-password"
          required
          minLength={MIN_PASSWORD}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <Input
          label="Confirm new password"
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
          {busy ? "Saving…" : "Save new password"}
        </Button>
      </form>
    </AuthLayout>
  );
}
