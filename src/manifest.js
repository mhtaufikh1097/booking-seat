import * as XLSX from 'xlsx'

export const MAX_SELECTION = 1

export const CARRIAGE_CONFIG = {
  '02': { startRow: 1, endRow: 18 },
  '03': { startRow: 1, endRow: 18 },
  '04': { startRow: 1, endRow: 16 },
  '05': { startRow: 1, endRow: 15 },
  '06': { startRow: 1, endRow: 18 },
  '07': { startRow: 1, endRow: 18 },
  '08': { startRow: 4, endRow: 11 },
}

const SEAT_LETTERS = ['A', 'B', 'C', 'D', 'F']

const cleanHeader = (value) => String(value ?? '').trim().toUpperCase().replace(/[^A-Z0-9]/g, '')
const findColumn = (headers, names) => headers.find((header) => names.includes(cleanHeader(header)))
const isManifestHeader = (value, type) => {
  const header = cleanHeader(value)
  if (type === 'train') return header === 'TRAIN' || header.includes('TRAINCODE') || (header.includes('TRAIN') && header.includes('CODE'))
  if (type === 'date') return header === 'DATE' || header.includes('TRIPDATE') || header.endsWith('DATE')
  if (type === 'seat') return header === 'SEAT' || (header.includes('SEAT') && !header.includes('CLASS'))
  return false
}

const readManifestRows = (sheet) => {
  const matrix = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '', blankrows: false })
  const headerIndex = matrix.findIndex((row) => {
    return ['train', 'date', 'seat'].every((type) => row.some((value) => isManifestHeader(value, type)))
  })

  if (headerIndex < 0) return { headers: [], rows: [] }

  const headers = matrix[headerIndex].map((header, index) => String(header || `COLUMN${index + 1}`).trim())
  const rows = matrix.slice(headerIndex + 1).map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])))
  return { headers, rows }
}

export const normalizeSeat = (value) => {
  const match = String(value ?? '').trim().toUpperCase().match(/^(\d{1,3})\s*([ABCDF])$/)
  if (!match) return null
  return `${Number(match[1])}${match[2]}`
}

export const extractCarriage = (seat) => {
  const normalized = normalizeSeat(seat)
  if (!normalized) return null
  const match = normalized.match(/^(\d+)([A-Z])$/)
  return match ? String(Number(match[1])).padStart(2, '0') : null
}

export const extractRow = (seat) => {
  const normalized = normalizeSeat(seat)
  return normalized ? Number(normalized.match(/^(\d+)/)[1]) : null
}

export const extractSeatLetter = (seat) => normalizeSeat(seat)?.slice(-1) ?? null

export const getCarriageLayout = (carriage) => {
  const config = CARRIAGE_CONFIG[carriage]
  if (!config) return []
  return Array.from({ length: config.endRow - config.startRow + 1 }, (_, index) => {
    const row = config.startRow + index
    return SEAT_LETTERS.map((letter) => `${row}${letter}`)
  })
}

const formatDate = (value) => {
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return value.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  }
  const raw = String(value ?? '').trim()
  const slashDate = raw.match(/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/)
  if (slashDate) {
    const date = new Date(Number(slashDate[3]), Number(slashDate[2]) - 1, Number(slashDate[1]))
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  }
  const parsed = new Date(raw)
  return Number.isNaN(parsed.getTime()) ? raw || 'Date unavailable' : parsed.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
}

const formatRoute = (value) => String(value ?? '').trim().replace(/[—–-]+/g, ' → ').replace(/\s*→\s*/g, ' → ') || 'Route unavailable'

export const parseExcel = async (file) => {
  const workbook = XLSX.read(await file.arrayBuffer(), { cellDates: true })
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  const { headers, rows } = readManifestRows(sheet)
  const trainColumn = findColumn(headers, ['TRAINCODE', 'TRAINNUMBER', 'TRAIN'])
  const dateColumn = findColumn(headers, ['TRIPDATE', 'DATE'])
  const seatColumn = findColumn(headers, ['SEAT', 'SEATNUMBER', 'SEATNO'])
  const carriageColumn = findColumn(headers, ['STAMFFORMCODE', 'STAFFORMCODE', 'STAMFORMCODE', 'CARRIAGE', 'CARRIAGECODE'])
  const routeColumn = findColumn(headers, ['ROUTE', 'TRIPROUTE'])
  const classColumn = findColumn(headers, ['CLASS', 'SEATCLASS'])

  if (!trainColumn || !dateColumn || !seatColumn) {
    throw new Error('Unable to read this manifest. Please make sure the Excel contains TRAIN CODE, TRIP DATE and SEAT columns.')
  }

  const bookedSeats = Object.fromEntries(Object.keys(CARRIAGE_CONFIG).map((carriage) => [carriage, new Set()]))
  let premiumRecords = 0
  rows.forEach((row) => {
    const carriageValue = carriageColumn ? String(row[carriageColumn] ?? '').trim() : ''
    const carriageMatch = carriageValue.match(/\d{1,2}/)
    const carriage = carriageMatch ? String(Number(carriageMatch[0])).padStart(2, '0') : extractCarriage(row[seatColumn])
    const seat = normalizeSeat(row[seatColumn])
    const className = String(row[classColumn] ?? '').trim()
    if (carriage && seat && bookedSeats[carriage] && (!className || /premium\s*economy/i.test(className))) {
      bookedSeats[carriage].add(seat)
      premiumRecords += 1
    }
  })

  const filenameTrain = file.name.match(/[A-Z]\d{3,5}/i)?.[0]?.toUpperCase() ?? file.name.replace(/\.xlsx?$/i, '')
  return {
    fileName: file.name,
    trainCode: String(rows[0][trainColumn] || filenameTrain).trim(),
    tripDate: formatDate(rows[0][dateColumn]),
    route: formatRoute(rows[0][routeColumn]),
    className: 'Premium Economy Class',
    passengerRecords: rows.length,
    premiumRecords,
    bookedSeats,
    otherClasses: [...new Set(rows.map((row) => String(row[classColumn] ?? '').trim()).filter((value) => value && !/premium\s*economy/i.test(value)))],
    isDemo: false,
  }
}

export const calculateCarriageSummary = (carriage, manifest, selectedSeats) => {
  const total = getCarriageLayout(carriage).flat().length
  const booked = manifest.bookedSeats[carriage]?.size ?? 0
  const selected = selectedSeats.filter((seat) => seat.startsWith(String(Number(carriage)))).length
  return { total, booked, selected, available: total - booked - selected }
}