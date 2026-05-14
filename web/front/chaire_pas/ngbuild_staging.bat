cmd /c ng build -c staging
del /Q ..\..\nginx\windows\html\*.js
del /Q ..\..\nginx\windows\html\*.css
xcopy /Y dist\chaire_pas\browser\*.* ..\..\nginx\windows\html
