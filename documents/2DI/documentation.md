# Problems and Solutions

## Camera
Geen camera input, met 1 module input, met opencv niet. Opgelost dmv legacy camera support aan te zetten.

## Color transform
Slechte detectie Rode buizen, veel ruis. Opgelost met HSV + blur.

## Library
Fout in steering library. Formule aangepast voor steering angle.

## Average slope
Auto stuurde te snel. Roling average toegevoegt, enkele buis kleinere weight op waardes.

## Trage reactie
lage proccessing speed. Test met videos uit (Verbetering)

## Boundries
Verkeerde detectie van lijnen. Boundries toegevoegd om dit te voorkomen (Lijnen op linkse deel links en rechts rechts)

## Slecht overzicht
Slecht overzicht van de baan. Camera naar achter verplaats zodat we deel van de auto zien en meer baan zien.

## Test buiten
	-Flashbang bij start. 1 second wachten om camera te initialiseren.
	-Slechte kleurdetectie. Brightness HSV aangepast.
	-Slechte ROI, auto zig-zagt. Hoger gezet om verder te kijken.
