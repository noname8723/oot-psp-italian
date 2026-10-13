OCARINA OF TIME PSP - PATCH ITALIANO (non ufficiale)
====================================================

Questo strumento mette i dialoghi in ITALIANO nel port per PSP di
Ocarina of Time (https://github.com/z2442/oot-PSP).

E' un adattamento del patcher spagnolo di Unbekantte (licenza MIT):
https://github.com/Unbekantte/oot-psp-spanish-patcher

Questo strumento utilizza la traduzione di XXCentury nel 2001, all'
epoca in esclusiva sul sito forum Clomax Dominion oggi noto come 
romhacking.it, per tanto la patch NON è inclusa.

Questo strumento è stato creato totalmente da Claude di proprietà di Anthropic



AVVISO LEGALE IMPORTANTE
------------------------
"The Legend of Zelda" e "Ocarina of Time" sono marchi registrati e opere
protette da copyright di Nintendo. Questo progetto non e' affiliato,
approvato o sponsorizzato da Nintendo.

Per usare questo strumento DEVI POSSEDERE LEGALMENTE il gioco originale
(The Legend of Zelda: Ocarina of Time, USA NTSC 1.0) e ricavare la ROM dalla
TUA copia. Questo repository non contiene ne' distribuisce ROM, file del gioco
o traduzioni, e non fornisce link per scaricarli. Chiedere o condividere ROM
o file del gioco qui non e' consentito.

Lo strumento e' fornito "cosi' com'e'", senza garanzie, per uso personale con
una copia di cui sei legittimo proprietario.


PRIMA DI INIZIARE: COSA DEVI GIA' AVERE
---------------------------------------
1. Il gioco oot-PSP GIA' FUNZIONANTE IN INGLESE.
   Cioe' hai gia' compilato il port dal repository originale
   (https://github.com/z2442/oot-PSP), messo la tua ROM nella cartella
   "data" e avviato il gioco almeno una volta, aspettando che finisse la
   preparazione iniziale. Se il gioco in inglese non parte, sistemalo prima:
   questa patch NON installa il gioco.

2. La ROM del TUO gioco originale Zelda Ocarina of Time USA NTSC 1.0
   (devi possedere il gioco), quella che usi gia' per il port, chiamata
   baserom.z64.
   Per controllarla (Windows, PowerShell nella cartella della ROM):
       certutil -hashfile baserom.z64 MD5
   Deve uscire: 5bd1fe107bf8106b2ab6650abecd54d6

3. La patch di traduzione italiana, un file .ips fatto per la ROM NTSC 1.0.
   (NON e' inclusa qui: cercala dagli autori della traduzione.)

4. Python 3 installato (https://www.python.org/downloads/).
   Durante l'installazione spunta "Add python.exe to PATH".

NON funziona con ROM PAL, USA 1.1 / 1.2.


I FILE DEL PORT CHE SERVONO
---------------------------
Nella cartella del tuo gioco ci sono questi due file. Servono ORIGINALI,
cioe' mai patchati:

   EBOOT.PBP
   data\segments\oot_psp_assets.bin

!! FAI UNA COPIA DI BACKUP di tutti e due prima di iniziare (per esempio in
   una cartella "originali"). Se qualcosa va storto, rimetti i backup.


PASSO PER PASSO
---------------
PASSO 1 - Prepara una cartella di lavoro
   Crea una cartella nuova mettici dentro questi file:

     oot_psp_it_patch.py      (da questo repository)
     avvia_patcher.bat        (da questo repository)
     baserom.z64              (la tua ROM USA NTSC 1.0)
     TRADUZIONE.ips           (la patch italiana, il nome puo' essere
                               qualsiasi)
     EBOOT.PBP                (copiato dal tuo gioco, originale)
     oot_psp_assets.bin       (copiato da data\segments\oot_psp_assets.bin)

PASSO 2 - Avvia il patcher
   Fai doppio clic su  avvia_patcher.bat
   (se non sei su Windows:  python3 oot_psp_it_patch.py )

   Aspetta. Alla fine deve comparire la scritta:   == FATTO ==
   Nella cartella e' comparsa una cartella nuova chiamata  output_it
   con dentro due file:  EBOOT.PBP  e  oot_psp_assets.bin

   Se compare un ERRORE, vai alla sezione "SE QUALCOSA NON VA" qui sotto.

PASSO 3 - Copia i due file nel tuo gioco
   Copia i due file di output_it nella cartella del tuo gioco,
   SOVRASCRIVENDO gli originali:

     output_it\EBOOT.PBP             ->  (cartella del gioco)\EBOOT.PBP
     output_it\oot_psp_assets.bin    ->  (cartella del gioco)\data\segments\
                                         oot_psp_assets.bin

   Attenzione: oot_psp_assets.bin va dentro data\segments, non nella
   cartella principale.
   NON toccare baserom.z64 del gioco e NON cancellare oot_psp_assets.bin
   (se lo cancelli il gioco lo ricrea in inglese).

PASSO 4 - Avvia il gioco
   Apri l'EBOOT.PBP della cartella del gioco (in PPSSPP, oppure sulla PSP).
   I dialoghi sono in italiano. Menu e alcune schermate restano in inglese:
   e' normale.

PER TORNARE ALL'INGLESE
   Rimetti i due file di backup al loro posto.


SE QUALCOSA NON VA
------------------
La finestra si chiude subito o non succede niente
   Usa avvia_patcher.bat (non il doppio clic sul .py). Se dice "Python non
   trovato", installa Python spuntando "Add python.exe to PATH".

"manca baserom.z64" / "manca EBOOT.PBP" / "manca oot_psp_assets.bin"
   Quel file non e' nella stessa cartella dello script. Controlla il
   PASSO 1.

"baserom.z64 non e' la ROM USA NTSC 1.0 pulita attesa"
   La ROM non e' quella giusta. Controlla l'MD5 (vedi sopra).

"oot_psp_assets.bin ha dimensione ... attesa ..." oppure
"Il blocco inglese nel file assets non coincide..."
   Il file oot_psp_assets.bin non e' l'originale (e' gia' stato patchato)
   oppure viene da un'altra versione del port. Usa il backup originale o
   avvia il port in inglese per rigenerarlo.

"Attesi 2115 messaggi, trovati ..." oppure "VROM ... non trovata"
   La patch .ips non e' compatibile (non e' per la ROM NTSC 1.0 da 32 MB).

"L'EBOOT non ha il descrittore atteso" / "Impossibile identificare ... la
tabella PSP"
   L'EBOOT e' gia' patchato oppure e' di una versione del port diversa da
   quella supportata da questo script.

Il gioco parte ma le scritte sono simboli senza senso
   Quasi sempre hai sostituito UN SOLO dei due file, oppure li hai copiati
   in una cartella diversa da quella che avvii. Controlla che entrambi i file
   del gioco siano uguali a quelli di output_it:
       certutil -hashfile EBOOT.PBP MD5
       certutil -hashfile data\segments\oot_psp_assets.bin MD5
   (confrontali con output_it\EBOOT.PBP e output_it\oot_psp_assets.bin)
   e avvia l'EBOOT.PBP della cartella giusta.

Il gioco e' ancora in inglese
   I file non sono stati sostituiti, oppure oot_psp_assets.bin e' stato
   cancellato e ricreato dal gioco.

COSA NON C'E' IN QUESTO REPOSITORY
----------------------------------
Solo script e istruzioni. NON ci sono e non vanno mai pubblicati qui:
ROM (originali o modificate), EBOOT.PBP, oot_psp_assets.bin, la patch .ips
e i testi della traduzione. Ognuno usa i propri file.


CREDITI E LICENZA
-----------------
Codice sotto licenza MIT (vedi LICENSE).
 - Patcher originale (spagnolo): Unbekantte
 - Port nativo PSP: z2442 e collaboratori
 - Decompilazione: zeldaret/oot
 - Traduzione italiana: [XXCentury]
Strumento non affiliato a Nintendo. "The Legend of Zelda" e "Ocarina of
Time" sono marchi registrati di Nintendo.
