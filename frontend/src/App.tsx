
import { useState } from 'react'
import type { FormEvent } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''


// Vehicle information returned by FastAPI
interface Vehicle {
  registration_number: string
  make: string
  model: string
  variant?: string | null
  fuel_type?: string | null
  engine_cc?: number | null
  registration_date?: string | null
  rto?: string | null
  ex_showroom_price?: number | null
}

// Normalized insurance quote
interface Quote {
  provider: string
  registration_number: string
  plan_name: string
  source_quote_id?: string | null
  coverage_type: string
  idv?: number | string | null
  base_premium: number | string
  tax_amount: number | string
  total_premium: number | string
  premium_basis: string
  addons: string[]
  valid_until?: string | null
}

// Aggregated quote response
interface QuoteResult {
  vehicle: Vehicle
  quote_date: string
  all_quotes: Quote[]
  valid_quotes: Quote[]
  expired_quotes: Quote[]
  declined: Array<Record<string, string>>
  provider_errors: Array<Record<string, string>>
  cheapest_quote: Quote | null
}

// Saved selection response
interface SelectionResponse {
  id: string
  registration_number: string
  provider: string
  plan_name: string
  total_premium: number | string
  status: string
}

// Currency formatter
const formatMoney = (value?: number | string | null) => {
  if (value === null || value === undefined || value === '') {
    return 'Not available'
  }

  const amount = Number(value)

  if (!Number.isFinite(amount)) {
    return 'Not available'
  }

  return amount.toLocaleString('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  })
}

function App() {
  // Vehicle lookup state
  const [registration, setRegistration] = useState('')
  const [vehicle, setVehicle] = useState<Vehicle | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Quote comparison state
  const [quoteResult, setQuoteResult] = useState<QuoteResult | null>(null)
  const [quoteLoading, setQuoteLoading] = useState(false)
  const [quoteError, setQuoteError] = useState('')

  // Plan selection state
  const [selectedQuote, setSelectedQuote] = useState<Quote | null>(null)
  const [savingSelection, setSavingSelection] = useState(false)
  const [selectionConfirmation, setSelectionConfirmation] =
    useState<SelectionResponse | null>(null)
  const [selectionError, setSelectionError] = useState('')

  // STEP 1: Vehicle lookup
  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const reg = registration.trim().replace(/[\s-]/g, '').toUpperCase()

    if (!reg) {
      setError('Please enter your vehicle registration number.')
      return
    }

    setLoading(true)
    setError('')
    setQuoteError('')
    setVehicle(null)
    setQuoteResult(null)
    setSelectedQuote(null)
    setSelectionConfirmation(null)
    setSelectionError('')

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/vehicles/${encodeURIComponent(reg)}`
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Vehicle not found.')
      }

      setVehicle(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Unable to connect to the server.'
      )
    } finally {
      setLoading(false)
    }
  }

  // STEP 2: Retrieve insurance quotes
  async function handleCompareQuotes() {
    if (!vehicle) return

    setQuoteLoading(true)
    setQuoteError('')
    setQuoteResult(null)
    setSelectedQuote(null)
    setSelectionConfirmation(null)
    setSelectionError('')

    try {
    const response = await fetch(
      `${API_BASE_URL}/api/quotes/${encodeURIComponent(vehicle.registration_number)}`
    )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(
          data.detail || 'Unable to retrieve insurance quotes.'
        )
      }

      setQuoteResult(data)
    } catch (err) {
      setQuoteError(
        err instanceof Error
          ? err.message
          : 'Unable to retrieve insurance quotes.'
      )
    } finally {
      setQuoteLoading(false)
    }
  }

  // STEP 3: Select an insurance plan
  function handleSelectPlan(quote: Quote) {
    setSelectedQuote(quote)
    setSelectionConfirmation(null)
    setSelectionError('')
  }

  // STEP 4: Save selected plan in PostgreSQL
  async function handleConfirmSelection() {
    if (!selectedQuote || !vehicle || savingSelection) return

    setSavingSelection(true)
    setSelectionError('')

    try {
      const response = await fetch(`${API_BASE_URL}/api/selections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          registration_number: vehicle.registration_number,
          provider: selectedQuote.provider,
          plan_name: selectedQuote.plan_name,
          coverage_type: selectedQuote.coverage_type || 'UNKNOWN',
          idv: selectedQuote.idv,
          base_premium: selectedQuote.base_premium,
          tax_amount: selectedQuote.tax_amount,
          total_premium: selectedQuote.total_premium,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to save selection.')
      }

      setSelectionConfirmation(data)
      setSelectedQuote(null)
    } catch (err) {
      setSelectionError(
        err instanceof Error
          ? err.message
          : 'Unable to save your selection.'
      )
    } finally {
      setSavingSelection(false)
    }
  }

  // Render an individual insurance quote
  function renderQuoteCard(
    quote: Quote,
    isCheapest = false,
    selectable = true
  ) {
    return (
      <article
        className="quote-card"
        key={`${quote.provider}-${quote.plan_name}-${quote.source_quote_id || ''}`}
      >
        {isCheapest && (
          <div className="best-value">LOWEST VALID PREMIUM</div>
        )}

        <div className="quote-header">
          <div>
            <span className="provider-label">
              PROVIDER {quote.provider}
            </span>
            <h3>{quote.plan_name}</h3>
          </div>

          <div className="quote-price">
            <strong>{formatMoney(quote.total_premium)}</strong>
            <small>Total premium</small>
          </div>
        </div>

        <div className="quote-details">
          <div>
            <small>Insured declared value</small>
            <strong>{formatMoney(quote.idv)}</strong>
          </div>

          <div>
            <small>Coverage</small>
            <strong>
              {quote.coverage_type?.replaceAll('_', ' ') || 'Unknown'}
            </strong>
          </div>

          <div>
            <small>Base premium</small>
            <strong>{formatMoney(quote.base_premium)}</strong>
          </div>

          <div>
            <small>GST / Tax</small>
            <strong>{formatMoney(quote.tax_amount)}</strong>
          </div>
        </div>

        <div className="quote-addons">
          <small>Included add-ons</small>

          <div className="addon-list">
            {quote.addons?.length ? (
              quote.addons.map((addon, index) => (
                <span key={`${addon}-${index}`}>{addon}</span>
              ))
            ) : (
              <span>No add-ons listed</span>
            )}
          </div>
        </div>

        <div className="quote-footer">
          <span>
            {quote.valid_until
              ? `Valid until ${quote.valid_until}`
              : 'Validity not specified'}
          </span>

          <span>
            {quote.premium_basis?.replaceAll('_', ' ')}
          </span>
        </div>

        {selectable && (
          <button
            className="select-plan-button"
            onClick={() => handleSelectPlan(quote)}
          >
            Select this plan →
          </button>
        )}
      </article>
    )
  }

  return (
    <main className="page">

      {/* NAVIGATION */}
      <nav className="navbar">
        <a className="brand" href="/">
          Auto<span>Cover</span>
        </a>

        <span className="nav-label">
          Smart Insurance Comparison
        </span>
      </nav>

      {/* HERO AND VEHICLE SEARCH */}
      <section className="hero">
        <div className="eyebrow">
          YOUR INSURANCE, SIMPLIFIED
        </div>

        <h1>
          Find the right cover.
          <br />
          <span>Not just the lowest price.</span>
        </h1>

        <p className="subtitle">
          Enter your vehicle registration number to discover
          insurance options from multiple providers.
        </p>

        <form className="search-form" onSubmit={handleSearch}>
          <label htmlFor="registration">
            VEHICLE REGISTRATION NUMBER
          </label>

          <div className="search-row">
            <input
              id="registration"
              value={registration}
              onChange={(event) => setRegistration(event.target.value)}
              placeholder="e.g. WB02AB1234"
              autoComplete="off"
            />

            <button type="submit" disabled={loading}>
              {loading ? 'Searching...' : 'Find my vehicle →'}
            </button>
          </div>
        </form>

        <div className="trust-note">
          <span>✓</span> Secure lookup
          <span>✓</span> Multiple providers
          <span>✓</span> Transparent comparison
        </div>

        {error && (
          <div className="error-message">{error}</div>
        )}

        {/* VEHICLE DETAILS */}
        {vehicle && (
          <section className="vehicle-card">
            <div className="vehicle-heading">
              <div>
                <span className="success-label">
                  VEHICLE FOUND
                </span>

                <h2>
                  {vehicle.make} {vehicle.model}
                </h2>
              </div>

              <span className="registration-badge">
                {vehicle.registration_number}
              </span>
            </div>

            <div className="vehicle-details">
              <div>
                <small>Variant</small>
                <strong>{vehicle.variant || 'Not available'}</strong>
              </div>

              <div>
                <small>Fuel type</small>
                <strong>{vehicle.fuel_type || 'Not available'}</strong>
              </div>

              <div>
                <small>Engine capacity</small>
                <strong>
                  {vehicle.engine_cc
                    ? `${vehicle.engine_cc} cc`
                    : 'Not available'}
                </strong>
              </div>

              <div>
                <small>Registration date</small>
                <strong>
                  {vehicle.registration_date || 'Not available'}
                </strong>
              </div>

              <div>
                <small>RTO</small>
                <strong>{vehicle.rto || 'Not available'}</strong>
              </div>
            </div>

            <button
              className="compare-button"
              onClick={handleCompareQuotes}
              disabled={quoteLoading}
            >
              {quoteLoading
                ? 'Comparing quotes...'
                : 'Compare insurance quotes →'}
            </button>

            <div className="vehicle-footer">
              Vehicle information retrieved from the supplied registry.
            </div>
          </section>
        )}

        {quoteError && (
          <div className="error-message">{quoteError}</div>
        )}

        {/* QUOTE COMPARISON */}
        {quoteResult && (
          <section className="comparison-section">
            <div className="comparison-heading">
              <span className="success-label">
                QUOTE COMPARISON
              </span>

              <h2>Choose the cover that suits you.</h2>

              <p>
                {quoteResult.valid_quotes.length} valid quotes found
                {' · '}
                Quote date: {quoteResult.quote_date}
              </p>
            </div>

            {/* CHEAPEST VALID QUOTE */}
            {quoteResult.cheapest_quote && (
              <div className="cheapest-banner">
                <div>
                  <span>LOWEST VALID PREMIUM</span>

                  <h3>
                    {quoteResult.cheapest_quote.provider}
                    {' · '}
                    {quoteResult.cheapest_quote.plan_name}
                  </h3>
                </div>

                <strong>
                  {formatMoney(
                    quoteResult.cheapest_quote.total_premium
                  )}
                </strong>
              </div>
            )}

            {/* VALID QUOTES */}
            {quoteResult.valid_quotes.length > 0 ? (
              <div className="quotes-grid">
                {quoteResult.valid_quotes.map((quote) =>
                  renderQuoteCard(
                    quote,
                    quote.provider === quoteResult.cheapest_quote?.provider &&
                      quote.plan_name === quoteResult.cheapest_quote?.plan_name &&
                      Number(quote.total_premium) ===
                        Number(quoteResult.cheapest_quote?.total_premium)
                  )
                )}
              </div>
            ) : (
              <p className="empty-quotes">
                No valid insurance quotes are available for this vehicle.
              </p>
            )}

            {/* EXPIRED QUOTES */}
            {quoteResult.expired_quotes.length > 0 && (
              <details className="expired-section">
                <summary>
                  View {quoteResult.expired_quotes.length} expired quotes
                </summary>

                <div className="quotes-grid">
                  {quoteResult.expired_quotes.map((quote) =>
                    renderQuoteCard(quote, false, false)
                  )}
                </div>
              </details>
            )}

            {/* PLAN REVIEW */}
            {selectedQuote && (
              <section className="selection-review">
                <span className="success-label">
                  REVIEW YOUR SELECTION
                </span>

                <h2>Confirm your insurance plan</h2>

                <div className="review-row">
                  <span>Registration</span>
                  <strong>{vehicle?.registration_number}</strong>
                </div>

                <div className="review-row">
                  <span>Provider</span>
                  <strong>{selectedQuote.provider}</strong>
                </div>

                <div className="review-row">
                  <span>Plan</span>
                  <strong>{selectedQuote.plan_name}</strong>
                </div>

                <div className="review-row">
                  <span>Coverage</span>
                  <strong>
                    {selectedQuote.coverage_type?.replaceAll('_', ' ')}
                  </strong>
                </div>

                <div className="review-row">
                  <span>Insured declared value</span>
                  <strong>{formatMoney(selectedQuote.idv)}</strong>
                </div>

                <div className="review-row">
                  <span>Base premium</span>
                  <strong>{formatMoney(selectedQuote.base_premium)}</strong>
                </div>

                <div className="review-row">
                  <span>Tax</span>
                  <strong>{formatMoney(selectedQuote.tax_amount)}</strong>
                </div>

                <div className="review-row">
                  <span>Total premium</span>
                  <strong>
                    {formatMoney(selectedQuote.total_premium)}
                  </strong>
                </div>

                <button
                  className="confirm-button"
                  onClick={handleConfirmSelection}
                  disabled={savingSelection}
                >
                  {savingSelection
                    ? 'Saving...'
                    : 'Confirm and save selection'}
                </button>

                <button
                  className="cancel-button"
                  onClick={() => setSelectedQuote(null)}
                  disabled={savingSelection}
                >
                  Cancel
                </button>
              </section>
            )}

            {selectionError && (
              <div className="error-message">
                {selectionError}
              </div>
            )}

            {/* SUCCESS CONFIRMATION */}
            {selectionConfirmation && (
              <section className="selection-success">
                <div className="success-icon">✓</div>

                <h2>Plan selection saved!</h2>

                <p>
                  Your insurance plan selection has been successfully
                  recorded in AutoCover.
                </p>

                <div className="review-row">
                  <span>Selection ID</span>
                  <strong>{selectionConfirmation.id}</strong>
                </div>

                <div className="review-row">
                  <span>Registration</span>
                  <strong>
                    {selectionConfirmation.registration_number}
                  </strong>
                </div>

                <div className="review-row">
                  <span>Provider</span>
                  <strong>{selectionConfirmation.provider}</strong>
                </div>

                <div className="review-row">
                  <span>Plan</span>
                  <strong>{selectionConfirmation.plan_name}</strong>
                </div>

                <div className="review-row">
                  <span>Total premium</span>
                  <strong>
                    {formatMoney(selectionConfirmation.total_premium)}
                  </strong>
                </div>

                <div className="review-row">
                  <span>Status</span>
                  <strong>{selectionConfirmation.status}</strong>
                </div>
              </section>
            )}

            {/* PROVIDER DECLINES */}
            {quoteResult.declined.length > 0 && (
              <details className="provider-notes">
                <summary>Provider declines</summary>

                <pre>
                  {JSON.stringify(quoteResult.declined, null, 2)}
                </pre>
              </details>
            )}

            {/* PROVIDER ERRORS */}
            {quoteResult.provider_errors.length > 0 && (
              <details className="provider-notes">
                <summary>Provider processing issues</summary>

                <pre>
                  {JSON.stringify(quoteResult.provider_errors, null, 2)}
                </pre>
              </details>
            )}
          </section>
        )}
      </section>

      {/* FOOTER */}
      <footer>
        <span>AutoCover</span> · Compare smarter. Drive safer.
      </footer>
    </main>
  )
}

export default App
