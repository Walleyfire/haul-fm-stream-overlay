# Haul.FM Stream Overlay — GitHub Pages (v2.0.0)

Tumppi066:n TruckersFM Stream Overlay -projektin innoittama erillinen Haul.FM:n OBS-overlay. Tämä versio on tehty **GitHub Pages** -julkaisua varten. Aiemman paikallisen Python-palvelimen käyttö ei ole tarpeen, kun HTTPS-kappaletietopalvelu on julkaistu.

## Julkaisutilanne (2.11.2026)

Projektin tiedostot ovat jo GitHub-repositorion `main`-haarassa: https://github.com/Walleyfire/haul-fm-stream-overlay.

**GitHub Pagesin käyttöönotto:** Avaa [Settings → Pages](https://github.com/Walleyfire/haul-fm-stream-overlay/settings/pages) ja valitse **Deploy from a branch → main → /docs → Save**. Julkaisun jälkeen overlayn osoite on https://walleyfire.github.io/haul-fm-stream-overlay/.

**Reaaliaikaiset kappaletiedot:** GitHub Pages ei suorita `worker/src/index.js`-koodia. Julkaise se erikseen Cloudflare Workersiin (ohje kohdassa A), tarkista `/api/nowplaying` ja aseta julkaistu osoite tiedostoon `docs/config.js`. **Kunnes API-osoite on määritetty, sivu näyttää asennuskehotteen eikä oikeaa kappaletietoa.** Testiä varten voit avata sivun parametrilla `?demo=1`.

## Ulkoasu ja toiminnot

- 580 × 170 px, läpinäkyvä tausta ja pyöristetyt kulmat **ilman ulkovarjoa**.
- Haul.FM:n virallinen wordmark oikeassa yläkulmassa; ei erillistä tekstiä tai lisäkuvaketta.
- Vasemmalla kappaleen kansikuva, tai Haul.FM:n `icon-96.webp`-kuvake kun kansikuvaa ei ole.
- Aikateksti `00:42 / 03:51`; tuntemattomalla kestolla `00:42 / --:--`.
- Edistymispalkki näkyy **vain** jos kappaleen kesto tiedetään; eteneminen lasketaan ensimmäisestä havainnosta (arvio).
- Käytössä olevat valinnaiset asetukset: `?scale=1.3`, `?accent=%2300E5AD` sekä `?demo=1`.
- Ei soita tai välitä ääntä.

## Miksi pelkkä GitHub Pages ei riitä?

GitHub Pages julkaisee HTML/CSS/JavaScript-tiedostot, mutta ei suorita Python-palvelinta. Radion lähde on HTTP-osoitteessa `http://stream.haul.fm:8000/haulmpfm.mp3`, joka ei sellaisenaan sovellu HTTPS-sivulla selaimesta luettavaksi (mixed content ja mahdolliset CORS-rajoitukset). Tarvitset **julkisen HTTPS-kappaletietopalvelun**, jonka toteutus on tässä paketissa `worker/`-kansiossa. Yksi vaihtoehto on Cloudflare Workers -palvelu, jolle on saatavissa maksuton käyttömäärätaso; tarkista oman tilisi suunnitelma ja rajat: https://developers.cloudflare.com/workers/platform/limits/.

**Haul.FM:n palvelinta ei saatu testausympäristöstä tavoitettua.** Worker-koodi on testattu simuloiduilla Icecast- ja ICY-vastauksilla, mutta todellisen lähetyksen vastaanotto ja Cloudflare-yhteensopivuus täytyy varmistaa julkaisun jälkeen.

## A. Julkaise rajapinta Cloudflare Workersiin

1. Kirjaudu Cloudflare-tilillesi. Node.js:n on oltava käytettävissä tietokoneella (tai Google Cloud Shellissä).
2. Avaa komentorivi **projektin `worker`-kansiossa**.
3. Suorita:

   ```bash
   npx wrangler@latest login
   npx wrangler@latest deploy
   ```

4. Hyväksy Cloudflare-kirjautuminen. `wrangler deploy` näyttää HTTPS-osoitteen, esimerkiksi `https://haulfm-overlay-api.oma-tunnus.workers.dev`.
5. Kokeile: `https://haulfm-overlay-api.oma-tunnus.workers.dev/api/nowplaying`.

Palautteen pitäisi olla JSON-muotoinen, esimerkiksi:

```json
{"status":"live","title":"Kappale","artist":"Artisti","artwork":null,"duration":null,"first_seen":1790000000,"last_checked":1790000000}
```

Jos vastauksessa näkyy `"status":"offline"`, Cloudflare ei tavoita Haul.FM:n palvelinta tai radioasema ei vastaa. Jos vastauksessa näkyy `"status":"no_metadata"`, lähetys tavoitettiin mutta siitä ei saatu kappalenimeä.

**Muista:** Cloudflare Worker voi olla julkisesti käytettävissä. Koodi hyväksyy vain ennalta määritellyt Haul.FM- ja iTunes-lähteet, eikä sisällä salasanoja tai muokattavaa proxy-kohdetta.

## B. Yhdistä GitHub Pages -sivu rajapintaan

Muokkaa `docs/config.js`:

```js
window.HAULFM_CONFIG = {
  apiUrl: 'https://haulfm-overlay-api.oma-tunnus.workers.dev/api/nowplaying'
};
```

Käytä **omaa** Workerin todellista osoitetta. Älä jätä esimerkkiarvoa. Jos haluat testata ilman `config.js`-muutosta, lisää osoite URL:iin `?api=https%3A%2F%2F...` (URL-koodattuna). Testinäkymä avautuu `?demo=1` ilman Worker-palvelinta.

## C. Julkaise tiedostot GitHubiin

Tavoiteltu uusi julkinen repo: `Walleyfire/haul-fm-stream-overlay`.

**Vaihtoehto 1 — GitHub-verkkosivu:**
1. Repositorio on jo luotu: https://github.com/Walleyfire/haul-fm-stream-overlay.
2. Tiedostot ovat jo repositorion juuressa (`docs/`, `worker/` ja `README.md`).
3. Avaa repo → **Settings → Pages**.
4. Valitse **Deploy from a branch**, branch **main**, folder **/docs**, paina **Save**.
5. GitHub Pages -osoite on julkaisun onnistuttua `https://walleyfire.github.io/haul-fm-stream-overlay/`.

**Vaihtoehto 2 — Git + GitHub CLI:**

```bash
cd HaulFM_Stream_Overlay_GitHub_Pages_v2.0.0
git init -b main
git add .
git commit -m "Publish Haul.FM Stream Overlay for GitHub Pages"
gh auth login
gh repo create haul-fm-stream-overlay --public --source=. --remote=origin --push
```

Avaa sitten GitHubista **Settings → Pages → Deploy from a branch → main → /docs → Save**. Jos repolla on sama nimi jo valmiina, älä luo uutta; aseta Git-etäosoite ja puske muutokset olemassa olevaan repoon.

GitHubin ohje: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

Päivitä `docs/config.js` ja julkaise muutos tarvittaessa komennolla:

```bash
git add docs/config.js
git commit -m "Configure live Haul.FM metadata endpoint"
git push
```

## D. Lisää OBS Studioon

OBS Studio → **Lähteet → + → Selain**:

| Asetus | Arvo |
|---|---|
| URL | `https://walleyfire.github.io/haul-fm-stream-overlay/` |
| Leveys | `580` |
| Korkeus | `170` |

Voit käyttää osoitteessa myös `?scale=1.2`; suurenna silloin selainlähteen mittoja vastaavasti. Testaa aluksi selaimessa `?demo=1`. OBS:n selainlähde voi vaatia päivittämistä, kun päivität `config.js`-tiedoston.

## Rakenne

```
README.md
worker/
  wrangler.toml
  src/index.js        # HTTPS-metadata-API, Cloudflare Worker
docs/
  .nojekyll
  config.js           # Cloudflare Worker -osoite
  index.html          # OBS-selainlähde
  assets/
    wordmark.png      # paikallinen varakuva
    autodj.png        # paikallinen varakuva
```

## Vianmääritys

- Sivulla näkyy “GitHub Pages: lisää kappaletietojen API-osoite”: `docs/config.js` on tyhjä. Julkaise Worker ja lisää sen HTTPS-osoite.
- Worker palauttaa `offline`: Haul.FM:n Icecast/ICY-palvelin ei vastaa tai Workersin yhteys porttiin 8000 ei onnistu. Tarkista ensin `...workers.dev/api/nowplaying`-osoite.
- `--:--` keston paikalla: kappaleelle ei löytynyt luotettavaa pituutta. Palkkia ei silloin piirretä.
- Kappalekuva jää Haul.FM:n kuvakkeeksi: lähetyksen tiedoista tai iTunesin hausta ei löydy luotettavaa kansikuvaa.
- Yläkulman Haul.FM-logo: käytössä ensisijaisesti `https://haul.fm/brand/wordmark-275.webp`; jos se ei avaudu, mukaan pakattu paikallinen `wordmark.png`.

## Versiohistoria

- **2.0.0 (GitHub Pages)** — staattinen GitHub Pages -julkaisu `docs/`-kansiosta, HTTPS-rajapinta Cloudflare Workerilla, Pagesin alihakemiston kanssa toimivat suhteelliset kuvapolut, alkuperäisten 1.2.6-ulkoasu- ja etenemissääntöjen säilytys, testitila `?demo=1` ja asennusohjeet.
- **1.2.6 (paikallinen)** — ulkovarjoton kortti ja läpinäkyvät kulmat; kappaleen kansikuva ja varakuva; aikateksti ja palkki vain tunnetulla kestolla.

Ei Haul.FM:n tai HaulMP:n virallinen julkaisu. Ulkoasun idea: https://github.com/Tumppi066/truckersfm-stream-overlay.
