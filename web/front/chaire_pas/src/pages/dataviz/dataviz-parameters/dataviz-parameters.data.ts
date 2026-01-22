import { Profession } from "./dataviz-parameters.interface";

const apl_professions: Profession[] = [
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

export const professions: {[key: string]: Profession[]} = {
  APL: apl_professions.sort((a, b) => a.label.localeCompare(b.label)),
}


