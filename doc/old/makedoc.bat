cd ..
md icip
copy adresses2pickles.py icip
copy adressesmatcher.py icip
copy cedex2pickle.py icip
copy cyrilload.py icip
copy entities.py icip
copy repositories.py icip
pdoc --html -f -o doc\html --close-stdin --skip-errors icip
move doc\html\icip\*.* doc\html
rmdir doc\html\icip
rmdir icip /S /Q

