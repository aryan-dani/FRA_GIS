import React from "react";
import { Navbar, Nav, Container } from "react-bootstrap";
import { NavLink } from "react-router-dom";
import {
  Globe,
  House,
  InfoCircle,
  Speedometer2,
  Table,
  BarChartLine,
  ClipboardData,
  FileEarmarkRichtext,
} from "react-bootstrap-icons";
import "./Navbar.css";

function AppNavbar() {
  return (
    <Navbar
      variant="dark"
      expand="lg"
      className="app-navbar"
      fixed="top"
      collapseOnSelect
    >
      <Container fluid="xl">
        <Navbar.Brand as={NavLink} to="/" className="navbar-brand-custom">
          <Globe className="brand-icon" size={18} />
          <span>FRA Atlas</span>
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link as={NavLink} to="/" end>
              <House size={14} /> Home
            </Nav.Link>
            <Nav.Link as={NavLink} to="/dashboard">
              <Speedometer2 size={14} /> Dashboard
            </Nav.Link>
            <Nav.Link as={NavLink} to="/claims-data">
              <Table size={14} /> Claims
            </Nav.Link>
            <Nav.Link as={NavLink} to="/analytics">
              <BarChartLine size={14} /> Analytics
            </Nav.Link>
            <Nav.Link as={NavLink} to="/fra-statistics">
              <ClipboardData size={14} /> FRA Stats
            </Nav.Link>
            <Nav.Link as={NavLink} to="/about">
              <InfoCircle size={14} /> About
            </Nav.Link>
            <Nav.Link as={NavLink} to="/e-poster">
              <FileEarmarkRichtext size={14} /> E-Poster
            </Nav.Link>
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default AppNavbar;
