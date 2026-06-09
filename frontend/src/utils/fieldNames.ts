export function displayFieldName(field: string) {
  if (field.startsWith("in-") || field.startsWith("out-")) {
    return field.slice(3);
  }
  return field;
}
