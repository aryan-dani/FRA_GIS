import React, { useMemo, useState } from "react";
import { Button, ButtonGroup, Col, Row, Table } from "react-bootstrap";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import "./FraStatisticsPanel.css";

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const FOCUS_STATES = new Set([
  "Madhya Pradesh",
  "Tripura",
  "Odisha",
  "Telangana",
]);

const formatNumber = (value) => {
  if (value == null || Number.isNaN(value)) return "—";
  return Number(value).toLocaleString("en-IN");
};

const sumField = (rows, field) =>
  rows.reduce((acc, row) => {
    const value = row[field];
    return typeof value === "number" ? acc + value : acc;
  }, 0);

function FraStatisticsPanel({ period }) {
  const [sortKey, setSortKey] = useState("claimsReceivedTotal");
  const [sortDir, setSortDir] = useState("desc");

  const rows = period?.rows || [];

  const kpis = useMemo(() => {
    const claims = sumField(rows, "claimsReceivedTotal");
    const titles = sumField(rows, "titlesDistributedTotal");
    const rate = claims > 0 ? (titles / claims) * 100 : null;
    return {
      claims,
      titles,
      states: rows.length,
      rate,
    };
  }, [rows]);

  const sortedRows = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "string" || typeof bv === "string") {
        const as = String(av || "");
        const bs = String(bv || "");
        return sortDir === "asc" ? as.localeCompare(bs) : bs.localeCompare(as);
      }
      const an = typeof av === "number" ? av : -Infinity;
      const bn = typeof bv === "number" ? bv : -Infinity;
      return sortDir === "asc" ? an - bn : bn - an;
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  const chartData = useMemo(() => {
    const top = [...rows]
      .sort(
        (a, b) =>
          (b.claimsReceivedTotal || 0) - (a.claimsReceivedTotal || 0)
      )
      .slice(0, 10);
    return {
      labels: top.map((r) => r.state),
      datasets: [
        {
          label: "Claims received",
          data: top.map((r) => r.claimsReceivedTotal || 0),
          backgroundColor: "rgba(0, 77, 64, 0.75)",
          borderRadius: 6,
        },
        {
          label: "Titles distributed",
          data: top.map((r) => r.titlesDistributedTotal || 0),
          backgroundColor: "rgba(46, 125, 50, 0.65)",
          borderRadius: 6,
        },
      ],
    };
  }, [rows]);

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: "top" },
      title: { display: false },
    },
    scales: {
      x: {
        ticks: { maxRotation: 45, minRotation: 0 },
      },
      y: {
        beginAtZero: true,
      },
    },
  };

  const hasRejected = rows.some((r) => r.rejectedTotal != null);
  const hasPending = rows.some(
    (r) => r.pendingIndividual != null || r.pendingCommunity != null
  );
  const hasForestLand = rows.some((r) => r.forestLandTotal != null);

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "state" ? "asc" : "desc");
    }
  };

  const sortMark = (key) =>
    sortKey === key ? (sortDir === "asc" ? " ↑" : " ↓") : "";

  return (
    <div className="fra-stats-panel">
      <Row className="g-3 mb-3">
        <Col md={3} sm={6}>
          <div className="fra-kpi">
            <span className="fra-kpi-label">Claims received</span>
            <strong className="fra-kpi-value">{formatNumber(kpis.claims)}</strong>
          </div>
        </Col>
        <Col md={3} sm={6}>
          <div className="fra-kpi">
            <span className="fra-kpi-label">Titles distributed</span>
            <strong className="fra-kpi-value">{formatNumber(kpis.titles)}</strong>
          </div>
        </Col>
        <Col md={3} sm={6}>
          <div className="fra-kpi">
            <span className="fra-kpi-label">States / UTs</span>
            <strong className="fra-kpi-value">{formatNumber(kpis.states)}</strong>
          </div>
        </Col>
        <Col md={3} sm={6}>
          <div className="fra-kpi">
            <span className="fra-kpi-label">Title distribution rate</span>
            <strong className="fra-kpi-value">
              {kpis.rate == null ? "—" : `${kpis.rate.toFixed(1)}%`}
            </strong>
          </div>
        </Col>
      </Row>

      <div className="fra-chart-card mb-3">
        <div className="fra-chart-header">
          <h2>Top states by claims received</h2>
          <p>Compared with titles distributed for this period.</p>
        </div>
        <div className="fra-chart-body">
          <Bar data={chartData} options={chartOptions} />
        </div>
      </div>

      <div className="fra-table-card">
        <div className="fra-table-header">
          <h2>State-wise statistics</h2>
          <p>
            SIH focus states (Madhya Pradesh, Tripura, Odisha, Telangana) are
            highlighted.
          </p>
        </div>
        <div className="fra-table-wrap">
          <Table hover responsive className="fra-stats-table mb-0">
            <thead>
              <tr>
                <th>
                  <Button
                    variant="link"
                    className="sort-btn"
                    onClick={() => toggleSort("state")}
                  >
                    State{sortMark("state")}
                  </Button>
                </th>
                <th>
                  <Button
                    variant="link"
                    className="sort-btn"
                    onClick={() => toggleSort("claimsReceivedTotal")}
                  >
                    Claims received{sortMark("claimsReceivedTotal")}
                  </Button>
                </th>
                <th>
                  <Button
                    variant="link"
                    className="sort-btn"
                    onClick={() => toggleSort("titlesDistributedTotal")}
                  >
                    Titles distributed{sortMark("titlesDistributedTotal")}
                  </Button>
                </th>
                {hasPending && <th>Pending (I / C)</th>}
                {hasRejected && <th>Rejected</th>}
                {hasForestLand && <th>Forest land (acres)</th>}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr
                  key={row.state}
                  className={FOCUS_STATES.has(row.state) ? "focus-state" : ""}
                >
                  <td>
                    <span className="state-name">{row.state}</span>
                    {FOCUS_STATES.has(row.state) && (
                      <span className="focus-badge">Focus</span>
                    )}
                  </td>
                  <td>
                    {formatNumber(row.claimsReceivedTotal)}
                    <span className="sub-metric">
                      I {formatNumber(row.claimsReceivedIndividual)} · C{" "}
                      {formatNumber(row.claimsReceivedCommunity)}
                    </span>
                  </td>
                  <td>
                    {formatNumber(row.titlesDistributedTotal)}
                    <span className="sub-metric">
                      I {formatNumber(row.titlesDistributedIndividual)} · C{" "}
                      {formatNumber(row.titlesDistributedCommunity)}
                    </span>
                  </td>
                  {hasPending && (
                    <td>
                      {formatNumber(row.pendingIndividual)} /{" "}
                      {formatNumber(row.pendingCommunity)}
                    </td>
                  )}
                  {hasRejected && (
                    <td>{formatNumber(row.rejectedTotal)}</td>
                  )}
                  {hasForestLand && (
                    <td>{formatNumber(row.forestLandTotal)}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      </div>
    </div>
  );
}

export function PeriodTabs({ periods, activeId, onChange }) {
  return (
    <ButtonGroup className="fra-period-tabs flex-wrap mb-3">
      {periods.map((period) => (
        <Button
          key={period.id}
          variant={period.id === activeId ? "primary" : "outline-secondary"}
          onClick={() => onChange(period.id)}
        >
          {period.label}
        </Button>
      ))}
    </ButtonGroup>
  );
}

export default FraStatisticsPanel;
