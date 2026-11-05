import axe from "axe-core";

/**
 * Runs axe on rendered output and returns its findings as short lines, so a failing
 * test says what is wrong. Only WCAG A/AA rules: the "best practice" rules assume a
 * whole page, and these tests render one component at a time.
 * color-contrast is off because jsdom doesn't compute styles; contrast was checked by
 * hand against the design tokens.
 */
export async function axeIssues(node: Element): Promise<string[]> {
  const results = await axe.run(node, {
    runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    rules: { "color-contrast": { enabled: false } },
  });
  return results.violations.map((v) => `${v.id}: ${v.help} (${v.nodes.length}x)`);
}