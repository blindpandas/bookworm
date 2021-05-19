# Guia do Usuário do Bookworm

## Introdução

O **Bookworm** é um leitor ACESSÍVEL de ebooks que habilita indivíduos cegos e de baixa visão a lerem e-books de maneira fácil e sem incômodos. Os principais destaques do Bookworm são:

* Suporta formatos populares de e-book, incluindo EPUB e PDF
* Podem-se adicionar marcadores com nome para marcar posições interessantes no texto para referência posterior
* Pode adicionar notas para capturar idéias interessantes ou criar um resumo do conteúdo numa posição específica do texto. O Bookworm lhe possibilita pular rapidamente para uma nota específica e exibi-la. Depois, pode exportar essas notas para um arquivo de texto ou um documento HTML para futura referência.
* Dois estilos diferentes de exibição de páginas: texto raso e imagens totalmente renderizadas e ampliáveis.
* Busca em todo o texto com opções de busca personalizáveis
* Suporta ostensiva navegação pelo livro via índice em todos os formatos de e-book
* Suporte a leitura de livros em voz alta usando Texto para Fala, com parâmetros de voz configuráveis.
* Possibilidade de personalizar o texto para fala com perfis de voz. Cada perfil de voz configura o estilo da fala e você pode ativar/desativar qualquer perfil de voz à vontade, mesmo enquanto lê em voz alta!
* Suporte a comandos padrão para zoom-in/zoom-out/restaurar, respectivamente Ctrl + =, Ctrl + - e Ctrl + 0. Essa funcionalidade é suportada na exibição de texto raso e na de página renderizada.
* Suporte à exportação de qualquer formato de e-book para arquivo de texto raso.


## Instalação

Para ter o Bookworm instalado e rodando em seu computador, siga estes passos:

1. Dirija seu navegador web para o [sítio oficial do Bookworm](https://mush42.github.io/bookworm/) e baixe o instalador apropriado a seu sistema operacional. O Bookworm existe em duas versões:

* Um instalador de 32 bits para computadores que rodam a variante de 32 bits de Windows 
* Um instalador de 64 bits para computadores que rodam a variante de 64 bits de Windows 

2. Rode o instalador e siga os diálogos
3. Depois que a instalação tiver acabado com sucesso, pode carregar o Bookworm a partir da *Área de Trabalho* ou da lista de programas localizada no menu Iniciar


## Uso

### Abrir um livro

Pode abrir um livro selecionando o item "Abrir..." no menu "Arquivo". Como alternativa, pode usar o atalho Ctrl+O. De qualquer das formas, o familiar diálogo "Abrir Arquivo" é mostrado. Navegue até o e-book e clique abrir para carregá-lo.

### A janela do leitor

A janela principal do Bookworm consiste nas seguintes duas partes:

1. O "Índice": Esta parte mostra os capítulos do e-book. Ela lhe possibilita explorar a estrutura dos conteúdos. Use as teclas de navegação para navegar pelos capítulos e pressione Enter para navegar a um capítulo específico.

2. A área "Exibição de texto": Esta parte contém o texto da página atual. Nesta parte, pode usar os comandos comuns de leitura para navegar pelo texto. Também pode usar as seguintes teclas de atalho para navegar no e-book:

* Enter: navega para a próxima página na seção atual
* Backspace: navega para a página anterior na seção atual
* Quando o cursor se encontra na primeira linha, pressionar a seta acima duas vezes sucessivamente navega para a página anterior.
* Quando o cursor se encontra na última linha, pressionar a seta abaixo duas vezes sucessivamente navega para a próxima página.
* Alt + Home: navega para a primeira página da seção atual
* Alt + End: navega para a última página da seção atual
* Alt + Page down: navega para a próxima seção
* Alt + Page up: navega para a seção anterior


### Marcadores & Notas

O Bookworm possibilita fazer anotações no livro aberto. Você pode adicionar um marcador para lembrar um local específico do livro e, depois, pular rapidamente para o mesmo. Pode também tomar uma nota para capturar uma idéia ou resumir algum conteúdo.

#### Adicionar marcadores

Enquanto lê um livro, você pode pressionar Ctrl + B (ou selecionar o item "Adicionar marcador" no menu "Anotações") para adicionar um marcador. O marcador é adicionado na posição atual do cursor. Será pedido que você forneça um título para ele. Digite o título desejado e clique no botão OK. Será adicionado um marcador na posição atual e a linha atual será visualmente realsada.

#### Exibindo marcadores

Pressione Ctrl + Shift + B, ou selecione o item "Exibir marcadores" no menu "Anotações". Será mostrado um diálogo contendo marcadores adicionados. Clicar em qualquer item da lista de marcadores levará imediatamente para a posição desse marcador.

Além disso, pode pressionar F2 para editar ali mesmo o título do marcador, ou pode clicar no botão "Delete" ou a tecla "Delete" do teclado para remover o marcador selecionado.

#### Tomar notas

Ao ler um livro, você pode pressionar Ctrl + N (ou selecionar o item "Tomar nota" no menu "Anotações") para tomar uma nota. Ela será adicionada na posição atual do cursor. Será pedido que você forneça o título e o conteúdo da nota. Digite o título e o conteúdo desejados e então clique no botão OK. Será adicionada uma nota no local atual.

Quando navegar para uma página que contém ao menos uma nota, você ouvirá um sonzinho indicando a existência de uma nota na página atual.

#### Gerir notas

Pressione Ctrl + Shift + N ou selecione o item "Gerir notas" no menu "Anotações". Será mostrado um diálogo contendo as notas adicionadas. Clicar em qualquer item da lista de notas levará imediatamente à posição daquela nota. Clicar no botão "Exibir" chamará um diálogo mostrando o título e o conteúdo da nota selecionada.

Também pode clicar no botão "Editar" para editar o título e o conteúdo da nota selecionada, pressionar F2 para editar ali mesmo o título da nota selecionada, ou pode clicar no botão "Delete" ou a tecla "Delete" do teclado para remover a nota selecionada.

#### Exportar notas

O Bookworm lhe possibilita exportar notas para um arquivo de texto raso, ou para um documento HTML que você pode então abrir no navegador web. Opcionalmente, possibilita também exportar as notas para markdown, que é um formato de texto base para escrever documentos estruturados, popular entre usuários expertos de computador.

Para exportar notas, siga estes passos:

1. No menu "Anotações", selecione o item "Exportador de notas..."
2. Selecione o intervalo de exportação. Isto informa ao Bookworm se você quer exportar as notas do livro todo ou quer exportar apenas as notas da seção atual. 
3. Selecione o formato de saída. Isto determina o formato do arquivo que você obtém após exportar. Exportar para um texto raso fornece um arquivo de texto simples e bem formatado, exportar para HTML fornece uma página web e exportar para um markdown fornece um documento markdown que é um formato de texto popular entre usuários expertos de computador.
4. Se quiser que o Bookworm abra o arquivo para o qual as notas forem exportadas, pode marcar a caixa de seleção "Abrir arquivo após exportar".
5. Clique em Exportar. Será pedido que você selecione o nome do arquivo exportado e o local no qual ele será salvo. Clicar em "Salvar" salvará o arquivo e o abrirá se você tiver instruído o Bookworm a fazer isso.


### Ler em voz alta

O Bookworm suporta a leitura do livro aberto em voz alta usando alguma voz de texto para fala instalada. Simplesmente pressione F5 para iniciar a fala, F6 para pausar ou retomar a fala e F7 para interrompê-la completamente.

Pode configurar a fala de duas maneiras:
1. Usando um perfil de voz: Um perfil de voz contém suas configurações personalizadas; você pode ativar/desativar o perfil de voz a qualquer hora. Pode acessar perfis de voz no menu Fala ou pressionando Ctrl + Shift + V. Note que o Bookworm já vem com alguns exemplos embutidos de perfis de voz.
2. As configurações globais de fala: Estas configurações serão usadas por padrão quando nenhum perfil de voz estiver ativo. Você pode mexer nas configurações globais de fala pelas Preferências do aplicativo.

Durante a leitura em voz alta, pode pular para trás ou para frente por parágrafo pressionando Alt mais as setas esquerda e direita.


### Configurar o estilo de leitura

Além das configurações de fala, o Bookworm lhe dá a possibilidade de refinar o comportamento de leitura por meio das seguintes opções. Todas as seguintes opções podem ser achadas na guia Leitura das Preferências do aplicativo.

* O que ler: Esta opção controla o que ocorre quando você instrui o Bookworm a "Reproduzir" o livro atual. Pode escolher "Ler o livro todo", "Ler a seção atual" ou ler apenas "A página atual". Por padrão, o Bookworm lê o livro todo de maneira contínua, a não ser que você o instrua a parar quando chega ao fim da página ou o fim da seção atual.
* Onde começar: Esta opção controla a posição de onde começar a leitura em voz alta. Você pode escolher começar a ler da "Posição do cursor" ou o "Início da página atual".
* Como ler: Este conjunto de opções controla como o Bookworm se comporta enquanto lê em voz alta. Você pode ligar/desligar qualquer uma das seguintes opções marcando/desmarcando a respectiva caixa de seleção:

* Realsar texto falado: Se esta opção estiver ligada, o texto atualmente falado é visualmente realsado.
* Selecionar texto falado: Se esta opção estiver ligada, o texto atualmente falado é selecionado. Isso lhe habilita, por exemplo, a pressionar Ctrl + C para copiar o parágrafo atualmente falado.
* Tocar som de fim de seção: Se esta opção estiver ligada, o Bookworm toca um sonzinho quando chega ao fim de uma seção.


### Modo de Leitura Contínua

Além dos recursos de texto para fala embutidos no Bookworm, você pode tirar proveito da função de leitura contínua de seu leitor de telas (também conhecida como "dizer tudo"). O Bookworm provê suporte a esta função por meio do "modo de leitura contínua". Esse modo está ativo por padrão e você pode desabilitá-lo na página Leitura das Preferências do aplicativo. Enquanto o modo de leitura contínua está ativo, as páginas são viradas automaticamente conforme o leitor de telas avança pelo livro.

Note que devido à maneira como este recurso é atualmente implementado, esperam-se as seguintes limitações:

* A leitura contínua será interrompida se encontrar uma página vazia. Caso tenha chegado a uma página vazia, simplesmente navegue para uma página não-vazia e reative dali a função de leitura contínua do leitor de telas.
* Mover o cursor para o último caractere da página alternará imediatamente para a próxima página



### Exibindo uma versão completamente renderizada da página atual

O Bookworm lhe possibilita ver uma versão completamente renderizada do livro. Quando um livro estiver aberto, pode pressionar Ctrl + R ou selecionar o item "Renderizar página" no menu Ferramentas. Esta exibição se chama "Exibição renderizada" em contraste com a exibição textual, a padrão.

Quando está na exibição renderizada, pode usar os comandos comuns de zoom para dar zoom-in e zoom-out na página:

* Ctrl + = zoom-in
* Ctrl + - zoom-out
* Ctrl + 0 restaura o nível de zoom

Note que você pode usar também os comandos de navegação em livro, mencionados acima,  para navegar de mesmo modo na exibição renderizada. Pode também pressionar a tecla escape para descartar essa exibição e retornar à exibição textual padrão.


### Navegar para uma página específica

Para navegar até uma página específica no livro atualmente aberto, pressione Ctrl + G ou selecione o item "Go To..." no menu Ferramentas para mostrar o diálogo "Ir para página". Nesse diálogo, pode digitar o número de qualquer página para a qual queira navegar e o Bookworm o levará até ela. Note que o diálogo indicará para você o número total de páginas que se encontram no livro atual.


### Procurar no livro

Para encontrar um termo específico, ou um trecho de texto no livro atualmente aberto, pode pressionar Ctrl + F para chamar o diálogo "Procurar no livro". Esse diálogo lhe possibilita digitar o texto que quer procurar, bem como configurar o próprio processo de procura. As opções seguintes estão disponíveis:

* Diferenciar maiúsculas: A procura levará em conta a caixa das letras no termo de busca.
* Somente palavra inteira: O termo procurado deve ser achado como palavra inteira, isto é, não como parte de outra palavra
* Intervalo de procura: Isto possibilita confinar a procura a certas páginas ou uma seção específica

Após clicar no botão OK no diálogo "Procurar livro", outro diálogo contendo resultados da procura será mostrado. Clicar em qualquer item na lista de resultados da procura o levará imediatamente à posição daquele resultado com o termo da procura realsado.

Note que se você fechou a janela de resultados da procura, pode pressionar F3 e Shift + F3 para mover até as ocorrências seguinte e anterior da última procura respectivamente.


## Gerir associações de arquivos

O botão "Gerir associações de arquivos", localizado na página geral das Preferências do aplicativo, lhe ajuda a gerir quais tipos de arquivo são associados ao Bookworm. Associar arquivos com o Bookworm significa que, quando você clica num arquivo no Windows Explorer, esse arquivo será aberto no Bookworm por padrão. Note que este diálogo sempre é mostrado ao usuário na primeira execução do programa.

Uma vez que carregue o Gestor de associações de arquivos, terá as seguintes opções:

* Associar todos: Isto altera as configurações de modo que, se um arquivo for suportado pelo Bookworm, o Windows usará o Bookworm para abri-lo.
* Desasociar todos os tipos de arquivo suportados: Isto removerá associações de arquivos anteriormente registradas
* Botões individuais para cada tipo de arquivo suportado: Clicar em qualquer botão desses vai associar o respectivo tipo de arquivo com o Bookworm.


## Atualizar o Bookworm

Por padrão, o Bookworm verifica novas versões ao iniciar. Isto garante que você tem o mais novo e o melhor do Bookworm o mais cedo possível. Você pode desabilitar este comportamento padrão nas Preferências do aplicativo.   Pode também verificar atualizações manualmente clicando no item "Verificar atualizações" localizado no menu "Ajuda".

Em qualquer dos casos, quando uma nova versão for achada, o Bookworm perguntará se você quer instalá-la. Caso você clique em "Sim", o aplicativo irá em frente, baixará o pacote de atualização e mostrará um diálogo indicando o progresso do download. Após a atualização ser baixada, o Bookworm o alertará com uma mensagem, dizendo que reiniciará o aplicativo para atualizá-lo. Simplesmente clique "OK" para completar o processo de atualização.


## Relatar Problemas & questões

Como desenvolvedores cegos, nossa responsabilidade é desenvolver aplicativos que ofereçam independência a nós e nossos companheiros cegos semelhantes ao redor do mundo. Assim, caso tenha achado o Bookworm útil de alguma maneira, por favor nos ajude a torná-lo melhor para você e para outros. Neste estágio inicial, queremos que você nos informe acerca de quaisquer erros que venha encontrar durante o uso do Bookworm. Para fazer isso, abra um novo issue com os detalhes do erro no [issue tracker](https://github.com/mush42/bookworm/issues/). Sua ajuda é muito bem-vinda.

Antes de submeter um novo issue, certifique-se que executou o Bookworm em modo debug. Para ligar o modo debug, vá ao menu "Ajuda", aí clique em "reiniciar com o modo debug habilitado" e tente reproduzir o issue com modo debug habilitado. Na maioria dos casos, quando o erro aparecer de novo com o modo debug habilitado, será mostrado um diálogo com os detalhes desse erro. Você pode então copiar essa informação e inclui-lo com o relato de problema.

Note que alguns issues podem ser complicados de reproduzir; eles desaparecem quando se reinicia o programa. Neste caso, pode relatar o issue sem as informações detalhadas do modo debug. Apenas certifique-se de incluir o máximo de informações possível acerca das particularidades de seus sistema e cenário de uso.


## Notícias & atualizações

Para manter-se atualizado com as notícias mais recentes sobre o Bookworm, pode visitar o sítio web do  Bookworm em: [mush42.github.io/bookworm](https://mush42.github.io/bookworm/). Também pode seguir o desenvolvedor principal, Musharraf Omer, em [@mush42](https://twitter.com/mush42/) no Twitter (perfil e postagens em Inglês.


## Licença

O **Bookworm** é copyright (c) 2019 Musharraf Omer e colaboradores do Bookworm. O mesmo é licenciado sob a [licença MIT](https://github.com/mush42/bookworm/blob/master/LICENSE).
