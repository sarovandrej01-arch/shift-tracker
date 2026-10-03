export function definedParams(
  values: Record<string, string | number | boolean | null | undefined>,
): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(values)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    params[key] = value;
  }
  return params;
}
