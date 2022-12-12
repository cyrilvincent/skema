# https://pyris.datajazz.io/doc/
# https://pyris.datajazz.io/api/coords?geojson=false&lat=45.0984914&lon=5.5783773
# https://pyris.datajazz.io/api/compiris/382050000?geojson=false Utiliser compiris au lieu d'iris (COMP = complete)
# https://pyris.datajazz.io/api/coords?geojson=false&lat=48.8588336&lon=2.2769951
# https://pyris.datajazz.io/api/compiris/751166216?geojson=false

# Le code IRIS de la tour eiffel peut se stocker de manière différentes :
# IRIS = 6216
# CodeCommune = 75116
# CompleteIRIS = 751166216
# Lans est ne commune non IRISEE => IRIS = 0000
# Wikipedia : À chaque îlot est associé un code IRIS. Composé de 9 caractères. Il permet d'identifier de manière univoque un îlot. Les cinq premiers caractères du code IRIS correspondent au code Insee de la commune sur le territoire de laquelle est situé l'îlot.
# Il faut donc stocker le CompleteIRIS

# A mettre dans adresse_norm ajouter iris (compiris)