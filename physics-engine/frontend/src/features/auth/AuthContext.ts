import { createContext, useContext } from "react";
import type { Session } from "@supabase/supabase-js";
import type { Role, RoleStatus } from "./useRole.ts";

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
  /** From GET /me. null while signed out, still loading, or if the check failed. */
  role: Role | null;
  roleStatus: RoleStatus;
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
  role: null,
  roleStatus: "idle",
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

/** For showing or hiding admin features only. The database enforces the real check. */
export function useIsAdmin(): boolean {
  return useContext(AuthContext).role === "admin";
}
