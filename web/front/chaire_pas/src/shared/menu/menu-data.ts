export interface MenuItem {
    id: number;
    nb: number;
    icon: string;
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
                label: "APL",
                url: "/apl",
            },
            {
                id:103,
                nb:1,
                icon: "place",
                label: "SAE",
                url: "/sae",
            },
        ]
    },
    {
        id:200,
        nb:2,
        icon: "science",
        label: "Recherche",
        url: "/research",
    },
    {
        id:300,
        nb:3,
        icon: "analytics",
        label: "Data",
        url: "/data",
    },
    {
        id: 400,
        nb:4,
        icon: "article",
        label: "Medias",
        url: "/media",
    },
    {
        id: 500,
        nb:5,
        icon: "info",
        label: "A propos",
        url: "/sustain",
        subMenuItems: [
            {
                id: 501,
                nb:5,
                icon: "support",
                label: "Nous soutenir",
                url: "/sustain",
            },
            {
                id:502,
                nb:5,
                icon: "info",
                label: "A propos",
                url: "/about",
            },
            {
                id:503,
                nb:5,
                icon: "group",
                label: "Les membres fondateurs",
                url: "/about",
                fragment: "members"
            },
            {
                id:504,
                nb:5,
                icon: "settings",
                label: "Paramètres",
                url: "/about",
                fragment: "versions"
            },
        ]
    },

]