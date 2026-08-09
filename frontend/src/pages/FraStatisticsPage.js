import React, { useMemo, useState } from "react";
import { Container } from "react-bootstrap";
import statisticsData from "../data/fraClaimsStatistics.json";
import FraStatisticsPanel, {
  PeriodTabs,
} from "../components/FraStatisticsPanel";
import "./FraStatisticsPage.css";

function FraStatisticsPage() {
  const periods = statisticsData.periods || [];
  const [activeId, setActiveId] = useState(periods[0]?.id || "");

  const activePeriod = useMemo(
    () => periods.find((p) => p.id === activeId) || periods[0],
    [periods, activeId]
  );

  return (
    <div className="fra-statistics-page">
      <Container fluid>
        <div className="page-header">
          <h1 className="page-title">FRA Claims Statistics</h1>
          <p className="page-subtitle">
            Official state-wise MoTA FRA claim and title statistics from{" "}
            {statisticsData.source}.
          </p>
          <div className="page-meta">
            <span className="meta-chip">
              {activePeriod?.label || "Period"}
            </span>
            {activePeriod?.asOf && (
              <span className="meta-chip">As of {activePeriod.asOf}</span>
            )}
            <span className="meta-chip">
              {activePeriod?.rows?.length || 0} states
            </span>
          </div>
        </div>

        <PeriodTabs
          periods={periods}
          activeId={activePeriod?.id}
          onChange={setActiveId}
        />

        {activePeriod ? (
          <FraStatisticsPanel period={activePeriod} />
        ) : (
          <p className="text-muted">No statistics data available.</p>
        )}
      </Container>
    </div>
  );
}

export default FraStatisticsPage;
