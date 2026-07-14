# Bookwormin käyttöopas

## Johdanto

Bookworm on asiakirjanlukija, jonka avulla voit lukea PDF-, ePub-, MOBI- ja monia muita asiakirjamuotoja käyttäen monipuolista mutta yksinkertaista ja helppokäyttöistä käyttöliittymää.

Bookworm tarjoaa runsaasti työkaluja asiakirjojen lukemiseen. Voit etsiä asiakirjasta, lisätä kirjanmerkkejä ja korostaa mielenkiintoista sisältöä, käyttää teksti puheeksi -toimintoa ja muuntaa skannatut asiakirjat pelkäksi tekstiksi tekstintunnistuksen avulla.

Bookworm toimii Windows-käyttöjärjestelmässä. Se toimii hyvin suosittujen ruudunlukijoiden, kuten NVDA:n ja JAWSin, kanssa. Vaikka mikään ruudunlukija ei olisi käytössä, Bookworm rd:\bookworm\bookworm
voi toimia puhuvana sovelluksena sisäänrakennettuja tekstistä puheeksi -ominaisuuksia hyödyntäen.

## Ominaisuudet

* Tuki yli 15 asiakirjamuodolle, kuten ePub, PDF, MOBI ja Microsoft Word.
* Rakenteellinen navigointi otsikoiden, luetteloiden, taulukoiden ja sisennettyjen lainausten välillä siirtymiseen pikanavigointikomentojen avulla.
* Koko tekstistä hakeminen mukautettavilla asetuksilla.
* Kehittyneet ja helppokäyttöiset merkintätyökalut. Voit lisätä nimettyjä kirjanmerkkejä merkitsemään mielenkiintoisia kohtia tekstissä myöhempää käyttöä varten ja lisätä kommentteja kiinnostavan ajatuksen vangitsemiseksi tai luoda yhteenvedon sisällöstä tietyssä tekstin kohdassa. Voit siirtyä nopeasti tiettyyn kommenttiin ja tarkastella sitä. Voit myös viedä kommentit tekstitiedostoon tai HTML-asiakirjaan myöhempää käyttöä varten.
* PDF-asiakirjojen sivujenkatselutyyleinä pelkkä teksti ja renderöidyt, zoomattavat kuvat.
* Tekstintunnistustoiminto tekstin poimimiseen skannatuista asiakirjoista ja kuvista. Bookworm tukee Windows 10:n sisäänrakennettua, avoimen lähdekoodin Tesseract OCR -moottoria sekä VIVO General OCR- ja tehokasta Baidu AI Cloud OCR -palvelua.
* Sanojen määritelmien etsiminen ja Wikipedia-artikkeleiden lukeminen.
* Sisäänrakennettu verkkoartikkelien poimija, jonka avulla voit avata URL-osoitteita ja poimia sivulta automaattisesti pääartikkelin.
* Navigointi sisällysluettelon avulla laajasti kaikissa asiakirjamuodoissa.
* Kirjojen ääneen lukeminen tekstistä puheeksi -toiminnolla, jonka asetuksia voi muokata ääniprofiileilla.
* Tekstin zoomaus tavallisilla lähennä-, loitonna- ja palautuskomennoilla.
* Asiakirjojen vienti pelkäksi tekstiksi.

## Asennus

Lataa Bookworm [sen viralliselta verkkosivulta.](https://github.com/blindpandas/bookworm)

Bookworm on saatavana kolmessa muodossa:

* 32-bittinen asennusohjelma tietokoneille, joissa on 32- tai 64-bittinen Windows
* 64-bittinen asennusohjelma tietokoneille, joissa on 64-bittinen Windows
* Massamuistiversio muistitikulta käytettäväksi

Jos järjestelmässäsi on asennettuna vanhoja SAPI 5 -puheääniä ja haluat käyttää niitä Bookwormissa, suosittelemme Bookwormin 32-bittisen version asentamista tai 32-bittisen massamuistiversion käyttöä.

Lataa itsellesi sopiva versio. Mikäli valitsit asennettavan version, suorita .exe-tiedosto ja seuraa näytölle tulevia ohjeita. Jos valitsit massamuistiversion, pura pakattu tiedosto haluamaasi kansioon ja käynnistä Bookworm suorittamalla bookworm.exe-tiedosto.


## Käyttö

### Asiakirjan avaaminen

Voit avata asiakirjan valitsemalla Tiedosto-valikosta Avaa. Vaihtoehtoisesti voit käyttää pikanäppäintä Ctrl+O. Käytitpä kumpaa tapaa tahansa, näkyviin tulee tuttu Avaa tiedosto -valintaikkuna. Etsi haluamasi asiakirja ja avaa se napsauttamalla Avaa-painiketta.

### Lukuikkuna

Bookwormin pääikkuna koostuu seuraavista osista:

1. Sisällysluettelo: Tämä osa näyttää asiakirjan luvut. Sen avulla voit tutkia sisällön rakennetta. Liiku lukujen välillä pystysuuntaisilla nuolinäppäimillä ja siirry tiettyyn lukuun painamalla Enteriä.

2. Tekstinäkymä: Tämä osa sisältää nykyisen sivun tekstin. Liiku tekstissä tavallisilla lukukomennoilla. Lisäksi voit käyttää seuraavia pikanäppäimiä:

* Enter: siirry nykyisen luvun seuraavalle sivulle
* Askelpalautin: siirry nykyisen luvun edelliselle sivulle
* Kun kohdistin on ensimmäisellä rivillä, ylänuolen painaminen kahdesti peräkkäin siirtää edelliselle sivulle.
* Kun kohdistin on viimeisellä rivillä, alanuolen painaminen kahdesti peräkkäin siirtää seuraavalle sivulle.
* Alt+Home: siirtää nykyisen luvun ensimmäiselle sivulle
* Alt+End: siirtää nykyisen luvun viimeiselle sivulle
* Alt+Page down: siirtää seuraavaan lukuun
* Alt+Page up: siirtää edelliseen lukuun
* F2: siirry seuraavaan kirjanmerkkiin
* Vaihto+F2: siirry edelliseen kirjanmerkkiin
* F8: siirry seuraavaan kommenttiin
* Vaihto+F8: siirry edelliseen kommenttiin
* F9: siirry seuraavaan korostukseen
* Vaihto+F9: siirry edelliseen korostukseen
* Ctrl+Enter: avaa mikä tahansa asiakirjan sisäinen tai ulkoinen linkki. Sisäisiä linkkejä on  joidenkin asiakirjamuotojen sisällysluetteloissa, kun taas ulkoiset ovat tavallisia selaimessa avattavia. Linkin tyypistä riippuen suoritetaan jompi kumpi seuraavista toiminnoista. Jos linkki on sisäinen eli osa sisällysluetteloa, silloin yllä olevan näppäinkomennon painaminen siirtää kohdistuksen haluttuun asiakirjan kohtaan. Jos linkki on ulkoinen, näppäinkomento avaa sen järjestelmän oletusselaimessa.

### Kirjanmerkit ja kommentit

Bookworm mahdollistaa merkintöjen tekemisen avoimeen asiakirjaan. Voit lisätä kirjanmerkin muistaaksesi tietyn sijainnin asiakirjassa ja siirtyä sitten nopeasti siihen. Lisäksi voit lisätä kommentin ajatuksen vangitsemiseksi tai tehdä yhteenvedon sisällöstä.

#### Kirjanmerkkien lisääminen

Lisää kirjanmerkki painamalla Ctrl+B tai valitsemalla Merkinnät-valikosta Lisää kirjanmerkki -vaihtoehto. Kirjanmerkki lisätään nykyiseen kohdistimen sijaintiin. Vaihtoehtoisesti voit lisätä nimetyn kirjanmerkin painamalla Ctrl+Vaihto+B (tai valitsemalla Merkinnät-valikosta Lisää nimetty kirjanmerkki), jonka jälkeen avautuvassa ikkunassa kysytään kirjanmerkin nimeä.

#### Kirjanmerkkien näyttäminen

Siirry Merkinnät-valikkoon ja valitse Näytä kirjanmerkit -vaihtoehto. Näyttöön tulee valintaikkuna, jossa lisätyt kirjanmerkit näytetään. Minkä tahansa kirjanmerkkiluettelossa olevan kohteen napsauttaminen siirtää heti kyseisen kirjanmerkin kohdalle. Vaihtoehtoisesti voit siirtyä nopeasti kirjanmerkkien välillä F2- ja Vaihto+F2-pikanäppäimillä, jotka siirtävät suoraan siihen kohdistimen sijaintiin, johon kirjanmerkki viittaa.

#### Kommenttien lisääminen

Lisää kommentti painamalla Ctrl+M tai valitsemalla Merkinnät-valikosta Lisää kommentti -vaihtoehto. Bookworm kysyy kommentin sisältöä. Kirjoita haluamasi kommentti ja napsauta OK. Kommentti lisätään nykyiseen kohdistimen sijaintiin.

Bookworm ilmoittaa sivulla olevasta kommentista lyhyellä merkkiäänellä.

#### Kommenttien hallinta

Valitse Tallennetut kommentit -vaihtoehto Merkinnät-valikosta. Näyttöön tulee valintaikkuna, jossa lisätyt kommentit näytetään. Napsauttamalla mitä tahansa kohtaa kommenttiluettelossa siirryt välittömästi kyseisen kommentin kohdalle. Näytä-painiketta napsauttamalla avautuu valintaikkuna, jossa näkyy valitun kommentin tunniste ja sisältö.

Vaihtoehtoisesti voit napsauttaa Muokkaa-painiketta muuttaaksesi valitun kommentin tunnistetta ja sisältöä, painaa F2 muokataksesi valitun kommentin tunnistetta tai painaa Del-näppäintä tai Alt+P-pikanäppäintä poistaaksesi valitun kommentin.

#### Kommenttien vienti

Kommentit viedään tekstitiedostoon tai selaimessa avattavaan HTML-asiakirjaan. Vaihtoehtoisesti Bookworm mahdollistaa kommenttien viennin Markdown-muotoon, joka on tehokäyttäjien keskuudessa suosittu rakenteellisten asiakirjojen tekstimuoto.

Vie kommentit seuraavasti:

1. Valitse Merkinnät-valikosta Tallennetut kommentit.
2. Etsi avautuvasta valintaikkunasta Vie-painike ja paina Enter tai avaa vaihtoehtoisesti vientivalikko pikanäppäimellä Alt+I.

Tämän jälkeen ovat käytettävissä seuraavat vaihtoehdot, joista voit valita tai jättää valitsematta haluamasi:

* Sisällytä kirjan nimi: Tämän vaihtoehdon avulla voit sisällyttää kirjan nimen lopulliseen tulostiedostoon  kommentteja viedessäsi.
* Sisällytä luvun otsikko: Vaihtoehto, jota käytetään sisällyttämään sen luvun otsikko, johon kommentti on jätetty.
* Sisällytä sivunumero: Tätä vaihtoehtoa käytetään sisällyttämään sivunumerot, joille kommentti on jätetty.
* Sisällytä tunnisteet: Tätä vaihtoehtoa käytetään sisällyttämään tai jättämään pois kommenttitunnisteet, jotka on luotu merkintää tehtäessä.

Kun olet määrittänyt oikeat vaihtoehdot tarpeidesi mukaan, valitse tiedoston tallennusmuoto, joita on tällä hetkellä kolme: pelkkä teksti, Html ja Markdown.
Tallennusmuodon valitsemisen jälkeen näkyviin tulee "Kohdetiedosto"-niminen ei-muokattava tekstikenttä, joka  on oletusarvoisesti tyhjä. Paina Selaa-painiketta tai vaihtoehtoisesti pikanäppäintä Alt+S avataksesi Resurssienhallinnan ikkunan, jossa voit  määrittää tiedostonimen ja kansion, johon tiedosto tallennetaan.
Tiedostonimeä ja kansiota määritettäessä on käytettävissä "Avaa tiedosto viennin jälkeen" -valintaruutu, jonka ollessa valittuna Bookworm avaa kohdetiedoston automaattisesti tallennuksen jälkeen. Poista tämän valintaruudun valinta, jos et halua avata tallennettua tiedostoa automaattisesti, ja paina sen jälkeen OK. Tiedosto tallennetaan määritettyyn kansioon ja voit avata sen joko Bookwormilla tai millä tahansa muulla tekstimuokkaimella, kuten Muistiolla.

## Tekstintunnistus

Bookworm voi tunnistaa ja poimia tekstiä kuvista ja skannatuista asiakirjoista tehokkaiden ja joustavien tekstintunnistusominaisuuksiensa avulla. Tämä on erityisen hyödyllistä, kun halutaan tehdä kuviin perustuvat PDF-tiedostot tai asiakirjakuvat täysin luettaviksi ja haettaviksi. Bookworm tukee useita tekstintunnistusmoottoreita, jolloin voit valita tarpeisiisi parhaiten sopivan.

Tekstintunnistustoiminnot löytyvät valikkorivin Tekstintunnistus-valikosta. Päätoiminnot ovat:
* **Tunnista nykyinen sivu (`F4`)**: Suorittaa tekstintunnistuksen asiakirjan nykyiselle sivulle.
* **Automaattinen tekstintunnistus (`Ctrl+F4`)**: Suorittaa tekstintunnistuksen automaattisesti jokaiselle uudelle sivulle siirtyessäsi asiakirjassa eteenpäin.
* **Kuva tekstiksi...**: Mahdollistaa kuvatiedoston valitsemisen ja tekstin poimimisen siitä.

Bookworm tukee seuraavia tekstintunnistusmoottoreita:

### Windows 10:n/11:n tekstintunnistus

Jos käytät Windows 
10:tä tai uudempaa, Bookworm voi hyödyntää käyttöjärjestelmään sisäänrakennettua laadukasta tekstintunnistusmoottoria. Tätä käytetään oletuksena, ja se on heti valmis käyttöön ilman lisämäärityksiä. Tunnistuksen tulokset ovat erinomaisia varsinkin järjestelmään asennetuilla kielillä.

### Tesseract OCR

Bookworm mahdollistaa vanhempien Windows-versioiden käyttäjille tai laajempaa kielitukea tarvitseville Googlen ylläpitämän avoimen lähdekoodin Tesseract OCR -tekstintunnistusmoottorin käytön.

Voit asentaa sen Bookwormiin seuraavasti:
1. Valitse `Tiedosto > Asetukset...` ja siirry **Tekstintunnistus**-kategoriaan.
2. Paina "Tesseract OCR" -osiossa "Lataa Tesseract OCR -tekstintunnistusmoottori" -painiketta ja noudata näytölle tulevia ohjeita.
3. Asennuksen valmistuttua voit hallita käytössä olevia tekstintunnistuskieliä painamalla "Hallitse Tesseract OCR:n kieliä" -painiketta.

### VIVO General OCR

Yhteistyössä VIVOn (vivo.com.cn) ja NVDA:n kiinalaisyhteisön (NVDA-CN) kanssa Bookworm tarjoaa ilmaisen VIVO OCR -tekstintunnistusmoottorin, joka tunnistaa laadukkaasti sekä kiinan- että englanninkielistä tekstiä.

VIVO OCR:n käyttöön tarvitaan maksuton NVDA-CN-tili.

#### Käyttöönotto

1. **Tilin luonti**: Mene rekisteröintisivulle [https://nvdacn.com/admin/register.php](https://nvdacn.com/admin/register.php).
    *   Rekisteröintisivu on kiinankielinen, joten selaimen käännöstoiminnon käyttö on suositeltavaa.
    *   Sivusto kysyy käyttäjänimeä, salasanaa ja toimivaa sähköpostiosoitetta. Tallenna salasana turvallisesti, sillä automaattinen salasanan palautus ei vielä ole käytettävissä.
2. **Sähköpostiosoitteen vahvistaminen**: Etsi Saapuneet-kansiostasi vahvistusviesti ja napsauta siinä olevaa linkkiä tilin aktivoimiseksi.
3. **Asetusten määrittäminen Bookwormissa**: Avaa Bookwormin asetukset valitsemalla `Tiedosto > Asetukset...` tai painamalla `Ctrl+Vaihto+P`.
4. **Tunnusten syöttäminen**: Siirry **Tekstintunnistus**-asetuskategoriaan ja syötä käyttäjänimi ja salasana "VIVO OCR" -osioon.
5. **Moottorin valinta**: Valitse oletusmoottoriksi VIVO OCR "Tekstintunnistuksen oletusmoottori" -luettelosta.

Kun asetukset on määritetty, VIVO-moottoria käytetään kaikissa Bookwormin tekstintunnistustoiminnoissa.

Tilin käyttöön liittyvissä ongelmissa voit ottaa yhteyttä NVDA-CN-tiimiin sähköpostitse osoitteella `support@nvdacn.com`.

### Baidu AI Cloud OCR

Paras tarkkuus saavutetaan erityisesti kiinan- ja englanninkielisessä sekatekstissä tai monimutkaisissa sivuasetteluissa Baidu AI Cloud OCR:n avulla. Tämä verkkopohjainen Palvelu tarjoaa sekä **vakion**- että **korkean tarkkuuden** moottorin.

Baidu OCR -moottoreiden käyttämiseksi tarvitaan ilmainen API- ja salainen avain.

#### Käyttöönotto

1. **Tilin rekisteröinti**: Mene [Baidu AI Cloud OCR:n sivulle](https://ai.baidu.com/tech/ocr/general) ja luo tili saadaksesi avaimet. Palvelu tarjoaa runsaan ilmaiskäytön, joka sisältää tuhansia tunnistuskutsuja kuukaudessa.
2. **Asetusten määrittäminen Bookwormissa**: Kun olet saanut API- ja salaisen avaimen, avaa Bookwormin asetukset valitsemalla `Tiedosto > Asetukset...` tai painamalla `Ctrl+Vaihto+P`.
3. **Avainten syöttäminen**: Siirry **Tekstintunnistus**-asetuskategoriaan ja täytä Baidu OCR -osiosta löytyvät "API-avain"- sekä "Salainen avain" -kentät.
4. **Moottorin valinta**: Avaimien syöttämisen jälkeen voit valita oletusmoottoriksi joko Baidu General OCR (vakio) tai Baidu General OCR (tarkka) "Tekstintunnistuksen oletusmoottori" -luettelosta.

Kun asetukset on määritetty, Baidu-moottoria käytetään kaikissa Bookwormin OCR-toiminnoissa.

### Ääneen lukeminen

Bookworm tukee avatun asiakirjan sisällön ääneen lukemista asennettua tekstistä puheeksi -ääntä käyttäen. Paina F5 aloittaaksesi puhumisen, F6 keskeyttääksesi tai jatkaaksesi ja F7 lopettaaksesi kokonaan.

Voit määrittää puheen kahdella tavalla:
1. Ääniprofiililla: Ääniprofiili sisältää muokkaamasi puheasetukset. Voit ottaa ääniprofiilin käyttöön tai poistaa sen käytöstä milloin tahansa. Ääniprofiilit otetaan käyttöön Puhe-valikosta tai painamalla Ctrl+Vaihto+V. Bookwormissa on sisäänrakennettuja esimerkkiääniprofiileja.
2. Yleisillä puheasetuksilla: Näitä asetuksia käytetään oletusarvoisesti, kun mikään ääniprofiili ei ole käytössä. Voit määrittää yleiset puheasetukset sovelluksen asetuksista.

Voit siirtyä taakse- tai eteenpäin kappale kerrallaan ääneen lukemisen aikana painamalla Alt- sekä vasenta tai oikeaa nuolinäppäintä.

### Medianäppäinten toiminta

Mediapainikkeet on liitetty tekstistä puheeksi -ominaisuuden ydintoimintoihin:

* **▶️ Toista/Pysäytä-näppäin**: Tekstistä puheeksi -ominaisuuden toisto, pysäytys tai jatkaminen.
* **⏭️ Seuraava kappale -näppäin**: Toimii "Kelaa eteenpäin" -komentona siirtäen **seuraavaan tekstikappaleeseen** (vastaa näppäinyhdistelmää `Alt+Oikea nuoli`).
* **⏮️ Edellinen kappale -näppäin**: Toimii "Kelaa taaksepäin" -komentona siirtäen **edelliseen tekstikappaleeseen** (vastaa näppäinyhdistelmää `Alt+Vasen nuoli`).

Toiminto tukee kahta eri tilaa:

1.  **Paikallistila (oletus)**: Medianäppäimet toimivat vain, kun Bookwormin ikkuna on aktiivisena.
2.  **Yleistila (valinnainen)**: Käyttäjä voi ottaa tämän käyttöön valitsemalla "**Ota käyttöön yleiset medianäppäimet**" -valintaruudun kohdassa `Asetukset > Lukeminen`. Tämä mahdollistaa toiston hallinnan kaikkialla käyttöjärjestelmässä myös Bookwormin ollessa taustalla.

Tätä asetusta on mahdollista muuttaa ilman sovelluksen uudelleenkäynnistystä.

**Huom: Medianäppäimet saattavat toimia epäluotettavasti, jos käynnissä on useita mediasovelluksia samanaikaisesti riippumatta siitä, onko järjestelmänlaajuinen tila käytössä vai ei.**

### Lukutyylin määrittäminen

Näiden asetusten avulla voit hienosäätää Bookwormissa puheasetusten lisäksi lukutyyliä. Kaikki seuraavat asetukset löytyvät sovellusasetusten Lukeminen-kategoriasta.

* Kun Toista-painiketta painetaan: Tämä asetus määrittää, mitä tapahtuu, kun laitat Bookwormin "toistamaan" nykyisen asiakirjan. Valittavissa ovat vaihtoehdot "Lue koko kirja", "Lue nykyinen luku" tai "Lue nykyinen sivu". Oletusarvoisesti Bookworm lukee koko asiakirjan, ellet keskeytä sitä sivun tai nykyisen luvun lopussa.
* Aloita lukeminen: Tämä asetus määrittää kohdan, josta ääneen lukeminen aloitetaan. Voit aloittaa lukemisen "kohdistimen sijainnista" tai "nykyisen sivun alusta".
* Ääneen lukeminen: Nämä asetukset määrittävät, miten Bookworm käyttäytyy ääneen luettaessa. Voit ottaa minkä tahansa seuraavista asetuksista käyttöön tai poistaa ne käytöstä valitsemalla tai poistamalla valinnan sitä vastaavasta valintaruudusta:

* Puhu sivunumero: Tekstistä puheeksi -ääni lukee jokaisen sivun numeron siirtyessäsi sille.
* Ilmoita lukujen loppumisesta: Tekstistä puheeksi -ääni ilmoittaa, kun luku on luettu.
* Pyydä vaihtamaan puheääneen, joka tukee nykyisen kirjan kieltä: Tämä asetus määrittää, varoittaako Bookworm yhteensopimattomasta puheäänestä, mikä tapahtuu oletusarvoisesti, jos valitun tekstistä puheeksi -äänen kieli on eri kuin avoimen asiakirjan kieli.
* Korosta puhuttava teksti: Jos tämä asetus on käytössä, senhetkinen puhuttava teksti korostetaan visuaalisesti.
* Valitse puhuttava teksti: Jos tämä asetus on käytössä, senhetkinen puhuttava teksti valitaan. Näin voit esim. painaa Ctrl+C kopioidaksesi puhuttavan kappaleen.



### Jatkuvan luvun tila

Bookwormin sisäänrakennettujen tekstistä puheeksi -ominaisuuksien lisäksi voit hyödyntää ruudunlukijan jatkuvan luvun toimintoa. Bookworm tukee tätä jatkuvan luvun tilansa avulla. Se on oletusarvoisesti käytössä, ja voit poistaa sen käytöstä sovellusasetusten Lukeminen-kategoriasta. Kun jatkuvan luvun tila on käytössä, sivuja käännetään automaattisesti ruudunlukijan edetessä asiakirjassa.

Huom: Ominaisuuden tämänhetkisen toteutustavan vuoksi odotettavissa on seuraavia rajoituksia:

* Jatkuva luku keskeytyy tyhjälle sivulle siirryttäessä. Jos siirryit tyhjälle sivulle, siirry vain ei-tyhjälle sivulle ja ota ruudunlukijan jatkuvan luvun toiminto uudelleen käyttöön.
* Kohdistimen siirtäminen sivun viimeisen merkin kohdalle vaihtaa heti seuraavalle sivulle.



### Nykyisen sivun renderöidyn version katselu

Bookwormin avulla voit tarkastella asiakirjan renderöityä versiota. Kun asiakirja on avattu, voit painaa Ctrl+R tai valita Asiakirja-valikosta Renderöi sivu -vaihtoehdon. Tätä kutsutaan renderöintinäkymäksi.

Kun olet renderöintinäkymässä, voit käyttää tavallisia zoomauskomentoja sivun suurentamiseen ja pienentämiseen:

* Ctrl+=: Suurenna
* Ctrl+-: Pienennä
* Ctrl+0: Palauta zoomauksen oletustaso

Voit käyttää yllä mainittuja asiakirjojen navigointikomentoja myös renderöintinäkymässä liikkumiseen. Voit myös sulkea tämän näkymän ja palata tekstimuotoiseen oletusnäkymään painamalla Esc-näppäintä.


### Tietylle sivulle siirtyminen

Voit siirtyä tietylle sivulle avoimessa asiakirjassa painamalla Ctrl+G tai valitsemalla Haku-valikosta Siirry sivulle... -vaihtoehto avataksesi Siirry sivulle -valintaikkunan. Kirjoita siihen sen sivun numero, johon haluat siirtyä ja hyväksy siirtyminen painamalla Enteriä. Valintaikkunassa näytetään myös nykyisen asiakirjan sivujen kokonaismäärä.

 
### Asiakirjasta etsiminen

Voit etsiä tiettyä hakusanaa tai tekstin osaa avoimesta asiakirjasta painamalla Ctrl+F, joka avaa Hae asiakirjasta -valintaikkunan. Tässä valintaikkunassa voit kirjoittaa etsimäsi tekstin sekä muuttaa haun valintoja. Seuraavat vaihtoehdot ovat käytettävissä:

* Sama kirjainkoko: Haku ottaa huomioon hakusanan kirjainkoon.
* Vain kokonaiset sanat: Hakusanan on löydyttävä kokonaisena sanana, eli ei osana toista sanaa.
* Hakualue: Tämän avulla voit rajoittaa haun tietyille sivuille tai tiettyyn lukuun.

Kun olet napsauttanut Hae asiakirjasta -valintaikkunassa OK-painiketta, toinen, hakutulokset näyttävä valintaikkuna avautuu. Minkä tahansa hakutulosluettelossa olevan kohteen napsauttaminen siirtää heti kyseisen tuloksen kohdalle, jossa hakusana on korostettuna.

Jos olet sulkenut hakutulosikkunan, voit siirtyä viimeisimmän haun seuraavaan ja edelliseen esiintymään painamalla F3 ja Vaihto+F3.


## Tiedostokytkentöjen hallinta

Tiedostokytkentöjen hallinta -painikkeella, joka löytyy sovellusasetusten Yleiset-kategoriasta, voit hallita Bookwormiin kytkettyjä tiedostotyyppejä. Tiedostojen kytkeminen Bookwormiin tarkoittaa, että tiedostot avautuvat oletusarvoisesti Bookwormissa napsauttaessasi niitä Windowsin Resurssienhallinnassa. Tämä valintaikkuna näytetään aina ohjelman ensimmäisen käynnistyksen yhteydessä, ja se on käytettävissä vain asennetussa versiossa. Tiedostokytkentöjen tekeminen ei ole mahdollista massamuistiversiossa, joten siinä tätä hallintapainiketta ei ole. Jos kuitenkin haluat Bookwormin massamuistiversion oletusarvoisesti avaavan tuettuja asiakirjoja, sinun on käytettävä muutamia kiertoteitä.

Tiedostokytkentöjen hallinnassa on käytettävissä seuraavat vaihtoehdot:

* Kytke kaikki: Tämä muuttaa asetuksiasi siten, että kaikki tuetut tiedostotyypit avautuvat Bookwormissa.
* Poista kaikki kytkennät: Tämä poistaa aiemmin rekisteröidyt tiedostokytkennät.
* Yksittäiset painikkeet jokaiselle tuetulle tiedostotyypille: Painikkeen napsauttaminen kytkee sitä vastaavan tiedostotyypin Bookwormiin.


## Bookwormin päivittäminen

Bookworm tarkistaa uuden version saatavuuden oletusarvoisesti aina käynnistyessään. Tämä varmistaa, että saat uusimman version niin pian kuin mahdollista. Voit poistaa tämän toiminnon käytöstä sovellusasetuksista. Myös päivitysten manuaalinen tarkistaminen on mahdollista valitsemalla Ohje-valikosta Tarkista päivitykset -vaihtoehto.

Kun uusi versio löytyy, Bookworm kysyy, haluatko asentaa sen. Jos valitset Kyllä, sovellus aloittaa päivityspaketin lataamisen ja näyttää edistymistä ilmaisevan valintaikkunan. Bookworm ilmoittaa latauksen valmistuttua, että se käynnistää itsensä uudelleen, jotta päivitys voidaan asentaa. Viimeistele päivitys painamalla OK.


## Ongelmista ilmoittaminen

Sokeina kehittäjinä vastuullamme on kehittää sovelluksia, jotka tarjoavat itsenäisyyttä meille ja sokeille ystävillemme kaikkialla maailmassa. Mikäli olet kokenut Bookwormin jollain tavalla hyödyllisenä, autathan meitä tekemään siitä entistäkin paremman. Haluamme sinun kertovan kaikista Bookwormin käytön aikana kohtaamistasi virheistä. Voit tehdä tämän luomalla virheen tiedot sisältävän ongelmaraportin [ongelmienseurannassa](https://github.com/blindpandas/bookworm/issues/). Apusi on meille erittäin arvokasta.

Varmista ennen uuden ongelmaraportin lähettämistä, että käytit Bookwormia vianmääritystilassa. Ota vianmääritystila käyttöön menemällä Ohje-valikkoon ja valitsemalla Käynnistä uudelleen vianmääritystilassa -vaihtoehto, ja yritä sen jälkeen toistaa ongelma. Useimmissa tapauksissa, kun virhe toistuu vianmääritystilan ollessa käytössä, näkyviin tulee valintaikkuna, jossa virheen tiedot näytetään. Kopioi tiedot tästä valintaikkunasta ja liitä ne ongelmaraporttiisi.

Joitakin ongelmia voi olla vaikea toistaa, koska ne häviävät, kun sovellus käynnistetään uudelleen. Tällöin on aivan hyväksyttävää ilmoittaa ongelmasta ilman vianmääritystilan antamia yksityiskohtaisia tietoja. Varmista vain, että sisällytät mahdollisimman paljon tietoa järjestelmästäsi ja käyttötilanteestasi.


## Uutiset ja päivitykset

Vieraile sovelluksen kotisivulla osoitteessa [github.com/blindpandas/bookworm](https://github.com/blindpandas/bookworm/) pysyäksesi ajan tasalla viimeisimmistä Bookwormia koskevista uutisista. Voit myös seurata pääkehittäjän, Musharraf Omerin, X-tiliä [@mush42](https://x.com/mush42/).


## Lisenssi

**Bookworm** on copyright (c) 2019-2026 Musharraf Omer sekä muut kehityksen tukijat. Se on suojattu [MIT-lisenssillä](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
