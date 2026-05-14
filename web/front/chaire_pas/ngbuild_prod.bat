cmd /c ng build -c production
del /Q ..\..\nginx\linux\html\*.js
del /Q ..\..\nginx\linux\html\*.css
xcopy /Y dist\chaire_pas\browser\*.* ..\..\nginx\linux\html