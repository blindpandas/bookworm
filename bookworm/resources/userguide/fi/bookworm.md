# Bookwormin käyttöohje

## Johdanto

Bookworm on asiakirjojen lukemiseen tarkoitettu sovellus, jolla voit lukea PDF-, EPUB- ja MOBI-tiedostoja sekä useita muita asiakirjamuotoja monipuolisen mutta yksinkertaisen ja erittäin saavutettavan käyttöliittymän avulla.

Bookworm tarjoaa kattavan valikoiman työkaluja asiakirjojen lukemiseen. Voit etsiä tekstiä asiakirjasta, lisätä kirjanmerkkejä ja korostuksia kiinnostaviin kohtiin, lisätä kommentteja, käyttää tekstistä puheeksi -toimintoa, järjestellä asiakirjoja Bookwormin kirjahyllyyn, avata verkkosivujen artikkeleita ja muuntaa skannattuja asiakirjoja muotoilemattomaksi tekstiksi tekstintunnistuksen avulla.

Bookworm on tarkoitettu Windows -käyttöjärjestelmälle, ja se toimii sujuvasti esimerkiksi NVDA- ja JAWS-ruudunlukijoilla. Käyttö on mahdollista myös ilman erillistä ruudunlukijaa, sillä sovelluksessa on  sisäänrakennettuja tekstistä puheeksi -ominaisuuksia.

## Ominaisuudet

* Tukee yli 20 asiakirjamuotoa, kuten EPUB, PDF, MOBI, Microsoft Word, HTML, muotoilematon teksti sekä Markdown.
* Tukee rakenteellista navigointia pikanavigointikomennoilla, joiden avulla voi siirtyä otsikoiden, linkkien, luetteloiden, taulukoiden, sisennettyjen lainausten ja kuvitusten välillä.
* Tekstistä etsiminen mukautettavilla asetuksilla, kuten säännöllisillä lausekkeilla sekä sivu- tai lukualueilla.
* Edistyneet ja helppokäyttöiset merkintätyökalut. Voit lisätä nimettyjä kirjanmerkkejä, kommentteja ja korostuksia, siirtyä nopeasti niiden välillä ja viedä kommentit tai korostukset muotoilemattomaksi tekstiksi, HTML- tai Markdown-asiakirjaksi.
* Bookworm tarjoaa kaksi erilaista sivujen katselutapaa graafista renderöintiä tukeville asiakirjoille: muotoilematon teksti ja renderöidyt, zoomattavat kuvat.
* Tukee tekstintunnistusta tekstin poimimiseksi skannatuista asiakirjoista ja kuvista. Bookwormiin on integroitu Windowsin sisäänrakennettu tekstintunnistus, avoimen lähdekoodin Tesseract OCR -moottori sekä VIVO General OCR- ja Baidu AI Cloud OCR -palvelut.
* Sisäänrakennettu verkkosivuilla olevien artikkelien poimija, jonka avulla voit avata URL-osoitteita ja poimia sivulta automaattisesti luettavan pääartikkelin.
* Tukee Wikipedian pikahakua ja mahdollistaa artikkelien avaamisen suoraan Bookwormissa.
* Bookwormin kirjahylly paikallisten asiakirjojen järjestelyyn, tiedostojen tai kansioiden tuomiseen, otsikoiden ja indeksoidun sisällön etsimiseen sekä asiakirjojen niputtamiseen offline-käyttöä varten.
* Tukee kattavasti navigointia sisällysluettelon avulla kaikissa sitä tukevissa asiakirjamuodoissa.
* Tukee kirjojen lukemista tekstistä puheeksi -toiminnon avulla. Puheäänen asetuksia voi mukauttaa ääniprofiileilla.
* Tukee tekstin zoomaamista tavanomaisilla lähennys-, loitonnus- ja palautuskomennoilla.
* Tukee kaikkien asiakirjamuotojen viemistä muotoilemattomaksi tekstitiedostoksi.

## Asennus

Voit asentaa Bookwormin vierailemalla [Bookwormin julkaisusivulla](https://github.com/blindpandas/bookworm/releases) ja lataamalla uusimman version.

Nykyiset versiot vaativat Windows 8.1 -käyttöjärjestelmän tai sitä uudemman. Windows 7:ää tai sitä vanhempia versioita ei tueta.

Bookwormista on saatavilla kolme eri versiota:

* 32-bittinen asennusohjelma 32- tai 64-bittiselle Windowsille
* 64-bittinen asennusohjelma 64-bittiselle Windowsille
* Massamuistiversio, jota voi käyttää esimerkiksi muistitikulta

Jos järjestelmääsi on asennettu vanhempia SAPI 5 -puheääniä ja haluat käyttää niitä Bookwormissa, suosittelemme asentamaan 32-bittisen version tai käyttämään 32-bittistä massamuistiversiota.

Kun olet valinnut tarpeisiisi sopivan version, lataa se tietokoneellesi. Jos latasit asennusohjelman, suorita .exe-tiedosto ja noudata näytöllä näkyviä ohjeita. Jos valitsit massamuistiversion, pura zip-paketin sisältö haluamaasi kansioon ja käynnistä sovellus suorittamalla bookworm.exe-tiedosto.

## Käyttö

### Asiakirjan avaaminen

Voit avata asiakirjan valitsemalla Tiedosto-valikosta "Avaa..."-toiminnon. Vaihtoehtoisesti voit käyttää pikanäppäintä Ctrl+O. Molemmissa tapauksissa näkyviin tulee tavanomainen tiedostonavausikkuna. Selaa asiakirjasi kohdalle ja avaa se valitsemalla "Avaa".

Tiedosto-valikosta voit myös avata uuden Bookworm-ikkunan painamalla Ctrl+N, sulkea nykyisen asiakirjan painamalla Ctrl+W tai kiinnittää nykyisen asiakirjan painamalla Ctrl+P. Kiinnitetyt ja äskettäin avatut asiakirjat löytyvät omista alavalikoistaan. Molemmat luettelot voi tyhjentää samasta valikosta.

Tiedosto-valikossa on myös Tuo-alavalikko. "Tuo QRD-tiedosto..." -toiminto tuo lukukohdan tiedot QRead-sovelluksen QRD-tiedostosta ja avaa alkuperäisen asiakirjan tallennetusta kohdasta. "Asetukset..."-toiminto avaa Bookwormin asetukset. Ne voidaan avata myös pikanäppäimellä Ctrl+Vaihto+P.

### Lukuikkuna

Bookwormin pääikkuna koostuu seuraavista osista:

1. Sisällysluettelo: Tämä osa näyttää asiakirjan luvut ja mahdollistaa sisällön rakenteen tarkastelun. Voit liikkua lukujen välillä nuolinäppäimillä ja siirtyä haluamaasi lukuun painamalla Enteriä. Kohdistuksen voi siirtää tekstinäkymästä sisällysluetteloon painamalla Ctrl+T.

2. Tekstinäkymä: Tässä osassa näytetään nykyisen sivun teksti. Voit liikkua siinä tavallisilla lukukomennoilla. Lisäksi asiakirjassa voidaan liikkua seuraavilla pikanäppäimillä:

* Enter tai Välilyönti: siirry nykyisen luvun seuraavalle sivulle
* Askelpalautin: siirry nykyisen luvun edelliselle sivulle
* Page down ja Page up: siirry nykyisellä sivulla enemmän eteen- tai taaksepäin
* Kaksi peräkkäistä ylänuolen painallusta siirtää edelliselle sivulle, kun kohdistin on sivun ensimmäisellä rivillä.
* Kaksi peräkkäistä alanuolen painallusta siirtää seuraavalle sivulle, kun kohdistin on sivun viimeisellä rivillä.
* Alt+Home: siirry nykyisen luvun ensimmäiselle sivulle
* Alt+End: siirry nykyisen luvun viimeiselle sivulle
* Alt+Page down: siirry seuraavaan lukuun
* Alt+Page up: siirry edelliseen lukuun
* F2: siirry seuraavaan kirjanmerkkiin
* Vaihto+F2: siirry edelliseen kirjanmerkkiin
* F8: siirry seuraavaan kommenttiin
* Vaihto+F8: siirry edelliseen kommenttiin
* F9: siirry seuraavaan korostukseen
* Vaihto+F9: siirry edelliseen korostukseen
* Ctrl+Enter: suorita erikoistoiminto nykyisessä kohdassa. Bookworm voi seurata sisäistä linkkiä, avata ulkoisen linkin oletusselaimessa, näyttää taulukon selattavassa valintaikkunassa tai avata upotetun kuvan.
* Ctrl+Vaihto+Enter: palaa edelliseen kohtaan sisäisen linkin seuraamisen jälkeen

3. Lukemisen edistymispalkki: Kun asetus "Näytä lukemisen edistyminen prosentteina" on otettu käyttöön, Bookworm näyttää lukemisen edistymisen tilapalkissa ja mahdollistaa asiakirjassa liikkumisen prosenttiosuuksien mukaan liukusäätimen avulla.

### Rakenteellinen navigointi

Jos avoinna olevan asiakirjan rakenne on merkitty saavutettavasti, voit liikkua elementtien välillä suoraan tekstinäkymässä. Siirry seuraavaan elementtiin painamalla sen kirjainta ja edelliseen painamalla Shift-näppäintä ja samaa kirjainta.

* h: otsikko
* 1–6: otsikkotasot 1–6
* k: linkki
* l: luettelo
* t: taulukko
* q: sisennetty lainaus
* i: kuva tai kuvitus

Vaihtoehtoisesti voit valita Asiakirja-valikosta "Elementtilista..."-toiminnon tai painaa Ctrl+F7. Elementtilistassa näytetään asiakirjan otsikot, linkit, luettelot, taulukot, sisennetyt lainaukset ja kuvat. Elementin valitseminen siirtää lukunäkymän kyseiseen kohtaan.

### Asiakirjakomennot

Asiakirja-valikon käytettävissä olevat komennot määräytyvät avoinna olevan asiakirjan perusteella:

* "Asiakirjan tiedot..." näyttää metatiedot ja asiakirjan tilastot, jos ne ovat saatavilla.
* "Elementtilista..." avaa rakenteellisen elementtilistan, johon pääsee myös pikanäppäimellä Ctrl+F7.
* "Vaihda lukutilaa..." avaa lukutilan valintaikkunan, johon pääsee myös pikanäppäimellä Ctrl+Vaihto+M. Käytettävissä olevat tilat määräytyvät asiakirjamuodon perusteella, ja tiloja ovat esim. oletustila, lukemisjärjestys, fyysinen asettelu, sivutettu tila, luvuittain lukeminen, muotoilematon teksti sekä koko teksti.
* "Renderöi sivu..." avaa nykyisen sivun renderöitynä kuvana, kun asiakirjamuoto tukee graafista esitystä. Pikanäppäimellä Ctrl+R voidaan myös käyttää.

### Kirjanmerkit, kommentit ja korostukset

Bookworm mahdollistaa merkintöjen tekemisen avoimeen asiakirjaan. Voit lisätä kirjanmerkin muistaaksesi tietyn kohdan asiakirjassa ja siirtyäksesi siihen myöhemmin nopeasti. Lisäksi voit lisätä kommentteja ajatusten tai tiivistelmien tallentamiseksi sekä korostaa valittua tekstiä myöhempää tarkastelua varten.

#### Kirjanmerkkien lisääminen

Voit lisätä kirjanmerkin asiakirjaa lukiessasi painamalla Ctrl+B tai valitsemalla Merkintä-valikosta "Lisää kirjanmerkki". Kirjanmerkki lisätään kohdistimen sijaintiin. Vaihtoehtoisesti voit lisätä nimetyn kirjanmerkin painamalla Ctrl+Vaihto+B tai valitsemalla Merkintä-valikosta "Lisää nimetty kirjanmerkki...".

#### Kirjanmerkkien tarkasteleminen

Avaa Merkintä-valikko ja valitse "Tallennetut kirjanmerkit...". Näkyviin tulee valintaikkuna, jossa lisätyt kirjanmerkit näytetään. Valitsemalla luettelosta minkä tahansa kirjanmerkin siirryt heti kyseiseen sijaintiin. Voit siirtyä lisättyjen kirjanmerkkien välillä suoraan tekstinäkymässä F2- ja Vaihto+F2-näppäimillä.

Tallennetut kirjanmerkit -ikkunassa voit nimetä valitun kirjanmerkin uudelleen painamalla F2 tai poistaa sen painamalla Delete-näppäintä.

#### Kommenttien lisääminen

Voit lisätä kommentin asiakirjaa lukiessasi painamalla Ctrl+M tai valitsemalla Merkintä-valikosta "Lisää kommentti..." -toiminnon. Sovellus pyytää kirjoittamaan kommentin sisällön. Kirjoita haluamasi teksti ja paina OK. Kommentti lisätään kohdistimen nykyiseen sijaintiin. Jos tekstiä on valittuna, kommentti liitetään valittuun tekstialueeseen.

Pidä Vaihto-näppäintä painettuna kommenttia lisätessäsi, jos haluat Bookwormin kysyvän tunnisteita kommentin luonnin jälkeen.

Bookworm ilmoittaa sivulla olevasta kommentista lyhyellä merkkiäänellä. Tätä toimintoa voi muuttaa asetusikkunan Merkintä-kategoriassa.

#### Korostusten lisääminen

Valitse tekstiä ja paina Ctrl+H tai valitse Merkintä-valikosta "Korosta valinta" tallentaaksesi valitun tekstin korostuksena. Korostus poistetaan, mikäli sama valinta on jo korostettu. Jos valinta on päällekkäinen olemassa olevan korostuksen kanssa, Bookworm laajentaa nykyistä korostusta.

Pidä Vaihto-näppäintä painettuna korostusta lisätessäsi, jos haluat Bookwormin kysyvän tunnisteita korostuksen luonnin jälkeen. Siirry seuraavaan ja edelliseen korostukseen näppäimillä F9 ja Vaihto+F9.

#### Kommenttien ja korostusten hallinta

Valitse Merkintä-valikosta "Tallennetut kommentit..." tai "Tallennetut korostukset...". Näkyviin tulee valintaikkuna, jossa tallennetut kohteet näytetään. Minkä tahansa luettelossa olevan kohteen aktivoiminen siirtää näkymän heti kyseisen kommentin kohdalle. Näytä-painiketta painamalla avautuu valintaikkuna, joka näyttää valitun kohteen tunnisteet ja sisällön.

Voit suodattaa tallennettuja kommentteja tai korostuksia tunnisteen, luvun tai sisällön mukaan. Niitä voi lajitella päivämäärän, sivun, sijainnin tai kirjan perusteella, jos kyseiset tiedot ovat saatavilla. Siirry suodattimiin painamalla F6, muokkaa tunnisteita painamalla F2, poista valittu kohde painamalla Delete tai kopioi merkinnän teksti painamalla Ctrl+C.

#### Kommenttien ja korostusten vienti

Bookworm mahdollistaa tallennettujen kommenttien ja korostusten viennin muotoilemattomaksi tekstitiedostoksi sekä HTML- tai Markdown-asiakirjaksi.

Vie kommentit tai korostukset seuraavasti:

1. Valitse Merkintä-valikosta "Tallennetut kommentit..." tai "Tallennetut korostukset...".
2. Etsi avautuvasta valintaikkunasta Vie-painike ja paina Enter, tai avaa vientivalikko pikanäppäimellä Alt+I.

Tämän jälkeen ovat käytettävissä seuraavat vaihtoehdot, joista voit valita tai jättää valitsematta haluamasi:

* Lisää kirjan nimi: tämä vaihtoehto lisää tulostiedostoon kirjan nimen.
* Lisää luvun nimi: tämä vaihtoehto lisää merkinnän sisältävän luvun nimen.
* Lisää sivunumero: tämä vaihtoehto lisää sen sivun numeron, jolla merkintä on.
* Lisää tunnisteet: tällä vaihtoehdolla voit lisätä tai jättää lisäämättä tulostiedostoon merkintöjen tunnisteet.

Kun olet määrittänyt tarpeitasi vastaavat asetukset, valitse tulostiedoston muoto, joita ovat muotoilematon teksti, HTML tai Markdown. Valitse lopuksi tulostiedosto. Jos "Avaa tiedosto viennin jälkeen" -asetus on valittuna, Bookworm avaa tulostiedoston automaattisesti tallennuksen jälkeen.

### Bookwormin kirjahylly

Bookwormin kirjahylly on paikallinen kirjasto, johon voit järjestellä Bookwormilla lukemiasi asiakirjoja. Se avataan Tiedosto-valikon "Kirjahylly"-alivalikosta valitsemalla "Avaa kirjahylly". Voit lisätä avoinna olevan paikallisen asiakirjan valitsemalla "Lisää paikalliseen kirjahyllyyn...".

Kun asiakirjoja lisätään tai tuodaan, Bookworm saattaa kysyä lukulistaan tai kokoelmiin lisäämisestä sekä siitä, lisätäänkö asiakirja koko tekstin hakuindeksiin. Asetusikkunan Kirjahylly-kategoriassa on valinta, jolla avatut kirjat voidaan lisätä automaattisesti paikalliseen kirjahyllyyn.

Paikallisen kirjahyllyn kategorioita ovat "Äskettäin lisätyt", "Luen parhaillaan", "Haluan lukea", "Suosikit", "Lukulistat", "Kokoelmat" ja "Tekijät". Kirjahyllyn Tiedosto-valikosta voit tuoda yksittäisiä asiakirjoja (myös pikanäppäimellä Ctrl+O), tuoda kaikki kansion asiakirjat, hakea kirjahyllystä, niputtaa asiakirjoja ja poistaa sellaisia asiakirjoja, joiden tiedostoja ei enää löydy.

Kirjahyllyn asiakirjaluettelossa:

* Avaa valittu asiakirja Bookwormin uudessa ikkunassa painamalla Enter.
* Nimeä valittu asiakirja uudelleen painamalla F2, jos uudelleennimeäminen on mahdollista.
* Päivitä luettelo painamalla F5.
* Siirry pikasuodattimeen painamalla Ctrl+F.
* Kun kohdistus on asiakirjaluettelossa, aloita kirjoittaminen suodattaaksesi luetteloa nimen perusteella.
* Palaa sisäkkäisestä kansiosta tai säilöstä painamalla Alt+Nuoli vasemmalle.

Kirjahyllyn pikavalikosta on mahdollista avata asiakirja Bookwormissa tai järjestelmän oletusarvoisessa lukusovelluksessa, muokata sen otsikkoa, näyttää asiakirjan tiedot, muokata lukulistaa tai kokoelmia, vaihtaa tilaa (luen parhaillaan, haluan lukea tai suosikit) sekä poistaa asiakirjan.

"Etsi kirjahyllystä..." -komento etsii tekstiä asiakirjojen nimistä ja indeksoidusta sisällöstä. Löytyneet asiakirjat voidaan avata hakutuloksista suoraan siltä sivulta ja kohdasta, josta etsitty teksti löytyi.

### URL-osoitteiden ja Wikipedian avaaminen

Bookwormilla on mahdollista avata verkkosivuja luettavina asiakirjoina. Avaa haluamasi verkkosivun osoite Valitsemalla Verkkopalvelut-valikosta "Avaa URL-osoite" tai avaa leikepöydällä oleva URL-osoite painamalla Ctrl+Vaihto+U. Bookworm lataa sivun ja poimii luettavan pääartikkelin tekstin aina kun mahdollista. Verkkosivut tukevat lukutiloja, kuten muotoilematonta tekstiä ja koko tekstiä.

"Wikipedian pikahaku" -toiminto on käytettävissä Verkkopalvelut-valikossa tai pikanäppäimellä Ctrl+Vaihto+W. Jos tekstiä on valittuna, Bookworm käyttää sitä haettavana tekstinä. Voit valita Wikipedian kielen, lukea tiivistelmän, avata artikkelin Bookwormissa tai avata sen selaimessa. Kun tekstiä on valittuna, pikavalikosta löytyy myös toiminto "Etsi määritelmä Wikipediasta".

## Tekstintunnistus

Voit poimia tekstiä kuvista ja skannatuista asiakirjoista Bookwormin tekstintunnistuksen avulla. Tämä on erityisen hyödyllistä, kun halutaan tehdä kuvapohjaisista PDF-tiedostoista tai asiakirjojen valokuvista luettavia ja etsittäviä. Bookworm tukee useita tekstintunnistusmoottoreita, joten voit valita tarpeisiisi parhaiten sopivan vaihtoehdon.

Tekstintunnistustoiminnot löytyvät valikkopalkin Tekstintunnistus-valikosta. Päätoiminnot ovat:

* "Skannaa nykyinen sivu..." (pikanäppäin F4): Suorittaa tekstintunnistuksen asiakirjan nykyiselle sivulle.
* "Automaattinen tekstintunnistus" (pikanäppäin Ctrl+F4): Suorittaa tekstintunnistuksen automaattisesti jokaiselle uudelle sivulle siirtyessäsi asiakirjassa eteenpäin.
* "Muuta tekstintunnistuksen asetuksia...": Tämän avulla voit muuttaa avoinna olevan kirjan tekstintunnistusasetuksia.
* "Skannaa tekstitiedostoon...": Skannaa sivut ja tallentaa tunnistetun tekstin .txt-tiedostoon.
* "Kuva tekstiksi...": Tämän avulla voit valita kuvatiedoston tietokoneeltasi ja avata tunnistetun tekstin virtuaalisena asiakirjana Bookwormissa.

Tekstintunnistuksen asetuksissa on mahdollista valita ensisijainen tunnistuskieli ja monikielistä tunnistusta tukevalle moottorille myös toissijainen kieli. Voit myös muuttaa valitun kuvan resoluutiota, ottaa käyttöön kuvan parannuksia ja tallentaa valitut asetukset nykyisen kirjan sulkemiseen saakka.

Kuvien esikäsittelysuodattimia ovat muun muassa resoluution suurentaminen, binarisointi, aukeamien jakaminen erillisiksi sivuiksi, kuvien yhdistäminen, sumennus, suoristus, kulutus, laajennus, terävöitys ja käänteiset värit. Käytettävissä olevat suodattimet ja moottorikohtaiset asetukset määräytyvät valitun tekstintunnistusmoottorin perusteella.

Bookworm tukee seuraavia tekstintunnistusmoottoreita:

### Windows 10:n ja 11:n tekstintunnistus

Windows 10:ssä ja uudemmissa Bookworm käyttää oletusarvoisesti käyttöjärjestelmän omaa tekstintunnistusmoottoria. Se toimii ilman asetusten muuttamista ja tuottaa hyvää jälkeä erityisesti järjestelmään asennetuilla kielillä.

### Tesseract OCR

Jos tarvitset laajempaa kielitukea, Bookwormiin on mahdollista integroida Googlen ylläpitämä tehokas avoimen lähdekoodin Tesseract OCR -tekstintunnistusmoottori.

Jos Tesseractia ei ole vielä asennettu Bookwormiin, voit ladata ja ottaa sen käyttöön suoraan sovelluksesta:

1. Valitse Tiedosto-valikosta "Asetukset..." ja siirry avautuvassa asetusikkunassa Tekstintunnistus-kategoriaan.
2. Paina Tesseract OCR -osiossa "Lataa Tesseract OCR" -painiketta ja noudata näytölle tulevia ohjeita.
3. Kun asennus on valmis, voit hallita kieliä napsauttamalla painiketta "Hallitse Tesseract OCR:n kieliä".

### VIVO General OCR -moottori

Bookworm tarjoaa yhteistyössä VIVOn (vivo.com.cn) ja kiinalaisen NVDA-yhteisön (NVDACN) kanssa pääsyn VIVO OCR -moottoriin. Tämä palvelu on maksuton ja tarjoaa korkealaatuisen tekstintunnistuksen sekä kiinan- että englanninkieliselle sisällölle.

VIVO OCR -moottorin käyttöä varten tarvitset maksuttoman NVDA-CN-käyttäjätilin.

#### Käyttöönotto

1. Luo käyttäjätili NVDA-CN:n rekisteröintisivulla: [https://nvdacn.com/admin/register.php](https://nvdacn.com/admin/register.php).
2. Vahvista sähköpostiosoitteesi napsauttamalla vahvistusviestissä olevaa linkkiä.
3. Avaa Bookwormin asetukset valitsemalla Tiedosto-valikosta "Asetukset..." tai painamalla Ctrl+Vaihto+P.
4. Siirry Tekstintunnistus-kategoriaan ja syötä käyttäjänimesi ja salasanasi VIVO OCR -osioon.
5. Valitse "VIVO OCR" oletusarvoiseksi tekstintunnistusmoottoriksi Oletusmoottori-luettelosta.

Kun asetukset on määritetty, Bookworm käyttää tekstintunnistustoimintoihin VIVO-moottoria. Tiliin liittyvissä ongelmissa voit ottaa yhteyttä NVDA-CN-tiimiin sähköpostitse osoitteella support@nvdacn.com.

### Baidu AI Cloud OCR

Baidu AI Cloud OCR tuottaa erittäin tarkkaa tunnistusjälkeä monimutkaisista asetteluista sekä kiinan ja englannin sekateksteistä. Tämä verkkopalvelu sisältää sekä vakio- että suurtarkkuusmoottorin.

Tarvitset Baidun tekstintunnistusmoottoreiden käyttöä varten maksuttoman rajapinta-avaimen (API key) ja salaisen avaimen (secret key).

#### Käyttöönotto

1. Rekisteröidy käyttäjäksi [Baidu AI Cloud OCR:n sivulla](https://ai.baidu.com/tech/ocr/general) saadaksesi edellä mainitut avaimet.
2. Avaa Bookwormin asetukset valitsemalla Tiedosto-valikosta "Asetukset..." tai painamalla Ctrl+Vaihto+P.
3. Siirry Tekstintunnistus-kategoriaan ja syötä rajapinta- ja salainen avaimesi Baidu OCR -osioon.
4. Valitse Oletusmoottori-luettelosta joko vakiomoottori "Baidu General OCR (vakio)" tai suurtarkkuusmoottori "Baidu General OCR (tarkka)".

Kun asetukset on määritetty, Bookworm käyttää tekstintunnistustoimintoihin Baidu-moottoria.

### Tekstistä puheeksi -toiminnolla lukeminen

Bookworm tukee avoimen asiakirjan sisällön lukemista asennetun tekstistä puheeksi -äänen avulla. Aloita lukeminen painamalla F5, keskeytä tai jatka lukemista painamalla F6 ja pysäytä lukeminen kokonaan painamalla F7.

Voit määrittää puheen asetukset kahdella tavalla:

1. Ääniprofiililla: Ääniprofiili sisältää mukauttamasi puheasetukset. Voit ottaa ääniprofiilin käyttöön tai poistaa sen käytöstä milloin tahansa. Ääniprofiileihin pääsee Puhe-valikosta tai painamalla Ctrl+Vaihto+V. Bookwormissa on valmiina muutama valmis esimerkkiprofiili.
2. Yleisillä puheasetuksilla: Näitä asetuksia käytetään oletusarvoisesti silloin, kun mikään ääniprofiili ei ole käytössä. Voit määrittää yleiset puheasetukset sovelluksen asetuksista.

Tekstistä puheeksi -lukemisen aikana voit siirtyä tekstissä edelliseen kappaleeseen painamalla Alt+Nuoli vasemmalle tai seuraavaan kappaleeseen painamalla Alt+Nuoli oikealle.

### Medianäppäinten toiminta

Medianäppäimet on määritetty tekstistä puheeksi -lukemisen keskeisiin toimintoihin:

* Toista/Keskeytä: aloittaa, keskeyttää tai jatkaa lukemista.
* Seuraava kappale: siirtyy nopeasti seuraavaan kappaleeseen. Tämä vastaa pikanäppäintä Alt+Nuoli oikealle.
* Edellinen kappale: siirtyy edelliseen kappaleeseen. Tämä vastaa pikanäppäintä Alt+Nuoli vasemmalle.

Medianäppäimet toimivat oletusarvoisesti vain Bookwormin ikkunan ollessa aktiivisena. Voit ottaa käyttöön järjestelmänlaajuiset medianäppäimet valitsemalla asetusikkunan Lukeminen-kategoriassa "Käytä järjestelmänlaajuisia medianäppäimiä" -valintaruudun. Tällöin Bookworm pystyy ohjaamaan toistoa myös taustalla ollessaan.

Medianäppäinten toiminta saattaa olla epäluotettavaa, jos useita mediasovelluksia on käynnissä samanaikaisesti.

### Lukutyylin määrittäminen

Puheasetusten lisäksi Bookwormissa voi hienosäätää lukemisen toimintaa. Kaikki seuraavat asetukset löytyvät asetusikkunan Lukeminen-kategoriasta.

* Kun Toista-painiketta painetaan: Tämä asetus määrittää, mitä nykyisen asiakirjan lukemista aloitettaessa tapahtuu. Voit valita vaihtoehdon "Lue koko kirja", "Lue nykyinen luku" tai "Lue nykyinen sivu".
* Aloita lukeminen: Tämä valinta määrittää kohdan, josta tekstistä puheeksi -toiminnolla lukeminen aloitetaan. Voit aloittaa lukemisen kohdistimen sijainnista tai nykyisen sivun alusta.
* Tekstistä puheeksi -toiminnolla luettaessa: Nämä asetukset vaikuttavat Bookwormin toimintaan tekstistä puheeksi -toiminnolla lukemisen aikana.
* Puhu sivunumero: Tekstistä puheeksi -ääni puhuu jokaisen sivun numeron sille siirryttäessä.
* Ilmoita lukujen loppuminen: Tekstistä puheeksi -ääni ilmoittaa luvun loppumisesta.
* Kysy, vaihdetaanko nykyisen kirjan kieltä tukevaan puheääneen: Tämä asetus määrittää, kysyykö Bookworm äänen vaihtamisesta silloin, kun valittu tekstinluentaääni on eri kuin avoimen asiakirjan kieli.
* Korosta puhuttava teksti: Luettava teksti korostetaan visuaalisesti, jos tämä asetus on käytössä.
* Valitse puhuttava teksti: Luettava teksti valitaan, jos tämä asetus on käytössä. Tämän ansiosta voit esimerkiksi kopioida luettavan kappaleen painamalla Ctrl+C.

Lukeminen-kategoriassa on myös asetuksia kuvista annettavalle palautteelle tekstissä liikkumisen aikana, kuten kuvien ilmaiseminen merkkiäänellä sekä siirtymisen salliminen sellaisten kuvien kohdalle, joilla ei ole vaihtoehtoista tekstiä.

### Jatkuvan luvun tila

Bookwormin omien tekstistä puheeksi -ominaisuuksien lisäksi voit hyödyntää ruudunlukijasi jatkuvan luvun toimintoa. Sovellus tukee tätä toimintoa jatkuvan luvun tilansa avulla. Tämä tila on oletusarvoisesti käytössä, ja se voidaan poistaa käytöstä sovelluksen asetusikkunan Lukeminen-kategoriasta. Sivua vaihdetaan automaattisesti jatkuvan luvun tilan ollessa aktiivisena ruudunlukijan edetessä asiakirjassa.

Seuraavat rajoitukset on hyvä ottaa huomioon:

* Jatkuva luku keskeytyy tyhjällä sivulla. Siirry tällöin tekstiä sisältävälle sivulle ja käynnistä ruudunlukijan jatkuva luku uudelleen.
* Kohdistimen siirtäminen sivun viimeisen merkin kohdalle vaihtaa heti seuraavalle sivulle.

### Nykyisen sivun renderöidyn version tarkastelu

Bookwormissa on mahdollista tarkastella nykyisen sivun renderöityä versiota, jos asiakirja tukee graafista esitystä. Paina avoimessa asiakirjassa Ctrl+R tai valitse Asiakirja-valikosta "Renderöi sivu..." -toiminto. Tätä näkymää kutsutaan renderöintinäkymäksi erotukseksi oletusarvoisesta tekstinäkymästä.

Voit käyttää renderöintinäkymässä tavanomaisia zoomauskomentoja:

* Ctrl+=: lähennä
* Ctrl+-: loitonna
* Ctrl+0: palauta zoomaustaso normaaliksi

Edellä mainittuja asiakirjan navigointikomentoja on mahdollista käyttää myös renderöintinäkymässä liikkumiseen. Sulje tämä näkymä painamalla Esc-näppäintä.

Kun upotettu kuva avataan Ctrl+Enter-näppäinyhdistelmällä, kuvaikkunassa on käytettävissä  seuraavia lisäkomentoja:

* Ctrl+=: lähennä
* Ctrl+-: loitonna
* Ctrl+0: todellinen koko
* Ctrl+S: tallenna kuva
* Ctrl+C: kopioi kuva
* Esc, Ctrl+W tai Alt+C: sulje kuvaikkuna

Kun taulukko avataan Ctrl+Enter-näppäinyhdistelmällä, Bookworm näyttää sen selattavassa HTML-valintaikkunassa.

### Tietylle sivulle siirtyminen

Kun haluat siirtyä tietylle sivulle avoinna olevassa asiakirjassa, paina Ctrl+G tai valitse Haku-valikosta "Siirry sivulle..." -toiminto, joka avaa Siirry sivulle -valintaikkunan. Kirjoita tähän ikkunaan sen sivun numero, jolle haluat siirtyä ja paina sen jälkeen Enter, jolloin Bookworm siirtää näkymän kyseiselle sivulle. Tämä ikkuna näyttää myös nykyisestä asiakirjasta löydettyjen sivujen kokonaismäärän.

Asiakirjoissa, joissa on sivutunnisteita (kuten joissakin PDF-asiakirjoissa) voit painaa Ctrl+Vaihto+G tai valita Haku-valikosta "Siirry sivulle tunnisteen perusteella..." ja syöttää haluamasi sivutunnisteen.

Voit siirtyä nykyisen sivun tai asiakirjan tietylle riville painamalla Ctrl+L tai valitsemalla Haku-valikosta "Siirry riville...".

### Asiakirjasta etsiminen

Avoinna olevasta asiakirjasta on mahdollista etsiä tekstiä painamalla Ctrl+F, joka avaa "Asiakirjasta etsiminen" -ikkunan. Tässä ikkunassa voit etsiä haluamaasi tekstiä ja määrittää haun asetukset. Seuraavat vaihtoehdot ovat käytettävissä:

* Sama kirjainkoko: Haku ottaa huomioon etsittävän tekstin kirjainkoon.
* Vain kokonaiset sanat: Etsittävän tekstin on löydyttävä kokonaisena sanana, ei osana toista sanaa.
* Säännöllinen lauseke: Etsittävää tekstiä käsitellään säännöllisenä lausekkeena. Kun tämä asetus on käytössä, kokonaisten sanojen haku on poissa käytöstä.
* Haun alue: Tämän avulla voit rajata haun koskemaan asiakirjasta riippuen vain tiettyjä sivuja, tiettyä lukua tai tiettyä tekstialuetta.

Kun olet painanut "Etsi asiakirjasta" -ikkunassa OK-painiketta, näkyviin tulee toinen ikkuna, jossa hakutulokset näytetään. Minkä tahansa hakutulosluettelossa olevan kohteen aktivoiminen siirtää heti kyseisen tuloksen kohdalle, ja etsitty teksti on valmiiksi korostettuna.

Jos olet sulkenut hakutulosten ikkunan, voit siirtyä edellisen haun seuraavaan tai edelliseen esiintymään painamalla F3 tai Vaihto+F3.

## Tiedostokytkentöjen hallinta

Sovelluksen asetusikkunan Yleiset-kategorian "Tiedostokytkentöjen hallinta" -painikkeesta avautuvassa valintaikkunassa voit määrittää, mitkä tiedostotyypit kytketään Bookwormiin. Tiedostojen kytkeminen Bookwormiin tarkoittaa, että se avaa ne oletusarvoisesti, kun napsautat niitä Windowsin Resurssienhallinnassa. Tämä ikkuna näytetään ensimmäisellä käynnistyskerralla, ja se on käytettävissä vain asennusohjelmalla asennetussa versiossa.

Kun olet avannut tiedostokytkentöjen hallinnan, seuraavat vaihtoehdot ovat käytettävissä:

* Kytke kaikki: Tämä muuttaa asetuksesi siten, että Windows avaa Bookwormilla kaikki sen tukemat tiedostotyypit.
* Poista kaikki kytkennät: Tämä poistaa aiemmin rekisteröidyt tiedostokytkennät.
* Yksittäiset painikkeet jokaiselle tuetulle tiedostotyypille: Minkä tahansa painikkeen painaminen kytkee kyseisen tiedostotyypin Bookwormiin.

## Bookwormin päivittäminen

Bookworm tarkistaa oletusarvoisesti päivitysten saatavuuden käynnistyksen yhteydessä. Näin varmistetaan, että saat uudet Bookwormin versiot käyttöösi mahdollisimman nopeasti. Voit poistaa tämän toiminnon käytöstä sovelluksen asetuksista. Päivitykset voidaan tarkistaa myös manuaalisesti valitsemalla Ohje-valikosta "Tarkista päivitykset" -toiminto.

Jos uusi versio on saatavilla, sovellus kysyy molempia päivitystapoja käytettäessä, haluatko asentaa sen. Jos valitset Kyllä, sovellus aloittaa päivityspaketin lataamisen ja näyttää samalla sen edistymisen. Kun päivitys on ladattu, Bookworm ilmoittaa, että päivitys viimeistellään sovelluksen uudelleenkäynnistyksen jälkeen. Suorita päivitys loppuun painamalla OK-painiketta.

## Ongelmista ja virheistä ilmoittaminen

Sokeina kehittäjinä vastuullamme on kehittää sovelluksia, jotka tarjoavat itsenäisyyttä sekä meille itsellemme että sokeille ystävillemme kaikkialla maailmassa. Jos olet kokenut Bookwormin jollain tavalla hyödylliseksi, autathan meitä tekemään siitä entistäkin paremman. Mikäli kohtaat virheen Bookwormia käyttäessäsi, luo uusi ongelman tiedot sisältävä virheraportti [ongelmienseurannassamme](https://github.com/blindpandas/bookworm/issues/).

Varmista ennen uuden ongelmaraportin lähettämistä, että käytit Bookwormia vianmääritystilassa. Ota vianmääritystila käyttöön avaamalla Ohje-valikko ja valitsemalla Käynnistä uudelleen vianmääritystilassa -vaihtoehto, ja yritä sen jälkeen toistaa ongelma. Kun virhe toistuu vianmääritystilan ollessa käytössä, näkyviin tulee useimmissa tapauksissa virheen tiedot näyttävä valintaikkuna. Kopioi tiedot tästä ikkunasta ja liitä ne ongelmaraporttiisi.

Joitakin ongelmia voi olla hankala toistaa, ja ne saattavat kadota, kun sovellus käynnistetään uudelleen. Tällaisessa tapauksessa on täysin hyväksyttävää ilmoittaa ongelmasta ilman vianmääritystilan yksityiskohtaisia tietoja. Varmistathan, että sisällytät ilmoitukseen mahdollisimman paljon tietoa järjestelmästäsi ja käyttötilanteestasi.

## Uutiset ja päivitykset

Jos haluat pysyä ajan tasalla Bookwormin tuoreimmista uutisista, vieraile [Bookwormin koodivarastossa](https://github.com/blindpandas/bookworm/) tai [julkaisusivulla](https://github.com/blindpandas/bookworm/releases).

## Lisenssi

**Bookworm** on copyright (c) 2026 Blind Pandas sekä muut Bookwormin kehittäjät. Se on lisensoitu [GNU GPL v2:n tai sitä uudemman lisenssin](https://github.com/blindpandas/bookworm/blob/master/LICENSE) ehtojen mukaisesti.
