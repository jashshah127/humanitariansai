import { useEffect } from "react";

const APP = "Physics Engine";

/** Sets the browser tab title. Screen readers read it when a page opens (WCAG 2.4.2). */
export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} – ${APP}` : APP;
  }, [title]);
}