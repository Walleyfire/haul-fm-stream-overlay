# Haul.FM Stream Overlay — GitHub Pages (v2.1.0)

Haul.FM:n OBS-selainlähde. **Ei Cloudflare Workeria eikä omalla koneella jatkuvasti pyörivää Python-palvelinta.** GitHub Actions hakee radiometadatan ja julkaisee GitHub Pages -sivun.

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
- Overlay ei toista musiikkia.

## Kansiot

- `docs/index.html` – OBS-selainlähde
- `docs/nowplaying.json` – julkaisun aikana generoitava radiotieto
- `docs/assets/` – paikalliset logojen varakuvat
- `scripts/update_nowplaying.py` – kappaletietojen haku GitHub Actionsissa
- `.github/workflows/pages.yml` – GitHub Pages -julkaisuautomaatio

## Versiohistoria

- **v2.1.0:** GitHub Pages + GitHub Actions; Cloudflare Worker -riippuvuus poistettu; ajastettu metadatahaku ja automaattinen Pages-julkaisu.
- **v2.0.0:** GitHub Pages -prototyyppi, jossa oli Cloudflare Worker -vaihtoehto.
- **v1.2.6:** Paikallisen version ulkoasu ja läpinäkyvät kulmat.

Ei Haul.FM:n tai HaulMP:n virallinen julkaisu. Alkuperäinen inspiraatio: https://github.com/Tumppi066/truckersfm-stream-overlay.
