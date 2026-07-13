# Flappy Bird — clone in SwiftUI + SpriteKit

Un clone completo e funzionante di Flappy Bird, per **iPhone, iPad e Mac**,
scritto in Swift usando SwiftUI (interfaccia) + SpriteKit (motore di gioco).
Nessun asset grafico esterno: tutta la grafica (uccellino, tubi, sfondo,
nuvole) è disegnata proceduralmente nel codice, quindi il progetto
compila e gira subito, senza dover importare immagini.

## Come aprirlo

1. Estrai lo zip.
2. Fai doppio clic su `FlappyBird.xcodeproj` per aprirlo in Xcode
   (consigliata Xcode 15 o successiva, macOS con SDK iOS 17+).
3. In alto a sinistra, scegli lo schema:
   - **FlappyBird (iOS)** → esegui su un simulatore iPhone/iPad o su un
     dispositivo reale.
   - **FlappyBird (macOS)** → esegui direttamente su Mac ("My Mac").
4. Premi ▶️ (Cmd+R) per avviare.

## Come si gioca

- **iPhone/iPad:** tocca lo schermo per far volare l'uccellino tra i tubi.
- **Mac:** clicca con il mouse oppure premi la barra spaziatrice.
- Ogni tubo superato vale 1 punto. Il punteggio migliore viene salvato
  in locale (UserDefaults) e mostrato nella schermata di game over.
- Premi "Rigioca" per ricominciare dopo un game over.

## Struttura del progetto

```
FlappyBird.xcodeproj/       → progetto Xcode (2 target: iOS e macOS)
FlappyBird/
  FlappyBirdApp.swift        → entry point SwiftUI (@main)
  ContentView.swift          → UI: SpriteView + punteggio + game over + restart
  GameState.swift             → stato di gioco osservabile (ObservableObject)
  GameScene.swift              → logica di gioco SpriteKit (fisica, tubi, collisioni)
  Assets.xcassets/            → AppIcon (segnaposto) + AccentColor
```

## Personalizzazioni facili

- **Difficoltà:** modifica `pipeGap`, `pipeSpacing`, `scrollSpeed` e
  `flapImpulse` in `GameScene.swift`.
- **Icona app:** sostituisci le immagini in
  `Assets.xcassets/AppIcon.appiconset` (attualmente vuoto/segnaposto).
- **Grafica:** l'uccellino e i tubi sono `SKShapeNode` disegnati a
  codice; puoi sostituirli con `SKSpriteNode` e le tue immagini se
  preferisci una grafica in stile pixel-art originale.

## Nota

Questo è un progetto didattico creato da zero, con meccaniche di
gioco ispirate al genere "endless flapper" (uccellino che vola tra
ostacoli) — non contiene asset grafici, codice o risorse originali del
gioco Flappy Bird ufficiale.
