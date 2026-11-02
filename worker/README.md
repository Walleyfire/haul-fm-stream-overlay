# Haul.FM - kappaletietojen välipalvelu (Cloudflare Worker)

Tämä Worker tekee pyynnöt Haul.FM:n Icecast-palvelimelle HTTPS-osoitteen takaa. 
Sivu käyttää sitä hakemalla `/api/nowplaying`-osoitetta 12 sekunnin välein.

Asennusohje on projektin juuressa olevassa README.md:ssä.

**Huom:** Haul.FM:n HTTP-portti 8000 ei ollut testausympäristöstä käytettävissä. 
Jos Worker ei saa sieltä vastausta, tilanne näkyy offline-tilana. Workers.dev-osoitetta ei ole vielä luotu.
