export function displayFieldName(field: string) {
  if (field.startsWith("in-") || field.startsWith("out-")) {
    return field.slice(3);
  }
  return field;
}

const PAIRING_LABELS: Record<string, string> = {
  adjacent: "相邻配对",
  random: "随机配对",
  correlation_greedy: "相关性贪心配对",
};

export function displayPairingMethod(method: string | null): string {
  if (!method) return "-";
  return PAIRING_LABELS[method] ?? method;
}
