import { useMemo, useState } from "react";
import "./App.css";
import logo from "./assets/Logo.svg";
import tradeHero from "./assets/trade-hero.png";

const sampleQueries = [
  "Who buys electrical panels from India?",
  "Which countries supply circuit breakers to India?",
  "Compare Germany vs UAE as suppliers of electrical panels to India",
  "Which markets import switchgear from India?",
  "Which countries supply isolators to India?",
  "Which countries import capacitor banks from India?",
];

const emptyOpportunityRows = Array.from({ length: 5 }, (_, index) => ({
  rank: index + 1,
}));

function localDateString(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function rollingRange(years) {
  const end = new Date();
  const start = new Date(end);
  start.setFullYear(start.getFullYear() - years);

  return {
    start: localDateString(start),
    end: localDateString(end),
  };
}

function formatMoney(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(Number(value));
}

function formatMoneyLong(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(1)}%`;
}

function average(values) {
  const valid = values.map(Number).filter((value) => !Number.isNaN(value));

  if (!valid.length) return null;

  return valid.reduce((total, value) => total + value, 0) / valid.length;
}
function MarketShareDonut({ opportunities }) {
  const palette = ["#ff5b57", "#278cff", "#26c8a5", "#8a62db", "#f5aa38"];
  const topFive = opportunities.slice(0, 5);

  const total = topFive.reduce((sum, item) => sum + Number(item.market_share_percent || 0), 0);

  const radius = 44;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="donut-wrap">
      <svg viewBox="0 0 120 120" aria-label="Market share donut chart">
        <circle className="donut-track" cx="60" cy="60" r={radius} />

        {topFive.map((item, index) => {
          const share = Math.max(0, Number(item.market_share_percent || 0));

          const previousShare = topFive
            .slice(0, index)
            .reduce(
              (sum, previousItem) =>
                sum + Math.max(0, Number(previousItem.market_share_percent || 0)),
              0,
            );

          const length = (share / 100) * circumference;
          const offset = -(previousShare / 100) * circumference;

          return (
            <circle
              key={item.country_id ?? index}
              className="donut-segment"
              cx="60"
              cy="60"
              r={radius}
              stroke={palette[index]}
              strokeDasharray={`${length} ${circumference}`}
              strokeDashoffset={offset}
            />
          );
        })}
      </svg>

      <div className="donut-center">
        <strong>{opportunities.length ? formatPercent(total) : "—"}</strong>
        <span>Top 5 Countries</span>
      </div>
    </div>
  );
}

function TrendChart({ history }) {
  const hasHistory = Array.isArray(history) && history.length > 1;

  const fallback = [
    { year: "2020", trade_value_usd: 8 },
    { year: "2021", trade_value_usd: 11 },
    { year: "2022", trade_value_usd: 14 },
    { year: "2023", trade_value_usd: 15 },
    { year: "2024", trade_value_usd: 18 },
    { year: "2025", trade_value_usd: 20 },
    { year: "2026", trade_value_usd: 23 },
  ];

  const points = hasHistory ? history : fallback;
  const values = points.map((item) => Number(item.trade_value_usd || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = Math.max(max - min, 1);

  const polyline = points
    .map((item, index) => {
      const x = (index / (points.length - 1)) * 100;
      const y = 82 - ((Number(item.trade_value_usd || 0) - min) / spread) * 62;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className={`trend-chart ${hasHistory ? "" : "trend-placeholder"}`}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none">
        <line x1="0" y1="20" x2="100" y2="20" />
        <line x1="0" y1="40" x2="100" y2="40" />
        <line x1="0" y1="60" x2="100" y2="60" />
        <line x1="0" y1="80" x2="100" y2="80" />
        <polyline points={polyline} />
        {points.map((item, index) => {
          const x = (index / (points.length - 1)) * 100;
          const y = 82 - ((Number(item.trade_value_usd || 0) - min) / spread) * 62;
          return <circle key={`${item.year}-${index}`} cx={x} cy={y} r="1.6" />;
        })}
      </svg>

      <div className="trend-years">
        {points.map((item) => (
          <span key={item.year}>{item.year}</span>
        ))}
      </div>

      {!hasHistory && <span className="placeholder-note">Awaiting yearly history from API</span>}
    </div>
  );
}

function App() {
  const defaultRange = useMemo(() => rollingRange(3), []);
  const today = useMemo(() => localDateString(new Date()), []);

  const [query, setQuery] = useState("");
  const [periodStart, setPeriodStart] = useState(defaultRange.start);
  const [periodEnd, setPeriodEnd] = useState(defaultRange.end);
  const [activePreset, setActivePreset] = useState(3);
  const [validationMessage, setValidationMessage] = useState("");
  const [apiError, setApiError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);

  function applyPreset(years) {
    const range = rollingRange(years);
    setPeriodStart(range.start);
    setPeriodEnd(range.end);
    setActivePreset(years);
    setValidationMessage("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!query.trim()) {
      setValidationMessage("Enter a trade opportunity question.");
      return;
    }

    if (!periodStart || !periodEnd || periodStart >= periodEnd) {
      setValidationMessage("Choose a valid analysis period.");
      return;
    }

    setValidationMessage("");
    setApiError("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/v1/trade/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query.trim(),
          period_start: periodStart,
          period_end: periodEnd,
        }),
      });

      const body = await response.json().catch(() => null);

      if (!response.ok) {
        const detail =
          body?.detail || body?.message || `Request failed with HTTP ${response.status}`;

        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
      }

      setApiResult(body);
    } catch (error) {
      setApiResult(null);
      setApiError(
        error instanceof Error ? error.message : "Unable to contact the trade analysis backend.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  const opportunities = Array.isArray(apiResult?.opportunities) ? apiResult.opportunities : [];

  const history = Array.isArray(apiResult?.history) ? apiResult.history : [];

  const totalTradeValue = opportunities.reduce(
    (total, item) => total + Number(item.trade_value_usd || 0),
    0,
  );

  const topOpportunity = opportunities[0] || null;
  const averageGrowth = average(
    opportunities.map((item) => item.yoy_growth_percent).filter((value) => value != null),
  );

  const topFiveShare = opportunities
    .slice(0, 5)
    .reduce((total, item) => total + Number(item.market_share_percent || 0), 0);

  const maxTradeValue = opportunities.length
    ? Math.max(...opportunities.map((item) => Number(item.trade_value_usd || 0)))
    : 0;

  const detailedRows = opportunities.length
    ? opportunities.slice(0, 7)
    : Array.from({ length: 7 }, (_, index) => ({ rank: index + 1 }));

  const insightRows = apiResult?.insights?.length
    ? apiResult.insights.slice(0, 4)
    : Array.from({ length: 4 }, (_, index) => ({
        title: index === 0 ? "Key insights will appear here" : "",
        description: "",
      }));

  const opportunityRows = opportunities.length ? opportunities.slice(0, 5) : emptyOpportunityRows;

  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="container header-inner">
          <a
            className="brand"
            href="https://www.hanjes-technologies.com"
            aria-label="Hanjes Technologies"
          >
            <img src={logo} alt="Hanjes Technologies" />
          </a>

          <a className="back-link" href="https://www.hanjes-technologies.com">
            ← Back to Hanjes Technologies
          </a>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-art" style={{ backgroundImage: `url(${tradeHero})` }} />
          <div className="hero-overlay" />

          <div className="container hero-grid">
            <div className="hero-copy">
              <p className="eyebrow">Global Trade Insights · AI-Powered · Real Opportunities</p>

              <h1>
                AI-Powered Trade
                <span>Opportunity Explorer</span>
              </h1>

              <p>
                Turn global trade data into real business opportunities. Ask questions, discover
                markets, find suppliers or buyers, and get AI-powered insights backed by trusted
                trade data.
              </p>
            </div>

            <form className="search-area" onSubmit={handleSubmit}>
              <div className="search-box">
                <span className="search-spark">✦</span>

                <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Ask anything about global trade opportunities..."
                />

                <button type="submit" disabled={isLoading}>
                  {isLoading ? "Analyzing…" : "⌕  Search"}
                </button>
              </div>

              <div className="date-toolbar">
                <div className="preset-buttons">
                  {[1, 3, 5].map((years) => (
                    <button
                      type="button"
                      key={years}
                      className={activePreset === years ? "active" : ""}
                      onClick={() => applyPreset(years)}
                    >
                      {years}Y
                    </button>
                  ))}
                </div>

                <label>
                  <span>From</span>
                  <input
                    type="date"
                    value={periodStart}
                    max={periodEnd || today}
                    onChange={(event) => {
                      setPeriodStart(event.target.value);
                      setActivePreset(null);
                    }}
                  />
                </label>

                <span className="date-arrow">→</span>

                <label>
                  <span>To</span>
                  <input
                    type="date"
                    value={periodEnd}
                    min={periodStart || undefined}
                    max={today}
                    onChange={(event) => {
                      setPeriodEnd(event.target.value);
                      setActivePreset(null);
                    }}
                  />
                </label>
              </div>

              <span className="example-label">Try these example queries:</span>

              <div className="example-queries">
                {sampleQueries.map((sample) => (
                  <button type="button" key={sample} onClick={() => setQuery(sample)}>
                    {sample}
                  </button>
                ))}
              </div>

              {(validationMessage || apiError) && (
                <p className="query-error">{validationMessage || apiError}</p>
              )}
            </form>
          </div>
        </section>

        <section className="dashboard">
          <div className="container">
            <div className="summary-grid">
              <article className="summary-card">
                <span className="summary-icon">▥</span>
                <div>
                  <p>Top Supplier</p>
                  <strong>{topOpportunity?.country_name || "—"}</strong>
                  <small>
                    {topOpportunity
                      ? `${formatPercent(topOpportunity.market_share_percent)} market share`
                      : "Waiting for analysis"}
                  </small>
                </div>
              </article>

              <article className="summary-card">
                <span className="summary-icon">◎</span>
                <div>
                  <p>Total Trade Value</p>
                  <strong>{opportunities.length ? formatMoney(totalTradeValue) : "—"}</strong>
                  <small>
                    {opportunities.length
                      ? `${opportunities.length} markets`
                      : "Waiting for analysis"}
                  </small>
                </div>
              </article>

              <article className="summary-card">
                <span className="summary-icon">◔</span>
                <div>
                  <p>Market Share (Top 5)</p>
                  <strong>{opportunities.length ? formatPercent(topFiveShare) : "—"}</strong>
                  <small>of analyzed trade</small>
                </div>
              </article>

              <article className="summary-card">
                <span className="summary-icon">▥</span>
                <div>
                  <p>YoY Growth</p>
                  <strong>{averageGrowth == null ? "—" : formatPercent(averageGrowth)}</strong>
                  <small>average across markets</small>
                </div>
              </article>

              <article className="summary-card">
                <span className="summary-icon">▤</span>
                <div>
                  <p>Data Source</p>
                  <strong className="summary-source">UN Comtrade</strong>
                  <small>Verified global trade data</small>
                </div>
              </article>

              <article className="summary-card">
                <span className="summary-icon">▣</span>
                <div>
                  <p>Latest Period</p>
                  <strong>{apiResult?.period_end?.slice(0, 4) || "—"}</strong>
                  <small>{apiResult ? "Selected analysis period" : "Waiting for analysis"}</small>
                </div>
              </article>
            </div>

            <div className="analysis-grid">
              <article className="panel supplier-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">⌂</span>
                    <h2>Top Supplier Countries</h2>
                  </div>
                  <span className="panel-select">By Trade Value⌄</span>
                </div>

                <div className="bar-chart">
                  {(opportunities.length
                    ? opportunities.slice(0, 5)
                    : Array.from({ length: 5 }, (_, index) => ({ rank: index + 1 }))
                  ).map((item, index) => {
                    const value = Number(item.trade_value_usd || 0);
                    const height = opportunities.length
                      ? Math.max(18, (value / maxTradeValue) * 100)
                      : [72, 52, 42, 34, 28][index];

                    return (
                      <div className="bar-column" key={item.country_id ?? index}>
                        <span className="bar-value">
                          {item.trade_value_usd ? formatMoney(item.trade_value_usd) : "—"}
                        </span>
                        <div className="bar-shell">
                          <div
                            className={`bar bar-${index + 1} ${
                              opportunities.length ? "" : "placeholder-bar"
                            }`}
                            style={{ height: `${height}%` }}
                          />
                        </div>
                        <strong>{item.country_name || `Market ${index + 1}`}</strong>
                      </div>
                    );
                  })}
                </div>
              </article>

              <article className="panel trend-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">⌁</span>
                    <h2>Trade Value Trend & Projection</h2>
                  </div>
                  <span className="panel-select">Trade Value (USD)⌄</span>
                </div>

                <TrendChart history={history} />
              </article>

              <article className="panel share-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">◉</span>
                    <h2>Market Share (Top 5 Countries)</h2>
                  </div>
                </div>

                <div className="share-layout">
                  <MarketShareDonut opportunities={opportunities} />

                  <div className="share-legend">
                    {(opportunities.length
                      ? opportunities.slice(0, 5)
                      : Array.from({ length: 5 }, (_, index) => ({
                          country_name: `Market ${index + 1}`,
                        }))
                    ).map((item, index) => (
                      <div key={item.country_id ?? index}>
                        <i className={`legend-dot dot-${index + 1}`} />
                        <span>{item.country_name}</span>
                        <strong>
                          {item.market_share_percent != null
                            ? formatPercent(item.market_share_percent)
                            : "—"}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              </article>

              <article className="panel insights-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">♢</span>
                    <h2>Key Insights & Recommendations</h2>
                  </div>
                </div>

                <div className="insight-list">
                  {insightRows.map((insight, index) => (
                    <div className="insight-row" key={`${insight.title}-${index}`}>
                      <span className="insight-bulb">◉</span>
                      <div>
                        <strong>{insight.title || "—"}</strong>
                        <p>
                          {insight.description ||
                            (apiResult
                              ? "No additional recommendation returned."
                              : "Live AI-generated insight will appear here.")}
                        </p>
                      </div>
                      <span className="insight-arrow">›</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel opportunity-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">◎</span>
                    <h2>Top Opportunities</h2>
                  </div>
                </div>

                <div className="opportunity-list">
                  {opportunityRows.map((item, index) => (
                    <div className="opportunity-row" key={item.country_id ?? index}>
                      <span className="rank-circle">{item.rank || index + 1}</span>
                      <div>
                        <strong>{item.country_name || "Awaiting market data"}</strong>
                        <span>
                          {item.trade_value_usd
                            ? `${formatMoney(item.trade_value_usd)} trade value`
                            : "Opportunity details will appear here"}
                        </span>
                      </div>
                      <em className={item.opportunity_score >= 70 ? "high" : ""}>
                        {item.opportunity_score != null
                          ? Number(item.opportunity_score).toFixed(0)
                          : "—"}
                      </em>
                      <span>›</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="panel comparison-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">⚖</span>
                    <h2>
                      Country Comparison {apiResult?.hs_code ? `(HS ${apiResult.hs_code})` : ""}
                    </h2>
                  </div>
                </div>

                <table>
                  <thead>
                    <tr>
                      <th>Country</th>
                      <th>Trade Value</th>
                      <th>YoY Growth</th>
                      <th>Market Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(opportunities.length
                      ? opportunities.slice(0, 5)
                      : Array.from({ length: 5 }, (_, index) => ({ rank: index + 1 }))
                    ).map((item, index) => (
                      <tr key={item.country_id ?? index}>
                        <td>{item.country_name || `Market ${index + 1}`}</td>
                        <td>{formatMoney(item.trade_value_usd)}</td>
                        <td>{formatPercent(item.yoy_growth_percent)}</td>
                        <td>{formatPercent(item.market_share_percent)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </article>

              <article className="panel detail-panel">
                <div className="panel-title">
                  <div>
                    <span className="panel-icon">▤</span>
                    <h2>Detailed Trade Data</h2>
                  </div>
                  <span className="panel-select">Export CSV</span>
                </div>

                <div className="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Country</th>
                        <th>Trade Value (USD)</th>
                        <th>YoY Growth</th>
                        <th>Market Share</th>
                        <th>Opportunity Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {detailedRows.map((item, index) => (
                        <tr key={item.country_id ?? index}>
                          <td>{item.rank || index + 1}</td>
                          <td>{item.country_name || "—"}</td>
                          <td>{formatMoneyLong(item.trade_value_usd)}</td>
                          <td>{formatPercent(item.yoy_growth_percent)}</td>
                          <td>{formatPercent(item.market_share_percent)}</td>
                          <td>
                            <span className="score-pill">
                              {item.opportunity_score != null
                                ? Number(item.opportunity_score).toFixed(0)
                                : "—"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </article>
            </div>

            <section className="architecture-panel">
              <div className="architecture-title">
                <span className="architecture-gear">⚙</span>
                <div>
                  <h2>How this demo works</h2>
                  <p>From your question to actionable trade insights</p>
                </div>
              </div>

              <div className="architecture-flow">
                <div className="architecture-card blue">
                  <span className="architecture-icon">●</span>
                  <div>
                    <strong>User Query</strong>
                    <p>Ask a question about trade opportunities</p>
                  </div>
                </div>

                <span className="flow-arrow">→</span>

                <div className="architecture-card cyan">
                  <span className="architecture-icon">◎</span>
                  <div>
                    <strong>React UI</strong>
                    <p>Modern web interface for seamless experience</p>
                  </div>
                </div>

                <span className="flow-arrow">→</span>

                <div className="architecture-card green">
                  <span className="architecture-icon">ϟ</span>
                  <div>
                    <strong>FastAPI Backend</strong>
                    <p>Processes requests and orchestrates workflow</p>
                  </div>
                </div>

                <span className="flow-arrow purple-arrow">→</span>

                <div className="architecture-card purple">
                  <span className="architecture-icon">◉</span>
                  <div>
                    <strong>OpenAI</strong>
                    <p>Query interpretation & trade analytics</p>
                  </div>
                </div>

                <span className="flow-arrow">→</span>

                <div className="architecture-card database">
                  <span className="architecture-icon">♙</span>
                  <div>
                    <strong>PostgreSQL Database</strong>
                    <p>Stores trade data and analytics results</p>
                  </div>
                </div>

                <div className="cron-flow">
                  <span>
                    Scheduled Cron
                    <br />
                    (Incremental Ingestion)
                  </span>
                  <i>←──────────────</i>
                </div>

                <div className="architecture-card api">
                  <span className="architecture-icon">◉</span>
                  <div>
                    <strong>UN Comtrade API</strong>
                    <p>Global trade data source</p>
                  </div>
                </div>
              </div>
            </section>

            {apiResult && (
              <details className="api-debug">
                <summary>View API response</summary>
                <pre>{JSON.stringify(apiResult, null, 2)}</pre>
              </details>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
