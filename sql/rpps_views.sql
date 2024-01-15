create or replace view structure_coord as
select structure.*, c.id as coord_id, c.complement_destinataire as complement_destinataire, c.complement_geo as complement_geo, c.numero as numero, c.indice as indice, c.code_type_voie as code_type_voie, c.voie as voie, c.mention as mention, c.cedex as cedex, c.cp as cp, c.code_commune as code_commune, c.commune as commune, c.code_pays as code_pays, c.tel as tel, c.mail as mail, c.date_maj as coord_date_maj, c.date_fin as coord_date_fin, c.lon as lon, c.lat as lat, c.precision as precision, n.iris as iris
from structure
full join coord as c on c.structure_id = structure.id
full join adresse_norm as n on c.adresse_norm_id = n.id;

create or replace view personne_coord as
select personne.*, c.id as coord_id, c.complement_destinataire as complement_destinataire, c.complement_geo as complement_geo, c.numero as numero, c.indice as indice, c.code_type_voie as code_type_voie, c.voie as voie, c.mention as mention, c.cedex as cedex, c.cp as cp, c.code_commune as code_commune, c.commune as commune, c.code_pays as code_pays, c.tel as tel, c.mail as mail, c.date_maj as coord_date_maj, c.date_fin as coord_date_fin, n.lon as lon, n.lat as lat, n.score as score, n.iris as iris
from personne
full join coord as c on c.personne_id = personne.id
full join adresse_norm as n on c.adresse_norm_id = n.id;

create or replace view personne_activite_coord as
select personne.*, a.id as activite_id, a.code_fonction as activite_code_fonction, a.fonction_id as activite_fonction_id, a.mode_exercice as activite_mode_exercice, a.date_debut as activite_date_debut, a.date_fin as activite_date_fin, a.region as activite_region, a.genre as activite_genre, a.motif_fin as activite_motif_fin, a.code_profession_id as activite_code_profession, a.categorie_pro as activite_categorie_pro, a.section_tableau_pharmaciens as activite_section, a.sous_section_tableau_pharmaciens as activite_sous_section, a.type_activite_liberale as activite_type, a.statut_ps_ssa as activite_statut_ps_ssa, a.statut_hospitalier as activite_status_hospitalier, c.id as coord_id, c.complement_destinataire as complement_destinataire, c.complement_geo as complement_geo, c.numero as numero, c.indice as indice, c.code_type_voie as code_type_voie, c.voie as voie, c.mention as mention, c.cedex as cedex, c.cp as cp, c.code_commune as code_commune, c.commune as commune, c.code_pays as code_pays, c.tel as tel, c.mail as mail, c.date_maj as coord_date_maj, c.date_fin as coord_date_fin, n.lon as lon, n.lat as lat, n.score as score, n.iris as iris
from personne
full join activite as a on a.personne_id = personne.id
full join coord as c on c.activite_id = a.id
full join adresse_norm as n on c.adresse_norm_id = n.id;

create or replace view ps_personne_activite_coord as
select ps.*,p.id as personne_id, p.inpp as personne_inpp, p.nom as personne_nom, p.prenom as personne_prenom, p.civilite as personne_civilite, p.nature as personne_nature, p.code_nationalite as personne_code_nationalite, p.date_effet as personne_date_effet, p.date_maj as personne_date_maj, a.id as activite_id, a.code_fonction as activite_code_fonction, a.fonction_id as activite_fonction_id, a.mode_exercice as activite_mode_exercice, a.date_debut as activite_date_debut, a.date_fin as activite_date_fin, a.region as activite_region, a.genre as activite_genre, a.motif_fin as activite_motif_fin, a.code_profession_id as activite_code_profession, a.categorie_pro as activite_categorie_pro, a.section_tableau_pharmaciens as activite_section, a.sous_section_tableau_pharmaciens as activite_sous_section, a.type_activite_liberale as activite_type, a.statut_ps_ssa as activite_statut_ps_ssa, a.statut_hospitalier as activite_status_hospitalier, c.id as coord_id, c.complement_destinataire as complement_destinataire, c.complement_geo as complement_geo, c.numero as numero, c.indice as indice, c.code_type_voie as code_type_voie, c.voie as voie, c.mention as mention, c.cedex as cedex, c.cp as cp, c.code_commune as code_commune, c.commune as commune, c.code_pays as code_pays, c.tel as tel, c.mail as mail, c.date_maj as coord_date_maj, c.date_fin as coord_date_fin, n.lon as lon, n.lat as lat, n.score as score, n.iris as iris
from ps
full join personne as p on p.inpp = ps."key"
full join activite as a on a.personne_id = p.id
full join coord as c on c.activite_id = a.id
full join adresse_norm as n on c.adresse_norm_id = n.id




