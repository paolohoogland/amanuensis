export function formatTime(seconds: number): string {
  const whole = Number.isFinite(seconds) ? Math.floor(seconds) : 0
  const remainder = String(whole % 60).padStart(2, '0')
  return `${Math.floor(whole / 60)}:${remainder}`
}
