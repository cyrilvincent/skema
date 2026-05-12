ng build -c staging
del ..\..\nginx\windows\html\*.js
del ..\..\nginx\windows\html\*.css
copy -Y dist\chaire_pas\browser\*.* ..\..\nginx\windows\html