# Bookwormin käyttöopas

## Johdanto

Bookworm on asiakirjanlukija, jonka avulla voit lukea PDF-, ePub-, MOBI- ja monia muita asiakirjamuotoja käyttäen monipuolista mutta yksinkertaista ja helppokäyttöistä käyttöliittymää.

Bookworm tarjoaa runsaasti työkaluja asiakirjojen lukemiseen. Voit etsiä asiakirjasta, lisätä kirjanmerkkejä ja korostaa mielenkiintoista sisältöä, käyttää teksti puheeksi -toimintoa ja muuntaa skannatut asiakirjat pelkäksi tekstiksi tekstintunnistusta käyttäen.

Bookworm toimii Windows-käyttöjärjestelmässä. Se toimii hyvin suosittujen ruudunlukijoiden, kuten NVDA:n ja JAWSin, kanssa. Vaikka mikään ruudunlukija ei olisi käytössä, Bookworm voi toimia puhuvana sovelluksena käyttäen sisäänrakennettuja teksti puheeksi -ominaisuuksia.

## Ominaisuudet

* Tukee yli 15 asiakirjamuotoa, mukaan lukien ePub, PDF, MOBI ja Microsoft Word
* Tukee rakenteellista navigointia otsikoiden, luetteloiden, taulukoiden ja sisennettyjen lainausten välillä siirtymiseen pikanavigointikomentoja käyttäen
* Haku koko tekstistä mukautettavilla asetuksilla
* Kehittyneet ja helppokäyttöiset merkintätyökalut. Voit lisätä nimettyjä kirjanmerkkejä merkitsemään mielenkiintoisia kohtia tekstissä myöhempää käyttöä varten, ja voit lisätä kommentteja kiinnostavan ajatuksen vangitsemiseksi tai luoda yhteenvedon sisällöstä tietyssä tekstin kohdassa. Voit siirtyä nopeasti tiettyyn kommenttiin ja tarkastella sitä. Voit myös viedä kommentit tekstitiedostoon tai HTML-asiakirjaan myöhempää käyttöä varten.
* Bookworm tukee PDF-asiakirjoille kahta eri sivujenkatselutyyliä; pelkkää tekstiä ja täysin renderöityjä, zoomattavia kuvia.
* Tuki tekstintunnistukselle tekstin poimimiseen skannatuista asiakirjoista ja kuvista Windows 10:n sisäänrakennettua tekstintunnistusmoottoria käyttäen. Ilmaiseksi saatavilla olevan Tesseract-tekstintunnistusmoottorin lataaminen ja käyttäminen on myös mahdollista.
* Etsi termien määritelmiä ja lue Wikipedia-artikkeleita
* Sisäänrakennettu verkkoartikkelien poimija, jonka avulla voit avata URL-osoitteita ja poimia sivulta automaattisesti pääartikkelin.
* Sisällysluettelon avulla tapahtuvaa navigointia tuetaan laajasti kaikissa asiakirjamuodoissa
* Tuki kirjojen ääneen lukemiselle käyttäen teksti puheeksi -toimintoa, jonka asetuksia voi muokata ääniprofiilien avulla
* Tuki tekstin zoomaukselle tavallisia zoomaa lähemmäs/zoomaa kauemmas/nollaa-komentoja käyttäen
* Tuki minkä tahansa asiakirjamuodon viemiselle pelkäksi tekstiksi.

## Asennus

Lataa Bookworm [sen viralliselta verkkosivulta.](https://github.com/blindpandas/bookworm)

Bookworm on saatavana kolmessa muodossa:

* 32-bittinen asennusohjelma tietokoneille, joissa on 32- tai 64-bittinen Windows
* 64-bittinen asennusohjelma tietokoneille, joissa on 64-bittinen Windows
* Massamuistiversio muistitikulta käytettäväksi

Jos järjestelmääsi on asennettu vanhoja SAPI 5 -ääniä ja haluat käyttää niitä Bookwormissa, suosittelemme Bookwormin 32-bittisen version asentamista tai 32-bittisen massamuistiversion käyttöä.

Lataa itsellesi sopiva versio. Mikäli valitsit asennettavan version, suorita .exe-tiedosto ja seuraa näytöllä olevia ohjeita. Jos valitsit massamuistiversion, pura pakattu tiedosto haluamaasi kansioon ja käynnistä Bookworm suorittamalla bookworm.exe-tiedosto.


## Käyttö

### Asiakirjan avaaminen

Voit avata asiakirjan valitsemalla Tiedosto-valikosta Avaa. Vaihtoehtoisesti voit käyttää pikanäppäintä Ctrl+O. Käytitpä kumpaa tapaa tahansa, näkyviin tulee tuttu Avaa tiedosto -valintaikkuna. Etsi haluamasi asiakirja ja avaa se napsauttamalla Avaa.

### Lukuikkuna

Bookwormin pääikkuna koostuu seuraavista kahdesta osasta:

1. Sisällysluettelo: Tämä osa näyttää asiakirjan luvut. Sen avulla voit tutkia sisällön rakennetta. Liiku lukujen välillä nuolinäppäimillä ja siirry tiettyyn lukuun painamalla Enteriä.

2. Tekstinäkymä-alue: Tämä osa sisältää nykyisen sivun tekstin. Voit käyttää siinä tavallisia lukukomentoja tekstissä liikkumiseen. Lisäksi voit käyttää seuraavia pikanäppäimiä:

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
* Ctrl+Enter: avaa mikä tahansa asiakirjan sisältämä sisäinen tai ulkoinen linkki. Sisäiset linkit ovat joidenkin asiakirjamuotojen sisällysluettelon luomia, ulkoiset tavallisia, selaimessa avattavia. Linkin tyypistä riippuen suoritetaan jompi kumpi seuraavista toiminnoista. Jos linkki on sisäinen eli osa sisällysluetteloa, silloin yllä olevan näppäinkomennon painaminen siirtää kohdistuksen haluttuun asiakirjan kohtaan. Jos linkki on ulkoinen, näppäinkomento avaa sen järjestelmän oletusselaimessa.

### Kirjanmerkit ja kommentit

Bookworm mahdollistaa merkintöjen tekemisen avoimeen asiakirjaan. Voit lisätä kirjanmerkin muistaaksesi tietyn sijainnin asiakirjassa ja siirtyä sitten nopeasti siihen. Lisäksi voit lisätä kommentin ajatuksen vangitsemiseksi tai tehdä yhteenvedon sisällöstä.

#### Kirjanmerkkien lisääminen

Voit lisätä asiakirjaa lukiessasi kirjanmerkin painamalla Ctrl+B tai valitsemalla Merkinnät-valikosta Lisää kirjanmerkki -vaihtoehdon. Kirjanmerkki lisätään nykyiseen kohdistimen sijaintiin. Vaihtoehtoisesti voit lisätä nimetyn kirjanmerkin painamalla Ctrl+Vaihto+B (tai valitsemalla Merkinnät-valikosta Lisää nimetty kirjanmerkki), jonka jälkeen avautuvassa ikkunassa kysytään kirjanmerkin nimeä.

#### Kirjanmerkkien näyttäminen

Siirry Merkinnät-valikkoon ja valitse Näytä kirjanmerkit -vaihtoehto. Näyttöön tulee valintaikkuna, jossa lisätyt kirjanmerkit näytetään. Minkä tahansa kohteen napsauttaminen kirjanmerkkiluettelossa siirtää välittömästi kyseisen kirjanmerkin kohtaan. Vaihtoehtoisesti voit siirtyä nopeasti lisättyjen kirjanmerkkien välillä käyttäen F2- ja Vaihto+F2-näppäinkomentoja, jotka siirtävät suoraan siihen kohdistimen sijaintiin, johon kirjanmerkki viittaa.

#### Kommenttien lisääminen

Voit asiakirjaa lukiessasi lisätä kommentin painamalla Ctrl+M tai valitsemalla Merkinnät-valikosta Lisää kommentti -vaihtoehdon. Sinulta kysytään kommentin sisältöä. Kirjoita haluamasi kommentti ja napsauta OK. Kommentti lisätään nykyiseen kohdistimen sijaintiin.

Kun siirryt sivulle, joka sisältää vähintään yhden kommentin, kuulet pienen äänen, joka ilmaisee, että nykyisellä sivulla on kommentti.

#### Kommenttien hallinta

Valitse Tallennetut kommentit -vaihtoehto Merkinnät-valikosta. Näyttöön tulee valintaikkuna, jossa lisätyt kommentit näytetään. Napsauttamalla mitä tahansa kohtaa kommenttiluettelossa siirryt välittömästi kyseisen kommentin kohdalle. Näytä-painiketta napsauttamalla avautuu valintaikkuna, jossa näkyy valitun kommentin tunniste ja sisältö.

Vaihtoehtoisesti voit napsauttaa Muokkaa-painiketta muuttaaksesi valitun kommentin tunnistetta ja sisältöä, painaa F2 muokataksesi valitun kommentin tunnistetta tai painaa Del-näppäintä tai Alt+P-pikanäppäintä poistaaksesi valitun kommentin.

#### Kommenttien vienti

Bookwormilla voit viedä kommentit tekstitiedostoon tai HTML-asiakirjaan, joka voidaan avata verkkoselaimessa. Vaihtoehtoisesti Bookworm mahdollistaa kommenttien viennin Markdown-muotoon, joka on tehokäyttäjien keskuudessa suosittu rakenteellisten asiakirjojen tekstimuoto.

Vie kommentit seuraavasti:

1. Valitse Merkinnät-valikosta Tallennetut kommentit.
2. Etsi avautuvassa valintaikkunassa Vie-painike ja paina Enter, tai vaihtoehtoisesti voit käyttää pikanäppäintä Alt+I avataksesi vientivalikon.

Käytettävissä ovat seuraavat vaihtoehdot,  joiden valinnan poistaminen tai valitseminen on mahdollista:

* Sisällytä kirjan nimi: Tämän vaihtoehdon avulla voit sisällyttää kirjan nimen lopulliseen tulostiedostoon  kommentteja viedessäsi.
* Sisällytä luvun otsikko: Vaihtoehto, jota käytetään sisällyttämään sen luvun otsikko, johon kommentti jätetään.
* Sisällytä sivunumero: Tätä vaihtoehtoa käytetään sisällyttämään sivunumerot, joille kommentti on jätetty.
* Sisällytä tunnisteet: Tätä vaihtoehtoa käytetään sisällyttämään tai jättämään pois kommenttitunnisteet, jotka on luotu merkintää tehtäessä.

Kun olet määrittänyt oikeat vaihtoehdot tarpeidesi mukaan, sinun on valittava tiedoston tallennusmuoto, joita on tällä hetkellä kolme: vain teksti, Html ja Markdown.
Kun olet valinnut haluamasi muodon, näkyviin tulee vain luku -tyyppinen tekstialue nimeltä "Kohdetiedosto", joka  on oletusarvoisesti tyhjä. Napsauta Selaa-painiketta tai vaihtoehtoisesti paina Alt+S avataksesi Resurssienhallinnan ikkunan, jossa voit  määrittää tiedostonimen ja kansion, johon tiedosto tallennetaan.
Tiedostonimeä ja kansiota määritettäessä on Avaa tiedosto viennin jälkeen -valintaruutu, jonka ollessa valittuna Bookworm avaa kohdetiedoston automaattisesti tallennuksen jälkeen. Poista tämän valintaruudun valinta, mikäli et halua avata tallennettua tiedostoa automaattisesti, ja napsauta OK. Tiedosto tallennetaan määritettyyn kansioon ja voit avata sen joko Bookwormilla tai millä tahansa muulla tekstimuokkaimella, kuten Muistiolla.


### Ääneen lukeminen

Bookworm tukee avatun asiakirjan sisällön ääneen lukemista asennettua teksti puheeksi -ääntä käyttäen. Paina F5 aloittaaksesi puhumisen, F6 keskeyttääksesi tai jatkaaksesi ja F7 lopettaaksesi kokonaan.

Voit määrittää puheen kahdella tavalla:
1. Ääniprofiilia käyttäen: Ääniprofiili sisältää muokkaamasi puheasetukset. Voit ottaa ääniprofiilin käyttöön tai poistaa sen käytöstä milloin tahansa. Ääniprofiilit otetaan käyttöön Puhe-valikosta tai painamalla Ctrl+Vaihto+V. Huomaa, että Bookwormissa on sisäänrakennettuja esimerkkiääniprofiileja.
2. Yleiset puheasetukset: Näitä asetuksia käytetään oletusarvoisesti, kun mikään ääniprofiili ei ole käytössä. Voit määrittää yleiset puheasetukset sovelluksen asetuksista.

Voit siirtyä taakse- tai eteenpäin kappale kerrallaan ääneen lukemisen aikana painamalla Alt- sekä vasenta tai oikeaa nuolinäppäintä.


### Lukutyylin määrittäminen

Näiden asetusten avulla Bookwormissa voi hienosäätää puheasetusten lisäksi lukutyyliä. Kaikki seuraavat asetukset löytyvät sovellusasetusten lukeminen-sivulta.

* Kun Toista-painiketta painetaan: Tämä asetus määrittää, mitä tapahtuu, kun laitat Bookwormin "toistamaan" nykyisen asiakirjan. Valittavissa ovat vaihtoehdot "Lue koko kirja", "Lue nykyinen luku" tai "Lue nykyinen sivu". Oletusarvoisesti Bookworm lukee koko asiakirjan, ellet käske sitä lopettamaan sivun tai nykyisen luvun lopussa.
* Aloita lukeminen: Tämä asetus määrittää kohdan, josta ääneen lukeminen aloitetaan. Voit aloittaa lukemisen "kohdistimen sijainnista" tai "nykyisen sivun alusta".
* Ääneen luettaessa: Nämä asetukset määrittävät, miten Bookworm käyttäytyy ääneen luettaessa. Voit ottaa minkä tahansa seuraavista asetuksista käyttöön tai poistaa ne käytöstä valitsemalla tai poistamalla valinnan sitä vastaavasta valintaruudusta:

* Puhu sivunumero: Teksti puheeksi -ääni lukee jokaisen sivun numeron siirtyessäsi sille.
* Ilmoita lukujen loppumisesta: Teksti puheeksi -ääni ilmoittaa, kun luku on luettu.
* Pyydä vaihtamaan ääneen, joka puhuu nykyisen kirjan kieltä: Tämä asetus määrittää, varoittaako Bookworm yhteensopimattomasta äänestä, mikä tapahtuu oletusarvoisesti, jos valitun teksti puheeksi -äänen kieli on eri kuin avoimen asiakirjan.
* Korosta puhuttu teksti: Jos tämä asetus on käytössä, senhetkinen puhuttu teksti korostetaan visuaalisesti.
* Valitse puhuttu teksti: Jos tämä asetus on käytössä, senhetkinen puhuttu teksti valitaan. Näin voit esim. painaa Ctrl+C kopioidaksesi puhutun kappaleen.



### Jatkuvan luvun tila

Bookwormin sisäänrakennettujen teksti puheeksi -ominaisuuksien lisäksi voit hyödyntää ruudunlukijan jatkuvan luvun toimintoa. Bookworm tukee tätä toimintoa jatkuvan luvun tilansa avulla. Tämä tila on oletusarvoisesti käytössä, ja voit poistaa sen käytöstä sovellusasetusten Lukeminen-sivulta. Kun jatkuvan luvun tila on käytössä, sivuja käännetään automaattisesti ruudunlukijan edetessä asiakirjassa.

Huomaa, että ominaisuuden tämänhetkisen toteutustavan takia odotettavissa on seuraavia rajoituksia:

* Jatkuva luku keskeytyy tyhjälle sivulle siirryttäessä. Jos siirryit tyhjälle sivulle, siirry vain ei-tyhjälle sivulle ja ota ruudunlukijan jatkuvan luvun toiminto uudelleen käyttöön siinä.
* Kohdistimen siirtäminen sivun viimeisen merkin kohdalle vaihtaa välittömästi seuraavalle sivulle.



### Nykyisen sivun täysin renderöidyn version katselu

Bookwormin avulla voit tarkastella asiakirjan täysin renderöityä versiota. Kun asiakirja on avattu, voit painaa Ctrl+R tai valita Asiakirja-valikosta Renderöi sivu -vaihtoehdon. Tätä kutsutaan renderöintinäkymäksi.

Kun olet renderöintinäkymässä, voit käyttää tavallisia zoomauskomentoja sivun lähentämiseen ja loitontamiseen:

* Ctrl+=: Zoomaa lähemmäs
* Ctrl+-: Zoomaa kauemmas
* Ctrl+0: Nollaa zoomaustaso

Huomaa, että voit käyttää yllä mainittuja asiakirjojen navigointikomentoja myös renderöintinäkymässä liikkumiseen. Voit myös sulkea tämän näkymän ja palata tekstimuotoiseen oletusnäkymään painamalla Esc-näppäintä.


### Tietylle sivulle siirtyminen

Voit siirtyä tietylle sivulle avoimessa asiakirjassa painamalla Ctrl+G tai valitse Haku-valikosta Siirry sivulle... -vaihtoehto avataksesi Siirry sivulle -valintaikkunan. Tässä valintaikkunassa voit kirjoittaa minkä tahansa sivun numeron, jolle haluat siirtyä, ja Bookworm siirtyy kyseiselle sivulle. Huomaa, että tässä valintaikkunassa näytetään nykyisen asiakirjan sivujen kokonaismäärä.

 
### Asiakirjasta etsiminen

Voit etsiä tietyn termin tai tekstin osaa avoimesta asiakirjasta painamalla Ctrl+F, joka avaa Hae asiakirjasta -valintaikkunan. Tässä valintaikkunassa voit kirjoittaa etsimäsi tekstin, sekä määrittää itse hakuprosessin. Seuraavat asetukset ovat käytettävissä:

* Sama kirjainkoko: Haku ottaa huomioon hakuehdon kirjainkoon.
* Vain kokonaiset sanat: Hakutermin on löydyttävä kokonaisena sanana, eli ei osana toista sanaa.
* Hakualue: Tämän avulla voit rajoittaa haun tietyille sivuille tai tiettyyn lukuun.

Kun olet napsauttanut Hae asiakirjasta -valintaikkunassa OK-painiketta, toinen, hakutulokset sisältävä valintaikkuna avautuu. Minkä tahansa kohteen napsauttaminen hakutulosluettelossa siirtää välittömästi kyseisen tuloksen kohdalle, jossa hakuehto on korostettuna.

Huomaa, että jos olet sulkenut hakutulosikkunan, voit painaa F3 ja Vaihto+F3 siirtyäksesi viimeisimmän haun seuraavaan ja edelliseen esiintymään.


## Tiedostokytkentöjen hallinta

Tiedostokytkentöjen hallinta -painikkeella, joka löytyy sovellusasetusten Yleiset-sivulta, voit hallita Bookwormiin liitettyjä tiedostotyyppejä. Tiedostojen kytkeminen Bookwormiin tarkoittaa, että kun napsautat tiedostoa Windowsin Resurssienhallinnassa, tiedosto avataan oletuksena Bookwormissa. Huomaa, että tämä valintaikkuna näytetään aina ohjelman ensimmäisen käynnistyksen yhteydessä ja se on käytettävissä vain käytettäessä asennusohjelmallaa asennettua versiota. Massamuistiversiossa tätä vaihtoehtoa ei ole. Massamuistiversiossa tiedostokytkentöjen tekeminen on poistettu käytöstä, ja muutama temppu vaaditaan, jos haluat edelleen Bookwormin avaavan oletusarvoisesti tuetut asiakirjat.

Tiedostokytkentöjen hallinnassa on käytettävissä seuraavat vaihtoehdot:

* Kytke kaikki: Tämä muuttaa asetuksiasi siten, että kaikki Bookwormin tukemat tiedostotyypit avautuvat sillä. 
* Poista kaikkien tuettujen tiedostotyyppien kytkennät: Tämä poistaa aiemmin rekisteröidyt tiedostokytkennät.
* Yksittäiset painikkeet kullekin tuetulle tiedostotyypille: Minkä tahansa painikkeen napsauttaminen kytkee sitä vastaavan tiedostotyypin Bookwormiin.


## Bookwormin päivittäminen

Oletusarvoisesti Bookworm tarkistaa uuden version saatavuuden käynnistyksen yhteydessä. Tämä varmistaa, että saat uusimman ja parhaan Bookwormin mahdollisimman aikaisin. Voit poistaa tämän toiminnon käytöstä sovellusasetuksista. Voit myös tarkistaa päivitykset manuaalisesti napsauttamalla Ohje-valikosta Tarkista päivitykset -vaihtoehtoa.

Kun uusi versio löytyy, Bookworm kysyy, haluatko asentaa sen. Jos napsautat Kyllä, sovellus lataa päivityspaketin ja näyttää valintaikkunan, joka ilmaisee latauksen edistymisen. Kun päivitys on ladattu, Bookworm ilmoittaa, että se käynnistää itsensä uudelleen, jotta päivitys voidaan asentaa. Viimeistele päivitys napsauttamalla OK.


## Ongelmista ilmoittaminen

Sokeina kehittäjinä vastuullamme on kehittää sovelluksia, jotka tarjoavat itsenäisyyttä meille ja sokeille ystävillemme kaikkialla maailmassa. Joten jos olet kokenut Bookwormin jollain tavalla hyödylliseksi, auta meitä tekemään Bookwormista entistä parempi. Tässä alkuvaiheessa haluamme sinun kertovan kaikista virheistä, joita saatat kohdata Bookwormia käyttäessäsi. Voit tehdä tämän luomalla uuden, virheen tiedot sisältävän ongelmaraportin [ongelmien seurannassa](https://github.com/mush42/bookworm/issues/). Apuasi arvostetaan suuresti.

Ennen kuin lähetät uuden ongelmaraportin, varmista, että käytit Bookwormia virheenkorjaustilassa. Ota virheenkorjaustila käyttöön menemällä Ohje-valikkoon ja napsauttamalla Käynnistä uudelleen virheenkorjaustilassa -vaihtoehtoa, ja yritä sitten toistaa ongelma. Useimmissa tapauksissa, kun virhe toistuu virheenkorjaustilan ollessa käytössä, näkyviin tulee valintaikkuna, jossa kyseisen virheen tiedot ovat. Voit kopioida tiedot tästä valintaikkunasta ja liittää ne ongelmaraporttiisi.

Huomaa, että joitakin ongelmia voi olla vaikea toistaa, koska ne poistuvat, kun käynnistät ohjelman uudelleen. Tällaisessa tapauksessa on hyväksyttävää ilmoittaa ongelmasta ilman virheenkorjaustilan yksityiskohtaisia tietoja. Varmista vain, että sisällytät mahdollisimman paljon tietoa järjestelmästäsi ja käyttöskenaariostasi.


## Uutiset ja päivitykset

Pysyäksesi ajan tasalla viimeisimmistä Bookworm-uutisista, vieraile sovelluksen sivustolla osoitteessa [github.com/blindpandas/bookworm](https://github.com/blindpandas/bookworm/). Voit myös seurata johtavan kehittäjän, Musharraf Omerin, Twitter-tiliä [@mush42](https://twitter.com/mush42/).


## Lisenssi

**Bookworm** on copyright (c) 2019-2022 Musharraf Omer sekä muut kehitykseen osallistuneet. Se on [MIT-lisenssin](https://github.com/blindpandas/bookworm/blob/master/LICENSE) alainen.
