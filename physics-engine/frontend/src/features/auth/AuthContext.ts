import { createContext, useContext } from "react";
import type { Session } from "@supabase/supabase-js";

export interface AuthValue {
  session: Session | null;
  /** The access token to send to server.py. Empty when signed out. */
  token: string;
  /** True until the saved session (if any) has been read. */
  loading: boolean;
  /** False when the build has no Supabase settings. */
  configured: boolean;
  /** This page load came from a password-reset email link. */
  recoveryLink: boolean;
  /** An email link was refused (expired or already used). */
  linkError: string | null;
  signIn(email: string, password: string): Promise<void>;
  /** needsConfirmation: the account exists but the email link must be clicked first. */
  signUp(email: string, password: string): Promise<{ needsConfirmation: boolean }>;
  signOut(): Promise<void>;
  requestReset(email: string): Promise<void>;
  updatePassword(password: string): Promise<void>;
}

const notSetUp = () => Promise.reject(new Error("Sign-in isn't set up on this site."));

// Used when there is no AuthProvider (e.g. a component test): signed out, nothing works.
export const signedOut: AuthValue = {
  session: null,
  token: "",
  loading: false,
  configured: false,
  recoveryLink: false,
  linkError: null,
  signIn: notSetUp,
  signUp: notSetUp,
  signOut: () => Promise.resolve(),
  requestReset: notSetUp,
  updatePassword: notSetUp,
};

export const AuthContext = createContext<AuthValue>(signedOut);

export function useAuth(): AuthValue {
  return useContext(AuthContext);
}
