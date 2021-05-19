# Manual de Usuario de Bookworm

## Introducción

**Bookworm** es un lector de Ebooks accesible que le permite a las personas ciegas y de baja visión leer libros electrónicos de manera fácil y sin complicaciones. Entre lo destacable de Bookworm se encuentra:

* Soporte para los formatos de E-book más populares, incluyendo EPUB y PDF
* Usted puede agregar marcadores con nombre indicando posiciones de interés en el texto para una referencia posterior
* Usted puede añadir notas para capturar opiniones de interés o crear un resumen del contenido en una posición específica del texto. Bookworm le permite desplazarse a una nota que desee para su revisión. Después, podrá exportar dichas notas a un archivo de texto o a un documento HTML para una referencia posterior.
* Hay dos estilos diferentes para visualizar las páginas: texto plano e imágenes completamente renderizadas y acercables.
* Búsqueda completa de texto con opciones de búsqueda personalizables
* Se soporta ampliamente la navegación del libro por tabla de contenidos para todos los formatos
* Soporte para la lectura de libros en voz alta usando Texto a Voz, con parámetros de voz configurables.
* Es posible personalizar el texto a voz mediante perfiles. ¡Cada perfil de voz configura el estilo de la voz y usted puede activar/desactivar cada perfil, incluso mientras se lee en voz alta!
* Soporta comandos estándar para acercar/alejar/restablecer zoom, Ctrl + =, Ctrl + - y Ctrl + 0 respectivamente. Esta funcionalidad está disponible tanto en la vista de texto plano como en la página renderizada.
* Se soporta la exportación de cualquier E-book a un archivo de texto plano.


## Instalación

Para hacer que Bookworm funcione en su equipo, siga estos pasos:

1. Lleve su navegador al  [sitio oficial de Bookworm](https://mush42.github.io/bookworm/) y descargue el instalador que corresponda a su sistema operativo. Bookworm se distribuye de dos formas: 

* Un instalador para ejecutarse en la variante 32 bits de Windows
* Un instalador para equipos con una variante 64 bits de Windows 

2. Abra el instalador y siga las instrucciones
3. Después de que la instalación se haya completado con éxito, puede iniciar Bookworm desde el escritorio o desde la lista de programas ubicada en el menú inicio


## Uso

### Abriendo un libro

puede abrir un libro seleccionando la opción  "Abrir..." desde el menú archivo. Como alternativa, puede usar el atajo de teclado Ctrl+O. De cualquier forma, se mostrará un conocido diálogo para abrir archivos. Navegue hasta el ebook y seleccione abrir para que se cargue.

### La ventana del lector

La ventana principal de Bookworm se compone de dos partes:

1. La "Tabla de contenido": Aquí aparecerán los capítulos del libro. Esto le permite explorar la estructura del contenido. Use las teclas de navegación para navegar por los capítulos y presione enter para desplazarse al que desee.
2. El área textual visible: Esta parte contiene el texto de la página actual. En esta sección puede usar los comandos regulares de lectura para navegar por el texto. Además, dispone de los siguientes comandos de teclado para navegar por el libro::

* Enter: se desplaza a la siguiente página en la sección actual
* Retroceso: se desplaza a la página anterior en la sección actual
* Si el cursor está en la primera línea, presionando la flecha arriba dos veces seguidas le llevará a la página anterior.
* Si el cursor está en la última línea, presionando la flecha abajo dos veces seguidas le llevará a la página siguiente.
* Alt + Inicio: se desplaza a la primera página de la sección actual
* Alt + Fin: se desplaza a la última página de la sección actual
* Alt + Avance de página: se desplaza a la sección siguiente
* Alt + Retroceso de página: se desplaza a la sección anterior


### Marcadores y notas

Bookworm le permite  hacer anotaciones en el libro actualmente abierto. Puede agregar un marcador para recordar una posición específica en el libro y, más tarde, saltar rápidamente hacia ella. También puede tomar una nota para capturar una idea o resumir su contenido.

#### Agregar marcadores

Durante la lectura, puede presionar Ctrl + B (o seleccionar el elemento "Agregar marcador" desde el menú "Anotaciones") para añadir un marcador. Éste se añadirá en la posición actual del cursor. Se le pedirá que proporcione un título para el marcador. Escriba el título que desee y haga clic en el botón Aceptar. Se añadirá un marcador en la posición correspondiente y la línea actual se verá resaltada.

#### Visualizando marcadores

Presione Ctrl + Shift + B o seleccione la opción "Ver marcadores" del menú "Anotaciones". Se mostrará un diálogo con los marcadores agregados. Haciendo clic en cualquier elemento de la lista de marcadores le llevará a la posición de dicho marcador.

Adicionalmente, puede presionar F2 para editar el título del marcador en cuestión, o puede hacer clic en el botón "eliminar", o presionar la tecla "Suprimir"  del teclado para eliminar el marcador seleccionado.

#### Tomar notas

Durante la lectura de un libro, puede presionar Ctrl + N o elegir  la opción "tomar nota" del menú "anotaciones" para proceder. Se agregará una nota en la posición actual del cursor. Se le pedirá que especifique un título y el contenido para la nota. Escriba el título deseado y el contenido y haga clic en el botón Aceptar. Se creará una nota en la ubicación actual.

Cuando navegue a una página que contenga al menos una nota, se oirá un sonido indicando que existe una nota en esa página.

#### Gestionando las notas

Presione Ctrl + Shift + N o seleccione el elemento "Gestionar notas" del menú "Anotaciones". Se mostrará un diálogo con las notas agregadas. Haciendo clic en la lista de notas lo llevará inmediatamente a la posición de la nota. Eligiendo el botón "Ver" se abrirá un diálogo mostrando el título y el contenido de la nota seleccionada.

También puede hacer clic en el botón "Editar" para editar el título y el contenido de la nota, presionar F2 para cambiar el título de la nota en cuestión, o puede hacer clic en el botón "Eliminar", o presionar suprimir en el teclado.

#### Exportando las notas

Bookworm le permite exportar sus notas a un archivo de texto plano o a un documento HTML, el cual podrá abrir en su explorador web. Bookworm también le permite opcionalmente exportar sus notas a markdown, que es un formato de texto base estructurado popular entre usuarios informáticos expertos.

Para exportar las notas, siga estos pasos:

1. En el menú "Anotaciones" seleccione el elemento "exportador de notas"...
2. Seleccione el rango de exportación. Esto indicará a Bookworm que desea exportar las notas ya sea de todo el libro o exportar las notas de la sección actual. 
3. Seleccione el formato de salida. Esto determinará el formato del archivo conseguido tras la exportación. Exportando a texto plano le entregará un archivo de texto simple pero formateado, exportando a HTML obtendrá una página web y seleccionando markdown recibirá un documento markdown que es un formato de texto base estructurado popular entre usuarios informáticos expertos.
4. Si necesita que Bookworm abra el archivo que contiene las notas exportadas, puede marcar la casilla "abrir archivo tras la exportación".
5. Haga clic en Exportar. Se le pedirá que seleccione un nombre para el archivo exportado y una ubicación hacia la que se guardará. Haciendo clic en "guardar" se almacenará el archivo y se abrirá si le ha indicado a Bookworm tal acción.


### Lectura en voz alta

Bookworm soporta leer el contenido del libro abierto utilizando una voz TTS. Solamente presione F5 para iniciar la voz, , F6 para pausar o reanudar y F7 para detenerla por completo.

Usted puede configurar la voz de dos maneras:
1. Usando un perfil de voz: un perfil de voz contiene sus ajustes personalizados del habla, que puede ser activado o desactivado en cualquier momento. Puede acceder a los perfiles de voz desde el menú voz o presionando Ctrl + Shift + V. Nótese que Bookworm ofrece algunos perfiles preestablecidos.
2. Mediante los ajustes globales TTS: estos ajustes se usarán de forma predeterminada si no hay un perfil de voz activo. Usted puede configurar los ajustes globales de voz desde las preferencias de la aplicación.

Durante la lectura, usted puede moverse hacia adelante y atrás por párrafo presionando Alt más las flechas izquierda y derecha.


### Configurando el estilo de lectura

Además de los ajustes de voz, Bookworm le dal a posibilidad de modificar su comportamiento al leer mediante estas configuraciones. Todos los ajustes siguientes se encuentran en la página "Lectura" desde las preferencias de la aplicación.

* Al reproducir: Esta opción controla lo que sucede al indicarle a Bookworm que reproduzca el libro actual. Puede elegir entre  "Leer todo el libro", "Leer la sección actual" o leer sólo "La página actual". De forma predeterminada, Bookworm lee todo el libro continuamente, a menos que se le ordene detenerse cuando se alcance el final de la página o de la sección.
* Empezar a leer desde: Esta opción controla la posición desde la que se inicia la lectura en voz alta. Usted puede elegir entre empezar a leer desde la posición del cursor o de la página actual.
* Durante la lectura: el siguiente conjunto de opciones controla cómo se comporta Bookworm mientras se lee en voz alta. Puede activar o desactivar cualquiera de las opciones siguientes marcando o desmarcando las casillas correspondientes:

* Resaltar texto leído: Si esta opción está activada, el texto que se lee será visualmente resaltado
* Seleccionar texto leído: si esta opción está activada, el texto leído será seleccionado. Por ejemplo, esto le permite presionar CTRL+C para copiar el párrafo leído actualmente.
* Reproducir sonido para fin de sección: Si esta opción está activada, Bookworm reproduce un sonido cuando se alcance el final de sección.


### Modo de lectura continua

Además de las funciones incluidas de Texto a voz en Bookworm, puede aprovechar la función lectura continua de lector de pantalla (también conocida como "Verbalizar todo"). Bookworm ofrece soporte para esta característica mediante el "modo de lectura continua". De forma predeterminada este modo está activo y puede desactivarse en la pestaña Lectura en las preferencias de la aplicación. Mientras que el modo de lectura continua esté en uso, se irán pasando las páginas en cuanto el lector de pantalla progrese en el libro.

Nótese que debido a la forma en que este modo se ha implementado, deben tenerse en cuenta las siguientes limitaciones:

* La lectura continua se interrumpirá si se llega a una página en blanco. Si este es el caso, simplemente navegue a una página que no esté en blanco y reactive la lectura continua del lector de pantalla desde allí.
* Si se mueve el cursor al último carácter en la página, se cambiará de inmediato a la página siguiente.



### Ver una versión renderizada de la página actual

Bookworm le permite ver una versión renderizada completa del libro. Mientras el libro esté abierto, puede presionar Ctrl + R o seleccionar la opción "Renderizar página" en el menú Herramientas. Le llamamos "vista renderizada" en contraste con la vista textual predeterminada.

Cuando esté en la vista renderizada, puede utilizar los comandos estándar para acercar o alejar la página:

* Ctrl + = Aumentar el zoom
* Ctrl + - Disminuir el zoom
* Ctrl + 0 Restablecer el nivel de zoom

Cabe mencionar que también puede usar los comandos de navegación del libro citados anteriormente  para desplazarse por la vista renderizada. También puede presionar Escape para cerrar esta vista y regresar a la ventana textual por defecto.


Navegando a una página específica

Para navegar a una página de su elección en el libro actualmente abierto, Presione Ctrl + G o seleccione la opción "Ir a..." desde el menú herramientas para mostrar este diálogo. Aquí puede escribir el número de cualquier página hacia donde quiera moverse y Bookworm lellevará a ella. Nótese que este diálogo le indicará el número total de páginas disponibles en el libro.

 
### Buscando en el libro

Para buscar un término específico o una porción de texto en el libro actualmente abierto, puede presionar Ctrl + F para mostrar el diálogo "buscar en el libro". Este diálogo le permite escribir el texto que desee buscar así como configurar el proceso de búsqueda. Las siguientes opciones están disponibles:

* Sensible a las mayúsculas: La búsqueda tendrá en cuenta las mayúsculas o minúsculas en el término de búsqueda.
* Buscar palabras completas: el término de búsqueda debe encontrarse como una palabra entera, p. ej. no como parte de otra existente.
* Rango de búsqueda: Esto le permite limitar la búsqueda a ciertas páginas o a una sección específica.

Tras hacer clic en Aceptar en el "diálogo buscar", aparecerá un segundo diálogo con los resultados de la búsqueda. Haciendo clic en cualquier elemento en la lista de resultados lo llevará a la posición correspondiente con el término de búsqueda resaltado para usted.

Nótese que si ya ha cerrado la ventana con la lista de resultados, puede presionar F3 y Shift+F3 para moverse a la aparición anterior y siguiente de la última búsqueda, respectivamente.


## Gestionando asociaciones de archivo

el botón "Administrar asociaciones" que se encuentra en la página general en las preferencias de la aplicación le ayuda a administrar qué tipos de archivo están asociados con Bookworm. Asociar archivos con Bookworm significa que cuando abra un archivo en el explorador de Windows, ese archivo será abierto por Bookworm por defecto. Nótese que este diálogo siempre se muestra al usuario tras la primera ejecución.

Una vez que inicie el gestor de asociaciones de archivo, contará con las siguientes opciones:

* Asociar todo: esto modifica los ajustes de tal forma que si Bookworm soporta un archivo, Windows lo utilizará para abrir el archivo.
* Desasociar todos los tipos de archivos soportados: esto eliminará las asociaciones de archivo anteriormente guardadas.
* Botones individuales para cada tipo de archivo soportado: haciendo clic en cualquier botón de ellos, se asociará su respectivo tipo de archivo con Bookworm.


Actualizando Bookworm

De forma predeterminada, Bookworm comprueba si hay nuevas versiones al iniciarse. Esto asegura que usted consiga lo último y lo mejor de Bookworm lo más pronto posible. Usted puede desactivar este comportamiento desde las preferencias de la aplicación. También puede hacer esto manualmente seleccionando el elemento "Comprovar actualizaciones" en el menú "Ayuda".

De cualquier forma, si se encuentra una nueva versión, Bookworm le preguntará si desea instalarla. Si selecciona "Sí", la aplicación proseguirá y descargará el paquete de actualización, mostrando un diálogo indicando el proceso de descarga. Después de que haya finalizado, Bookworm le alertará con un mensaje indicando que la aplicación debe reiniciarse para actualizarse.


## Reportando problemas / dificultades

Como desarrolladores ciegos, nuestra responsabilidad es desarrollar aplicaciones que brinden independencia para nosotros y nuestros compañeros ciegos por todo el mundo. Por lo tanto, si ha encontrado útil Bookworm de alguna forma, por favor ayúdenos en mejorar Bookworm para usted y los demás. En esta etapa inicial, queremos que nos haga saber sobre cualquier error que encuentre al usar Bookworm. Para ello, abra un nuevo asunto con detalles del error en [el Rastreador de problemas](https://github.com/mush42/bookworm/issues/). Muchas gracias por su ayuda.

Antes de  enviar un nuevo problema, asegúrese de haber ejecutado Bookworm en modo de depuración. Para activarlo, vaya al menú "Ayuda" y haga clic en iniciar en modo de depuración activado e intente reproducir dicho problema. En la mayoría de los casos, cuando se produzca el error de nuevo con este modo activo, se mostrará un diálogo con los detalles del error. Así podrá copiar esta información e incluirla con el reporte del fallo.

Note que algunos fallos pueden ser difíciles de reproducir ya que desaparecen al reiniciar el programa. En este caso, es válido reportar el error con el modo de depuración activado. Sólo asegúrese de incluir cuanta más información le sea posible particularmente de su sistema y el escenario de uso.


## Noticias y actualizaciones

Para mantenerse al tanto con las últimas noticias de Bookworm, puede visitar el sitio web de Bookworm (en inglés): [mush42.github.io/bookworm](https://mush42.github.io/bookworm/). También puede seguir al desarrollador principal, Musharraf Omer, como [@mush42](https://twitter.com/mush42/) en Twitter.


## Licencia

**Bookworm** es copyright (c) 2019 Musharraf Omer y ayudantes de Bookworm. Bajo la [Licencia MIT License](https://github.com/mush42/bookworm/blob/master/LICENSE).
