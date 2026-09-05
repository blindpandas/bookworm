# A Bookworm felhasználói kézikönyve

## Bevezetés

A Bookworm sokoldalú, egyszerűen kezelhető és kiemelkedően akadálymentes dokumentumolvasó. PDF-, EPUB- és MOBI-fájlok mellett számos más dokumentumformátum megnyitására és olvasására alkalmas.

A program gazdag eszközkészletet kínál a dokumentumok olvasásához és feldolgozásához. Kereshet a dokumentum szövegében, könyvjelzőket és kiemeléseket hozhat létre, megjegyzéseket fűzhet a tartalomhoz, használhatja a beépített szövegfelolvasást, rendszerezheti dokumentumait a Bookworm Könyvespolcán, webes cikkeket nyithat meg, valamint optikai karakterfelismeréssel (OCR) egyszerű szöveggé alakíthatja a szkennelt dokumentumokat.

A Bookworm Microsoft Windows operációs rendszeren fut, és jól együttműködik az olyan képernyőolvasókkal, mint az NVDA és a JAWS. Ha nem fut képernyőolvasó, a program saját szövegfelolvasó funkcióival önállóan is felolvashatja a tartalmat.

## Főbb szolgáltatások

* Több mint húsz dokumentumformátum támogatása, köztük az EPUB-, PDF- és MOBI-fájlok, a Microsoft Word-dokumentumok, a HTML, az egyszerű szöveg és a Markdown.
* Strukturált navigáció egybillentyűs parancsokkal: gyorsan lépkedhet a címsorok, hivatkozások, listák, táblázatok, idézetek és képek között.
* Teljes szöveges keresés részletesen szabályozható beállításokkal, többek között reguláris kifejezésekkel, valamint oldal- és fejezettartományok megadásával.
* Fejlett, mégis egyszerűen használható jelölési lehetőségek. Elnevezett könyvjelzőket, megjegyzéseket és kiemeléseket készíthet, gyorsan lépkedhet közöttük, a megjegyzéseket és kiemeléseket pedig egyszerű szöveges, HTML- vagy Markdown-dokumentumba exportálhatja.
* A grafikus megjelenítést támogató formátumoknál kétféle oldalnézet közül választhat: használhatja a szöveges nézetet, vagy megnyithatja az oldal nagyítható grafikus változatát.
* Optikai karakterfelismerés (OCR) szkennelt dokumentumok és képek szövegének kinyeréséhez. A Bookworm együttműködik a Windows beépített OCR-motorjával, a nyílt forráskódú Tesseracttal, a Vivo General OCR-rel és a Baidu AI Cloud OCR-szolgáltatással.
* Beépített webcikk-kivonatoló: URL-címeket nyithat meg, a program pedig automatikusan megpróbálja kinyerni az oldal fő cikkének olvasható szövegét.
* Gyorskeresés a Wikipédián; a Wikipédia-szócikkeket közvetlenül a Bookwormban is megnyithatja.
* A Bookworm Könyvespolca a helyi dokumentumok rendszerezéséhez: fájlok és mappák importálása, keresés cím és indexelt tartalom alapján, valamint a dokumentumok helyi másolatainak tárolása offline használathoz.
* Kiterjedt navigáció a tartalomjegyzék segítségével az ezt támogató dokumentumformátumokban.
* Könyvek felolvasása a beépített szövegfelolvasóval; a hangbeállítások hangprofilokba menthetők és tetszés szerint testre szabhatók.
* A szöveg nagyítása és kicsinyítése a megszokott nagyítási parancsokkal, valamint az alapértelmezett méret visszaállítása.
* Bármely támogatott dokumentum exportálása egyszerű szöveges fájlba.

## Telepítés

A Bookworm telepítéséhez és használatához nyissa meg a [Bookworm kiadási oldalát](https://github.com/blindpandas/bookworm/releases), majd töltse le a legfrissebb kiadást.

A jelenlegi változatok használatához Windows 8.1 vagy újabb rendszer szükséges. A Windows 7 és a korábbi Windows-verziók nem támogatottak.

A Bookworm háromféle csomagban érhető el:

* 32 bites telepítő 32 vagy 64 bites Windows rendszert futtató számítógépekhez;
* 64 bites telepítő 64 bites Windows rendszerekhez;
* hordozható változat, amely például pendrive-ról is futtatható.

Ha régebbi, SAPI 5-kompatibilis beszédhangokat telepített a rendszerre, és ezeket a Bookwormmal is használni szeretné, a 32 bites Bookworm telepítését vagy a 32 bites hordozható változat használatát javasoljuk.

Válassza ki a rendszerének megfelelő változatot, majd töltse le. Ha a telepítőcsomagot választotta, indítsa el az `.exe`-fájlt, és kövesse a képernyőn megjelenő utasításokat. A hordozható változat használatához csomagolja ki az archívum tartalmát egy tetszőleges mappába, majd indítsa el a Bookworm futtatható fájlját.

## A program használata

### Dokumentum megnyitása

Dokumentum megnyitásához válassza a **Fájl** menü **Megnyitás...** parancsát, vagy nyomja meg a Ctrl+O billentyűkombinációt. Mindkét esetben a megszokott fájlmegnyitó párbeszédpanel jelenik meg. Keresse meg a kívánt dokumentumot, majd a betöltéséhez válassza a **Megnyitás** gombot.

A **Fájl** menüből új Bookworm-ablakot is nyithat a Ctrl+N billentyűkombinációval, bezárhatja az aktuális dokumentumot a Ctrl+W billentyűkombinációval, illetve rögzítheti azt a Ctrl+P billentyűkombinációval. A rögzített és a legutóbb megnyitott dokumentumok külön almenükben találhatók; mindkét lista ugyanebből a menüből üríthető.

A **Fájl** menü **Importálás** almenüt is tartalmaz. A **QRD-fájl importálása** parancs egy QRead által létrehozott QRD-fájlból beolvassa az elmentett olvasási pozíciót, majd az eredeti dokumentumot a mentett helyen nyitja meg. A **Beállítások...** paranccsal megnyithatja a Bookworm beállításait; ugyanez a Ctrl+Shift+P billentyűkombinációval is elérhető.

### Az olvasóablak

A Bookworm főablaka a következő részekből áll:

1. **Tartalomjegyzék:** itt jelennek meg a dokumentum fejezetei. Segítségével áttekintheti a dokumentum szerkezetét, és közvetlenül a kívánt fejezetre ugorhat. A fejezetek között a szokásos navigációs billentyűkkel mozoghat; a kiválasztott fejezet megnyitásához nyomja meg az Enter billentyűt. A szöveges nézetből a Ctrl+T billentyűkombinációval viheti a fókuszt a tartalomjegyzékre.

2. **Szöveges nézet:** ez a terület tartalmazza az aktuális oldal szövegét. A szövegben a megszokott olvasási parancsokkal mozoghat. Ezenfelül a következő billentyűparancsokkal navigálhat a dokumentumban:

* Enter vagy Szóköz: továbblépés az aktuális fejezet következő oldalára;
* Backspace: visszalépés az aktuális fejezet előző oldalára;
* Page Down és Page Up: előre- vagy visszalépés nagyobb lépésekben az aktuális oldalon belül;
* ha a kurzor az első sorban áll, a Fel nyíl kétszeri, egymást követő megnyomása az előző oldalra lép;
* ha a kurzor az utolsó sorban áll, a Le nyíl kétszeri, egymást követő megnyomása a következő oldalra lép;
* Alt+Home: ugrás az aktuális fejezet első oldalára;
* Alt+End: ugrás az aktuális fejezet utolsó oldalára;
* Alt+Page Down: ugrás a következő fejezetre;
* Alt+Page Up: ugrás az előző fejezetre;
* F2: ugrás a következő könyvjelzőre;
* Shift+F2: ugrás az előző könyvjelzőre;
* F8: ugrás a következő megjegyzésre;
* Shift+F8: ugrás az előző megjegyzésre;
* F9: ugrás a következő kiemelésre;
* Shift+F9: ugrás az előző kiemelésre;
* Ctrl+Enter: az aktuális pozícióhoz tartozó speciális művelet végrehajtása. A Bookworm ilyenkor követhet egy belső hivatkozást, megnyithat egy külső hivatkozást az alapértelmezett böngészőben, böngészhető párbeszédpanelen jeleníthet meg egy táblázatot, illetve megnyithat egy beágyazott képet;
* Ctrl+Shift+Enter: visszatérés az előző olvasási pozícióhoz egy belső hivatkozás követése után.

3. **Olvasási előrehaladást jelző csúszka:** ha a beállításokban engedélyezte az **Olvasási előrehaladás megjelenítése százalékban** lehetőséget, a Bookworm az állapotsorban megjeleníti, hogy a dokumentum hány százalékát olvasta el. A csúszka segítségével százalékos pozíció alapján is gyorsan mozoghat a dokumentumban.

### Strukturált navigáció

Ha az aktuális dokumentum szemantikai szerkezettel rendelkezik, a szöveges nézetből közvetlenül is lépkedhet a különböző elemek között. A következő elemre az adott betű megnyomásával ugorhat; az előző elemre a Shift billentyű és ugyanazon betű együttes használatával léphet.

* H: címsor;
* 1–6: az adott szintű címsor;
* K: hivatkozás;
* L: lista;
* T: táblázat;
* Q: idézet;
* I: kép vagy ábra.

Az elemek listája a **Dokumentum** menü **Elemlista...** parancsával vagy a Ctrl+F7 billentyűkombinációval is megnyitható. A lista címsorokat, hivatkozásokat, listákat, táblázatokat, idézeteket és képeket tartalmazhat. Egy elem aktiválásakor a Bookworm az adott elemhez ugrik.

### Dokumentumműveletek

A **Dokumentum** menü olyan parancsokat tartalmaz, amelyek elérhetősége az aktuális dokumentumtól függ:

* **Dokumentum adatai...:** megjeleníti az elérhető metaadatokat és dokumentumstatisztikákat.
* **Elemlista...:** megnyitja a szerkezeti elemek listáját; ugyanez a Ctrl+F7 billentyűkombinációval is elérhető.
* **Olvasási mód módosítása...:** megnyitja az olvasási mód kiválasztására szolgáló párbeszédpanelt; ugyanez a Ctrl+Shift+M billentyűkombinációval is elérhető. A rendelkezésre álló módok dokumentumformátumonként eltérhetnek; ilyen lehet többek között az **Alapértelmezett olvasási mód**, az **Olvasási sorrend**, a **Fizikai elrendezés**, a **Lapozott**, a **Fejezetenként**, a **Tisztított szöveg** és a **Teljes szöveg** mód.
* **Oldal grafikus megjelenítése...:** grafikus oldalnézetben nyitja meg az aktuális oldalt, ha a dokumentumformátum támogatja a grafikus megjelenítést; ugyanez a Ctrl+R billentyűkombinációval is elérhető.

### Könyvjelzők, megjegyzések és kiemelések

A Bookwormban könyvjelzőket, megjegyzéseket és kiemeléseket adhat a megnyitott dokumentumhoz. Könyvjelzővel megjelölhet egy fontos helyet, amelyhez később gyorsan visszatérhet. Megjegyzésekben gondolatokat, emlékeztetőket vagy összefoglalókat rögzíthet, a fontos szövegrészeket pedig kiemeléssel jelölheti meg későbbi áttekintéshez.

#### Könyvjelző hozzáadása

Dokumentum olvasása közben nyomja meg a Ctrl+B billentyűkombinációt, vagy válassza a **Jelölések** menü **Könyvjelző hozzáadása** parancsát. A könyvjelző az aktuális kurzorpozícióhoz kerül. Elnevezett könyvjelzőt a Ctrl+Shift+B billentyűkombinációval, illetve a **Jelölések** menü **Elnevezett könyvjelző hozzáadása...** parancsával hozhat létre.

#### Könyvjelzők megtekintése

Nyissa meg a **Jelölések** menüt, és válassza a **Mentett könyvjelzők...** parancsot. Megjelenik a létrehozott könyvjelzőket tartalmazó párbeszédpanel. A listában bármelyik könyvjelző aktiválásakor a Bookworm azonnal az adott pozícióra ugrik. A szöveges nézetben az F2, illetve a Shift+F2 billentyűvel a következő, illetve az előző könyvjelzőre ugorhat.

A mentett könyvjelzőket tartalmazó párbeszédpanelen az F2 billentyűvel átnevezheti, a Delete billentyűvel pedig eltávolíthatja a kijelölt könyvjelzőt.

#### Megjegyzés hozzáadása

Dokumentum olvasása közben nyomja meg a Ctrl+M billentyűkombinációt, vagy válassza a **Jelölések** menü **Megjegyzés hozzáadása...** parancsát. A program kéri a megjegyzés szövegét. Írja be a kívánt szöveget, majd válassza az **OK** gombot. A megjegyzés az aktuális pozícióhoz kerül; ha előzőleg szöveget jelölt ki, a megjegyzés a kijelölt tartományhoz kapcsolódik.

Ha a megjegyzés hozzáadásakor lenyomva tartja a Shift billentyűt, a Bookworm ezután a címkék megadását is kéri.

Amikor olyan oldalra lép, amely legalább egy megjegyzést tartalmaz, a Bookworm rövid hangjelzéssel jelezheti, hogy az oldalon megjegyzés található. Ez a viselkedés a beállítások **Jelölések** oldalán módosítható.

#### Kiemelés hozzáadása

Jelölje ki a kívánt szöveget, majd nyomja meg a Ctrl+H billentyűkombinációt, vagy válassza a **Jelölések** menü **Kijelölés kiemelése** parancsát. A Bookworm kiemelésként menti a kijelölt szöveget. Ha ugyanaz a kijelölés már kiemelésként szerepel, a művelet eltávolítja a kiemelést. Ha a kijelölés egy meglévő kiemeléssel átfedésben van, a program kibővítheti a meglévő kiemelés tartományát.

Ha a kiemelés hozzáadásakor lenyomva tartja a Shift billentyűt, a Bookworm a művelet után a címkék megadását is kéri. Az F9 és Shift+F9 billentyűkkel a következő, illetve az előző kiemelésre ugorhat.

#### Megjegyzések és kiemelések kezelése

A **Jelölések** menüből válassza a **Mentett megjegyzések...** vagy a **Mentett kiemelések...** parancsot. A megjelenő párbeszédpanelen a mentett elemek listája látható. A lista bármely elemének aktiválásakor a Bookworm azonnal annak dokumentumbeli helyére ugrik. A **Megtekintés** gomb egy külön párbeszédpanelen jeleníti meg a kijelölt elem címkéit és tartalmát.

A mentett megjegyzéseket és kiemeléseket címke, fejezet vagy tartalom alapján szűrheti. Ha az adott adatok rendelkezésre állnak, dátum, oldal, pozíció vagy könyv szerint is rendezheti őket. Az F6 billentyűvel a szűrés vezérlőelemeihez léphet, az F2-vel szerkesztheti a címkéket, a Delete billentyűvel törölheti a kijelölt elemet, a Ctrl+C pedig a kijelölt megjegyzés vagy kiemelés szövegét a vágólapra másolja.

#### Megjegyzések és kiemelések exportálása

A mentett megjegyzéseket és kiemeléseket egyszerű szöveges fájlba, HTML-dokumentumba vagy Markdown-dokumentumba exportálhatja.

Az exportálás menete:

1. Nyissa meg a **Jelölések** menü **Mentett megjegyzések...** vagy **Mentett kiemelések...** parancsát.
2. Keresse meg az **Exportálás** gombot, majd nyomja meg az Enter billentyűt; az exportálási menüt az Alt+X billentyűparanccsal is megnyithatja.

A következő beállításokat tetszés szerint engedélyezheti vagy letilthatja:

* **A könyv címének feltüntetése:** a könyv címe bekerül az exportált fájlba.
* **A fejezet címének feltüntetése:** az exportált tartalom tartalmazza annak a fejezetnek a címét, amelyben a jelölés található.
* **Az oldalszám feltüntetése:** az exportált tartalom tartalmazza azt az oldalszámot, amelyen a jelölés készült.
* **Címkék feltüntetése:** meghatározza, hogy a jelölésekhez tartozó címkék bekerüljenek-e az exportált fájlba.

A kívánt beállítások megadása után válassza ki a kimeneti formátumot – egyszerű szöveg, HTML vagy Markdown –, majd adja meg a célfájlt. A **Fájl megnyitása exportálás után** jelölőnégyzet bekapcsolásával a Bookworm mentés után automatikusan megnyitja az elkészült fájlt.

### Bookworm Könyvespolc

A Bookworm Könyvespolca egy helyi dokumentumtár, amelyben rendszerezheti a Bookwormmal olvasott dokumentumokat. A **Fájl** menü **Könyvespolc** almenüjének **Könyvespolc megnyitása** parancsával nyithatja meg. Az aktuális, helyi fájlként tárolt dokumentumot a **Hozzáadás a helyi könyvespolchoz...** paranccsal adhatja hozzá.

Dokumentum hozzáadásakor vagy importálásakor a Bookworm megkérdezheti, melyik olvasási listához, illetve mely gyűjteményekhez szeretné hozzárendelni a dokumentumot, valamint hogy bekerüljön-e a teljes szöveges keresési indexbe. A beállítások **Könyvespolc** oldalán engedélyezhető az is, hogy a program automatikusan hozzáadja a megnyitott könyveket a helyi könyvespolchoz.

A helyi könyvespolc többek között a **Legutóbb hozzáadottak**, **Jelenleg olvasom**, **El szeretném olvasni**, **Kedvencek**, **Olvasási listák**, **Gyűjtemények** és **Szerzők** kategóriákat tartalmazza. A Könyvespolc **Fájl** menüjében a Ctrl+O billentyűkombinációval dokumentumokat, külön paranccsal pedig teljes mappák tartalmát importálhatja. Ugyanitt kereshet a könyvespolcon, helyi másolatokat készíthet a dokumentumokról, valamint eltávolíthatja az érvénytelenné vált dokumentumbejegyzéseket.

A Könyvespolc dokumentumlistáján a következő billentyűparancsok használhatók:

* Enter: a kijelölt dokumentum megnyitása új Bookworm-ablakban;
* F2: a kijelölt dokumentum átnevezése, ha az adott elem átnevezhető;
* F5: a lista frissítése;
* Ctrl+F: ugrás a gyorsszűrő mezőre;
* ha a fókusz a dokumentumlistán van, gépelés közben a lista cím alapján szűrődik;
* Alt+Bal nyíl: visszalépés egy almappából vagy tárolóból.

A Könyvespolc helyi menüjéből megnyithat egy dokumentumot a Bookwormban vagy a rendszer alapértelmezett alkalmazásával, módosíthatja a címét, megtekintheti a dokumentum adatait, szerkesztheti az olvasási listát és a gyűjteményeket, módosíthatja, hogy szerepeljen-e a **Jelenleg olvasom**, **El szeretném olvasni** vagy **Kedvencek** kategóriában, illetve teljesen eltávolíthatja a Könyvespolcról.

A **Keresés a könyvespolcon...** parancs a dokumentumok címében és indexelt tartalmában keres. Egy találat megnyitásakor a Bookworm közvetlenül arra az oldalra és azon belül arra a pozícióra ugrik, ahol az egyezés található.

### URL-címek és Wikipédia-szócikkek megnyitása

A Bookworm weboldalakat is képes olvasható dokumentumként megnyitni. Válassza a **Webszolgáltatások** menü **URL megnyitása** parancsát, majd írja be a címet. A Ctrl+Shift+U billentyűkombinációval közvetlenül a vágólapon található URL-címet nyithatja meg. A Bookworm betölti az oldalt, és amikor lehetséges, kinyeri belőle a fő cikk olvasható szövegét. Weboldalaknál is rendelkezésre állhat például a tisztított szöveg és a teljes szöveg olvasási mód.

A **Gyorskeresés a Wikipédián** parancs a **Webszolgáltatások** menüből, illetve a Ctrl+Shift+W billentyűkombinációval érhető el. Ha előzőleg szöveget jelölt ki, a Bookworm ezt használja keresőkifejezésként. Kiválaszthatja a Wikipédia nyelvét, elolvashatja a szócikk összefoglalóját, megnyithatja a teljes cikket a Bookwormban vagy a böngészőben. Kijelölt szöveg esetén a helyi menüben a **Meghatározás keresése a Wikipédián** parancs is megjelenik.

## Optikai karakterfelismerés (OCR)

A Bookworm optikai karakterfelismerési (OCR) funkcióival szöveget nyerhet ki képekből és szkennelt dokumentumokból. Ez különösen hasznos képalapú PDF-fájlok és lefényképezett dokumentumok olvashatóvá, kereshetővé tételéhez. A program több OCR-motort támogat, így a feladathoz leginkább megfelelő megoldást választhatja.

Az OCR-funkciók a menüsor **OCR** menüjéből érhetők el. A legfontosabb parancsok:

* **Aktuális oldal felismerése...** (F4): OCR-t futtat az aktuális dokumentumoldalon.
* **Automatikus OCR** (Ctrl+F4): lapozáskor minden új oldalon automatikusan elvégzi a felismerést.
* **OCR-beállítások módosítása...:** az aktuális könyvre érvényes OCR-beállításokat módosítja.
* **Felismerés szövegfájlba...:** felismeri a megadott oldalak szövegét, majd az eredményt `.txt`-fájlba menti.
* **Kép szöveggé alakítása...:** kiválaszthat egy képfájlt a számítógépéről; a felismert szöveg virtuális dokumentumként nyílik meg a Bookwormban.

Az OCR-beállítások párbeszédpanelén kiválaszthatja az elsődleges felismerési nyelvet, továbbá – ha a kiválasztott motor támogatja a többnyelvű felismerést – másodlagos felismerési nyelvet is megadhat. Módosíthatja a bemeneti kép felbontását, engedélyezheti a képjavító műveleteket, és az aktuális könyv bezárásáig elmentheti a kiválasztott beállításokat.

A rendelkezésre álló kép-előfeldolgozó műveletek között szerepelhet a képfelbontás növelése, a binarizálás, a két oldalt tartalmazó beolvasások külön oldalakra bontása, a képek egyesítése, az elmosás, a ferdeségkorrekció, az erózió, a dilatáció, a kép élesítése és a színek invertálása. Az elérhető szűrők és motorspecifikus beállítások az alkalmazott OCR-motortól függenek.

A Bookworm a következő OCR-motorokat támogatja:

### Windows 10/11 OCR

Windows 10 vagy újabb rendszer használata esetén a Bookworm közvetlenül az operációs rendszerbe épített OCR-motort is igénybe veheti. Ha rendelkezésre áll, ez az alapértelmezett motor, és külön telepítést nem igényel. Különösen azoknál a nyelveknél ad jó eredményt, amelyekhez telepítve van a szükséges nyelvi támogatás.

### Tesseract OCR

Ha sokféle nyelv támogatására van szüksége, a Bookworm a Tesseract OCR-rel is együttműködik. A Tesseract nagy teljesítményű, nyílt forráskódú optikai karakterfelismerő motor, amelyet a Google tart karban.

Ha a Tesseract még nincs telepítve, közvetlenül a Bookwormból töltheti le és állíthatja be:

1. Nyissa meg a **Fájl > Beállítások...** párbeszédpanelt, majd válassza az **OCR** oldalt.
2. A **Tesseract OCR-motor** csoportban válassza a **Tesseract OCR-motor letöltése** gombot, és kövesse a megjelenő utasításokat.
3. A telepítés után a **Tesseract OCR nyelveinek kezelése** gombbal tölthet le és távolíthat el nyelvi modelleket.

### Vivo General OCR az NVDA-CN szolgáltatásán keresztül

A Vivo (vivo.com.cn) és a kínai NVDA-közösség (NVDACN) együttműködésének köszönhetően a Bookworm a Vivo OCR-motorhoz is hozzáférést biztosít. A szolgáltatás díjmentesen használható, és kínai, illetve angol nyelvű tartalmak felismerésekor jó eredményt nyújt.

A Vivo OCR használatához ingyenes NVDA-CN-fiókra van szükség.

#### A Vivo OCR beállítása

1. Hozzon létre fiókot az NVDA-CN regisztrációs oldalán: [https://nvdacn.com/admin/register.php](https://nvdacn.com/admin/register.php).
2. A megerősítő levélben található hivatkozás megnyitásával igazolja az e-mail-címét.
3. Nyissa meg a Bookworm beállításait a **Fájl > Beállítások...** paranccsal vagy a Ctrl+Shift+P billentyűkombinációval.
4. Lépjen az **OCR** beállítási oldalra, majd a **Vivo OCR-motor** csoportban adja meg felhasználónevét és jelszavát.
5. Az **Alapértelmezett OCR-motor** listában válassza a **Vivo OCR** lehetőséget.

A beállítások mentése után a Bookworm a Vivo OCR-motort használja az OCR-műveletekhez. Fiókkal kapcsolatos probléma esetén az NVDA-CN csapata a support@nvdacn.com címen érhető el.

### Baidu AI Cloud OCR

A Bookworm a Baidu AI Cloud OCR webes szolgáltatásával is együttműködik. Különösen pontos eredményt adhat összetett elrendezésű, illetve vegyesen kínai és angol szöveget tartalmazó anyagoknál. A szolgáltatás normál és nagy pontosságú felismerési módot egyaránt biztosít.

A Baidu OCR használatához API-kulcsra (API Key) és titkos kulcsra (Secret Key) van szükség; ezeket ingyenes fiók létrehozása után szerezheti be.

#### A Baidu OCR beállítása

1. Regisztráljon a [Baidu AI Cloud OCR oldalán](https://ai.baidu.com/tech/ocr/general), és szerezze be a szükséges kulcsokat.
2. Nyissa meg a Bookworm beállításait a **Fájl > Beállítások...** paranccsal vagy a Ctrl+Shift+P billentyűkombinációval.
3. Lépjen az **OCR** beállítási oldalra, majd a **Baidu OCR-motor** csoportban adja meg az API-kulcsot és a titkos kulcsot.
4. Az **Alapértelmezett OCR-motor** listában válassza a **Baidu General OCR (normál)** vagy a **Baidu General OCR (nagy pontosságú)** lehetőséget.

A beállítások mentése után a Bookworm a kiválasztott Baidu OCR-motort használja az OCR-műveletekhez.

### Felolvasás

A Bookworm a megnyitott dokumentum tartalmát a rendszerre telepített szövegfelolvasó hangok egyikével is felolvashatja. A felolvasás indításához nyomja meg az F5 billentyűt, szüneteltetéséhez vagy folytatásához az F6 billentyűt, leállításához pedig az F7 billentyűt.

A felolvasás beállításait kétféleképpen adhatja meg:

1. **Hangprofil használata:** a hangprofil az egyéni beszédbeállításokat tartalmazza. Egy profilt bármikor aktiválhat, illetve kikapcsolhat. A hangprofilok a **Beszéd** menüből vagy a Ctrl+Shift+V billentyűkombinációval érhetők el. A Bookworm néhány beépített mintaprofilt is tartalmaz.
2. **Globális beszédbeállítások:** ha nincs aktív hangprofil, a program alapértelmezés szerint ezeket a beállításokat használja. A globális beszédbeállítások a Bookworm beállításai között módosíthatók.

Felolvasás közben az Alt+Bal nyíl az előző bekezdésre, az Alt+Jobb nyíl pedig a következő bekezdésre lép.

### A médiabillentyűk működése

A médiabillentyűk a szövegfelolvasás legfontosabb műveleteit vezérlik:

* **Lejátszás/Szünet:** elindítja, szünetelteti, illetve folytatja a felolvasást.
* **Következő szám:** a következő bekezdésre lép; ez az Alt+Jobb nyíl billentyűkombinációnak felel meg.
* **Előző szám:** az előző bekezdésre lép; ez az Alt+Bal nyíl billentyűkombinációnak felel meg.

Alapértelmezés szerint a médiabillentyűk csak akkor vezérlik a Bookwormot, amikor a program ablaka aktív. Ha a beállítások **Olvasás** oldalán bekapcsolja a **Rendszerszintű médiabillentyűk engedélyezése** lehetőséget, a Bookworm akkor is vezérelhető a médiabillentyűkkel, amikor a háttérben fut.

A médiabillentyűk működése megbízhatatlan lehet, ha egyszerre több médiaalkalmazás is fut.

### Az olvasási stílus beállítása

A hangbeállításokon túl a Bookworm olvasási viselkedését is részletesen testre szabhatja. Az alábbi lehetőségek a program beállításainak **Olvasás** oldalán találhatók.

* **A felolvasás indításakor:** meghatározza, mi történjen a felolvasás elindításakor. A következő lehetőségek közül választhat: **A teljes könyv felolvasása**, **Az aktuális fejezet felolvasása** vagy **Az aktuális oldal felolvasása**.
* **Felolvasás kezdete:** megadja, honnan induljon a felolvasás. A **Kurzor helye** választásakor az aktuális kurzorpozíciótól, az **Oldal eleje** választásakor pedig az aktuális oldal elejétől kezdődik.
* **Felolvasás közben:** az itt található beállítások a Bookworm felolvasás közbeni viselkedését szabályozzák.
* **Oldalszám bemondása:** a szövegfelolvasó minden új oldalra lépéskor bemondja az oldalszámot.
* **Fejezetek végének bemondása:** a szövegfelolvasó jelzi, amikor egy fejezet végére ér.
* **A könyv nyelvének megfelelő hangra váltás felajánlása:** meghatározza, hogy a Bookworm felajánlja-e a hangváltást, ha a kiválasztott beszédhang nyelve eltér a megnyitott dokumentum nyelvétől.
* **Felolvasott szöveg kiemelése:** vizuálisan kiemeli az éppen elhangzó szövegrészt.
* **Felolvasott szöveg kijelölése:** kijelöli az éppen felolvasott szöveget. Ennek köszönhetően például a Ctrl+C billentyűkombinációval a vágólapra másolhatja az aktuálisan felolvasott bekezdést.

Az **Olvasás** oldalon a képekhez kapcsolódó navigációs visszajelzések is beállíthatók. Megadhatja, hogy hangjelzés szólaljon meg, amikor a kurzor képhez ér, valamint azt is, hogy a képek közötti navigáció az üres alternatív szövegű képeket is figyelembe vegye.

### Folyamatos olvasási mód

A Bookworm saját szövegfelolvasása mellett a képernyőolvasó folyamatos felolvasási funkcióját – más néven a „mindent felolvas” parancsot – is használhatja. A Bookworm ezt automatikus lapozással támogatja. A támogatás alapértelmezés szerint engedélyezett, és a program beállításainak **Olvasás** oldalán kapcsolható ki. Amíg a funkció aktív, a Bookworm a képernyőolvasó előrehaladásával összhangban automatikusan lapoz.

A következő korlátozásokkal számolni kell:

* Ha a folyamatos olvasás üres oldalhoz ér, megszakad. Ilyenkor lépjen egy nem üres oldalra, majd onnan indítsa újra a képernyőolvasó folyamatos felolvasását.
* Ha a kurzort az oldal utolsó karakterére viszi, a Bookworm azonnal a következő oldalra vált.

### Az aktuális oldal teljes grafikus megjelenítése

Ha a dokumentumformátum támogatja, az aktuális oldalt grafikus nézetben is megnyithatja; ebben a nézetben az oldal vizuális elrendezése is megmarad. Megnyitott dokumentumnál nyomja meg a Ctrl+R billentyűkombinációt, vagy válassza a **Dokumentum** menü **Oldal grafikus megjelenítése...** parancsát. Ezt a nézetet a továbbiakban **grafikus nézetnek** nevezzük, megkülönböztetve az alapértelmezett szöveges nézettől.

A grafikus nézetben a megszokott nagyítási parancsok használhatók:

* Ctrl+=: nagyítás;
* Ctrl+-: kicsinyítés;
* Ctrl+0: a nagyítás alaphelyzetbe állítása.

A korábban ismertetett dokumentumnavigációs parancsok a grafikus nézetben is használhatók. A nézet bezárásához és a szöveges nézethez való visszatéréshez nyomja meg az Escape billentyűt.

Ha a Ctrl+Enter egy dokumentumba ágyazott képet nyit meg, a képet megjelenítő párbeszédpanelen a következő parancsok állnak rendelkezésre:

* Ctrl+=: nagyítás;
* Ctrl+-: kicsinyítés;
* Ctrl+0: tényleges méret;
* Ctrl+S: a kép mentése;
* Ctrl+C: a kép másolása;
* Escape, Ctrl+W vagy Alt+C: a képet megjelenítő párbeszédpanel bezárása.

Ha a Ctrl+Enter egy táblázatot nyit meg, a Bookworm azt böngészhető HTML-párbeszédpanelen jeleníti meg.

### Ugrás egy megadott oldalra

Az aktuális dokumentum egy adott oldalára a Ctrl+G billentyűkombinációval, illetve a **Keresés** menü **Ugrás oldalra...** parancsával léphet. A megjelenő párbeszédpanelen írja be a kívánt oldalszámot; a Bookworm azonnal az adott oldalra ugrik. A párbeszédpanel az aktuális dokumentum oldalainak számát is jelzi.

Az oldalcímkéket tartalmazó dokumentumoknál – például egyes PDF-fájlokban – a Ctrl+Shift+G billentyűkombinációval vagy a **Keresés** menü **Ugrás oldalra oldalcímke alapján...** parancsával a kívánt oldalra annak címkéje alapján is ugorhat.

Az aktuális oldal vagy dokumentum megadott sorára a Ctrl+L billentyűkombinációval, illetve a **Keresés** menü **Ugrás sorra...** parancsával léphet.

### Keresés a dokumentumban

Ha egy kifejezést vagy szövegrészletet szeretne megkeresni az aktuálisan megnyitott dokumentumban, nyomja meg a Ctrl+F billentyűkombinációt. Megnyílik a **Keresés a dokumentumban** párbeszédpanel, ahol beírhatja a keresett szöveget, és részletesen beállíthatja a keresés módját.

A következő lehetőségek állnak rendelkezésre:

* **Kis- és nagybetűk megkülönböztetése:** a keresés különbséget tesz a kis- és nagybetűk között.
* **Csak teljes szavak keresése:** a keresőkifejezésnek önálló, teljes szóként kell szerepelnie; egy hosszabb szó részeként előforduló egyezés nem számít találatnak.
* **Reguláris kifejezés:** a Bookworm a keresőkifejezést reguláris kifejezésként értelmezi. Ennek bekapcsolásakor a **Csak teljes szavak keresése** beállítás nem használható.
* **Keresési tartomány:** a keresést megadott oldalakra, egy konkrét fejezetre vagy – a dokumentumtól függően – egy szövegtartományra korlátozhatja.

Miután a **Keresés a dokumentumban** párbeszédpanelen az **OK** gombot választotta, megjelenik a találati lista. Egy találat aktiválásakor a Bookworm azonnal annak helyére ugrik, és a keresett szöveget kiemeli.

Ha bezárta a keresési eredmények ablakát, az F3 és Shift+F3 billentyűkkel továbbra is az utolsó keresés következő, illetve előző előfordulására ugorhat.

## Fájltársítások kezelése

A program beállításainak **Általános** oldalán található **Fájltársítások kezelése** gombbal meghatározhatja, mely fájltípusokat nyissa meg alapértelmezés szerint a Bookworm. Ha egy fájltípust a Bookwormhoz társít, a Windows Fájlkezelőben az ilyen fájlok megnyitásakor alapértelmezés szerint a Bookworm indul el. Ez a párbeszédpanel az első indításkor is megjelenik, de csak a telepítőcsomagból telepített változatban érhető el; a hordozható változatban a fájltársítások nem kezelhetők.

A fájltársítás-kezelő a következő lehetőségeket kínálja:

* **Összes társítása:** úgy módosítja a Windows beállításait, hogy minden, a Bookworm által támogatott fájltípus alapértelmezés szerint a Bookwormmal nyíljon meg.
* **Minden támogatott fájltípus társításának megszüntetése:** eltávolítja a korábban regisztrált fájltársításokat.
* **Külön gomb minden támogatott fájltípushoz:** az adott gomb kiválasztásával csak a hozzá tartozó fájltípust társíthatja a Bookwormhoz.

## A Bookworm frissítése

A Bookworm alapértelmezés szerint minden indításkor ellenőrzi, hogy elérhető-e újabb változat. Így az új kiadásokról a lehető leghamarabb értesülhet. Az automatikus ellenőrzést a program beállításaiban kikapcsolhatja. A **Súgó** menü **Frissítések keresése** parancsával kézzel is ellenőrizheti a frissítéseket.

Ha a Bookworm új verziót talál, rákérdez, hogy szeretné-e telepíteni. Az **Igen** választásakor letölti a frissítési csomagot, és párbeszédpanelen mutatja a letöltés előrehaladását. A letöltés befejezése után a program értesíti, hogy a frissítés végrehajtásához újraindul. A folyamat befejezéséhez válassza az **OK** gombot.

## Hibák és problémák bejelentése

Vak fejlesztőkként feladatunknak tekintjük, hogy olyan alkalmazásokat készítsünk, amelyek nekünk és vak társainknak világszerte nagyobb önállóságot biztosítanak. Ha hasznosnak találja a Bookwormot, kérjük, segítsen nekünk abban, hogy a programot még jobbá tehessük minden felhasználó számára. Ha a Bookworm használata közben hibát tapasztal, a hiba részleteivel nyisson új hibajegyet a [Bookworm hibakövető oldalán](https://github.com/blindpandas/bookworm/issues/).

Új hibajegy beküldése előtt lehetőség szerint indítsa el a Bookwormot hibakeresési módban. Ehhez nyissa meg a **Súgó** menüt, válassza az **Újraindítás hibakeresési módban** parancsot, majd próbálja ismét előidézni a problémát. Sok esetben a hiba ismételt jelentkezésekor egy párbeszédpanel részletes műszaki adatokat jelenít meg. Ezt az információt kimásolhatja, és a hibajelentéshez csatolhatja.

Bizonyos hibák nehezen reprodukálhatók, és a program újraindítása után átmenetileg eltűnhetnek. Ilyenkor a problémát a hibakeresési mód részletes adatai nélkül is bejelentheti. Törekedjen arra, hogy a rendszeréről és a hiba jelentkezésekor végzett műveletekről a lehető legtöbb releváns információt megadja.

## Hírek és frissítések

A Bookwormmal kapcsolatos legújabb hírekért keresse fel a [Bookworm GitHub-tárhelyét](https://github.com/blindpandas/bookworm/) vagy a [Bookworm kiadási oldalát](https://github.com/blindpandas/bookworm/releases).

## Licenc

**Bookworm** © 2026 Blind Pandas és a Bookworm közreműködői. A program a [GNU General Public License 2. vagy újabb verziójának](https://github.com/blindpandas/bookworm/blob/master/LICENSE) feltételei szerint használható és terjeszthető.
