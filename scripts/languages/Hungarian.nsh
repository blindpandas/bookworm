; Hungarian Modern UI language file for the Bookworm installer.
; Professionally reviewed Hungarian localization, 2026.

!insertmacro LANGFILE "Hungarian" = "Magyar" =

!ifdef MUI_WELCOMEPAGE
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TITLE "A $(^NameDA) telepítése"
  ${LangFileString} MUI_TEXT_WELCOME_INFO_TEXT "Ez a telepítő végigvezeti a szükséges lépéseken.$\r$\n$\r$\nA telepítés megkezdése előtt célszerű bezárni minden más futó alkalmazást. Így a szükséges rendszerfájlok frissítése általában a számítógép újraindítása nélkül elvégezhető.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_UNWELCOMEPAGE
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TITLE "A $(^NameDA) eltávolítása"
  ${LangFileString} MUI_UNTEXT_WELCOME_INFO_TEXT "A következő lépések segítségével eltávolíthatja a $(^NameDA) programot a számítógépről.$\r$\n$\r$\nA művelet megkezdése előtt győződjön meg arról, hogy a $(^NameDA) nem fut.$\r$\n$\r$\n$_CLICK"
!endif

!ifdef MUI_LICENSEPAGE
  ${LangFileString} MUI_TEXT_LICENSE_TITLE "Licencfeltételek"
  ${LangFileString} MUI_TEXT_LICENSE_SUBTITLE "A telepítés előtt olvassa el a $(^NameDA) licencfeltételeit."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM "A továbblépéshez el kell fogadnia a licencfeltételeket. Ha egyetért velük, válassza az Elfogadom gombot."
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_CHECKBOX "A licencfeltételek elfogadása szükséges. Ha egyetért velük, jelölje be az alábbi jelölőnégyzetet. $_CLICK"
  ${LangFileString} MUI_INNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "A licencfeltételek elfogadása szükséges. Ha egyetért velük, válassza az első lehetőséget. $_CLICK"
!endif

!ifdef MUI_UNLICENSEPAGE
  ${LangFileString} MUI_UNTEXT_LICENSE_TITLE "Licencfeltételek"
  ${LangFileString} MUI_UNTEXT_LICENSE_SUBTITLE "Az eltávolítás előtt olvassa el a $(^NameDA) licencfeltételeit."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM "A továbblépéshez el kell fogadnia a licencfeltételeket. Ha egyetért velük, válassza az Elfogadom gombot."
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_CHECKBOX "A licencfeltételek elfogadása szükséges. Ha egyetért velük, jelölje be az alábbi jelölőnégyzetet. $_CLICK"
  ${LangFileString} MUI_UNINNERTEXT_LICENSE_BOTTOM_RADIOBUTTONS "A licencfeltételek elfogadása szükséges. Ha egyetért velük, válassza az első lehetőséget. $_CLICK"
!endif

!ifdef MUI_LICENSEPAGE | MUI_UNLICENSEPAGE
  ${LangFileString} MUI_INNERTEXT_LICENSE_TOP "A licenc hivatalos szövege angol nyelvű. A további rész megtekintéséhez nyomja meg a Page Down billentyűt."
!endif

!ifdef MUI_COMPONENTSPAGE
  ${LangFileString} MUI_TEXT_COMPONENTS_TITLE "Összetevők kiválasztása"
  ${LangFileString} MUI_TEXT_COMPONENTS_SUBTITLE "Válassza ki a $(^NameDA) telepítendő összetevőit."
!endif

!ifdef MUI_UNCOMPONENTSPAGE
  ${LangFileString} MUI_UNTEXT_COMPONENTS_TITLE "Összetevők kiválasztása"
  ${LangFileString} MUI_UNTEXT_COMPONENTS_SUBTITLE "Válassza ki a $(^NameDA) eltávolítandó összetevőit."
!endif

!ifdef MUI_COMPONENTSPAGE | MUI_UNCOMPONENTSPAGE
  ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_TITLE "Leírás"
  ${LangFileString} MUI_INNERTEXT_COMPONENTS_DESCRIPTION_INFO "A leírás megtekintéséhez jelöljön ki egy összetevőt."
!endif

!ifdef MUI_DIRECTORYPAGE
  ${LangFileString} MUI_TEXT_DIRECTORY_TITLE "Telepítési hely kiválasztása"
  ${LangFileString} MUI_TEXT_DIRECTORY_SUBTITLE "Válassza ki a $(^NameDA) telepítési mappáját."
!endif

!ifdef MUI_UNDIRECTORYPAGE
  ${LangFileString} MUI_UNTEXT_DIRECTORY_TITLE "Eltávolítási hely kiválasztása"
  ${LangFileString} MUI_UNTEXT_DIRECTORY_SUBTITLE "Válassza ki a mappát, amelyből a programot el szeretné távolítani."
!endif

!ifdef MUI_INSTFILESPAGE
  ${LangFileString} MUI_TEXT_INSTALLING_TITLE "Telepítés folyamatban"
  ${LangFileString} MUI_TEXT_INSTALLING_SUBTITLE "Kérjük, várjon, amíg a $(^NameDA) telepítése befejeződik."
  ${LangFileString} MUI_TEXT_FINISH_TITLE "Sikeres telepítés"
  ${LangFileString} MUI_TEXT_FINISH_SUBTITLE "A $(^NameDA) telepítése befejeződött."
  ${LangFileString} MUI_TEXT_ABORT_TITLE "A telepítés megszakadt"
  ${LangFileString} MUI_TEXT_ABORT_SUBTITLE "A $(^NameDA) nem lett telepítve."
!endif

!ifdef MUI_UNINSTFILESPAGE
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_TITLE "Eltávolítás folyamatban"
  ${LangFileString} MUI_UNTEXT_UNINSTALLING_SUBTITLE "Kérjük, várjon, amíg a $(^NameDA) eltávolítása befejeződik."
  ${LangFileString} MUI_UNTEXT_FINISH_TITLE "Sikeres eltávolítás"
  ${LangFileString} MUI_UNTEXT_FINISH_SUBTITLE "A $(^NameDA) eltávolítása befejeződött."
  ${LangFileString} MUI_UNTEXT_ABORT_TITLE "Az eltávolítás megszakadt"
  ${LangFileString} MUI_UNTEXT_ABORT_SUBTITLE "A program eltávolítása nem fejeződött be."
!endif

!ifdef MUI_FINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_INFO_TITLE "A telepítés befejezése"
  ${LangFileString} MUI_TEXT_FINISH_INFO_TEXT "A $(^NameDA) telepítése befejeződött.$\r$\n$\r$\nAz ablak bezárásához válassza a Befejezés gombot."
  ${LangFileString} MUI_TEXT_FINISH_INFO_REBOOT "A telepítés befejezéséhez a számítógép újraindítása szükséges. Szeretné ezt most megtenni?"
!endif

!ifdef MUI_UNFINISHPAGE
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TITLE "Az eltávolítás befejezése"
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_TEXT "A $(^NameDA) eltávolítása befejeződött.$\r$\n$\r$\nAz ablak bezárásához válassza a Befejezés gombot."
  ${LangFileString} MUI_UNTEXT_FINISH_INFO_REBOOT "Az eltávolítás befejezéséhez a számítógép újraindítása szükséges. Szeretné ezt most megtenni?"
!endif

!ifdef MUI_FINISHPAGE | MUI_UNFINISHPAGE
  ${LangFileString} MUI_TEXT_FINISH_REBOOTNOW "Újraindítás &most"
  ${LangFileString} MUI_TEXT_FINISH_REBOOTLATER "Újraindítás &később"
  ${LangFileString} MUI_TEXT_FINISH_RUN "A $(^NameDA) &indítása"
  ${LangFileString} MUI_TEXT_FINISH_SHOWREADME "A tájékoztató fájl meg&nyitása"
  ${LangFileString} MUI_BUTTONTEXT_FINISH "&Befejezés"
!endif

!ifdef MUI_STARTMENUPAGE
  ${LangFileString} MUI_TEXT_STARTMENU_TITLE "Start menü mappájának kiválasztása"
  ${LangFileString} MUI_TEXT_STARTMENU_SUBTITLE "Válassza ki a Start menü mappáját a $(^NameDA) parancsikonjaihoz."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_TOP "Válassza ki azt a mappát a Start menüben, amelybe a program parancsikonjai kerüljenek. Új mappa létrehozásához új nevet is megadhat."
  ${LangFileString} MUI_INNERTEXT_STARTMENU_CHECKBOX "Ne hozzon létre parancsikonokat"
!endif

!ifdef MUI_UNCONFIRMPAGE
  ${LangFileString} MUI_UNTEXT_CONFIRM_TITLE "A $(^NameDA) eltávolítása"
  ${LangFileString} MUI_UNTEXT_CONFIRM_SUBTITLE "A program eltávolítása a számítógépről."
!endif

!ifdef MUI_ABORTWARNING
  ${LangFileString} MUI_TEXT_ABORTWARNING "Biztosan megszakítja a $(^Name) telepítését?"
!endif

!ifdef MUI_UNABORTWARNING
  ${LangFileString} MUI_UNTEXT_ABORTWARNING "Biztosan megszakítja a $(^Name) eltávolítását?"
!endif

!ifdef MULTIUSER_INSTALLMODEPAGE
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_TITLE "Felhasználók kiválasztása"
  ${LangFileString} MULTIUSER_TEXT_INSTALLMODE_SUBTITLE "Adja meg, mely felhasználók számára legyen telepítve a $(^NameDA)."
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_TOP "Adja meg, hogy a $(^NameDA) csak az Ön számára vagy a számítógép minden felhasználója számára legyen elérhető. $(^ClickNext)"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_ALLUSERS "Telepítés minden felhasználó számára"
  ${LangFileString} MULTIUSER_INNERTEXT_INSTALLMODE_CURRENTUSER "Telepítés csak számomra"
!endif

!if 0
  ${LangFileString} LANGDLL_WINDOWTITLE "A telepítés nyelve"
  ${LangFileString} LANGDLL_INFO "Válassza ki a telepítés nyelvét."
!endif
