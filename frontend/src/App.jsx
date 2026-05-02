import { useState } from 'react'
import TripForm from './components/TripForm'
import TripSummary from './components/TripSummary'
import RouteMap from './components/RouteMap'
import StopsTimeline from './components/StopsTimeline'
import ELDLogSheet from './components/ELDLogSheet'

const API_URL = import.meta.env.VITE_API_URL || 'https://web-production-94f3a.up.railway.app'
function App() {
  const [tripData, setTripData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (formData) => {
    setLoading(true)
    setError(null)
    setTripData(null)

    try {
      const res = await fetch(`${API_URL}/api/plan-trip/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.error || 'Failed to plan trip.')
      }

      setTripData(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div className="bg-grid" />

      <nav className="navbar">
        <div className="navbar-brand">
          <div className="navbar-logo">🚛</div>
          <div>
            <div className="navbar-title">TruckLog Pro</div>
            <div className="navbar-subtitle">ELD Trip Planner</div>
          </div>
        </div>
        <div className="navbar-badge">FMCSA HOS Compliant</div>
      </nav>

      <main className="main-content">
        <TripForm onSubmit={handleSubmit} loading={loading} />

        {error && (
          <div className="error-message">
            <span>⚠️</span> {error}
          </div>
        )}

        {loading && (
          <div className="loading-text">
            <div className="spinner" />
            Calculating HOS-compliant route and generating ELD logs...
          </div>
        )}

        {tripData && (
          <div className="results-container">
            <TripSummary summary={tripData.summary} locations={tripData.locations} />

            <section className="map-section">
              <div className="section-header">
                <h2 className="section-title">🗺️ Route Map</h2>
                <p className="section-subtitle">
                  Route with all mandatory stops marked
                </p>
              </div>
              <RouteMap
                route={tripData.route}
                stops={tripData.stops}
                locations={tripData.locations}
              />
            </section>

            <section className="stops-section">
              <div className="section-header">
                <h2 className="section-title">📋 Trip Stops & Schedule</h2>
                <p className="section-subtitle">
                  Chronological list of all stops along the route
                </p>
              </div>
              <StopsTimeline stops={tripData.stops} />
            </section>

            <section className="logs-section">
              <div className="section-header">
                <h2 className="section-title">📊 Daily ELD Log Sheets</h2>
                <p className="section-subtitle">
                  FMCSA-compliant Driver Daily Logs for the entire trip
                </p>
              </div>
              {tripData.daily_logs.map((log, idx) => (
                <ELDLogSheet key={idx} log={log} driverName="Driver" carrierName="Carrier" />
              ))}
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
