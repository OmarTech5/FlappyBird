import pygame
import random
import sys
import math
import struct
import os

# --- INIZIALIZZAZIONE PYGAME E SCHERMO ---
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)
SCHERMO = pygame.display.set_mode((288, 512))
pygame.display.set_caption("Flappy Bird")
pygame.display.set_icon(pygame.image.load("Assets/icon.png"))

# --- CARICAMENTO IMMAGINI ---
titolo = pygame.image.load("Assets/title.png")
sfondo = pygame.image.load("Assets/sfondo.png")
base = pygame.image.load("Assets/base.png")
gameover = pygame.image.load("Assets/gameover.png")
tubo_giu = pygame.image.load("Assets/tubo_giu.png")
tubo_su = pygame.transform.flip(tubo_giu, False, True)
bottone_restart = pygame.image.load("Assets/restart.png")
bottone_restart = pygame.transform.scale(bottone_restart, (100, 50))
titolo = pygame.transform.scale(titolo, (200, 50))

# --- CARICAMENTO ANIMAZIONE UCCELLINO ---
frames_uccello = []
nomi_file_uccello = ["Assets/faby_up.png", "Assets/faby.png", "Assets/faby_down.png"]
for nome in nomi_file_uccello:
    if os.path.exists(nome):
        frames_uccello.append(pygame.image.load(nome).convert_alpha())
if not frames_uccello:
    frames_uccello.append(pygame.image.load("Assets/faby.png").convert_alpha())

# --- CARICAMENTO IMMAGINI NUMERI (0-9) ---
numeri = []
for i in range(10):
    img_num = pygame.image.load(f"Assets/{i}.png").convert_alpha()
    numeri.append(img_num)

# --- FUNZIONE PER AGGIUNGERE BORDO NERO E OMBRA AI NUMERI ---
def crea_numero_con_effetto(img_numero):
    w, h = img_numero.get_width(), img_numero.get_height()
    superficie_effetto = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    offset_outline = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]
    
    mask_num = pygame.mask.from_surface(img_numero)
    ombra_surf = mask_num.to_surface(setcolor=(0, 0, 0, 120), unsetcolor=(0, 0, 0, 0))
    superficie_effetto.blit(ombra_surf, (3 + 2, 3 + 2))
    
    for ox, oy in offset_outline:
        outline_surf = mask_num.to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(0, 0, 0, 0))
        superficie_effetto.blit(outline_surf, (3 + ox, 3 + oy))
        
    superficie_effetto.blit(img_numero, (3, 3))
    return superficie_effetto

numeri_con_effetti = [crea_numero_con_effetto(num) for num in numeri]

# --- GESTIONE SALVATAGGIO RECORD ---
def carica_record():
    if os.path.exists("record.txt"):
        try:
            with open("record.txt", "r") as file:
                return int(file.read().strip())
        except ValueError:
            return 0
    return 0

def salva_record(nuovo_record):
    try:
        with open("record.txt", "w") as file:
            file.write(str(nuovo_record))
    except IOError:
        print("Impossibile salvare il record su file.")

# --- GENERATORE DI SUONI RETRO ---
def genera_suono_sintetico(tipo):
    sample_rate = 22050
    buffer = bytearray()
    
    if tipo == "salto":
        durata = 0.12
        num_samples = int(sample_rate * durata)
        for i in range(num_samples):
            t = i / sample_rate
            freq = 350 + (500 * (t / durata))  
            volume = 1.0 - (t / durata)        
            val = int(16383 * math.sin(2 * math.pi * freq * t) * volume)
            buffer.extend(struct.pack('<h', val))
            
    elif tipo == "punto":
        durata = 0.16
        num_samples = int(sample_rate * durata)
        for i in range(num_samples):
            t = i / sample_rate
            freq = 880 if t < 0.07 else 1320
            volume = 0.6 * (1.0 - (t / durata))
            val = int(16383 * math.sin(2 * math.pi * freq * t) * volume)
            buffer.extend(struct.pack('<h', val))
            
    elif tipo == "scontro":
        durata = 0.45
        num_samples = int(sample_rate * durata)
        for i in range(num_samples):
            t = i / sample_rate
            freq = max(50, 450 - (900 * (t / durata)))  
            onda = 1 if math.sin(2 * math.pi * freq * t) > 0 else -1
            volume = 0.8 * (1.0 - (t / durata))
            val = int(12000 * onda * volume)
            buffer.extend(struct.pack('<h', val))
            
    return pygame.mixer.Sound(buffer=bytes(buffer))

suono_salto = genera_suono_sintetico("salto")
suono_punto = genera_suono_sintetico("punto")
suono_scontro = genera_suono_sintetico("scontro")

# --- CONFIGURAZIONI SCHERMO E FONT ---
FPS = 60
FONT = pygame.font.SysFont("04b_19", 40, bold=True)
FONT_BOTTONI = pygame.font.SysFont("04b_19", 24, bold=True)
FONT_PICCOLO = pygame.font.SysFont("Arial", 16, bold=True) 
clock = pygame.time.Clock()

base_temp = pygame.image.load("Assets/base.png")
LARGHEZZA_BASE = base_temp.get_width() - 2 

# --- VARIABILI DI STATO GLOBALI ---
stato_gioco = "MENU"
provenienza_pausa = "GIOCO"
volume_attivo = True
difficolta = "NORMALE"  
tubi = []
record = carica_record()

# --- VARIABILI DINAMICHE DELLA FISICA E ANIMAZIONE ---
vel_avanz_attuale = 3
gravita_attuale = 1.0
salto_attuale = -10

uccellox = 60
uccelloy = 150
uccello_vely = 0.0
indice_frame_uccello = 0
timer_animazione = 0
basex = 0
punti = 0
fra_i_tubi = False

uccello_w = frames_uccello[0].get_width()
uccello_h = frames_uccello[0].get_height()

# --- CLASSE TUBI ---
class tubi_classe:
    def __init__(self):
        self.x = 300
        self.y = random.randint(-75, 150)
        
    def avanza(self):
        self.x -= vel_avanz_attuale
        
    def disegna(self):
        SCHERMO.blit(tubo_giu, (self.x, self.y + 210))
        SCHERMO.blit(tubo_su, (self.x, self.y - 210))
        
    def collisione(self, u_x, u_y):
        tolleranza = 8
        uccello_lato_dx = u_x + uccello_w - tolleranza
        uccello_latosx = u_x + tolleranza
        tubi_lato_sx = self.x
        tubi_lato_dx = self.x + tubo_giu.get_width()
        uccello_lato_su = u_y + tolleranza
        uccello_lato_giu = u_y + uccello_h - tolleranza
        tubi_lato_su = self.y + 110
        tubi_lato_giu = self.y + 210
        if uccello_lato_dx > tubi_lato_sx and uccello_latosx < tubi_lato_dx:
            if uccello_lato_su < tubi_lato_su or uccello_lato_giu > tubi_lato_giu:
                hai_perso()
                
    def fra_i_tubi(self, u_x):
        tolleranza = 10
        uccello_lato_dx = u_x + uccello_w - tolleranza
        uccello_latosx = u_x + tolleranza
        tubi_lato_sx = self.x
        tubi_lato_dx = self.x + tubo_giu.get_width()
        if uccello_lato_dx > tubi_lato_sx and uccello_latosx < tubi_lato_dx:
            return True

# --- FUNZIONE DISEGNO BOTTONI IN STILE PIXEL ART ---
def disegna_bottone_pixel(testo, centro_x, centro_y, larghezza, altezza, colore_box=(216, 91, 19)):
    colore_bordo_scuro = (54, 27, 11)
    
    rect_ombra = pygame.Rect(0, 0, larghezza, altezza)
    rect_ombra.center = (centro_x + 3, centro_y + 4)
    pygame.draw.rect(SCHERMO, colore_bordo_scuro, rect_ombra)
    
    rect_bordo = pygame.Rect(0, 0, larghezza, altezza)
    rect_bordo.center = (centro_x, centro_y)
    pygame.draw.rect(SCHERMO, colore_bordo_scuro, rect_bordo)
    
    rect_interno = pygame.Rect(rect_bordo.x + 3, rect_bordo.y + 3, larghezza - 6, altezza - 6)
    pygame.draw.rect(SCHERMO, colore_box, rect_interno)
    
    rect_bianco = pygame.Rect(rect_interno.x + 2, rect_interno.y + 2, rect_interno.width - 4, rect_interno.height - 4)
    pygame.draw.rect(SCHERMO, (255, 255, 255), rect_bianco, width=2)
    
    testo_render = FONT_BOTTONI.render(testo, True, (255, 255, 255))
    testo_rect = testo_render.get_rect(center=(centro_x, centro_y))
    SCHERMO.blit(testo_render, testo_rect)
    
    return rect_bordo

# --- FUNZIONI DI DISEGNO E GESTIONE CON ANIMAZIONE UCCELLINO ---
def disegna_oggetti():
    SCHERMO.blit(sfondo, (0, 0))
    for t in tubi:
        t.disegna()
    
    SCHERMO.blit(base, (basex, 461))
    SCHERMO.blit(base, (basex + LARGHEZZA_BASE, 461))
    SCHERMO.blit(base, (basex + (LARGHEZZA_BASE * 2), 461))
    
    frame_corrente = frames_uccello[indice_frame_uccello % len(frames_uccello)]
    angolo_rotazione = max(-90, min(25, -uccello_vely * 3))
    uccello_ruotato = pygame.transform.rotate(frame_corrente, angolo_rotazione)
    SCHERMO.blit(uccello_ruotato, (uccellox, int(uccelloy)))
    
    cifre = [int(c) for c in str(punti)]
    larghezza_totale = sum(numeri_con_effetti[cifra].get_width() for cifra in cifre)
    spaziatura = 2
    larghezza_totale += spaziatura * (len(cifre) - 1)
    
    x_corrente = 144 - larghezza_totale // 2
    y_punteggio = 16 
    
    for cifra in cifre:
        img_cifra = numeri_con_effetti[cifra]
        SCHERMO.blit(img_cifra, (x_corrente, y_punteggio))
        x_corrente += img_cifra.get_width() + spaziatura
    
    if stato_gioco in ["GIOCO", "GAMEOVER"]:
        btn_pausa_gioco = pygame.Rect(243, 20, 30, 30)
        pygame.draw.rect(SCHERMO, (60, 60, 60), btn_pausa_gioco, border_radius=6)
        pygame.draw.rect(SCHERMO, (255, 255, 255), (251, 26, 4, 18))
        pygame.draw.rect(SCHERMO, (255, 255, 255), (260, 26, 4, 18))

def aggiorna():
    pygame.display.update()
    clock.tick(FPS)

def applica_bilanciamento_difficolta():
    global vel_avanz_attuale, gravita_attuale, salto_attuale
    if difficolta == "DIFFICILE":
        vel_avanz_attuale = 3
        gravita_attuale = 0.6     
        salto_attuale = -8.5      
    elif difficolta == "NORMALE":
        vel_avanz_attuale = 3     
        gravita_attuale = 0.35    
        salto_attuale = -6.5      
    elif difficolta == "FACILE":
        vel_avanz_attuale = 1.8   
        gravita_attuale = 0.3     
        salto_attuale = -5.8      

def inizializza():
    global uccellox, uccelloy, uccello_vely, basex, tubi, punti, fra_i_tubi, indice_frame_uccello
    applica_bilanciamento_difficolta()
    uccellox, uccelloy = 60, 150
    uccello_vely = 0.0
    indice_frame_uccello = 0
    basex = 0
    punti = 0
    tubi = []
    tubi.append(tubi_classe())
    fra_i_tubi = False

def hai_perso():
    global record, stato_gioco
    if stato_gioco != "GAMEOVER": 
        if punti > record:
            record = punti
            salva_record(record)  
        if volume_attivo:
            suono_scontro.play()
        stato_gioco = "GAMEOVER"

# --- SCHERMATE DEI MENU (CON GESTIONE MOUSE RIPRISTINATA) ---
def gestisci_menu_iniziale():
    global stato_gioco, timer_animazione, indice_frame_uccello
    SCHERMO.blit(sfondo, (0, 0))
    SCHERMO.blit(base, (0, 461))
    
    timer_animazione += 1
    if timer_animazione % 10 == 0:
        indice_frame_uccello = (indice_frame_uccello + 1) % len(frames_uccello)
    
    frame_menu = frames_uccello[indice_frame_uccello]
    SCHERMO.blit(frame_menu, (144 - uccello_w//2, 130))
    SCHERMO.blit(titolo, (144 - titolo.get_width()//2, 60))
    
    btn_start = disegna_bottone_pixel("START", 144, 200, 150, 48)
    btn_setup = disegna_bottone_pixel("SETUP", 144, 275, 150, 48)
    btn_score = disegna_bottone_pixel("SCORE", 144, 350, 150, 48)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if btn_start.collidepoint(pos):
                inizializza()
                stato_gioco = "GIOCO"
            elif btn_score.collidepoint(pos):
                stato_gioco = "RECORD"
            elif btn_setup.collidepoint(pos):
                stato_gioco = "IMPOSTAZIONI"
    aggiorna()

def gestisci_menu_record():
    global stato_gioco
    SCHERMO.blit(sfondo, (0, 0))
    SCHERMO.blit(base, (0, 461))
    titolo_rec = FONT.render("BEST SCORE", True, (255, 255, 255))
    SCHERMO.blit(titolo_rec, (144 - titolo_rec.get_width()//2, 100))
    
    score_render = FONT.render(f"{record} PTS", True, (255, 215, 0))
    SCHERMO.blit(score_render, (144 - score_render.get_width()//2, 200))
    
    btn_indietro = disegna_bottone_pixel("INDIETRO", 144, 380, 140, 45, (150, 50, 50))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if btn_indietro.collidepoint(pygame.mouse.get_pos()):
                stato_gioco = "MENU"
    aggiorna()

def gestisci_menu_impostazioni():
    global stato_gioco, volume_attivo, difficolta
    SCHERMO.blit(sfondo, (0, 0))
    SCHERMO.blit(base, (0, 461))
    titolo_set = FONT.render("IMPOSTAZIONI", True, (255, 255, 255))
    SCHERMO.blit(titolo_set, (144 - titolo_set.get_width()//2, 70))
    
    testo_vol = "AUDIO: SI" if volume_attivo else "AUDIO: NO"
    colore_vol = (50, 150, 50) if volume_attivo else (150, 50, 50)
    btn_volume = disegna_bottone_pixel(testo_vol, 144, 180, 180, 45, colore_vol)
    
    testo_diff = f"DIFF: {difficolta}"
    if difficolta == "DIFFICILE":
        colore_diff = (180, 40, 40)   
    elif difficolta == "NORMALE":
        colore_diff = (210, 130, 0)   
    else:
        colore_diff = (40, 140, 200)  
        
    btn_difficolta = disegna_bottone_pixel(testo_diff, 144, 255, 200, 45, colore_diff)
    btn_indietro = disegna_bottone_pixel("INDIETRO", 144, 380, 140, 45, (120, 120, 120))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if btn_volume.collidepoint(pos):
                volume_attivo = not volume_attivo
            elif btn_difficolta.collidepoint(pos):
                if difficolta == "DIFFICILE":
                    difficolta = "NORMALE"
                elif difficolta == "NORMALE":
                    difficolta = "FACILE"
                else:
                    difficolta = "DIFFICILE"
            elif btn_indietro.collidepoint(pos):
                stato_gioco = "MENU"
    aggiorna()

def gestisci_menu_gameover():
    global stato_gioco, provenienza_pausa
    disegna_oggetti()
    
    SCHERMO.blit(gameover, (50, 180))
    bottone_rect = bottone_restart.get_rect(center=(144, 280))
    SCHERMO.blit(bottone_restart, bottone_rect)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            inizializza()
            stato_gioco = "GIOCO"
            
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
            provenienza_pausa = "GAMEOVER"
            stato_gioco = "PAUSA"
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            btn_pausa_gioco = pygame.Rect(243, 20, 30, 30)
            
            if bottone_rect.collidepoint(pos):
                inizializza()
                stato_gioco = "GIOCO"
            elif btn_pausa_gioco.collidepoint(pos):
                provenienza_pausa = "GAMEOVER"
                stato_gioco = "PAUSA"
    aggiorna()

def gestisci_menu_pausa():
    global stato_gioco
    disegna_oggetti()
    
    if provenienza_pausa == "GAMEOVER":
        SCHERMO.blit(gameover, (50, 180))
        bottone_rect = bottone_restart.get_rect(center=(144, 280))
        SCHERMO.blit(bottone_restart, bottone_rect)
        
    testo_pausa = FONT.render("IN PAUSA", True, (255, 255, 255))
    SCHERMO.blit(testo_pausa, (144 - testo_pausa.get_width()//2, 130))
    
    btn_riprendi = disegna_bottone_pixel("RIPRENDI", 144, 230, 140, 45, (50, 150, 50))
    btn_home = disegna_bottone_pixel("HOME", 144, 300, 140, 45, (150, 50, 50))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
            stato_gioco = provenienza_pausa
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            if btn_riprendi.collidepoint(pos):
                stato_gioco = provenienza_pausa
            elif btn_home.collidepoint(pos):
                stato_gioco = "MENU"
    aggiorna()

# --- LOOP PRINCIPALE ---
while True:
    if stato_gioco == "MENU":
        gestisci_menu_iniziale()
    elif stato_gioco == "RECORD":
        gestisci_menu_record()
    elif stato_gioco == "IMPOSTAZIONI":
        gestisci_menu_impostazioni()
    elif stato_gioco == "PAUSA":
        gestisci_menu_pausa()
    elif stato_gioco == "GAMEOVER":
        gestisci_menu_gameover()
        
    elif stato_gioco == "GIOCO":
        basex -= vel_avanz_attuale
        if basex <= -LARGHEZZA_BASE: 
            basex += LARGHEZZA_BASE
            
        uccello_vely += gravita_attuale
        uccelloy += uccello_vely
        
        timer_animazione += 1
        if timer_animazione % 6 == 0:
            indice_frame_uccello = (indice_frame_uccello + 1) % len(frames_uccello)
        
        for t in tubi:
            t.avanza()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_p or event.key == pygame.K_ESCAPE):
                provenienza_pausa = "GIOCO"
                stato_gioco = "PAUSA"
                
            elif event.type == pygame.KEYDOWN and (event.key == pygame.K_UP or event.key == pygame.K_SPACE):
                uccello_vely = salto_attuale
                if volume_attivo:
                    suono_salto.play()
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                btn_pausa_gioco = pygame.Rect(243, 20, 30, 30)
                
                if btn_pausa_gioco.collidepoint(pos):
                    provenienza_pausa = "GIOCO"
                    stato_gioco = "PAUSA"
                else:
                    uccello_vely = salto_attuale
                    if volume_attivo:
                        suono_salto.play()

        # Collisioni Terreno
        uccello_rect = pygame.Rect(uccellox, int(uccelloy), uccello_w, uccello_h)
        base_rect = pygame.Rect(0, 461, 288, 51)
        if uccello_rect.colliderect(base_rect):
            hai_perso()
            continue

        # Generazione Tubi proporzionata alla velocità attuale
        distanza_generazione = 140 if vel_avanz_attuale == 3 else 100
        if len(tubi) > 0 and tubi[-1].x < distanza_generazione:
            tubi.append(tubi_classe())

        # Collisioni Tubi
        for t in tubi:
            t.collisione(uccellox, uccelloy)
            if stato_gioco == "GAMEOVER":
                break
        if stato_gioco == "GAMEOVER":
            continue

        # Logica Punteggio
        if not fra_i_tubi:
            for t in tubi:
                if t.fra_i_tubi(uccellox):
                    fra_i_tubi = True
                    break
        if fra_i_tubi:
            fra_i_tubi = False
            for t in tubi:
                if t.fra_i_tubi(uccellox):
                    fra_i_tubi = True
                    break
            if not fra_i_tubi:
                punti += 1
                if volume_attivo:
                    suono_punto.play()
                
        if len(tubi) > 0 and tubi[0].x < -50:
            tubi.pop(0)

        disegna_oggetti()
        aggiorna()