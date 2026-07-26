import React from "react";
import { Navbar, Nav, Container } from "react-bootstrap";
import { NavLink } from "react-router-dom";
import {
  House,
  InfoCircle,
  Speedometer2,
  Table,
  BarChartLine,
} from "react-bootstrap-icons";
import "./Navbar.css";

function AppNavbar() {
  return (
    <Navbar variant="light" expand="lg" className="floating-navbar" fixed="top">
      <Container>
        <Navbar.Brand as={NavLink} to="/" className="navbar-brand-custom">
          <span className="brand-mark" aria-hidden="true" />
          <span className="brand-text">
            <span className="brand-name">FRA Atlas</span>
            <span className="brand-sub">WebGIS DSS</span>
          </span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link as={NavLink} to="/" end>
              <House className="me-1" /> Home
            </Nav.Link>
            <Nav.Link as={NavLink} to="/dashboard">
              <Speedometer2 className="me-1" /> Dashboard
            </Nav.Link>
            <Nav.Link as={NavLink} to="/claims-data">
              <Table className="me-1" /> Claims
            </Nav.Link>
            <Nav.Link as={NavLink} to="/analytics">
              <BarChartLine className="me-1" /> Analytics
            </Nav.Link>
            <Nav.Link as={NavLink} to="/about">
              <InfoCircle className="me-1" /> About
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default AppNavbar;
