import difflib

s1 = "AVENUE J F KENNEDY"
s2 = "AVENUE JEANNE D'ARC"
s3 = "Av du Pdt J Fitzgerald Kennedy".upper()
sm = difflib.SequenceMatcher(None, s1, s2)
print(sm.ratio()) #70.3%
sm = difflib.SequenceMatcher(None, s1, s3)
print(sm.ratio()) #62.5%
s3 = s3.replace("AV", "AVENUE")
sm = difflib.SequenceMatcher(None, s1, s3)
print(sm.ratio()) #69.2%
s4 = "avenue Jean-Jaurès".upper()
s5 = "VILLA Jean Jaurès".upper()
s6 = "boulevard Jean-Jaurès".upper()
sm = difflib.SequenceMatcher(None, s4, s5)
print(sm.ratio()) #68.6%
sm = difflib.SequenceMatcher(None, s4, s6)
print(sm.ratio()) #66.7%
s1 = "AV J F KENNEDY"
s2 = "AV JEANNE D'ARC"
s3 = "AV du Pdt J Fitzgerald Kennedy".upper()
sm = difflib.SequenceMatcher(None, s1, s2)
print(sm.ratio()) #62.1%
sm = difflib.SequenceMatcher(None, s1, s3)
print(sm.ratio()) #63.6%


