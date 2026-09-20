import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  GoogleMap,
  useJsApiLoader,
  useGoogleMap,
  InfoWindow,
  Polygon,
} from "@react-google-maps/api";
import "./WebGISMap.css";

const INDIA_CENTER = { lat: 20.5937, lng: 78.9629 };
// "marker" library required for AdvancedMarkerElement
const MAPS_LIBRARIES = ["marker"];
// Cloud map style ID — DEMO_MAP_ID is fine for local/dev; create your own in GCP for production
const MAP_ID =
  process.env.REACT_APP_GOOGLE_MAPS_MAP_ID || "DEMO_MAP_ID";

const CLAIM_TYPE_COLORS = {
  IFR: "#0d6efd",
  CR: "#198754",
  CFR: "#ffc107",
  default: "#6c757d",
};

const STATUS_COLORS = {
  Approved: "#166534",
  Pending: "#b45309",
  Rejected: "#b91c1c",
  default: "#6c757d",
};

const mapContainerStyle = {
  width: "100%",
  height: "100%",
};

const defaultOptions = {
  disableDefaultUI: false,
  zoomControl: true,
  mapTypeControl: true,
  streetViewControl: false,
  fullscreenControl: true,
  mapTypeId: "hybrid",
  mapId: MAP_ID,
};

function getClaimColor(claim, colorBy) {
  if (colorBy === "status") {
    return STATUS_COLORS[claim.status] || STATUS_COLORS.default;
  }
  return CLAIM_TYPE_COLORS[claim.claim_type] || CLAIM_TYPE_COLORS.default;
}

function toLatLng(claim) {
  const lat = Number(claim.latitude);
  const lng = Number(claim.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { lat, lng };
}

function hashSeed(str) {
  let h = 2166136261;
  const s = String(str || "");
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed) {
  let a = seed;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Stable irregular parcel polygon around a claim point.
 * Vertices stay in ascending angle order (varying radius only) so Google Maps
 * draws one solid polygon — not self-overlapping triangles.
 */
function buildFreeformParcel(center, claim) {
  const id = claim.id || claim.claim_id || `${center.lat},${center.lng}`;
  const rand = mulberry32(hashSeed(id));
  const land = Number(claim.land_area_ha);
  const areaHa = Number.isFinite(land) && land > 0 ? land : 1.5;
  const baseRadius = 0.0032 + Math.min(Math.sqrt(areaHa), 5) * 0.0022;
  const vertexCount = 8 + Math.floor(rand() * 3); // 8–10 edges
  const cosLat = Math.max(Math.cos((center.lat * Math.PI) / 180), 0.2);
  const startAngle = rand() * Math.PI * 2;
  const path = [];

  for (let i = 0; i < vertexCount; i += 1) {
    const angle = startAngle + (i / vertexCount) * Math.PI * 2;
    const radius = baseRadius * (0.62 + rand() * 0.55);
    path.push({
      lat: center.lat + Math.sin(angle) * radius,
      lng: center.lng + (Math.cos(angle) * radius) / cosLat,
    });
  }
  path.push({ ...path[0] });
  return path;
}

function MapsFallback({ height, children }) {
  return (
    <div className="google-map-fallback" style={{ height }}>
      {typeof children === "string" ? <p>{children}</p> : children}
    </div>
  );
}

/**
 * google.maps.marker.AdvancedMarkerElement (replaces deprecated Marker).
 */
function AdvancedClaimMarker({ position, color, zIndex = 2, onClick, title }) {
  const map = useGoogleMap();
  const markerRef = useRef(null);
  const onClickRef = useRef(onClick);
  onClickRef.current = onClick;

  useEffect(() => {
    if (!map || !window.google?.maps?.marker?.AdvancedMarkerElement) {
      return undefined;
    }

    const { AdvancedMarkerElement, PinElement } = window.google.maps.marker;
    const pin = new PinElement({
      background: color,
      borderColor: "#ffffff",
      glyphColor: "#ffffff",
      scale: 1.05,
    });

    const marker = new AdvancedMarkerElement({
      map,
      position,
      content: pin.element,
      title: title || "",
      zIndex,
      gmpClickable: true,
    });

    const handleClick = () => {
      if (onClickRef.current) onClickRef.current();
    };
    // Preferred Maps event API for AdvancedMarkerElement
    const clickListener = marker.addListener("click", handleClick);
    markerRef.current = marker;

    return () => {
      if (clickListener) clickListener.remove();
      marker.map = null;
      markerRef.current = null;
    };
  }, [map, position.lat, position.lng, color, zIndex, title]);

  return null;
}

function GoogleMapCanvas({
  apiKey,
  claims,
  height,
  zoom,
  center,
  onClaimClick,
  colorBy,
  showAreas,
}) {
  const { isLoaded, loadError } = useJsApiLoader({
    id: "fra-google-maps",
    googleMapsApiKey: apiKey,
    libraries: MAPS_LIBRARIES,
  });

  const [activeClaim, setActiveClaim] = useState(null);

  const validClaims = useMemo(
    () => claims.map((c) => ({ claim: c, pos: toLatLng(c) })).filter((x) => x.pos),
    [claims]
  );

  const drawAreas =
    showAreas != null ? showAreas : validClaims.length > 0 && validClaims.length <= 400;

  const computedCenter = useMemo(() => {
    if (center) return center;
    if (validClaims.length === 0) return INDIA_CENTER;
    if (validClaims.length === 1) return validClaims[0].pos;
    const lat =
      validClaims.reduce((s, x) => s + x.pos.lat, 0) / validClaims.length;
    const lng =
      validClaims.reduce((s, x) => s + x.pos.lng, 0) / validClaims.length;
    return { lat, lng };
  }, [center, validClaims]);

  const computedZoom = zoom != null ? zoom : validClaims.length <= 1 ? 12 : 5;

  const onLoad = useCallback(
    (mapInstance) => {
      if (validClaims.length > 1 && window.google?.maps) {
        const bounds = new window.google.maps.LatLngBounds();
        validClaims.forEach(({ pos }) => bounds.extend(pos));
        mapInstance.fitBounds(bounds, 48);
      }
    },
    [validClaims]
  );

  if (loadError) {
    return (
      <MapsFallback height={height}>
        Google Maps failed to load. Check the API key, Maps JavaScript API
        enablement, and billing on project fra-gis-378539.
      </MapsFallback>
    );
  }

  if (!isLoaded) {
    return <MapsFallback height={height}>Loading Google Maps…</MapsFallback>;
  }

  return (
    <div className="google-map-wrap" style={{ height }}>
      <GoogleMap
        mapContainerStyle={mapContainerStyle}
        mapContainerClassName="google-map-container"
        center={computedCenter}
        zoom={computedZoom}
        onLoad={onLoad}
        options={defaultOptions}
      >
        {validClaims.map(({ claim, pos }) => {
          const color = getClaimColor(claim, colorBy);
          const id = claim.id || claim.claim_id;
          const parcelPath = drawAreas ? buildFreeformParcel(pos, claim) : null;
          const select = () => {
            setActiveClaim(claim);
            if (onClaimClick) onClaimClick(claim);
          };
          return (
            <React.Fragment key={id}>
              {parcelPath && (
                <Polygon
                  paths={parcelPath}
                  options={{
                    strokeColor: color,
                    strokeOpacity: 0.95,
                    strokeWeight: 2,
                    fillColor: color,
                    fillOpacity: 0.28,
                    clickable: true,
                    zIndex: 1,
                  }}
                  onClick={select}
                />
              )}
              <AdvancedClaimMarker
                position={pos}
                color={color}
                zIndex={2}
                title={claim.name || claim.claim_id || "Claim"}
                onClick={select}
              />
            </React.Fragment>
          );
        })}

        {activeClaim && toLatLng(activeClaim) && (
          <InfoWindow
            position={toLatLng(activeClaim)}
            onCloseClick={() => setActiveClaim(null)}
          >
            <div className="google-map-info">
              <strong>{activeClaim.name || activeClaim.claim_id || "Claim"}</strong>
              <div>Village: {activeClaim.village || "—"}</div>
              <div>District: {activeClaim.district || "—"}</div>
              <div>Type: {activeClaim.claim_type || "—"}</div>
              <div>Status: {activeClaim.status || "—"}</div>
              {activeClaim.land_area_ha != null && (
                <div>Area: {Number(activeClaim.land_area_ha).toFixed(2)} ha</div>
              )}
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
}

function WebGISMap({
  claims = [],
  height = "75vh",
  zoom,
  center,
  onClaimClick,
  colorBy = "claim_type",
  showAreas,
}) {
  const apiKey = String(process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "")
    .replace(/^\uFEFF/, "")
    .trim();

  if (!apiKey) {
    return (
      <MapsFallback height={height}>
        <>
          Set <code>REACT_APP_GOOGLE_MAPS_API_KEY</code> in{" "}
          <code>frontend/.env</code> (or <code>.env.development</code>), enable the{" "}
          <strong>Maps JavaScript API</strong>, then fully restart{" "}
          <code>npm run dev</code> (env is only read at startup).
        </>
      </MapsFallback>
    );
  }

  return (
    <GoogleMapCanvas
      apiKey={apiKey}
      claims={claims}
      height={height}
      zoom={zoom}
      center={center}
      onClaimClick={onClaimClick}
      colorBy={colorBy}
      showAreas={showAreas}
    />
  );
}

export default WebGISMap;
