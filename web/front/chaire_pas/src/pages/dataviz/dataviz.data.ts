import { Specialite, GeoTupleDTO } from "./dataviz.interfaces";

const sae_etablissements: Specialite[] = [
  {
    id: 1,
    label: "Urgences générales",
    shortLabel: "urgence_gen",
    time: 30
  },
  {
    id: 2,
    label: "Urgences pédiatriques",
    shortLabel: "urgence_ped",
    time: 30
  },
  {
    id: 3,
    label: "Etablissements psychiatriques",
    shortLabel: "psy",
    time: 30
  },
  {
    id: 4,
    label: "Pharmacies",
    shortLabel: "pharma",
    time: 30
  },
  {
    id: 5,
    label: "EHPAD",
    shortLabel: "ehpad",
    time: 30
  },
]

const apl_specialites: Specialite[] = [
  {
    id: 1,
    label: "Psychiatre",
    shortLabel: "Psychiatre",
    time: 45
  },
  {
    id: 2,
    label: "Anesthésiste",
    shortLabel: "Anest",
    time: 45
  },
  {
    id:3,
    label: "Dermatologue",
    shortLabel: "Dermato",
    time: 45
  },
  {
    id: 4,
    label: "Gastro-entérologue",
    shortLabel: "Gastro",
    time: 45
  },
  {
    id: 5,
    label: "Gynécologue",
    shortLabel: "Gyneco",
    time: 45
  },
  {
    id: 6,
    label: "Opthtalmogue",
    shortLabel: "Opthtalmo",
    time: 45
  },
  {
    id: 7,
    label: "Pédiatre",
    shortLabel: "Pediatre",
    time: 45
  },
  {
    id: 8,
    label: "Radiologue",
    shortLabel: "Radio",
    time: 45
  },
  {
    id: 10,
    label: "Généraliste",
    shortLabel: "Generaliste",
    time: 30
  },
  {
    id: 11,
    label: "Cardiologue",
    shortLabel: "Cardio",
    time: 45
  },
  {
    id: 12,
    label: "Chirugien",
    shortLabel: "Chirugien",
    time: 45
  },
  {
    id: 13,
    label: "Endocrinologue",
    shortLabel: "Endocrino",
    time: 45
  },
  {
    id: 15,
    label: "Neurologue",
    shortLabel: "Neuro",
    time: 45
  },
  {
    id: 16,
    label: "Oto-rhino-laryngologiste",
    shortLabel: "ORL",
    time: 45
  },
  {
    id: 17,
    label: "Pneumologue",
    shortLabel: "Pneumo",
    time: 45
  },
  {
    id: 19,
    label: "Rhumatologue",
    shortLabel: "Rhumato",
    time: 45
  },
  {
    id: 21,
    label: "Infirmier",
    shortLabel: "Infirmier",
    time: 30
  },
  {
    id: 22,
    label: "Sage-femme",
    shortLabel: "Sage-femme",
    time: 45
  },
  {
    id: 23,
    label: "Masseur-Kinésithérapeute",
    shortLabel: "Kine",
    time: 30
  },
  {
    id: 24,
    label: "Pédicure-podologue",
    shortLabel: "Podologue",
    time: 30
  },
  {
    id: 25,
    label: "Orthophoniste",
    shortLabel: "Orthophoniste",
    time: 45
  },
  {
    id: 27,
    label: "Chirurgien-dentaire",
    shortLabel: "Dentiste",
    time: 30
  },
]

export const specialites: {[key: string]: Specialite[]} = {
  APL: apl_specialites.sort((a, b) => a.label.localeCompare(b.label)),
  SAE: sae_etablissements,
}

export const emptyGeo: GeoTupleDTO = [{"center_lat": 0, "center_lon": 0, "label": "Erreur", "q": "", "commune_nom": "Erreur", "meanws": [1], "years": {"2020": {"code_insee": [""], "nom_commune": [""], "code_iris": [""], "nom_iris": [""], "type_iris": [""], "fid": [1], "lon": [5], "lat": [45], "year": [1], "specialite": [1], "nb": [1], "apl": [1], "R": [1], "swpop": [1], "pop_gp": [1], "pop": [1], "meanw": [1], "pretty": [1], "pop_ajustee": [1], "apl_clip": [1]}}},{"type": "FeatureCollection", "features": [{"id": "1", "type": "Feature", "properties": {"cleabs": "", "code_insee": "", "nom_commune": "", "iris": "", "code_iris": "", "nom_iris": "", "type_iris": "", "fid": 1, "lon": 5, "lat": 45}, "geometry": {"type": "MultiPolygon", "coordinates": [[[[5, 45], [6, 45], [6, 46], [5, 46], [5, 45]]]]}, "bbox": [5,45, 6, 46]}], "bbox": [5, 8, 6, 46]}];
  


