import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { Link } from "react-router-dom";
import {
  Speedometer2,
  Table,
  BarChartLine,
  ArrowRight,
} from "react-bootstrap-icons";
import "./HomePage.css";

const ACTIONS = [
  {
    to: "/dashboard",
    icon: Speedometer2,
    title: "Dashboard",
    text: "Claim KPIs and live WebGIS map",
  },
  {
    to: "/claims-data",
    icon: Table,
    title: "Claims",
    text: "Search, filter, and update status",
  },
  {
    to: "/analytics",
    icon: BarChartLine,
    title: "Analytics",
    text: "Trends by status, type, and region",
  },
];

function HomePage() {
  return (
    <div className="homepage">
      <section className="home-hero rise-in">
        <Container fluid="xl">
          <p className="home-brand">FRA Atlas</p>
          <h1 className="home-headline">
            Digitize and monitor Forest Rights Act claims
          </h1>
          <p className="home-lead">
            WebGIS decision support for Madhya Pradesh, Tripura, Odisha, and
            Telangana — SIH12508, Ministry of Tribal Affairs.
          </p>
          <div className="welcome-actions">
            <Link to="/dashboard" className="btn btn-primary">
              Open Dashboard <ArrowRight className="ms-1" />
            </Link>
            <Link to="/claims-data" className="btn btn-outline-secondary">
              Browse Claims
            </Link>
          </div>
        </Container>
      </section>

      <Container fluid="xl" className="home-actions-wrap">
        <nav className="home-action-strip" aria-label="Quick links">
          <Row className="g-0">
            {ACTIONS.map(({ to, icon: Icon, title, text }, i) => (
              <Col md={4} key={to}>
                <Link
                  to={to}
                  className={`home-action-link rise-in rise-in-delay-${i + 1}`}
                >
                  <span className="home-action-icon">
                    <Icon size={20} />
                  </span>
                  <span className="home-action-copy">
                    <strong>{title}</strong>
                    <span>{text}</span>
                  </span>
                  <ArrowRight className="home-action-arrow" />
                </Link>
              </Col>
            ))}
          </Row>
        </nav>
      </Container>
    </div>
  );
}

export default HomePage;
