import {
  addDoc,
  collection,
  doc,
  getDoc,
  getDocs,
  orderBy,
  query,
  serverTimestamp,
  updateDoc,
} from "firebase/firestore";
import { CLAIMS_COLLECTION, db } from "../firebaseClient";

const claimsRef = collection(db, CLAIMS_COLLECTION);

const serializeValue = (value) => {
  if (value && typeof value.toDate === "function") {
    return value.toDate().toISOString();
  }
  return value;
};

const mapClaim = (snapshot) => {
  const data = snapshot.data();
  return {
    id: snapshot.id,
    ...data,
    created_at: serializeValue(data.created_at),
  };
};

export async function fetchClaims() {
  const claimsQuery = query(claimsRef, orderBy("created_at", "desc"));
  const snapshot = await getDocs(claimsQuery);
  return snapshot.docs.map(mapClaim);
}

export async function fetchClaimById(claimId) {
  const snapshot = await getDoc(doc(db, CLAIMS_COLLECTION, claimId));
  if (!snapshot.exists()) {
    throw new Error("Claim not found");
  }
  return mapClaim(snapshot);
}

export async function createClaim(claimData) {
  const { entities, ...insertData } = claimData;
  const docRef = await addDoc(claimsRef, {
    ...insertData,
    latitude:
      insertData.latitude === ""
        ? null
        : Number(insertData.latitude) || insertData.latitude,
    longitude:
      insertData.longitude === ""
        ? null
        : Number(insertData.longitude) || insertData.longitude,
    created_at: serverTimestamp(),
  });
  return docRef.id;
}

export async function updateClaimStatus(claimId, status) {
  await updateDoc(doc(db, CLAIMS_COLLECTION, claimId), { status });
}
