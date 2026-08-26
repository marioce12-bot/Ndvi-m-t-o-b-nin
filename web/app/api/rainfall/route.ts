import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const tableDefinitions = [
  { id: "decades", title: "DECADES", description: "Entrée réseau pluviométrique : relevés journaliers par poste et par décade.", editable: true },
  { id: "agro", title: "RENSEIGNEMENTS AGRO", description: "Entrée stations synoptiques : observations météo par station et par jour.", editable: true },
  { id: "normales", title: "NORMALES", description: "Référentiels intégrés : normales pluviométriques RESA et normales agro-synoptiques.", editable: false },
  { id: "resa", title: "RESA-01", description: "Sortie automatisée calculée à partir des deux entrées et de l’historique.", editable: false },
] as const;

export function GET() {
  return NextResponse.json({
    tableDefinitions,
    inputModel: {
      requiredFiles: ["DECADES_xxx.xlsx", "Renseignements_Agro_xxx.xls"],
      history: "Les relevés sont conservés par poste, année et code de décade; un nouvel upload ne remplace pas les décades précédentes.",
      defaultReference: "La feuille Normales est intégrée comme référentiel par défaut.",
    },
    seasons: {
      north: { start: "01-04", end: "31-10", areas: ["Atacora", "Donga", "Borgou", "Alibori"] },
      south: { seasons: [{ start: "01-03", end: "31-07" }, { start: "01-09", end: "30-11" }], areas: ["Collines", "Zou", "Mono", "Couffo", "Atlantique", "Littoral", "Ouémé", "Plateau"] },
    },
  });
}
