import React from "react";
import { Container, Row, Col, Card } from "react-bootstrap";
import { Link } from "react-router-dom";
import {
  Speedometer2,
  Table,
  BarChartLine,
  ArrowRight,
} from "react-bootstrap-icons";
import "./HomePage.css";

function HomePage() {
  return (
    <div className="homepage">
      <Container className="text-center welcome-section rise-in">
        <p className="welcome-kicker">SIH12508 · Ministry of Tribal Affairs</p>
        <h1 className="display-5">FRA-GIS Platform</h1>
        <p className="lead text-muted">
          Digitize, map, and monitor Forest Rights Act claims with WebGIS and
          analytics — focused on Madhya Pradesh, Tripura, Odisha, and Telangana.
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

      <Container>
        <Row className="justify-content-center">
          <Col md={10} lg={9}>
            <Row>
              <Col md={4} className="mb-4">
                <Card as={Link} to="/dashboard" className="action-card rise-in">
                  <Card.Body>
                    <div className="action-icon">
                      <Speedometer2 size={28} />
                    </div>
                    <Card.Title>Dashboard</Card.Title>
                    <Card.Text>
                      View claim stats and the live WebGIS map.
                    </Card.Text>
                    <div className="go-arrow">
                      <ArrowRight />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4} className="mb-4">
                <Card
                  as={Link}
                  to="/claims-data"
                  className="action-card rise-in rise-in-delay-1"
                >
                  <Card.Body>
                    <div className="action-icon">
                      <Table size={28} />
                    </div>
                    <Card.Title>Claims Data</Card.Title>
                    <Card.Text>
                      Search, filter, and update claim status.
                    </Card.Text>
                    <div className="go-arrow">
                      <ArrowRight />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={4} className="mb-4">
                <Card
                  as={Link}
                  to="/analytics"
                  className="action-card rise-in rise-in-delay-2"
                >
                  <Card.Body>
                    <div className="action-icon">
                      <BarChartLine size={28} />
                    </div>
                    <Card.Title>Analytics</Card.Title>
                    <Card.Text>
                      Explore trends by status, type, and region.
                    </Card.Text>
                    <div className="go-arrow">
                      <ArrowRight />
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default HomePage;
