const fs = require("node:fs");
const admin = require("firebase-admin");

const serviceAccount = JSON.parse(
  process.env.FIREBASE_SERVICE_ACCOUNT_JSON
);

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
});

const db = admin.firestore();

const collections = [
  "jobs",
  "agroStations",
  "agroRainDaily",
  "agroObservations",
  "agroEwEtp",
  "pentadeCatalog",
];

function serialize(value) {
  if (value && typeof value.toDate === "function") {
    return value.toDate().toISOString();
  }

  if (Array.isArray(value)) {
    return value.map(serialize);
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, serialize(item)])
    );
  }

  return value;
}

async function exportCollection(name) {
  const snapshot = await db.collection(name).get();

  if (name === "pentadeCatalog") {
    const result = {};

    for (const document of snapshot.docs) {
      result[document.id] = {
        id: document.id,
        ...serialize(document.data()),
      };
    }

    return result;
  }

  return snapshot.docs.map((document) => ({
    id: document.id,
    ...serialize(document.data()),
  }));
}

async function main() {
  const output = {};

  for (const collection of collections) {
    console.log(`Export de ${collection}...`);
    output[collection] = await exportCollection(collection);
  }

  fs.writeFileSync(
    "firebase-export.json",
    JSON.stringify(output, null, 2),
    "utf8"
  );

  console.log("Export terminé : firebase-export.json");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
