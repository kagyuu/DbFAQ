const pad = (n: number) => String(n).padStart(2, '0')

/** ISO 8601 の日時をブラウザのローカル時刻で YYYY-MM-DD HH:mm:ss にする */
export function formatLocalDateTime(iso: string): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
