import { NextResponse } from "next/server"
import { csvParse, tsvParse } from "d3-dsv"
import * as fs from "node:fs/promises"
import * as path from "node:path"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

// Adjust if your repo layout changes
const CSV_PATH = path.join(process.cwd(), "..", "backend", "data", "powerpulse-datas.csv")

function parseMaybeCSV(text: string) {
  // Try comma first; fall back to TSV if needed
  const byComma = csvParse(text)
  if (byComma.columns.length > 1) return byComma
  return tsvParse(text)
}

export async function GET(req: Request) {
  try {
    const url = new URL(req.url)
    const homeId = url.searchParams.get("homeId") // optional
    const appliance = url.searchParams.get("appliance") // optional

    const text = await fs.readFile(CSV_PATH, "utf8")
    const rows = parseMaybeCSV(text)

    const shaped = rows.map((r: any) => ({
      homeId: String(r["Home ID"] ?? "").trim(),
      date: String(r["Date"] ?? "").trim(),
      time: String(r["Time"] ?? "").trim(),
      appliance: String(r["Appliance Type"] ?? "").trim(),
      kwh: Number(r["Energy Consumption (kWh)"] ?? 0),
      tou: String(r["TOU Period"] ?? r["TOU period"] ?? "").trim(),
      tariff: Number(r["Tariff ($/kWh)"] ?? r["Tariff"] ?? 0),
      outC: Number(r["Outdoor Temperature (C)"] ?? r["Outdoor Temperature (°C)"] ?? 0),
      inC: Number(r["Indoor Temperature (C)"] ?? 0),
    }))

    let filtered = shaped
    if (homeId) filtered = filtered.filter((r) => r.homeId === homeId)
    if (appliance) filtered = filtered.filter((r) => r.appliance === appliance)

    return NextResponse.json(filtered)
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}