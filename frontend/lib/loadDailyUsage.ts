import { parse } from "date-fns"

type ApiRow = {
  homeId: string
  date: string
  time: string
  kwh: number
}

function hourFromTime(t: string) {
  // Expect "HH:mm". If "24:00" appears, map to "00:00"
  const [hStr] = t.split(":")
  const h = Math.min(23, Math.max(0, Number(hStr) || 0))
  return h
}

function hourLabel(h: number) {
  return `${String(h).padStart(2, "0")}:00`
}

export async function loadDailyUsageByHour(homeId: string, date?: string) {
  // 1) fetch all rows for the home
  const res = await fetch(`/api/energy?homeId=${encodeURIComponent(homeId)}`, { cache: "no-store" })
  const all = (await res.json()) as ApiRow[]

  if (!all.length) return Array.from({ length: 24 }, (_, h) => ({ time: hourLabel(h), kwh: 0 }))

  // 2) choose target date (passed in or latest date for that home)
  let targetDate = date
  if (!targetDate) {
    // find max date using Date parsing (file is m/d/yy)
    const latest = all
      .map(r => ({ r, d: parse(r.date, "M/d/yy", new Date()) }))
      .sort((a, b) => b.d.getTime() - a.d.getTime())[0]
    targetDate = latest?.r.date
  }

  // 3) filter rows for that date
  const rows = all.filter(r => r.date === targetDate)

  // 4) sum kWh per hour across ALL appliances
  const sums = new Array(24).fill(0)
  for (const r of rows) {
    const h = hourFromTime(r.time)
    sums[h] += Number.isFinite(r.kwh) ? r.kwh : 0
  }

  // 5) return 24 points with labels
  return sums.map((v, h) => ({ time: hourLabel(h), kwh: +v.toFixed(3) }))
}