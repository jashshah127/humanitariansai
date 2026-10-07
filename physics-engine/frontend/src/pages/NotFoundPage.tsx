import { Link } from "react-router";

export default function NotFoundPage() {
  return (
    <main className="page">
      <h1>Page not found</h1>
      <p>This address doesn't match any page.</p>
      <Link to="/app">Go to the workspace</Link>
    </main>
  );
}