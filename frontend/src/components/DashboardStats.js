import React from "react";
import { Row, Col } from "react-bootstrap";
import { BarChart, CheckCircle, ClockHistory } from "react-bootstrap-icons";
import "./DashboardStats.css";

function StatCard({ icon, value, label, tone }) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-copy">
        <p className="stat-label">{label}</p>
        <p className="stat-value">{value}</p>
      </div>
    </div>
  );
}

function DashboardStats({ stats }) {
  return (
    <Row className="mb-4 g-3">
      <Col md={4}>
        <StatCard
          icon={<BarChart size={22} />}
          value={stats.totalClaims}
          label="Total Claims"
          tone="forest"
        />
      </Col>
      <Col md={4}>
        <StatCard
          icon={<ClockHistory size={22} />}
          value={stats.claimsInReview}
          label="Pending Review"
          tone="amber"
        />
      </Col>
      <Col md={4}>
        <StatCard
          icon={<CheckCircle size={22} />}
          value={stats.claimsApproved}
          label="Approved"
          tone="leaf"
        />
      </Col>
    </Row>
  );
}

export default DashboardStats;
