import art
import config
import sys
import difflib
from adressesmatcher import AdresseMatcher

if __name__ == '__main__':
    art.tprint(config.name, "big")
    print("String Comparer")
    print("===============")
    print(f"V{config.version}")
    print(config.copyright)
    print()
    am = AdresseMatcher()
    while True:
        s1 = input("Phrase1 (Entrer pour quitter): ")
        if s1 == "":
            sys.exit(0)
        s1 = am.normalize_street(s1.upper())
        s2 = input("Phrase2: ")
        s2 = am.normalize_street(s2.upper())
        print(s1)
        print(s2)
        _, score = am.gestalts(s1, [s2])
        sys.stdout.writelines(difflib.ndiff(s1, s2))
        print(f"\nScore avec pondération: {score * 100:.1f}%")
        print(f"Score brut: {am.gestalt(s1, s2) * 100:.1f}%")
