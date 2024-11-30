# Guide de l'Utilisateur Bookworm

## Introduction

Bookworm est un lecteur de documents qui vous permet de lire des fichiers PDF, EPUB, MOBI et de nombreux autres formats de documents à l'aide d'une interface polyvalente, simple et hautement accessible.
Bookworm vous fournit un riche ensemble d'outils pour lire vos documents. Vous pouvez rechercher le document, ajouter un signet et mettre en évidence le contenu intéressant, utiliser la synthèse vocale et convertir des documents numérisés en texte brut à l'aide de la reconnaissance optique de caractères (OCR).
Bookworm fonctionne sur le système d'exploitation Windows de Microsoft. Il fonctionne bien avec votre lecteur d'écran préféré tel que NVDA et JAWS. Même si aucun lecteur d'écran n'est actif, Bookworm peut fonctionner comme une application d'auto-voix en utilisant ses fonctionnalités de synthèse vocale intégrées.

## Fonctionnalités

* Prise en charge de plus de 15 formats de documents, y compris les documents EPUB, PDF, MOBI et Microsoft Word
* Prise en charge de la navigation structurée à l'aide de commandes de navigation à une seule lettre pour sauter entre les titres, les listes, les tableaux et les citations
* Recherche dans le texte avec options de recherche personnalisables
* Outils d'annotation avancés et simples à utiliser. Vous pouvez ajouter des signets nommés pour marquer des positions intéressantes dans le texte pour référence ultérieure, et vous pouvez ajouter des notes pour capturer une idée intéressante ou créer un résumé du contenu à une position spécifique du texte. Bookworm vous permet d'accéder rapidement à une note spécifique et de la visualiser. Plus tard, vous pouvez exporter ces notes vers un fichier texte ou un document HTML pour référence future.
* Pour les documents PDF, Bookworm prend en charge deux styles différents d'affichage des pages ; des images en texte brut et entièrement restituées, zoomables.
* Prise en charge de l'utilisation de l'OCR pour extraire du texte à partir de documents numérisés et d'images à l'aide du moteur OCR intégré de Windows10. Vous avez également la possibilité de télécharger et d'utiliser le moteur OCR Tesseract disponible gratuitement dans Bookworm.
* Recherche de la définition d'un terme dans Wikipédia et lecture des articles de Wikipédia à partir de Bookworm
* Extracteur d'articles Web intégré, qui vous permet d'ouvrir des URL et de demander à Bookworm d'extraire automatiquement l'article principal de la page
* La navigation dans le document via la table des matières est largement prise en charge pour tous les formats de document
* Prise en charge de la lecture de livres à voix haute à l'aide de la synthèse vocale, avec des options vocales personnalisables à l'aide de profils vocaux
* Prise en charge du zoom de texte à l'aide des commandes standard de zoom avant/arrière/réinitialiser
* Prise en charge de l'exportation de n'importe quel format de document vers un fichier texte brut.

## Installation

Pour installer et exécuter Bookworm sur votre ordinateur, procédez comme suit :

1. Pointez votre navigateur Web sur [(github.com/blindpandas/bookworm), le site officiel de Bookworm](https://github.com/blindpandas/bookworm/)
2. Bookworm est disponible en trois versions. Téléchargez celle qui vous convient :
* Installateur 32 bits pour les ordinateurs exécutant une variante 32 bits ou 64 bits de Windows
* Installateur 64 bits pour les ordinateurs exécutant une variante 64 bits de Windows
* Version portable pour fonctionner à partir d'une clé USB
Si vous avez d'anciennes voix SAPI5 installées sur votre système et que vous souhaitez les utiliser avec Bookworm, nous vous recommandons d'installer la variante 32 bits de Bookworm.

2. Exécutez le programme d'installation et suivez les invites
3. Une fois l'installation terminée avec succès, vous pouvez lancer Bookworm à partir du *Bureau* ou de la liste de programmes trouvée dans le menu Démarrer


## Utilisation

### Ouvrir un Document

Vous pouvez ouvrir un document en sélectionnant l'élément de menu "Ouvrir..." dans le menu "Fichier". Vous pouvez également utiliser le raccourci Ctrl+O. Dans tous les cas, la boîte de dialogue "Ouvrir le fichier" familière s'affiche. Accédez à votre document et cliquez sur Ouvrir pour le charger.

### La Fenêtre du Lecteur

La fenêtre principale de Bookworm se compose des deux parties suivantes :

1. La "Table des matières" : Cette partie présente les chapitres du document. Elle vous permet d'explorer la structure du contenu. Utilisez les touches de navigation pour parcourir les chapitres et appuyez sur Entrée pour accéder à un chapitre spécifique.

2. La zone "Vue textuelle" : Cette partie contient le texte de la page en cours. Dans cette partie, vous pouvez utiliser vos commandes de lecture habituelles pour naviguer dans le texte. De plus, vous pouvez utiliser les raccourcis clavier suivants pour parcourir le document :

* Entrée : accédez à la page suivante dans la section actuelle
* Retour arrière : accédez à la page précédente dans la section actuelle
* Quand le curseur est sur la première ligne, appuyez deux fois de suite sur la flèche vers le haut pour accéder à la page précédente.
* Quand le curseur est sur la dernière ligne, appuyez deux fois de suite sur la flèche vers le bas pour accéder à la page suivante.
* Alt + Début : accédez à la première page de la section actuelle
* Alt + Fin : accédez à la dernière page de la section actuelle
* Alt + Page suivante : naviguez à la section suivante
* Alt + Page précédente : naviguez à la section précédente


### Signets & Notes

Bookworm vous permet d'annoter le document ouvert. Vous pouvez ajouter un signet pour mémoriser un emplacement spécifique dans le document et, plus tard, y accéder rapidement. En outre, vous pouvez prendre une note pour capturer une idée ou résumer un contenu.

#### Ajouter des Signets

Pendant la lecture d'un document, vous pouvez appuyer sur Ctrl + B (ou sélectionner l'élément de menu « Ajouter un signet » dans le menu « Annotations » pour ajouter un signet. Le signet est ajouté à la position actuelle du curseur. Vous serez invité à fournir un titre pour le signet. Tapez le titre souhaité et cliquez sur le bouton OK. Un signet sera ajouté à l'emplacement actuel et la ligne actuelle sera mise en surbrillance visuelle.

#### Afficher les Signets

Appuyez sur Ctrl + Maj + B ou sélectionnez l'élément de menu "Afficher les signets" dans le menu "Annotations". Une boîte de dialogue contenant des signets ajoutés s'affichera. Cliquer sur n'importe quel élément de la liste des signets vous amènera immédiatement à la position de ce signet.

De plus, vous pouvez appuyer sur F2 pour modifier le titre du signet sélectionné, ou cliquer sur le bouton "Supprimer" ou sur la touche "Supprimer" de votre clavier pour supprimer le signet sélectionné.

#### Prendre des Notes

Pendant la lecture d'un document, vous pouvez appuyer sur Ctrl + N (ou sélectionner l'élément de menu « Prendre une note » dans le menu « Annotations » pour prendre une note. La note sera ajoutée à la position actuelle du curseur. Il vous sera demandé de fournir le titre et le contenu de la note. Saisissez le titre et le contenu souhaités, puis cliquez sur le bouton OK. Une note sera ajoutée à l'emplacement actuel.

Lorsque vous naviguez vers une page contenant au moins une note, vous entendrez un petit son indiquant l'existence d'une note dans la page en cours.

#### Gérer les Notes

Appuyez sur Ctrl + Maj + N ou sélectionnez l'élément de menu "Gérer les notes" dans le menu "Annotations". Une boîte de dialogue contenant des notes ajoutées sera affichée. Cliquer sur n'importe quel élément de la liste des notes vous amènera immédiatement à la position de cette note. Cliquer sur le bouton "Afficher" fera apparaître une boîte de dialogue affichant le titre et le contenu de la note sélectionnée.

De plus, vous pouvez cliquer sur le bouton "Modifier" pour modifier le titre et le contenu de la note sélectionnée, appuyer sur F2 pour modifier le titre de la note sélectionnée, ou vous pouvez cliquer sur le bouton "Supprimer" ou la touche "Supprimer" sur votre clavier pour supprimer la note sélectionnée.

#### Exporter des Notes

Bookworm vous permet d'exporter vos notes dans un fichier en texte brut ou dans un document HTML que vous pouvez ensuite ouvrir dans votre navigateur Web. En option, Bookworm vous permet d'exporter vos notes vers Markdown, qui est un format de base de texte pour écrire des documents structurés populaires parmi les utilisateurs experts d'ordinateurs.

Pour exporter vos notes, procédez comme suit :

1. Dans le menu "Annotations", sélectionnez l'élément de menu "Exportateur de notes..."
2. Sélectionnez la plage d'exportation. Cela indique à Bookworm si vous souhaitez exporter les notes de l'ensemble du document ou si vous souhaitez simplement exporter les notes de la section actuelle.
3. Sélectionnez le format de sortie. Cela détermine le format du fichier que vous obtenez après l'exportation. L'exportation vers un texte brut vous donne un fichier texte simple et joliment formaté, l'exportation vers HTML vous donne une page Web et l'exportation vers un démarquage vous donne un document démarqué qui est un format de texte populaire parmi les utilisateurs d'ordinateurs experts.
4. Si vous souhaitez que Bookworm ouvre le fichier dans lequel vos notes ont été exportées, vous pouvez cocher la case "Ouvrir le fichier après l'exportation".
5. Cliquez sur Exporter. Il vous sera demandé de sélectionner le nom de fichier du fichier exporté et l'emplacement où le fichier est enregistré. Cliquer sur "Enregistrer" enregistrera le fichier et l'ouvrira si vous avez demandé à Bookworm de le faire.


### Lire à Haute Voix

Bookworm prend en charge la lecture à haute voix du contenu du document ouvert à l'aide d'une voix de synthèse vocale installée. Appuyez simplement sur F5 pour démarrer la lecture, F6 pour mettre en pause ou reprendre la lecture et F7 pour arrêter complètement la lecture.

Vous pouvez configurer le discours de deux manières :
1. Utilisation d'un profil vocal : Un profil vocal contient vos configurations vocales personnalisées, vous pouvez activer/désactiver le profil vocal à tout moment. Vous pouvez accéder aux profils vocaux à partir du menu "Parole" ou en appuyant sur Ctrl + Maj + V. Notez que Bookworm est fourni avec des exemples de profils vocaux intégrés.
2. Les paramètres de voix globaux : ces paramètres seront utilisés par défaut lorsqu'aucun profil vocal n'est actif. Vous pouvez configurer les paramètres vocaux globaux à partir des préférences de l'application.

Lors de la lecture à haute voix, vous pouvez revenir en arrière ou aller en avant par paragraphe en appuyant sur Alt plus les flèches gauche et droite.


### Configurer le Style de Lecture

En plus des paramètres de parole, Bookworm vous donne la possibilité d'affiner son comportement de lecture grâce à ces paramètres. Tous les paramètres suivants peuvent être trouvés dans la page "Lecture" des préférences de l'application.

* Que lire : cette option contrôle ce qui se passe lorsque vous demandez à Bookworm de « jouer » le document en cours. Vous pouvez choisir de "Lire l'intégralité du document", "Lire la section courante", ou lire simplement "La page courante". Par défaut, Bookworm lit l'intégralité du document de manière continue, sauf si vous lui demandez de s'arrêter lorsqu'il atteint la fin de la page ou la fin de la section en cours.
* Par où commencer : cette option contrôle la position à partir de laquelle commencer la lecture à voix haute. Vous pouvez choisir de commencer la lecture à partir de la "Position du curseur" ou du "Début de la page courante".
* Comment lire : cet ensemble d'options contrôle le comportement de Bookworm lors de la lecture à haute voix. Vous pouvez activer/désactiver l'une des options suivantes en cochant/décochant sa case respective :


* Surligner le texte parlé : si cette option est activée, le texte actuellement prononcé est mis en évidence visuellement.
* Sélectionner le texte parlé : si cette option est activée, le texte actuellement parlé est sélectionné. Cela vous permet, par exemple, d'appuyer sur Ctrl + C pour copier le paragraphe actuellement prononcé.
* Jouer le son de fin de section : si cette option est activée, Bookworm joue un petit son lorsqu'il atteint la fin d'une section.


### Mode de Lecture en Continu

En plus des fonctionnalités de synthèse vocale intégrées de Bookworm, vous pouvez profiter de la fonctionnalité de lecture continue de votre lecteur d'écran (également appelée « dire tout »). Bookworm prend en charge cette fonctionnalité via son « mode de lecture continue ». Ce mode est actif par défaut, et vous pouvez le désactiver depuis la page "Lecture" des préférences de l'application. Lorsque le mode de lecture continue est actif, les pages sont tournées automatiquement au fur et à mesure que le lecteur d'écran progresse dans le document.

Notez qu'en raison de la manière dont cette fonctionnalité est actuellement implémentée, les limitations suivantes doivent être attendues :

* La lecture continue sera interrompue si une page vide est atteinte. Si vous avez atteint une page vide, accédez simplement à une page non vide et réactivez la fonctionnalité de lecture continue de votre lecteur d'écran à partir de là.
* Déplacer le curseur vers le dernier caractère de la page passera immédiatement à la page suivante



### Affichage d'une Version Entièrement Rendue de la Page Actuelle

Bookworm vous permet d'afficher une version entièrement rendue du document. Lorsqu'un document est ouvert, vous pouvez appuyer sur Ctrl + R ou sélectionner l'élément de menu "Rendu de la page" dans le menu Outils. Nous appelons cette vue « la vue de rendu » par opposition à la vue textuelle par défaut.

Lorsque vous êtes dans la vue de rendu, vous pouvez utiliser les commandes de zoom habituelles pour effectuer un zoom avant et arrière sur la page :

* Ctrl + = zoom-avant 
* Ctrl + - zoom-arrière
* Ctrl + 0 rétablir le niveau de zoom

Notez que vous pouvez également utiliser les commandes de navigation dans le document, mentionnées ci-dessus, pour naviguer dans la vue de rendu. Vous pouvez appuyer sur la touche d'échappement pour fermer cette vue et revenir à la vue textuelle par défaut.


### Accéder à une Page Spécifique

Pour accéder à une page spécifique du document actuellement ouvert, appuyez sur Ctrl + G ou sélectionnez l'élément de menu "Aller à..." dans le menu Outils pour afficher la boîte de dialogue "Aller à la page". Dans cette boîte de dialogue, vous pouvez saisir le numéro de n'importe quelle page vers laquelle vous souhaitez naviguer, et Bookworm vous y amènera. Notez que cette boîte de dialogue vous indiquera le nombre total de pages trouvées dans le document en cours.

 
### Chercher dans le Document

Pour rechercher un terme spécifique ou une partie de texte dans le document actuellement ouvert, vous pouvez appuyer sur Ctrl + F pour faire apparaître la « boîte de dialogue de recherche de document ». Cette boîte de dialogue vous permet de saisir le texte que vous souhaitez rechercher ainsi que de configurer le processus de recherche lui-même. Les options suivantes sont disponibles :

* Sensible à la casse : La recherche prendra en compte la casse des lettres du terme recherché.
* Mot entier uniquement : le terme de recherche doit être trouvé comme un mot entier, c'est-à-dire pas comme une partie d'un autre mot
* Plage de recherche : Cela vous permet de limiter la recherche à certaines pages ou à une section spécifique.

Après avoir cliqué sur le bouton OK dans la "Boîte de dialogue de recherche de document", une autre boîte de dialogue contenant les résultats de la recherche s'affichera. Cliquer sur n'importe quel élément de la liste des résultats de recherche vous amènera immédiatement à la position de ce résultat avec le terme de recherche mis en évidence pour vous.

Notez que si vous avez fermé la fenêtre des résultats de la recherche, vous pouvez appuyer sur F3 et Maj + F3 pour passer respectivement à l'occurrence suivante et précédente de la dernière recherche.


## Gérer les Associations de Fichiers

Le bouton "Gérer les associations de fichiers", situé dans la page générale des préférences de l'application, vous aide à gérer les types de fichiers associés à Bookworm. Associer des fichiers à Bookworm signifie que lorsque vous cliquez sur un fichier dans l'explorateur Windows, ce fichier est ouvert par défaut dans Bookworm. Notez que cette boîte de dialogue est toujours présentée à l'utilisateur lors de la première exécution du programme.

Après avoir lancé le gestionnaire d'associations de fichiers, vous aurez les options suivantes :

* Associer tout : cela modifie vos paramètres de sorte que si un fichier est pris en charge par Bookworm, Windows utilisera Bookworm pour l'ouvrir.
* Dissocier tous les types de fichiers pris en charge : cela supprimera les associations de fichiers précédemment enregistrées
* Boutons individuels pour chaque type de fichier pris en charge : cliquer sur n'importe quel bouton associera son type de fichier respectif à Bookworm.


## Mettre à Jour Bookworm

Par défaut, Bookworm recherche de nouvelles versions au démarrage. Cela garantit que vous obtenez le plus tôt possible le dernier et le meilleur de Bookworm. Vous pouvez désactiver ce comportement par défaut à partir des préférences de l'application. Vous pouvez également rechercher les mises à jour manuellement en cliquant sur l'élément de menu « Rechercher les mises à jour » situé dans le menu « Aide ».

Dans tous les cas, lorsqu'une nouvelle version est trouvée, Bookworm vous demandera si vous souhaitez l'installer. Si vous cliquez sur "Oui", l'application ira de l'avant et téléchargera le pack de mise à jour et affichera une boîte de dialogue indiquant la progression du téléchargement. Une fois la mise à jour téléchargée, Bookworm vous alertera avec un message, vous indiquant qu'il va redémarrer l'application afin de mettre à jour. Cliquez simplement sur "OK" pour terminer le processus de mise à jour.


## Signaler des Problèmes

En tant que développeurs aveugles, notre responsabilité est de développer des applications qui nous offrent une indépendance, ainsi qu'à nos amis aveugles du monde entier. Donc, si vous avez trouvé Bookworm utile de quelque manière que ce soit, aidez-nous à améliorer Bookworm pour vous et pour les autres. À ce stade initial, nous souhaitons que vous nous informiez de toute erreur que vous pourriez rencontrer lors de votre utilisation de Bookworm. Pour ce faire, ouvrez un nouveau problème avec les détails de l'erreur sur [le suivi des problèmes](https://github.com/mush42/bookworm/issues/). Votre aide est grandement appréciée.

Avant de soumettre un nouveau problème, assurez-vous que vous avez exécuté Bookworm en mode débogage. Pour activer le mode débogage, allez dans le menu "Aide", puis cliquez sur "Redémarrer avec le mode débogage activé" et essayez de reproduire le problème avec le mode débogage activé. Dans la majorité des cas, lorsque l'erreur se reproduit avec le mode débogage activé, une boîte de dialogue s'affiche avec les détails de cette erreur. Vous pouvez ensuite copier ces informations et les inclure dans votre rapport de problème.

Notez que certains problèmes peuvent être difficiles à reproduire, ils disparaissent lorsque vous redémarrez le programme. Dans ce cas, vous pouvez signaler le problème sans les informations détaillées du mode de débogage. Assurez-vous simplement d'inclure autant d'informations que possible sur les détails de votre système et le scénario d'utilisation.


## Nouvelles et Mises à Jour

Pour vous tenir au courant des dernières nouvelles concernant Bookworm, vous pouvez visiter le site Web de Bookworm à l'adresse : [github.com/blindpandas/bookworm](https://github.com/blindpandas/bookworm/). Vous pouvez également suivre le développeur principal, Musharraf Omer, sur [\@mush42](https://twitter.com/mush42/) sur Twitter.


## Licence

**Bookworm ** est protégé par le droit d'auteur (c) 2019 Musharraf Omer et les contributeurs de Bookworm. Il est sous licence [MIT License](https://github.com/mush42/bookworm/blob/master/LICENSE).
