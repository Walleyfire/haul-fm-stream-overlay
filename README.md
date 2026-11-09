# HaulFM Overlay

Kevyt Windows-overlay, joka näyttää Haul.FM-radion parhaillaan soivan kappaleen omassa, muiden ikkunoiden päällä pysyvässä ikkunassa.

![HaulFM Overlayn esimerkkikuva](preview.png)

*Esimerkkikuva ulkoasusta. Kappale, kansikuva ja aikatiedot vaihtuvat lähetyksen mukaan.*

## Lataa

**[Lataa HaulFM Overlay installer.exe](https://github.com/Walleyfire/haul-fm-stream-overlay/raw/refs/heads/main/HaulFM%20Overlay%20installer.exe)**

Windowsin 64-bittinen versio. Pythonia ei tarvitse asentaa. Sovellus tarvitsee internet-yhteyden ja Microsoft Edge WebView2 Runtimen, joka on yleensä valmiina Windowsissa.

## Käyttöönotto

1. Lataa **HaulFM Overlay installer.exe** ja käynnistä se.
2. Seuraa asennusohjelman ohjeita. Sovellus asennetaan omalle Windows-käyttäjällesi.
3. Avaa overlay työpöydän tai Käynnistä-valikon **HaulFM Overlay** -pikakuvakkeesta.
4. Siirrä overlay vetämällä kortista ja muuta kokoa vetämällä reunasta tai kulmasta.

**Installerin voi poistaa asennuksen jälkeen.** Pikakuvake avaa asennetun sovelluksen, joten se ei tarvitse ladattua installeria.

Asennuskansio on `%LOCALAPPDATA%\Programs\HaulFM Overlay`. Sovellus ei vaadi järjestelmänvalvojan oikeuksia.

## Ominaisuudet

- Parhaillaan soiva kappale ja artisti.
- Kappaleen kansikuva, kun se on saatavilla; muuten varakuva.
- Pyöristetyt kulmat ja säädettävä koko.
- Muiden ikkunoiden päällä pysyvä overlay.
- Kappaleen ensihavainnosta kulunut aika. Etenemispalkki näkyy, kun kappaleen kesto tunnetaan.
- Työpöydän pikakuvake ja sovelluksen sisäinen päivitystoiminto.

Aikalaskuri alkaa siitä, kun sovellus havaitsee kappaleen. Se ei ole lähetyksen tarkka toistoaika. Sovellus näyttää kappaletiedot, mutta **ei toista radion ääntä**.

## Käyttö pelin kanssa

Valitse pelin näyttötilaksi **reunaton koko näyttö** tai **ikkunatila**, jotta overlay voi näkyä pelin päällä. Yksinomaisessa koko näytön tilassa näkyminen ei ole taattua.

## Valikko ja sulkeminen

Napsauta overlayta hiiren oikealla:

- **Tarkista päivitykset** hakee GitHubissa olevan uusimman EXE:n.
- **GitHub-repository…** vaihtaa päivityslähteen. Tämän projektin osoite on valmiiksi asetettu.
- **Sulje** lopettaa sovelluksen.

## Päivitykset

Uusi versio tarkistetaan myös käynnistyessä. Kun hyväksyt päivityksen, sovellus lataa uuden EXE:n, korvaa nykyisen tiedoston ja käynnistyy uudelleen. Aiemmasta EXE:stä jää `.previous`-varmuuskopio.

Päivitys vaatii internet-yhteyden ja kirjoitusoikeuden kansioon, jossa EXE sijaitsee. Voit myös sulkea sovelluksen ja suorittaa uusimman installerin uudelleen. Se päivittää aiemman asennuksen samaan kansioon.

Jos käytössäsi on vanha versio, jossa päivityksen jälkeen tulee **Failed to load Python DLL** -virhe, sulje sovellus ja asenna uusin versio yllä olevalla installerilla. Korjaus sisältyy versioon **1.2.10**.

## Asennuksen poistaminen

1. Sulje overlay: hiiren oikea painike → **Sulje**.
2. Avaa Windowsin **Asetukset → Sovellukset → Asennetut sovellukset** (Windows 10: **Sovellukset ja ominaisuudet**).
3. Etsi **HaulFM Overlay** ja valitse **Poista asennus**.

Vaihtoehtoisesti avaa Käynnistä-valikon **HaulFM Overlay** -kansiosta **Poista HaulFM Overlay**.

Poistaminen poistaa asennetun sovelluksen, sen pikakuvakkeet, päivityksen varmuuskopion sekä overlayn oman päivitysasetuksen ja tallennetut kuvakkeet. Alkuperäistä ladattua installeria ei tarvita poistamiseen. Lataukset-kansioon jääneen installerin voit poistaa itse.

Jos olet käyttänyt aiempaa erillistä, asentamatonta EXE-versiota, poista myös sen vanha `HaulFM-Overlay.exe` ja mahdollinen `.previous`-varmuuskopio siitä kansiosta, johon itse tallensit ne.

## Huomioitavaa

Kappaletiedot ja kansikuvat riippuvat ulkoisten palveluiden saatavuudesta. Puuttuvia kappaletietoja ei keksitä.

EXE:tä ei ole digitaalisesti allekirjoitettu, joten Windows voi näyttää SmartScreen-ilmoituksen.

Tämä on epävirallinen Haul.FM-overlay. Haul.FM:n nimet, logot ja kappaleiden kansikuvat kuuluvat omistajilleen.
