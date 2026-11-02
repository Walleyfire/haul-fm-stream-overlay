# Haul.FM Stream Overlay — GitHub Pages (v2.2.1)

Haul.FM:n OBS-selainlähde. **Ei Cloudflare Workeria eikä omalla koneella jatkuvasti pyörivää Python-palvelinta.** GitHub Actions hakee radiometadatan ja julkaisee GitHub Pages -sivun.

## Radioääni (v2.2.1)

Overlay sisältää **automaattisesti käynnistyvän piilotetun HTML-äänisoittimen**. Sivulla **ei ole play/pause-näppäimiä eikä äänenvoimakkuussäädintä**. OBS:ssä äänenvoimakkuuden voi tarvittaessa säätää OBS:n äänimikseristä.

- Ensisijaisesti kokeillaan `https://stream.haul.fm/haulmpfm.mp3`, sitten `https://stream.haul.fm:8000/haulmpfm.mp3` ja viimeiseksi alkuperäistä `http://stream.haul.fm:8000/haulmpfm.mp3`-osoitetta.
- **Tärkeää:** HTTPS-osoitteiden olemassaoloa ja toimivuutta ei ole pystytty vahvistamaan. GitHub Pages on HTTPS-sivu, ja selain voi estää HTTP-äänivirran sekä äänen automaattisen käynnistymisen. Siksi ääni **ei ole vielä taatusti toimiva** pelkällä GitHub Pagesilla.
- Jos Haul.FM tarjoaa toimivan HTTPS-muotoisen suoran audiostreamin, sen voi antaa sivulle URL-parametrina `?stream=https%3A%2F%2F...` (oikea HTTPS-osoite URL-koodattuna).
- OBS Studio: avaa selainlähteen ominaisuudet ja ota tarvittaessa käyttöön **Hallitse ääntä OBS:n kautta (Control audio via OBS)**. OBS:n äänimikserissä voi silloin hallita lähteen ääntä. 
- Jos stream ei toimi sivulle upotettuna, **varma vararatkaisu OBS:ssä** on lisätä *Medialähde (Media Source)*, poistaa *Paikallinen tiedosto (Local file)* -valinta ja asettaa URL:ksi `http://stream.haul.fm:8000/haulmpfm.mp3`. Tämä on erillinen OBS-äänilähde, ei HTML-overlayssa toistettava ääni. Vältä kahden äänilähteen samanaikaista toistoa.
- Tavallisen selaimen automaattisen toiston esto voi vaatia käyttäjän napsautuksen; OBS:n selainlähde toimii eri selaimen asetuksilla. `?demo=1` näyttää testikappaleen eikä käynnistä radion ääntä.


### Jos verkkosivulla ei kuulu ääntä

Versiossa 2.2.1 näkyy alarivillä virhetilanteessa syy, ei soittopainikkeita:

- **Selain esti äänen • klikkaa overlayta kerran**: selain torjuu automaattisen äänen. Klikkaus voi sallia toiston, jos valittu äänivirta on muuten toimiva.
- **Ääni ei toimi • HTTPS-äänivirta tarvitaan**: yksikään kokeiltu äänilähde ei vastannut selaimelle sopivasti. Pelkkä klikkaaminen ei voi korjata rikkoutunutta tai HTTP-only streamia.

**Huomautus:** `https://stream.haul.fm/haulmpfm.mp3` ja portin 8000 HTTPS-versio ovat vain mahdollisia osoitteita, eivät vahvistettuja toimivia kuuntelulinkkejä. Jos Haul.FM:n oma nettisoitin toimii, oikean HTTPS-lähteen voi etsiä selaimessa F12 → Network → Media / All → käynnistä radion toisto ja tarkista audiopyynnön URL. Jos löydät toimivan linkin, testaa sitä overlayn URL:ssa `?stream=URL_KOODATTUNA`. HTTP-linkki ei riitä turvalliseen GitHub Pages -upotukseen.

GitHub Pages on staattinen hosting. Se ei voi muuntaa alkuperäistä HTTP-radiovirtaa HTTPS-äänivirraksi eikä ohittaa selaimen autoplay-käytäntöjä. Verkkosivulle ei ole mahdollista taata automaattista ääntä ilman toimivaa HTTPS-äänilähdettä ja selaimen myöntämää toisto-oikeutta. OBS:n erillinen medialähde alkuperäiselle HTTP-streamille pysyy varmimpana vaihtoehtona OBS-käytössä.

## Käyttöönotto

1. Avaa [Settings → Pages](https://github.com/Walleyfire/haul-fm-stream-overlay/settings/pages).
2. Valitse **Build and deployment → Source → GitHub Actions** (ei *Deploy from a branch*).
3. Siirry [GitHub Actionsiin](https://github.com/Walleyfire/haul-fm-stream-overlay/actions/workflows/pages.yml) ja käynnistä **Publish Haul.FM overlay (GitHub Pages)** painamalla **Run workflow**.
4. Tarkista, että suoritus päättyy vihreään merkkiin. Jos se epäonnistuu, avaa suoritus ja tarkista lokit.
5. GitHub Pages -osoite: **https://walleyfire.github.io/haul-fm-stream-overlay/**. OBS:ään **Selain**-lähde, leveys **580**, korkeus **170**.

Testaa ensin sivua osoitteessa https://walleyfire.github.io/haul-fm-stream-overlay/?demo=1 (simuloitu kappale).

## Päivittyminen ja rajoitukset

- GitHub Actions -työnkulku `.github/workflows/pages.yml` käynnistyy ajastetusti noin **5 minuutin välein**, manuaalisesti ja koodimuutosten jälkeen. GitHub voi viivästyttää tai jättää ajastettuja suorituksia tekemättä.
- `scripts/update_nowplaying.py` hakee tiedot Haul.FM:n Icecast-tilasta (tai varalla MP3-virran ICY-metadatasta). Kansikuvan ja keston voi saada iTunesin julkisesta hakupalvelusta.
- Työnkulku luo tiedoston `docs/nowplaying.json` ja julkaisee koko `docs/`-kansion Pagesiin **ilman, että luodaan uutta commitia jokaisesta päivityksestä**.
- Selain tarkistaa julkaistun JSON-tiedoston **30 sekunnin välein** ja piilottaa yli 16 minuuttia vanhat kappaletiedot.
- Tämä **ei ole reaaliaikainen nyt soi -palvelu**: lyhyet kappaleet saattavat vaihtua ennen seuraavaa päivitystä, ja arvioitu etenemisaika alkaa havaintohetkestä.
- Haul.FM:n palvelin käyttää HTTP-porttia 8000. **GitHub Actions -palvelinten verkkoyhteyttä asemaan ei ole voitu vahvistaa**. Jos haku epäonnistuu, sivulla näytetään virhetila. Tällöin tarvitaan toimiva julkinen HTTPS-metadatalähde tai muu jatkuvasti toimiva välipalvelu.

## Ulkoasu

- 580 × 170 px, läpinäkyvä tausta ja pyöristetyt kulmat ilman ulkovarjoa.
- Oikealla Haul.FM:n virallinen wordmark, vasemmalla kappaleen kansikuva tai virallinen Haul.FM-kuvake.
- Aikateksti sekä etenemispalkki **vain kun kesto tunnetaan** (tuntemattomalla kestolla aikateksti muodossa `01:25 / --:--`, ei keinotekoista palkkia).
- Parametrit: `?demo=1`, `?scale=1.2`, `?accent=%2300E5AD`.
- Overlay yrittää toistaa Haul.FM:n live-radion äänen automaattisesti ilman näkyviä säätimiä. Se edellyttää, että selaimelle sopiva stream-osoite toimii.

## Kansiot

- `docs/index.html` – OBS-selainlähde
- `docs/nowplaying.json` – julkaisun aikana generoitava radiotieto
- `docs/assets/` – paikalliset logojen varakuvat
- `scripts/update_nowplaying.py` – kappaletietojen haku GitHub Actionsissa
- `.github/workflows/pages.yml` – GitHub Pages -julkaisuautomaatio

## Versiohistoria

- **v2.2.1:** korjattu äänentoiston virhetilojen käsittely, äänilähteen aikakatkaisu ja yhden klikkauksen toistoyritys ilman näkyviä hallintapainikkeita. HTTPS-lähteen toimivuutta ei ole vielä voitu vahvistaa.

- **v2.2.0:** lisätty automaattinen HTML-radioääni ilman toisto-, tauko- tai äänenvoimakkuussäätimiä. HTTPS-saatavuus ja automaattinen toisto pitää vielä varmistaa OBS:ssä.

- **v2.1.0:** GitHub Pages + GitHub Actions; Cloudflare Worker -riippuvuus poistettu; ajastettu metadatahaku ja automaattinen Pages-julkaisu.
- **v2.0.0:** GitHub Pages -prototyyppi, jossa oli Cloudflare Worker -vaihtoehto.
- **v1.2.6:** Paikallisen version ulkoasu ja läpinäkyvät kulmat.

Ei Haul.FM:n tai HaulMP:n virallinen julkaisu. Alkuperäinen inspiraatio: https://github.com/Tumppi066/truckersfm-stream-overlay.
