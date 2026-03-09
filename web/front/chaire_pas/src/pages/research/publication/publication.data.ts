export interface PublicationDTO {
    id: number;
    title: string;
    authors?: string;
    source?: string;
    year?: number;
    type: string;
    url?: string;
    publisher?: string;
}

export const publications: PublicationDTO[] = [
    {
        id:1,
        title: "Spatial dependence in physicians' prices and additional fees: Evidence from France",
        authors: "MONTMARTIN B. & HERRERA M.",
        year: 2023,
        source: "Journal of Health Economics, Volume 88, 102724, https://doi.org/10.1016/j.jhealeco.2023.102724",
        url: "https://www.sciencedirect.com/science/article/abs/pii/S0167629623000012",
        type: "P"
    },
    {
        id:2,
        title: "Socioeconomic determinants of pandemics: a spatial methodological approach with evidence from COVID-19 in Nice, France",
        authors: "BAILLY, L., BELGAIED, R., JOBERT, T. et MONTMARTIN, B.",
        year: 2025,
        source: "Geospatial Health, 20(2)",
        url: "https://www.geospatialhealth.net/gh/article/view/1383",
        type: "P"
    },
    {
        id:3,
        title: "Balancing health and sustainability: Optimizing investments in organic vs. conventional agriculture through pesticide reduction",
        authors: "BARGNA, L., LA TORRE, D., MAGGISTRO, R. et MONTMARTIN, B.",
        year: 2026,
        source: "Journal of Economic Behavior and Organization, 243, pp. 107442",
        url: "https://www.sciencedirect.com/science/article/abs/pii/S0167268126000302",
        type: "P"
    },
    {
        id:4,
        title: "Chronic air pollution exposure is associated with lower chance of live birth after frozen embryo transfer",
        authors: "Crouzat, A., Cremoni, M., Boukaïdi, S., Seitz-Polski, B., & Gauci, P. A.",
        year: 2026,
        source: "Reproductive BioMedicine Online, Volume 52, Issue 4",
        url: "https://www.rbmojournal.com/article/S1472-6483(25)00625-X/fulltext",
        type: "P"
    },
    {
        id:5,
        title: "Air pollution exposure induces a decrease in type II interferon response: A paired cohort study",
        authors: "Allouche J, Cremoni M, Brglez V, Graça D, Benzaken S, Zorzi K, Fernandez C, Esnault V, Levraut M, Oppo S, Jacquinot M, Armengaud A, Pradier C, Bailly L, Seitz-Polski B.",
        year: 2022,
        source: "EBioMedicine, Volume 85, 104291, doi: 10.1016/j.ebiom.2022.104291",
        url: "https://www.thelancet.com/journals/ebiom/article/PIIS2352-3964(22)00473-X/fulltext",
        type: "P"
    },
    {
        id:6,
        title: "Toxic Occupational Exposures and Membranous Nephropathy",
        authors: "Cremoni M, Agbekodo S, Teisseyre M, Zorzi K, Brglez V, Benzaken S, Esnault V, Planchard JH, Seitz-Polski B.",
        year: 2022,
        source: "Clinical Journal of the American Society of Nephrology, Volume 17(11), p.1609-1619. doi: 10.2215/CJN.02930322",
        url: "https://journals.lww.com/cjasn/fulltext/2022/11000/toxic_occupational_exposures_and_membranous.8.aspx",
        type: "P"
    },
]

export const works: PublicationDTO[] = [
    {
        id:7,
        title: "Conformity, Competition, and Voluntary Price Regulation: Evidence from French Physicians",
        authors: "Lambotte M. & Montmartin B.",
        type: "W"
    },
    {
        id:8,
        title: "Adenomyosis and Time to Live Birth in Assisted Reproductive Technology: A Retrospective Matched Cohort Study",
        authors: "Gauci P.A & Montmartin B.",
        type: "W"
    },
    {
        id:9,
        title: "Where patients live matters: Linking environmental exposure, healthcare access, and income to IVF success",
        authors: "Montmartin B., Laffineur C. & Gauci P.A",
        type: "W"
    },
]

export const studies: PublicationDTO[] = [
    {
        id:10,
        year: 2026,
        title: "Reconversion professionnelle : désir et obstacle",
        url: "https://www.cepremap.fr/2026/02/reconversion-professionnelle-desir-et-obstacles/",
        publisher: "CEPREMAP",
        type: "S"
    },
    {
        id:11,
        year: 2025,
        title: "Lutte contre les déserts médicaux en France : Les avantages de l'installation obligatoire",
        url: "https://publika.skema.edu/fr/lutte-contre-les-deserts-medicaux-en-france/",
        publisher: "SKEMA Publika",
        type: "S"
    },
    {
        id:12,
        year: 2024,
        title: "Etude sur les Dépassements d'honoraires",
        publisher: "UFC que Choisir",
        type: "S"
    },
    {
        id:13,
        year: 2023,
        title: "Etude sur l'aggravation de l'accès aux soins",
        publisher: "UFC que Choisir",
        type: "S"
    },
    {
        id:14,
        year: 2023,
        title: "Etude sur la tension dans les services d'urgences",
        publisher: "UFC que Choisir",
        type: "S"
    },
    {
        id:15,
        year: 2022,
        title: "Etude sur le fracture sanitaire et les déserts médicaux",
        publisher: "UFC que Choisir",
        type: "S"
    },
]