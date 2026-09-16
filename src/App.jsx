import { useRef, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Armchair,
  Check,
  FileSpreadsheet,
  Info,
  Map,
  TrainFront,
  Upload,
  UserRound,
} from "lucide-react";
import "./App.css";
import {
  calculateCarriageSummary,
  CARRIAGE_CONFIG,
  getCarriageLayout,
  parseExcel,
} from "./manifest";

const carriages = Object.keys(CARRIAGE_CONFIG);

function BrandMark() {
  return (
    <div className="brand-mark" aria-label="Whoosh">
      Whoosh<span>.</span>
    </div>
  );
}

function BottomNav({ onUpload, onGuide }) {
  return (
    <nav className="bottom-nav" aria-label="Mobile navigation">
      <button
        className="bottom-nav-item"
        onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      >
        <Map size={18} />
        <span>Overview</span>
      </button>
      <button className="bottom-nav-upload" onClick={onUpload}>
        <span>
          <Upload size={20} />
        </span>
        <small>Upload</small>
      </button>
      <button className="bottom-nav-item" onClick={onGuide}>
        <Info size={18} />
        <span>Guide</span>
      </button>
    </nav>
  );
}

function GuidePanel({ onClose }) {
  return (
    <div className="guide-backdrop" onClick={onClose}>
      <section
        className="guide-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="guide-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="guide-panel-handle" />
        <div className="guide-panel-heading">
          <div>
            <span className="kicker">Quick guide</span>
            <h2 id="guide-title">Read the seat map</h2>
          </div>
          <button
            className="guide-close"
            onClick={onClose}
            aria-label="Close guide"
          >
            ×
          </button>
        </div>
        <div className="guide-items">
          <div>
            <span className="guide-dot ready" />
            <div>
              <strong>Ready for employee</strong>
              <p>Seat is not listed in the passenger manifest.</p>
            </div>
          </div>
          <div>
            <span className="guide-dot booked" />
            <div>
              <strong>Booked by passenger</strong>
              <p>Seat appears in the uploaded manifest and cannot be used.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function Header({ onBack, showBack }) {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        {showBack ? (
          <button
            className="icon-button back-button"
            onClick={onBack}
            aria-label="Back"
          >
            <ArrowLeft size={19} />
          </button>
        ) : (
          <BrandMark />
        )}
        <div className="header-title">Employee Seat Availability</div>
        <div className="employee-chip">
          <UserRound size={16} />
          <span>Muhammad Taufik</span>
        </div>
      </div>
    </header>
  );
}

function ImportManifest({ onImport, error, onGuide }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const handleFile = async (file) => {
    if (file) await onImport(file);
  };
  return (
    <>
      <main className="import-page">
        <section className="import-hero">
          <div className="eyebrow">
            <span className="eyebrow-dot" /> HPR workspace
          </div>
          <h1>Turn a passenger manifest into a seat map.</h1>
          <p>
            Import the latest Excel manifest to see premium economy availability
            at a glance.
          </p>
        </section>
        <section
          className={`upload-panel ${isDragging ? "is-dragging" : ""}`}
          onDragOver={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            handleFile(event.dataTransfer.files[0]);
          }}
        >
          <div className="upload-icon">
            <FileSpreadsheet size={28} />
          </div>
          <h2>Passenger manifest</h2>
          <p>
            Drag and drop an Excel file here, or choose one from your device.
          </p>
          <button
            className="primary-button"
            onClick={() => inputRef.current?.click()}
          >
            <Upload size={18} /> Choose Excel file
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xls"
            hidden
            onChange={(event) => handleFile(event.target.files[0])}
          />
          <span className="file-hint">Supported format: .xlsx or .xls</span>
          {error && <div className="error-message">{error}</div>}
        </section>
        {/* <div className="import-note"><Check size={16} /> Data stays in your browser. No server upload.</div> */}
      </main>
      <BottomNav
        onUpload={() => inputRef.current?.click()}
        onGuide={() => onGuide()}
      />
    </>
  );
}

function TripInformation({ manifest }) {
  const routeParts = manifest.route.split(" → ");
  return (
    <section className="trip-card">
      <div className="trip-main">
        <div className="trip-icon">
          <TrainFront size={22} />
        </div>
        <div>
          <span className="label">Train</span>
          <strong>{manifest.trainCode}</strong>
        </div>
      </div>
      <div className="trip-route">
        <div className="route-line">
          <span>{routeParts[0]}</span>
          <ArrowRight size={16} />
          <span>{routeParts[1] || manifest.route}</span>
        </div>
        <span className="trip-date">{manifest.tripDate}</span>
      </div>
      <div className="class-pill">{manifest.className}</div>
    </section>
  );
}

function MobileTripPanel({ manifest, selectedCarriage, onSelect }) {
  return (
    <section className="mobile-trip-panel">
      <div className="mobile-passenger-row">
        <span>Passenger</span>
        <strong>Muhammad Taufik <span>›</span></strong>
      </div>
      <span className="mobile-select-label">Select carriage</span>
      <div className="mobile-carriage-list">
        {carriages.map((carriage) => (
          <button
            key={carriage}
            className={selectedCarriage === carriage ? "active" : ""}
            onClick={() => onSelect(carriage)}
          >
            {carriage}
          </button>
        ))}
      </div>
    </section>
  )
}

function ManifestStats({ manifest }) {
  return (
    <div className="manifest-stats">
      <div>
        <span>Passenger records</span>
        <strong>{manifest.passengerRecords}</strong>
      </div>
      <div>
        <span>Premium economy</span>
        <strong>{manifest.premiumRecords}</strong>
      </div>
      <div>
        <span>Available carriages</span>
        <strong>02–08</strong>
      </div>
    </div>
  );
}

function CarriageSelector({ selectedCarriage, onSelect }) {
  return (
    <section className="selector-section">
      <div className="section-heading">
        <div>
          <span className="kicker">Seat map</span>
          <h2>Select carriage</h2>
        </div>
        <span className="section-note">Premium economy</span>
      </div>
      <div className="carriage-list">
        {carriages.map((carriage) => (
          <button
            key={carriage}
            className={`carriage-button ${selectedCarriage === carriage ? "active" : ""}`}
            onClick={() => onSelect(carriage)}
          >
            {carriage}
          </button>
        ))}
      </div>
    </section>
  );
}

function SeatButton({ seat, booked }) {
  const state = booked ? "booked" : "available";
  return (
    <div className={`seat-button ${state}`} aria-label={`${seat}, ${state}`}>
      <Armchair className="seat-icon" size={24} strokeWidth={2.5} />
      <span>{seat}</span>
    </div>
  );
}

function SeatMap({ carriage, manifest }) {
  const bookedSeats = manifest.bookedSeats[carriage] ?? new Set();
  const rows = getCarriageLayout(carriage);
  return (
    <section className="seat-map-card">
      <div className="map-title">
        <div>
          <span className="kicker">Carriage {carriage}</span>
          <h2>Select seat</h2>
        </div>
        <span className="row-count">Selected: <strong>0</strong></span>
      </div>
      <div className="seat-grid">
        <div className="seat-header">
          <span>Row</span>
          <span>A</span>
          <span>B</span>
          <span>C</span>
          <span className="aisle-label">Aisle</span>
          <span>D</span>
          <span>F</span>
        </div>
        {rows.map((row) => (
          <div className="seat-row" key={row[0]}>
            <span className="row-label">{row[0].replace(/[A-Z]/g, "")}</span>
            {row.map((seat, index) => (
              <span className={index === 3 ? "aisle-space" : ""} key={seat}>
                <SeatButton seat={seat} booked={bookedSeats.has(seat)} />
              </span>
            ))}
          </div>
        ))}
      </div>
      {!bookedSeats.size && (
        <p className="empty-state">
          All seats are currently available based on the uploaded manifest.
        </p>
      )}
    </section>
  );
}

function Legend() {
  return (
    <div className="legend">
      <div>
        <span className="legend-seat available" />
        Ready for employee
      </div>
      <div>
        <span className="legend-seat booked" />
        Booked by passenger
      </div>
    </div>
  );
}

function BookingSummary({ carriage, manifest, onUploadNew }) {
  const summary = calculateCarriageSummary(carriage, manifest, []);
  return (
    <aside className="summary-card">
      <div className="summary-heading">
        <div>
          <span className="kicker">Live summary</span>
          <h2>Availability</h2>
        </div>
        <span className="summary-status">
          <span /> Ready
        </span>
      </div>
      <div className="summary-stats">
        <div>
          <span>Total seats</span>
          <strong>{summary.total}</strong>
        </div>
        <div>
          <span>Passenger booked</span>
          <strong>{summary.booked}</strong>
        </div>
        <div>
          <span>Ready for employee</span>
          <strong>{summary.available}</strong>
        </div>
      </div>
      <p className="availability-copy">
        Employees do not need to submit a booking. Use the map to identify seats
        that are not occupied by passengers.
      </p>
      <Legend />
      <button className="text-button" onClick={onUploadNew}>
        <Upload size={15} /> Upload new manifest
      </button>
    </aside>
  );
}

function BookingPage({ manifest, onUploadNew, onGuide }) {
  const [selectedCarriage, setSelectedCarriage] = useState("02");
  return (
    <>
      <Header showBack onBack={onUploadNew} />
      <main className="booking-page">
        <div className="page-heading">
          <div>
            <span className="eyebrow">
              <span className="eyebrow-dot" /> Manifest imported{" "}
              {manifest.isDemo && "· Demo mode"}
            </span>
            <h1>Passenger seat availability.</h1>
            <p>View which Premium Economy seats are ready for employees.</p>
          </div>
          <div className="file-badge">
            <FileSpreadsheet size={17} />
            <span>{manifest.fileName}</span>
          </div>
        </div>
        <TripInformation manifest={manifest} />
        <ManifestStats manifest={manifest} />
        {manifest.otherClasses?.length > 0 && (
          <div className="info-note">
            <span>i</span> Employee view is limited to Premium Economy carriages
            02–08. Other classes were ignored.
          </div>
        )}
        <CarriageSelector
          selectedCarriage={selectedCarriage}
          onSelect={setSelectedCarriage}
        />
        <MobileTripPanel
          manifest={manifest}
          selectedCarriage={selectedCarriage}
          onSelect={setSelectedCarriage}
        />
        <div className="booking-layout">
          <SeatMap carriage={selectedCarriage} manifest={manifest} />
          <BookingSummary
            carriage={selectedCarriage}
            manifest={manifest}
            onUploadNew={onUploadNew}
          />
        </div>
      </main>
      <footer>
        <BrandMark />
        <span>Employee Seat Availability Prototype · Frontend only</span>
      </footer>
      <BottomNav onUpload={onUploadNew} onGuide={onGuide} />
    </>
  );
}

function App() {
  const [manifest, setManifest] = useState(null);
  const [importError, setImportError] = useState("");
  const [showGuide, setShowGuide] = useState(false);
  const handleImport = async (file) => {
    if (!/\.xlsx?$/i.test(file.name)) {
      setImportError("Please choose an Excel file in .xlsx or .xls format.");
      return;
    }
    try {
      setImportError("");
      setManifest(await parseExcel(file));
    } catch (error) {
      setImportError(error.message);
    }
  };
  const handleUploadNew = () => {
    setManifest(null);
    setImportError("");
  };
  return (
    <>
      {manifest ? (
        <BookingPage
          manifest={manifest}
          onUploadNew={handleUploadNew}
          onGuide={() => setShowGuide(true)}
        />
      ) : (
        <>
          <Header />
          <ImportManifest
            onImport={handleImport}
            error={importError}
            onGuide={() => setShowGuide(true)}
          />
          <footer>
            <BrandMark />
            <span>Employee Seat Booking </span>
          </footer>
        </>
      )}
      {showGuide && <GuidePanel onClose={() => setShowGuide(false)} />}
    </>
  );
}

export default App;
