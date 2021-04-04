from adressesmatcher import AdresseMatcher

am = AdresseMatcher()
s1 = "AVENUE J F KENNEDY"
s2 = "AVENUE JEANNE D'ARC"
s3 = "Av du Pdt J Fitzgerald Kennedy".upper()
ratio = am.gestalt(s1, s2)
print(ratio) #70.3%
ratio = am.gestalt(s1, s3)
print(ratio) #62.5%
s3 = s3.replace("AV", "AVENUE")
ratio = am.gestalt(s1, s3)
print(ratio) #69.2%
s4 = "avenue Jean-Jaurès".upper()
s5 = "VILLA Jean Jaurès".upper()
s6 = "boulevard Jean-Jaurès".upper()
ratio = am.gestalt(s4, s5)
print(ratio) #68.6%
ratio = am.gestalt(s4, s6)
print(ratio) #66.7%
s1 = "AV J F KENNEDY"
s2 = "AV JEANNE D'ARC"
s3 = "AV du Pdt J Fitzgerald Kennedy".upper()
ratio = am.gestalt(s1, s2)
print(ratio) #62.1%
ratio = am.gestalt(s1, s3)
print(ratio) #63.6%

import shutil
shutil.copy2("toto.txt", "c:\\")
