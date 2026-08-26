import { NextResponse } from "next/server";

export const dynamic = "force-static";

const sources = [
  {
    id: "resa-01-aout-2026",
    name: "RESA-01 AOUT 2026.xls",
    type: "stations-synoptiques",
    description: "Réseau pluviométrique, cumuls observés, normales et bilan hydrique.",
    url: "/data/RESA-01-AOUT-2026.xls",
    sheets: ["Feuil1, 2, 3", "Normales"],
    editableFields: ["EW", "ETP"],
  },
  {
    id: "renseignements-agro-aout-2026",
    name: "Renseignements Agro 1ère décade AOUT 2026.xls",
    type: "renseignements-agro",
    description: "Tableaux de renseignements agro-climatiques de la première décade.",
    url: "/data/Renseignements-Agro-1ere-decade-AOUT-2026.xls",
    sheets: [],
    editableFields: ["EW", "ETP"],
  },
  {
    id: "decades-aout-2026",
    name: "DECADES AOUT 2026.xlsx",
    type: "cumuls-decadaires",
    description: "Décades 1, 2, 3 et cumul mensuel par département et localité.",
    url: "/data/DECADES-AOUT-2026.xlsx",
    sheets: ["Decade1", "Decade2", "Decade3", "Cumul"],
    editableFields: ["EW", "ETP"],
  },
] as const;

export function GET() {
  return NextResponse.json({ sources });
}
