export interface Specialite {
    id: number;
    label: string;
    shortLabel: string;
    time: number;
}

export interface GeoInputDTO {
    code: string;
    id: number;
    bor: string;
    time: number;
    exp: number;
    hc: string;
    resolution: string;
}

export interface GeometryDTO {
    type: string;
    coordinates: any[][];
}

export interface FeaturePropertiesDTO {
    // cleabs: string;
    // code_insee: string;
    // nom_commune: string;
    //iris: string;
    // code_iris: string;
    // nom_iris: string;
    //type_iris: string;
    fid: number;
    // lon: number;
    // lat: number;
}


export interface FeatureDTO {
    id: string;
    type: string;
    properties: FeaturePropertiesDTO;
    geometry: GeometryDTO;
    bbox: number[];
}

export interface FeatureCollectionDTO {
    type: string;
    features: FeatureDTO[];
    bbox: number[];
}

export interface GeoYearDTO {
    code_insee: string[];
    nom_commune: string[];
    code_iris: string[];
    nom_iris: string[];
    //type_iris: string[];
    fid: number[];
    lon: number[];
    lat: number[];
    year: number[];
    //specialite: number[];
    nb: number[];
    apl: number[]; // TODO
    //R: number[]; // TODO
    swpop: number[]; // TODO
    //pop_gp: number[]; // TODO
    pop: number[];
    meanw: number[];
    //pretty: number[]; //TODO
    pop_ajustee: number[]; //TODO
    //apl_clip: number[]; //TODO
    apl_max: number[];
}

export interface GeoDTO {
    center_lat: number;
    center_lon: number;
    label: string;
    q: string;
    commune_nom: string;
    meanws: number[];
    years: {[key: string]: GeoYearDTO};
}

export type GeoTupleDTO = [GeoDTO, FeatureCollectionDTO];

// {"center_lat": 45.120971854318064, 
// "center_lon": 5.590172891026883, 
// "label": "Généraliste", 
// "q": "38205", 
// "commune_nom": "Lans-en-Vercors",
//  "meanws": [83.67865634668131, 82.44747634418418, 81.325369754328, 81.9900075563502, 80.71305375458552, 81.6848815475473], 
// "years": {
//      "2020": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [20], "specialite": [10], "nb": [6.0], "apl": [98.2905193815697], "R": [54.87711363156735], "swpop": [10933.519645881262], "pop_gp": [2412.6757772064325], "pop": [2673.0], "meanw": [179.71623688129824], "pretty": [98], "pop_ajustee": [2412.6757772064325], "apl_clip": [98.2905193815697]}, 
//      "2021": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [21], "specialite": [10], "nb": [5.0], "apl": [88.2203441059961], "R": [45.522629581412716], "swpop": [10983.548283514674], "pop_gp": [2420.8653758078735], "pop": [2668.0], "meanw": [161.05392623869068], "pretty": [88], "pop_ajustee": [2420.8653758078735], "apl_clip": [88.2203441059961]}, 
//      "2022": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [22], "specialite": [10], "nb": [5.0], "apl": [87.9248606733234], "R": [45.52126046495237], "swpop": [10983.878629304629], "pop_gp": [2419.6643102032194], "pop": [2668.0], "meanw": [160.41975209377233], "pretty": [88], "pop_ajustee": [2419.6643102032194], "apl_clip": [87.9248606733234]}, 
//      "2023": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [23], "specialite": [10], "nb": [5.0], "apl": [88.04236903883476], "R": [45.53002706246097], "swpop": [10981.7637339435], "pop_gp": [2418.9209114379914], "pop": [2668.0], "meanw": [160.6212363169184], "pretty": [88], "pop_ajustee": [2418.9209114379914], "apl_clip": [88.04236903883476]}, 
//      "2024": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [24], "specialite": [10], "nb": [5.25], "apl": [92.82919423230348], "R": [47.78230072570823], "swpop": [10987.331962387803], "pop_gp": [2421.6409888483845], "pop": [2668.0], "meanw": [169.52803167484635], "pretty": [93], "pop_ajustee": [2421.6409888483845], "apl_clip": [92.82919423230348]}, 
//      "2025": {"code_insee": ["38205"], "nom_commune": ["Lans-en-Vercors"], "code_iris": ["382050000"], "nom_iris": ["Lans-en-Vercors"], "type_iris": ["Z"], "fid": [30007], "lon": [5.590172891026883], "lat": [45.120971854318064], "year": [25], "specialite": [10], "nb": [5.25], "apl": [95.5480019132784], "R": [47.78230072570823], "swpop": [10987.331962387803], "pop_gp": [2421.6409888483845], "pop": [2668.0], "meanw": [174.49321658752265], "pretty": [96], "pop_ajustee": [2421.6409888483845], "apl_clip": [95.5480019132784]}}}

// {"type": "FeatureCollection", "features": [{"id": "30007", "type": "Feature", "properties": {"cleabs": "IRIS____0000000382050000", "code_insee": "38205", "nom_commune": "Lans-en-Vercors", "iris": "0000", "code_iris": "382050000", "nom_iris": "Lans-en-Vercors", "type_iris": "Z", "fid": 30007, "lon": 5.590172891026883, "lat": 45.120971854318064}, "geometry": {"type": "MultiPolygon", "coordinates": [[[[5.620031138252177, 45.09046954895193], [5.62003596211817, 45.09027394194188], [5.619781496080767, 45.089891640396644], [5.619840367742657, 45.08962809673324], [5.619549303942684, 45.08911602598694], [5.619032328199043, 45.0888
