export function githubPermalink(
  repo: string,
  branch: string,
  filePath: string,
  line?: number,
): string {
  const normalized = filePath.replace(/^\//, "");
  const base = `https://github.com/${repo}/blob/${branch}/${normalized}`;
  return line ? `${base}#L${line}` : base;
}

export function fileFromTarget(target: string): { path: string; line?: number } {
  const colon = target.indexOf(":");
  if (colon === -1) return { path: target };
  const path = target.slice(colon + 1);
  const hash = path.lastIndexOf("#");
  if (hash === -1) return { path };
  const line = Number(path.slice(hash + 1));
  return { path: path.slice(0, hash), line: Number.isNaN(line) ? undefined : line };
}
