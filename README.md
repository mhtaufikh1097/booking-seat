# Whoosh Employee Seat Booking

Frontend-only React/Vite prototype for turning a passenger Excel manifest into an employee Premium Economy seat map.

## Run locally

```bash
npm install
npm run dev
```

Create a production build with:

```bash
npm run build
npm run preview
```

## Excel import

Choose or drag in an `.xlsx`/`.xls` file. The first worksheet is read in the browser with SheetJS. The importer looks for these columns (spacing and capitalization do not matter):

- `TRAIN CODE` (required)
- `TRIP DATE` (required)
- `SEAT` (required)
- `ROUTE` (optional)
- `CLASS` (optional)

The first row supplies train, date, and route metadata. If the train code is blank, a code such as `G1013` is extracted from the filename. Dates such as `16/09/2026` are shown as `16 September 2026`.

Only rows whose class is Premium Economy are used as passenger bookings. If no `CLASS` column exists, all valid seats are accepted. Invalid manifests show a friendly error instead of crashing.

## Seat rules

Seats are generated from the master configuration in `src/manifest.js`, never from the Excel rows alone. Every carriage uses `A B C | D F`; seat `E` does not exist. Employee carriages are limited to `02` through `08`:

| Carriage | Rows |
| --- | --- |
| 02, 03, 06, 07 | 1–18 |
| 04 | 1–16 |
| 05 | 1–15 |
| 08 | 4–11 |

Leading zero values such as `002A` are normalized to `2A`. `STAMFFORM CODE` determines the carriage, while `SEAT` determines the passenger-occupied seat within that carriage. Excel seats become grey and disabled; seats absent from the manifest remain visibly ready for employees.

The app starts with the manifest upload screen. This prototype is read-only for employees: it does not create bookings or store employee seat selections.

## GitHub Pages

The Vite `base` is set to `./`, so the static build works from a GitHub Pages project path. Build the app, then publish the generated `dist/` directory with your preferred Pages workflow or static hosting action.

This prototype intentionally has no database, API, authentication, Laravel, or server-side Excel processing.