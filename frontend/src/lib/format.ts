const TIME_ZONE = "Asia/Dhaka";

const dateFormat = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const dateTimeFormat = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: TIME_ZONE,
});
const monthFormat = new Intl.DateTimeFormat("en-GB", { month: "short", year: "2-digit", timeZone: "UTC" });
const numberFormat = new Intl.NumberFormat("en-US");

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  return dateFormat.format(new Date(`${value.slice(0, 10)}T00:00:00Z`));
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return dateTimeFormat.format(new Date(value));
}

export function formatMonth(value: string): string {
  return monthFormat.format(new Date(`${value}-01T00:00:00Z`));
}

export function formatNumber(value: number | null | undefined): string {
  return value === null || value === undefined ? "—" : numberFormat.format(value);
}

export function todayInDhaka(): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(new Date());
}

export function localInputToIso(value: string): string {
  return `${value.length === 16 ? `${value}:00` : value}+06:00`;
}

export function isoToLocalInput(value: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(value));
  const get = (type: string) => parts.find((part) => part.type === type)?.value ?? "00";
  const hour = get("hour") === "24" ? "00" : get("hour");
  return `${get("year")}-${get("month")}-${get("day")}T${hour}:${get("minute")}`;
}

export function nowLocalInput(): string {
  return isoToLocalInput(new Date().toISOString());
}

export function daysUntil(date: string): number {
  const today = new Date(`${todayInDhaka()}T00:00:00Z`).getTime();
  return Math.round((new Date(`${date}T00:00:00Z`).getTime() - today) / 86_400_000);
}
