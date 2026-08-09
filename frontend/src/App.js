import React from "react";
import { Routes, Route } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import "react-toastify/dist/ReactToastify.css";
import "./App.css";

import AppNavbar from "./components/Navbar";
import Footer from "./components/Footer";
import HomePage from "./pages/HomePage";
import DashboardPage from "./pages/DashboardPage";
import AboutPage from "./pages/AboutPage";
import ClaimsDataPage from "./pages/ClaimsDataPage";
import ClaimDetailPage from "./pages/ClaimDetailPage";
import AddClaimPage from "./pages/AddClaimPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import FraStatisticsPage from "./pages/FraStatisticsPage";
import { ToastContainer } from "react-toastify";

function App() {
  return (
    <div className="App">
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
      <AppNavbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/claims-data" element={<ClaimsDataPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/fra-statistics" element={<FraStatisticsPage />} />
          <Route path="/claim/:id" element={<ClaimDetailPage />} />
          <Route path="/add-claim" element={<AddClaimPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

export default App;
