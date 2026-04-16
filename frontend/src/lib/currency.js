const VND_FORMATTER = new Intl.NumberFormat("vi-VN", {
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function toVndInteger(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.round(numeric);
}

export function formatVnd(value) {
  return `${VND_FORMATTER.format(toVndInteger(value))} VND`;
}
