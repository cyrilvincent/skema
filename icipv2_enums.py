from sqlentities import Context, EtablissementType, Convention, Nature, Source, FamilleActe, Profession, ModeExercice
import config
import art


class EnumsCreator:

    def source(self):
        print("Source")
        context = Context()
        context.create()
        s = Source()
        s.id = 1
        s.name = "OSM"
        context.session.add(s)
        s = Source()
        s.id = 2
        s.name = "BAN"
        context.session.add(s)
        s = Source()
        s.id = 3
        s.name = "Etab"
        context.session.add(s)
        s = Source()
        s.id = 4
        s.name = "BAN+OSM"
        context.session.add(s)
        s = Source()
        s.id = 5
        s.name = "Manually"
        context.session.add(s)
        context.session.commit()

    def etablissementType(self):
        print("EtablissementType")
        context = Context()
        context.create()
        et = EtablissementType()
        et.id = 1
        et.type = "Public"
        context.session.add(et)
        et = EtablissementType()
        et.id = 2
        et.type = "Privé non lucratif"
        context.session.add(et)
        et = EtablissementType()
        et.id = 3
        et.type = "Privé commercial"
        context.session.add(et)
        context.session.commit()

    def convention(self):
        print("Convention")
        context = Context()
        context.create()
        c = Convention()
        c.id = 0
        c.code = "NC"
        c.libelle = "Non conventionné"
        context.session.add(c)
        c = Convention()
        c.id = 1
        c.code = "C1"
        c.libelle = "Secteur 1 ou conventionné"
        context.session.add(c)
        c = Convention()
        c.id = 2
        c.code = "C2"
        c.libelle = "Secteur 1 ou conventionné avec droit au dépassement permanent"
        context.session.add(c)
        c = Convention()
        c.id = 3
        c.code = "C3"
        c.libelle = "Secteur 2"
        context.session.add(c)
        context.session.commit()

    def nature(self):
        print("Nature")
        context = Context()
        context.create()
        n = Nature()
        n.id = 1
        n.libelle = "N’exerce pas actuellement"
        context.session.add(n)
        n = Nature()
        n.id = 2
        n.libelle = "Libéral activité salariée"
        context.session.add(n)
        n = Nature()
        n.id = 3
        n.libelle = "Libéral intégral"
        context.session.add(n)
        n = Nature()
        n.id = 4
        n.libelle = "Libéral temps partiel hospitalier"
        context.session.add(n)
        n = Nature()
        n.id = 5
        n.libelle = "Libéral temps plein hospitalier"
        context.session.add(n)
        n = Nature()
        n.id = 6
        n.libelle = "Pharmacie mutualiste"
        context.session.add(n)
        n = Nature()
        n.id = 7
        n.libelle = "T. plein hosp. contrat mixte"
        context.session.add(n)
        n = Nature()
        n.id = 8
        n.libelle = "T. plein hosp./mal. aut. med."
        context.session.add(n)
        context.session.commit()

    def famille_acte(self):
        print("FamilleActe")
        context = Context()
        context.create()
        for i in range(1, 221):
            f = FamilleActe()
            f.id = i
            f.libelle = "TODO"
            context.session.add(f)
        context.session.commit()

    def profession(self):
        print("Profession")
        context = Context()
        context.create()
        for i in range(1, 75):
            p = Profession()
            p.id = i
            p.libelle = "TODO"
            context.session.add(p)
        context.session.commit()

    def mode_exercice(self):
        print("ModeExercice")
        context = Context()
        context.create()
        for i in range(1, 9):
            m = ModeExercice()
            m.id = i
            m.libelle = "TODO"
            context.session.add(m)
        context.session.commit()


if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("Sql Enums")
    print("=========")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    context = Context()
    context.create()
    print(f"Database {context.db_name}: {context.db_size():.0f} Mo")
    e = EnumsCreator()
    # e.source()
    # e.etablissementType()
    # e.nature()
    # e.convention()
    e.famille_acte()
    e.profession()
    e.mode_exercice()