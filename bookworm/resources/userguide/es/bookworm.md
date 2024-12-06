# Guía de usuario de Bookworm

## Introducción

Bookworm es un lector de documentos que le permite leer PDF, EPUB, MOBI y muchos otros formatos de documentos utilizando una interfaz versátil, pero sencilla y muy accesible.

Bookworm te proporciona un rico conjunto de herramientas para leer tus documentos. Puede buscar en sus documentos, marcar y resaltar contenidos de interés, utilizar la conversión de texto a voz y convertir documentos escaneados a texto sin formato mediante el reconocimiento óptico de caracteres (OCR).

Bookworm funciona con el sistema operativo Microsoft Windows. Funciona bien con tus lectores de pantalla favoritos, como NVDA y JAWS. Incluso cuando un lector de pantalla no está activo, Bookworm puede actuar como una aplicación de voz utilizando las funciones incorporadas de texto a voz.


## Características

* Admite más de 15 formatos de documento, incluidos EPUB, PDF, MOBI y documentos de Microsoft Word.
* Admite navegación estructurada mediante comandos de navegación de una sola letra para saltar entre títulos, listas, tablas y citas
* Búsqueda de texto completo con opciones de búsqueda personalizables
* Herramientas de anotación avanzadas y fáciles de usar. Puede añadir marcadores con nombre para marcar lugares de interés en el texto para su posterior consulta, y puede añadir comentarios para capturar un pensamiento interesante o crear un resumen del contenido en una posición concreta del texto. Bookworm te permite saltar rápidamente a un comentario concreto y visualizarlo. Más tarde, puede exportar estos comentarios a un archivo de texto o documento HTML para su uso posterior.
* Para los documentos PDF, Bookworm admite dos estilos diferentes de visualización de las páginas: texto sin formato e imágenes con zoom.
* Soporta el uso de OCR para extraer texto de documentos e imágenes escaneados utilizando el motor OCR integrado de Windows10. También tiene la opción de descargar y utilizar el motor de OCR Tesseract disponible gratuitamente dentro de Bookworm.
* Busque la definición de un término en Wikipedia y lea artículos de Wikipedia desde Bookworm.
* Un extractor de artículos web incorporado que le permite abrir URLs y extraer automáticamente el artículo principal de la página.
* La navegación de documentos a través de la tabla de contenido está ampliamente soportada para todos los formatos de documento.
* Soporte para lectura de libros en voz alta usando Texto-a-voz, con opciones de voz personalizables usando perfiles de voz.
* Soporte para zoom de texto usando los comandos estándar de zoom-in/zoom-out/reset.
* Soporte para exportar cualquier formato de documento a un archivo de texto plano.


## Instalación

Para instalar y ejecutar Bookworm en su ordenador, visite primero el [sitio web oficial de Bookworm](https://github.com/blindpandas/bookworm)

Bookworm está disponible en tres versiones:

* Instalador de 32 bits para ordenadores con Windows de 32 o 64 bits.
* Instalador de 64 bits para ordenadores con Windows de 64 bits.
* Versión portable para ejecutar desde una unidad flash

Si tiene voces SAPI5 heredadas instaladas en su sistema y desea utilizarlas con Bookworm, le recomendamos que instale la versión de 32 bits de Bookworm o que utilice la versión portable de 32 bits.

Tras seleccionar la versión que más te convenga, descárgala. Si has descargado la versión instalable de Bookworm, ejecuta el archivo .exe y sigue las instrucciones que aparecen en pantalla, o si has optado por utilizar una copia portable de Bookworm, descomprime el contenido del archivo donde quieras y ejecuta el ejecutable de Bookworm para iniciar la copia portable.


## Uso


### Abrir un documento

Puede abrir un documento seleccionando la opción «Abrir...» del menú «Archivo». También puede utilizar el atajo de teclado Ctrl+O. En cualquiera de los dos casos, aparecerá el conocido cuadro de diálogo «Abrir archivo». Busque su documento y haga clic en Abrir para cargarlo.


### La ventana del lector

La ventana principal de Bookworm consta de las dos partes siguientes:

1. La «Tabla de contenidos»: Esta parte muestra los capítulos del documento. Le permite explorar la estructura del contenido. Utilice las teclas de navegación para navegar por los capítulos, y pulse intro para navegar a un capítulo específico.

2. El área «Vista textual»: Esta parte contiene el texto de la página actual. En esta parte puede utilizar sus comandos de lectura habituales para navegar por el texto. Además, puede utilizar los siguientes atajos de teclado para navegar por el documento:

* Intro: pasar a la página siguiente de la sección actual.
* Retroceso: navegar a la página anterior de la sección actual.
* Mientras el cursor está en la primera línea, pulsando dos veces seguidas la flecha hacia arriba se pasa a la página anterior.
* Mientras el cursor está en la última línea, pulsando dos veces seguidas la flecha hacia abajo se pasa a la página siguiente.
* Alt + Inicio: navegar a la primera página de la sección actual.
* Alt + Fin: navegar a la última página de la sección actual.
* Alt + página abajo: navegar a la sección siguiente.
* Alt + página arriba: navegar a la sección anterior;
* F2: ir al siguiente marcador;
* Mayús + F2: ir al marcador anterior;
* F8: ir al comentario siguiente;
* Mayús + F8: ir al comentario anterior;
* F9: ir al siguiente resaltado
* Shift + F9: ir al resaltado anterior;
* ctrl + enter: abrir cualquier enlace interno o externo si el documento lo contiene. Los enlaces internos son enlaces creados por el índice del documento en algunos formatos, los enlaces externos son enlaces normales abiertos por el navegador. Dependiendo del tipo de enlace, si el enlace es interno, es decir, el enlace a la tabla de contenidos, al pulsar el atajo de teclado anterior se moverá el foco a la tabla de contenidos deseada, y si el enlace es externo, se abrirá en el navegador predeterminado del sistema.


### Marcadores y comentarios

Bookworm le permite hacer anotaciones en un documento abierto. Puede añadir un marcador para recordar una ubicación específica en un documento y saltar rápidamente a ella. Además, puede añadir un comentario para capturar una idea o resumir el contenido.


#### Añadir marcadores

Mientras lees un documento, puedes pulsar Ctrl + B (o seleccionar la opción de menú Añadir marcador) en el menú Anotaciones para añadir un marcador. El marcador se añadirá en la posición actual del cursor. Alternativamente, puede añadir un marcador con nombre pulsando ctrl+mayús+b, se abrirá una ventana que le pedirá el nombre del marcador o, alternativamente, seleccione Añadir marcador con nombre en el menú Anotaciones.


#### Visualización de marcadores

Vaya al menú Anotaciones y seleccione la opción «Ver marcadores». Aparecerá un cuadro de diálogo con los marcadores añadidos. Al hacer clic en cualquier elemento de la lista de marcadores, accederá inmediatamente a la posición de ese marcador. Alternativamente, para saltar rápidamente a través de los marcadores añadidos, puedes utilizar las teclas f2 y shift+f2, que irán directamente a la posición del cursor del marcador.


#### Añadir comentarios

Mientras lees un documento, puedes pulsar Ctrl+m (o seleccionar la opción de menú Añadir comentario) en el menú Anotaciones para añadir un comentario. Se te pedirá el contenido del comentario. Introduzca el contenido y haga clic en «Aceptar». El comentario se añadirá en la ubicación actual.

Cuando vaya a una página que contenga al menos un comentario, oirá un pequeño sonido que le indicará que hay un comentario en la página actual.


#### Gestión de comentarios

Seleccione la opción «Comentarios guardados» del menú «Anotaciones». Aparecerá un cuadro de diálogo con los comentarios añadidos. Si hace clic en cualquier elemento de la lista de comentarios, saltará inmediatamente a la posición de ese comentario. Al hacer clic en el botón «Ver» se abrirá un cuadro de diálogo que mostrará la etiqueta y el contenido del comentario seleccionado.

También puede hacer clic en el botón «Editar» para cambiar la etiqueta y el contenido del comentario seleccionado, pulsar F2 para editar la etiqueta del comentario seleccionado en su lugar, o puede pulsar la tecla Supr de su teclado o el atajo de teclado Alt+d para eliminar el comentario seleccionado.


#### Exportar comentarios

Bookworm le permite exportar sus comentarios a un archivo de texto plano o a un documento HTML, que puede abrirse en un navegador web. Opcionalmente, Bookworm le permite exportar sus comentarios a Markdown, que es un formato de texto para escribir documentos estructurados muy popular entre los usuarios avanzados de ordenadores.

Para exportar comentarios, siga estos pasos:

1. En el menú de anotaciones, navegue hasta Comentarios guardados;
2. Busque «Exportar» y pulse Intro. También puede utilizar la combinación de teclas Alt+x para abrir el menú de exportación;

A continuación, tiene las siguientes opciones, puede desmarcar o dejar marcada cualquier opción que desee:

* Incluir título del libro - esta opción le permite incluir el título del libro en el archivo de salida final cuando exporta comentarios;
* Incluir título de sección - opción que se utiliza para incluir el título de la sección en la que se deja el comentario;
* Incluir número de página - esta opción se utiliza para incluir los números de las páginas en las que se hizo el comentario;
* Incluir etiquetas - esta opción se utiliza para incluir o no las etiquetas del comentario que se hicieron durante la anotación.

Después de especificar la opción correcta según sus necesidades, debe seleccionar el formato de salida del archivo, de los que actualmente hay tres: formato de texto sin formato, Html y Markdown.
Una vez seleccionado el formato deseado, aparece un área de texto de sólo lectura denominada «Archivo de salida» y vacía por defecto. Debe hacer clic en el botón Examinar o, alternativamente, utilizar alt+b para abrir una ventana del explorador y especificar el nombre de archivo y la carpeta donde se guardará el archivo de salida.
Al especificar un nombre de archivo y una carpeta de archivo, hay una casilla de verificación «Abrir archivo después de exportar» que permite a Bookworm abrir automáticamente el archivo de salida después de guardarlo. Desactive esta casilla si no desea abrir automáticamente el archivo guardado y haga clic en Aceptar. El archivo se guardará en la carpeta especificada y podrá abrirlo con Bookworm o con cualquier otro editor de texto, como «Bloc de notas».


### Lectura en voz alta

Bookworm permite leer en voz alta el contenido del documento abierto utilizando una voz de texto a voz instalada. Basta con pulsar F5 para iniciar la reproducción, F6 para pausarla o reanudarla y F7 para detenerla por completo.

Puede configurar el habla de dos maneras:
1. Utilizando un perfil de voz: Un perfil de voz contiene sus configuraciones de habla personalizadas, puede activar/desactivar el perfil de voz en cualquier momento. Puede acceder a los perfiles de voz desde el menú de voz o pulsando Ctrl + Mayús + V. Tenga en cuenta que Bookworm viene con algunos perfiles de voz incorporados ejemplares.
2. Los ajustes globales de voz: estos ajustes se utilizarán por defecto cuando no haya ningún perfil de voz activo. Puede configurar los ajustes globales de voz desde las preferencias de la aplicación. 

Durante la lectura en voz alta, puedes saltar hacia atrás o hacia delante por párrafos pulsando Alt más las teclas de flecha izquierda y derecha.


### Configuración del estilo de lectura

Además de los ajustes de voz, Bookworm te da la posibilidad de ajustar su comportamiento de lectura a través de estos ajustes. Todos los ajustes siguientes se pueden encontrar en la página de lectura de las preferencias de la aplicación.

* Al pulsar Reproducir: Esta configuración determina lo que sucede cuando le dices a Bookworm que «Reproduzca» el documento actual. Puede seleccionar «Leer todo el documento», «Leer la sección actual» o leer sólo la «página actual». Por defecto, Bookworm lee continuamente todo el documento a menos que le digas que se detenga cuando llegue al final de la página o al final de la sección actual.
* Empezar a leer desde: esta opción determina la posición desde la que empezar a leer en voz alta. Puedes empezar a leer desde la «Posición del cursor» o desde el «Inicio de la página actual».
* Durante la lectura en voz alta: este conjunto de opciones controla cómo se comporta Bookworm durante la lectura en voz alta. Puede activar/desactivar cualquiera de las siguientes opciones marcando/desmarcando su respectiva casilla:

* Pronunciar el número de página: el texto a voz pronunciará cada página a medida que navegue hasta ella;
* Anunciar el final de las secciones: cuando termine una sección, la voz le avisará;
* Pedir que se cambie a una voz que hable el idioma del libro actual - esta opción determinará si Bookworm avisará o no de una voz incompatible, lo que ocurre por defecto cuando la voz del idioma de texto-a-voz seleccionado difiere del idioma del documento abierto;
* Resaltar texto hablado: si esta opción está activada, el texto hablado en ese momento se resalta visualmente.
* Seleccionar texto hablado: si esta opción está activada, se selecciona el texto hablado en ese momento. Esto le permite, por ejemplo, pulsar Ctrl + C para copiar el párrafo hablado en ese momento.


### Modo de lectura continua

Además de las funciones incorporadas de texto a voz de Bookworm, puede aprovechar la funcionalidad de lectura continua de su lector de pantalla (también conocida como «decirlo todo»). Bookworm proporciona soporte para esta funcionalidad a través de su «modo de lectura continua». Este modo está activo por defecto, y puedes desactivarlo desde la página de lectura de las preferencias de la aplicación. Mientras el modo de lectura continua está activo, las páginas se pasan automáticamente a medida que el lector de pantalla avanza por el documento.

Tenga en cuenta que, debido a la forma en que esta función está implementada actualmente, cabe esperar las siguientes limitaciones:

* La lectura continua se interrumpirá si se llega a una página vacía. Si llega a una página vacía, simplemente navegue a una página que no esté vacía y reactive la funcionalidad de lectura continua de su lector de pantalla desde allí.
* Si mueve el cursor hasta el último carácter de la página, pasará inmediatamente a la página siguiente.


### Ver una versión completamente renderizada de la página actual

Bookworm le permite ver una versión completamente renderizada del documento. Mientras el documento está abierto, puede pulsar Ctrl + R o seleccionar la opción «Renderizar página» del menú del documento. Llamamos a esta vista «Vista de renderizado», en contraposición a la vista textual por defecto.

Cuando esté en la vista de renderizado, puede utilizar los comandos de zoom habituales para acercar o alejar la página:

* Ctrl + = acercar 
* Ctrl + - alejar
* Ctrl + 0 restablecer el nivel de zoom

Tenga en cuenta que también puede utilizar los comandos de navegación del documento, mencionados anteriormente, para navegar por la vista de renderizado. También puedes pulsar la tecla escape para descartar esta vista y volver a la vista textual por defecto.


### Navegar a una página específica

Para navegar a una página específica en el documento actualmente abierto, pulse Ctrl + G, o seleccione la opción «Ir a la página...» del menú de búsqueda para mostrar el diálogo «Ir a la página». En este diálogo puede escribir el número de cualquier página a la que desee navegar, y Bookworm le llevará a ella. Tenga en cuenta que este diálogo le indicará el número total de páginas encontradas en el documento actual.

 
### Búsqueda en el documento

Para encontrar un término específico, o un fragmento de texto en el documento actualmente abierto, puede pulsar Ctrl + F para abrir el «Diálogo de búsqueda en el documento». Este diálogo le permite escribir el texto que desea buscar y configurar el proceso de búsqueda. Dispone de las siguientes opciones:

* Sensible a mayúsculas y minúsculas: La búsqueda tendrá en cuenta las mayúsculas y minúsculas del término buscado.
* Buscar sólo palabra completa: El término buscado debe encontrarse como palabra completa, es decir, no como parte de otra palabra.
* Rango de búsqueda: Permite limitar la búsqueda a determinadas páginas o a una sección específica.

Tras pulsar el botón OK en el «Diálogo del documento de búsqueda», se mostrará otro diálogo con los resultados de la búsqueda. Si hace clic en cualquier elemento de la lista de resultados de la búsqueda, irá inmediatamente a la posición de ese resultado con el término de búsqueda resaltado para usted.

Tenga en cuenta que si ha cerrado la ventana de resultados de búsqueda, puede pulsar F3 y Mayúsculas + F3 para desplazarse a la aparición siguiente y anterior de la última búsqueda, respectivamente.


## Gestionar Asociaciones de Archivos

El botón administrar asociaciones de archivos», que se encuentra en la página general de las preferencias de la aplicación, le ayuda a gestionar qué tipos de archivos están asociados con Bookworm. Asociar archivos con Bookworm significa que cuando pulses sobre un archivo en el explorador de Windows, ese archivo se abrirá en Bookworm por defecto. Tenga en cuenta que este cuadro de diálogo siempre se muestra al usuario la primera vez que inicia el programa y sólo está disponible cuando se utiliza el instalador, en la versión portable esta opción no es necesaria, respectivamente, en la versión portable, la capacidad de asociar archivos está desactivada y se requieren algunos trucos si aún desea que Bookworm abra cualquier documento soportado por defecto.

Una vez que lances el administrador de asociaciones de archivos, tendrás las siguientes opciones:

* Asociar todos: cambia la configuración de modo que si un archivo es compatible con Bookworm, Windows lo abrirá con Bookworm. 
* Desasociar todos los tipos de archivos compatibles: esto eliminará las asociaciones de archivos registradas previamente.
* Botones individuales para cada tipo de archivo soportado: al hacer clic en cualquiera de ellos se asociará su respectivo tipo de archivo con Bookworm.


## Actualizar Bookworm

Por defecto, Bookworm busca nuevas versiones al iniciarse. Esto asegura que obtengas la última y mejor versión de Bookworm lo antes posible. Puedes desactivar este comportamiento por defecto desde las preferencias de la aplicación.   También puedes buscar actualizaciones manualmente haciendo clic en la opción «comprobar actualizaciones» del menú «Ayuda».

En cualquier caso, cuando se encuentre una nueva versión, Bookworm le preguntará si desea instalarla. Si haces clic en «Sí», la aplicación descargará el paquete de actualización y mostrará un cuadro de diálogo indicando el progreso de la descarga. Una vez descargada la actualización, Bookworm te avisará con un mensaje, indicándote que reiniciará la aplicación para actualizar. Haz clic en «Aceptar» para completar el proceso de actualización.


## Notificación de problemas

Como desarrolladores ciegos, nuestra responsabilidad es desarrollar aplicaciones que nos proporcionen independencia a nosotros y a nuestros amigos ciegos de todo el mundo. Así que, si has encontrado Bookworm útil de alguna manera, por favor ayúdanos a hacer Bookworm mejor para ti y para los demás. En esta fase inicial, queremos que nos comentes cualquier error que encuentres durante el uso de Bookworm. Para ello, abre una nueva incidencia con los detalles del error en [el gestor de incidencias](https://github.com/blindpandas/bookworm/issues/). Agradecemos enormemente tu ayuda.

Antes de enviar una nueva incidencia, asegúrate de que has ejecutado Bookworm en modo depuración. Para activar el modo de depuración, vaya al menú «Ayuda» y haga clic en «Reiniciar con el modo de depuración habilitado» e intente reproducir el problema con el modo de depuración activado. En la mayoría de los casos, cuando el error vuelva a producirse con el modo de depuración activado, se mostrará un cuadro de diálogo con los detalles de dicho error. A continuación, puede copiar esta información e incluirla en su informe del problema.

Tenga en cuenta que algunos problemas pueden ser difíciles de reproducir, desaparecen cuando reinicia el programa. En este caso, está bien informar del problema sin la información detallada del modo de depuración. Sólo asegúrese de incluir tanta información como sea posible acerca de las particularidades de su sistema y escenario de uso.


## Noticias y actualizaciones

Para mantenerte al día con las últimas noticias sobre Bookworm, puedes visitar el sitio web de Bookworm en: [github.com/blindpandas/bookworm](https://github.com/blindpandas/bookworm/). También puedes seguir al desarrollador principal, Musharraf Omer, en [@mush42](https://twitter.com/mush42/) en Twitter.


## Licencia

**Bookworm** es copyright (c) 2019-2023 Musharraf Omer y Bookworm Contributors. Está licenciado bajo la [Licencia MIT](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
