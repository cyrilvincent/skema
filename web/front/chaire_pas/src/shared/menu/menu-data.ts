export interface MenuItem {
    id: number;
    nb: number;
    icon: string;
    style?: string;
    label: string;
    url?: string;
    fragment?: string;
    subMenuItems?: MenuItem[];
}

export const data: MenuItem[] = [
    {
        id:0,
        nb:0,
        icon: "home",
        label: "Missions",
        url: "/",
    },
    {
        id:100,
        nb:1,
        icon: "travel_explore",
        label: "L'observatoire",
        url: "/observatoire",
        subMenuItems: [
            {
                id:101,
                nb:1,
                icon: "travel_explore",
                label: "L'observatoire",
                url: "/observatoire",
            },
            {
                id:102,
                nb:1,
                icon: "map",
                label: "Accessibilité aux soins de premier recours",
                url: "/apl",
            },
            {
                id:103,
                nb:1,
                icon: "place",
                label: "Accessibilité aux soins hospitaliers",
                url: "/sae",
            },
            {
                id:104,
                nb:1,
                icon: "place",
                label: "Accessibilité aux autres services de santé",
                url: "/sae2",
            }
        ]
    },
    {
        id:200,
        nb:2,
        icon: "science",
        label: "Recherche",
        url: "/research",
        subMenuItems: [
            {
                id:201,
                nb:2,
                icon: "travel_explore",
                label: "Axes de recherche",
                url: "/research",
            },
            {
                id:202,
                nb:2,
                icon: "map",
                label: "Publications et travaux scientifiques",
                url: "/publication",
            },
            {
                id:203,
                nb:2,
                icon: "place",
                label: "Etudes",
                url: "/publication",
                fragment: "studies"
            },
        ]
    },
    {
        id: 300,
        nb: 3,
        icon: "article",
        label: "Equipe",
        url: "/members",
    },
    {
        id: 400,
        nb: 4,
        icon: "article",
        label: "Partenaires",
        url: "/partners",
    },
    {
        id: 500,
        nb: 5,
        icon: "info",
        label: "Nous soutenir",
        url: "/sustain",
        subMenuItems: [
            {
                id: 501,
                nb: 5,
                icon: "support",
                label: "Nous soutenir",
                url: "/sustain",
            },
            {
                id: 502,
                nb: 5,
                icon: "info",
                label: "A propos",
                url: "/about",
            },
            {
                id: 503,
                nb: 5,
                icon: "group",
                label: "Les membres fondateurs",
                url: "/about",
                fragment: "members"
            },
            {
                id: 504,
                nb: 5,
                icon: "settings",
                label: "Paramètres",
                url: "/about",
                fragment: "versions"
            },
        ]
    },
    {
        id: 600,
        nb: 6,
        icon: "person",
        //style: "color: white; -webkit-text-stroke: 1px #0B586F;",
        label: "",
        url: "/e0206m2205",
    },

]