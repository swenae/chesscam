#!/usr/bin/python

#*****************************************************************************
#
# This is the "chess cam" script.
#
# Module        : main module, chesscam.py
# Author        : Swen Hopfe (dj)
# Design        : 2019-01-16
# Last modified : 2019-02-26
#
# The python script works on Raspberry Pi 2/3/B/+
# with PiCam, TFT display and keyboard.
#
# Play chess games against a chess engine under camera control 
# on a conventional chess board without any additional sensors and wires.
#
#*****************************************************************************

import os
import string
import subprocess
import chess
import chess.uci

# Debug-Modus hier einschalten
dbg = False

# globaler Counter
gcnt = 0

# Arbeitsverzeichnis Aufnahmen
# auf eigene Beduerfnisse anpassen
basedir = "/home/pi/scripts/imaging/"

# String fuer Tastaturabfragen
menu_str = ""

# String fuer externe Calls
envstr = ""

# Counter fuer die Feldkoordinaten
iy = 0
ix = 0

# Haeufigkeit fuer gefundene Start- oder Ende-Stellen
efl = 0
sfl = 0

# Start-Ende-Koordinaten des letzten Zuges
e_iy = -1
e_ix = -1
s_iy = -1
s_ix = -1

# Merker fuer zuletzt ziehende Figur
p_m = "."

# Startplatz der ziehenden Figur
spl_str = ""

# Endeplatz der ziehenden Figur
epl_str = ""

# ermittelter Zug, gesamt
zstr = "unbekannt"

# ermittelter Primitivzug (nur das Ziel)
pstr = "unbekannt"

# Anzahl der Zuege
num_moves = 0

# Koordinaten der einzelnen Felder, wenn Kameraaufloesung und Cropping
# wie in unseren Routinen gewaehlt werden
# Abstand der Feldmitten ist dann 172px

#  A         B         C         D         E         F         G         H

#8 98, 98   270, 98   442, 98   614, 98   786, 98   958, 98   1130, 98  1302, 98

#7 98,270   270,270   442,270   614,270   786,270   958,270   1130,270  1302,270

#6 98,442   270,442   442,442   614,442   786,442   958,442   1130,442  1302,442

#5 98,614   270,614   442,614   614,614   786,614   958,614   1130,614  1302,614

#4 98,786   270,786   442,786   614,786   786,786   958,786   1130,786  1302,786

#3 98,925   270,958   442,958   614,958   786,958   958,958   1130,958  1302,958

#2 98,1130  270,1130  442,1130  614,1130  786,1130  958,1130  1130,1130 1302,1130

#1 98,1302  270,1302  442,1302  614,1302  786,1302  958,1302  1130,1302 1302,1302

#  A         B         C         D         E         F         G         H

# Feldbezeichner
fy = ["8", "7", "6", "5", "4", "3", "2", "1"]
fx = ["a", "b", "c", "d", "e", "f", "g", "h"]

# Markierung der Zuege fuer Debugmodus
carr = [ \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "], \
["   ", "   ", "   ", "   ", "   ", "   ", "   ", "   "]]

# Ausgangsbrett vor dem Ziehen
parr = [ \
["t", "s", "l", "d", "k", "l", "s", "t"], \
["b", "b", "b", "b", "b", "b", "b", "b"], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
["B", "B", "B", "B", "B", "B", "B", "B"], \
["T", "S", "L", "D", "K", "L", "S", "T"]]

# Neues Brett nach dem Ziehen
nparr = [ \
["t", "s", "l", "d", "k", "l", "s", "t"], \
["b", "b", "b", "b", "b", "b", "b", "b"], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
[".", ".", ".", ".", ".", ".", ".", "."], \
["B", "B", "B", "B", "B", "B", "B", "B"], \
["T", "S", "L", "D", "K", "L", "S", "T"]]

# Rochaden
# Rochadeerkennung
# Kleine Weiss
krw = "e1g1"
# Kleine Schwarz
krs = "e8g8"
# Grosse Weiss
grw = "e1c1"
# Grosse Schwarz
grs = "e8c8"
# Flags, wenn erkannt
krw_f = False
grw_f = False
krs_f = False
grs_f = False

#-----------------------------------------------------------------------------------------------------------------

# Neues Brett auf altes uebertragen
def ptrans():
    iy = 0
    for fystr in fy:
        ix = 0
        for fxstr in fx:
            parr[iy][ix] = nparr[iy][ix]
            ix += 1
        iy += 1

#-----------------------------------------------------------------------------------------------------------------

# Altes und neues Brett anzeigen
def board2(cl):
    iy = 0

    print "  -------------------       -------------------"
    for fystr in fy:
       ix = 0
       print fystr + " |",
       for fxstr in fx :
          if parr[iy][ix] != '.' :
              if parr[iy][ix].isupper() :
                  print '\x1b[1;37;40m' + parr[iy][ix] + '\x1b[0m',
              else :
                  print '\x1b[1;34;40m' + parr[iy][ix] + '\x1b[0m',
          else:
              print parr[iy][ix] + "",
          ix += 1
       print "|",
       ix = 0
       print "    " + fystr + " |",
       for fxstr in fx:
          if iy == e_iy and ix == e_ix:
             print cl + nparr[iy][ix] + '\x1b[0m' + "",
          else:
              if iy == s_iy and ix == s_ix:
                  print cl + nparr[iy][ix] + '\x1b[0m' + "",
              else:
                  if parr[iy][ix] != '.' :
                      if parr[iy][ix].isupper() :
                          print '\x1b[1;37;40m' + parr[iy][ix] + '\x1b[0m',
                      else :
                          print '\x1b[1;34;40m' + parr[iy][ix] + '\x1b[0m',
                  else:
                      print nparr[iy][ix] + "",
          ix += 1
       print "|"
       iy += 1
    print "  -------------------       -------------------"
    print "    a b c d e f g h           a b c d e f g h"

#-----------------------------------------------------------------------------------------------------------------

# Analyse der Aufnahmen
def analyze() :

    # Haeufigkeit fuer gefundene Start- oder Ende-Stellen
    global efl
    global sfl

    # Start-Ende-Koordinaten des letzten Zuges
    global e_iy
    global e_ix
    global s_iy
    global s_ix

    # Merker fuer zuletzt ziehende Figur
    global p_m

    # Rochadeerkennung
    global krw_f
    global grw_f

    # Counter fuer die Feldkoordinaten
    iy = 0
    ix = 0

    # Counter fuer die grafischen Koordinaten
    py = 98
    px = 98

    # Feldabstand in Pixel
    ps = 172

    if dbg: print
    if dbg: print "Analyse... "

    # carr leeren
    iy = 0
    for fystr in fy:
       ix = 0
       for fxstr in fx:
           carr[iy][ix] = "   "
           ix += 1
       iy += 1

    iy = 0
    for fystr in fy:
       if dbg: print "-------------------------------------------------------------------------------------------------"
       px = 98
       ix = 0
       for fxstr in fx:
          # ------------------------------------
          cx = px-20
          cy = py-20
          cxstr = str(cx)
          cystr = str(cy)
          spath = basedir + "diff.jpg"
          tpath = basedir + "test.jpg"
          rpath = basedir + "ref.jpg"
          envstr = "convert " + spath + " -crop 40x40+" + cxstr + "+" + cystr + " " + tpath
          os.popen(envstr)
          # ------------------------------------
          envstr = "compare -fuzz 4.8% -metric AE " + tpath + " " + rpath + " null: 2>&1"
          proc = subprocess.Popen(envstr, stdout=subprocess.PIPE, stderr=None, shell=True)
          df = proc.stdout.read()
          if int(df) < 800:
              # --------------------------------
              # Feld mit Veraenderung mit keiner Figur belegt gewesen
              # zum zweiten Mal oder mehr gefunden
              # Fehler oder Rochade
              if efl > 0 and parr[iy][ix] == ".":
                  carr[iy][ix] = "EEE"
                  efl += 1
              # --------------------------------
              # Feld mit Veraenderung mit keiner Figur belegt gewesen - Zug-Ende
              if efl == 0 and parr[iy][ix] == ".":
                  carr[iy][ix] = "EEE"
                  efl += 1
                  # Koordinaten merken
                  e_iy = iy
                  e_ix = ix
              # --------------------------------
              # Feld mit Veraenderung mit Figur belegt gewesen
              # zum zweiten Mal oder mehr gefunden
              # eine Figur wurde geschlagen oder Rochade
              if sfl > 0 and parr[iy][ix] != ".":
                  carr[iy][ix] = "SSS"
                  sfl += 1
                  # auf Rochade pruefen
                  # alles auf Grundlinie ?
                  if iy == 7 :
                        # Koenig vorher abgetastet ?
                        if s_ix == 4 :
                            # Bin ich rechter Turm ?
                            if ix == 7:
                                krw_f = True
                        # linken Turm vorher abgetastet ?
                        if s_ix == 0 :
                            # Bin ich Koenig ? 
                            if ix == 4:
                                grw_f = True
              # --------------------------------
              # Feld mit Veraenderung mit Figur belegt gewesen - Zug-Start
              if sfl == 0 and parr[iy][ix] != ".":
                  carr[iy][ix] = "SSS"
                  sfl += 1
                  # Koordinaten und Figur merken
                  s_iy = iy
                  s_ix = ix
                  p_m = parr[iy][ix]
              # --------------------------------
          if len(df) < 4:
              df = "0" + df
          if len(df) < 4:
              df = "0" + df
          if len(df) < 4:
              df = "0" + df
          if dbg: print "| " + "   " + df + "  ",
          px = px + ps
          ix = ix + 1
          # ------------------------------------
       if dbg: print "|"
       ix = 0
       for fxstr in fx:
          if dbg: print "| " + fxstr + fystr + "  " + parr[iy][ix] + "    ",
          ix = ix + 1
       if dbg: print "|"
       ix = 0
       for fxstr in fx:
          if dbg: print "| " + "   " + carr[iy][ix] + "   ",
          ix = ix + 1
       if dbg: print "|"
       py = py + ps
       iy = iy + 1
    if dbg: print "-------------------------------------------------------------------------------------------------"
    if dbg: print

#-----------------------------------------------------------------------------------------------------------------

print
print "-----------------------------------------------"
print "swSchach  chesscam R 0.1                02/2019"
print "-----------------------------------------------"
print

# Engine laden und initialisieren
print "Engines laden..."
engine_b = chess.uci.popen_engine("stockfish")
command_b = engine_b.uci(async_callback=True)
command_b.result()

# Neues Spiel kreieren
print "Neues Spiel..."
command_b = engine_b.ucinewgame(async_callback=True)
command_b.result()
board = chess.Board()
print

print "Es kann losgehen."
print "s - Startet Aufnahme                   q - Quit"
print "-----------------------------------------------"

menu_str = str(raw_input("Eingabe: "))
while menu_str != "s" and menu_str != "q":
    menu_str = str(raw_input("Eingabe: "))
if menu_str == "q":
    os.popen("sudo shutdown now")
print

# Aufnahme vom Brett in Startposition machen
if dbg: print "Startbrett aufnehmen..."
envstr = "raspistill -w 2400 -h 1800 -o " + basedir + "start.jpg"
os.popen(envstr)

# Zuschneiden
if dbg: print "Zuschneiden..."
envstr = "convert " + basedir + "start.jpg" + " -crop 1400x1400+517+20 " + basedir + "start_crop.jpg"
os.popen(envstr)

# Entzerren
if dbg: print "Entzerren..."
envstr = "convert " + basedir + "start_crop.jpg" + " -distort barrel '0.0 -0.05 0.0' " + basedir + "start_dist.jpg"
os.popen(envstr)

# Bildkorrektur
if dbg: print "Bildkorrektur..."
envstr = "convert " + basedir + "start_dist.jpg" + " -modulate 100,30 -channel 'RGBA' -contrast-stretch 0.8% " + basedir + "start_icorr.jpg"
os.popen(envstr)

#-----------------------------------------------------------------------------------------------------------------

# Zug fuer Zug...

while True:

    efl = 0
    sfl = 0
    e_iy = -1
    e_ix = -1
    s_iy = -1
    s_ix = -1
    p_m = "."
    spl_str = ""
    epl_str = ""
    zstr = "unbekannt"
    pstr = "unbekannt"
    krw_f = False
    grw_f = False
    krs_f = False
    grs_f = False

    print "Du ziehst als Weiss. Jetzt ziehen!"
    print "z - Zug gemacht                        q - Quit"
    print "-----------------------------------------------"
    menu_str = str(raw_input("Eingabe: "))
    while menu_str != "z" and menu_str != "q":
        menu_str = str(raw_input("Eingabe: "))
    if menu_str == "q":
        os.popen("sudo shutdown now")

    # Aufnahme eigener Zug (Weiss)
    if dbg: print "Zug aufnehmen..."
    envstr = "raspistill -w 2400 -h 1800 -o " + basedir + "zugw.jpg"
    os.popen(envstr)

    # Zuschneiden
    if dbg: print "Zuschneiden..."
    envstr = "convert " + basedir + "zugw.jpg" + " -crop 1400x1400+517+20 " + basedir + "zugw_crop.jpg"
    os.popen(envstr)

    # Entzerren
    if dbg: print "Entzerren..."
    envstr = "convert " + basedir + "zugw_crop.jpg" + " -distort barrel '0.0 -0.05 0.0' " + basedir + "zugw_dist.jpg"
    os.popen(envstr)

    # Bildkorrektur
    if dbg: print "Bildkorrektur..."
    envstr = "convert " + basedir + "zugw_dist.jpg" + " -modulate 100,30 -channel 'RGBA' -contrast-stretch 0.8% " + basedir + "zugw_icorr.jpg"
    os.popen(envstr)

    # Differenzbild
    if dbg: print "Differenzbild..."
    envstr = "compare -metric AE -fuzz 4.8% -compose src " + basedir + "start_icorr.jpg " + basedir + "zugw_icorr.jpg " + basedir + "diff.jpg" 
    os.popen(envstr)
    print

    # Analyse der Aufnahmen
    analyze()

    # Bei Rochaden auf die Start- und Endekoordinaten des Koenigs korrigieren
    if krw_f :
        p_m = "K"
        s_ix = 4
        s_iy = 7
        e_ix = 6
        e_iy = 7
    if grw_f :
        p_m = "K"
        s_ix = 4
        s_iy = 7
        e_ix = 2
        e_iy = 7

    # Debug-Auswertung ausgeben
    if dbg:
        print "Auswertung... "
        print
        print "Es wurde(n) " + str(sfl) + " Stelle(n) mit Figurbelegung erkannt."
        print "Es wurde(n) " + str(efl) + " Stelle(n) ohne Figurbelegung erkannt."
        if krw_f : print "Weiss hat klein rochiert."
        if grw_f : print "Weiss hat gross rochiert."
        if sfl > 2 or efl > 2 : "Zuviel Veraenderung erkannt. Fehler?"
        print p_m + " hat gezogen."
        print "Startkoordinaten waren (" + str(s_ix) + "," + str(s_iy) + ")."
        print "Endkoordinaten waren (" + str(e_ix) + "," + str(e_iy) + ")."
        print

    # Zug zusammenbauen
    spl_str = str(fx[s_ix]) + str(fy[s_iy])
    epl_str = str(fx[e_ix]) + str(fy[e_iy])
    pstr = p_m + epl_str
    zstr = spl_str + epl_str
    # wenn Bauer zieht, dann Figurkennung entfernen
    if p_m == "B" or p_m == "b":
        pstr = epl_str

    # Weiss hat gezogen, Daten zur Chess-Engine geben
    # --------------------------------------------------------------

    # Gueltigkeit ueberpruefen, legale Moves vorschlagen
    move = chess.Move.from_uci(zstr)
    move_str = str(move)
    while (move in board.legal_moves) == False :
        print str(move) + " scheint kein gueltiger Zug zu sein."
        if dbg: print board.legal_moves
        print "Bitte vierstellig nachsetzen..."
        zstr = str(raw_input("Weiss   : "))
        print
        move = chess.Move.from_uci(zstr)
        # Daten des handgesetzten Zugs nachziehen
        move_str = str(zstr)
        s_iy = fy.index(move_str[1:2])
        s_ix = fx.index(move_str[0:1])
        e_iy = fy.index(move_str[3:4])
        e_ix = fx.index(move_str[2:3])
        p_m = parr[s_iy][s_ix]
        spl_str = str(fx[s_ix]) + str(fy[s_iy])
        epl_str = str(fx[e_ix]) + str(fy[e_iy])
        pstr = p_m + epl_str
        zstr = spl_str + epl_str
        # wenn Bauer zieht, dann Figurkennung entfernen
        if p_m == "B" or p_m == "b":
            pstr = epl_str

    # Figur neuen Platz einnehmen lassen
    nparr[e_iy][e_ix] = p_m
    # Startplatz der Figur loeschen
    nparr[s_iy][s_ix] = "."

    # Auf kleine oder grosse Rochade von Weiss ueberpruefen
    # um noch den Turm nachzuziehen
    # Kleine Rochade
    if krw_f :
                # rechten Turm neuen Platz einnehmen lassen
                nparr[7][5] = "T"
                # Startplatz des rechten Turms loeschen
                nparr[7][7] = "."
    # Grosse Rochade
    if grw_f :
                # linken Turm neuen Platz einnehmen lassen
                nparr[7][3] = "T"
                # Startplatz des linken Turms loeschen
                nparr[7][0] = "."

    # Auf Ende ueberpruefen
    if move is None or board.result() != "*":
        if board.result() == "1/2-1/2":
            print("\nRemis.")
            break
        print("\nSchwarz gewinnt!")
        break

    # Altes und neues Brett anzeigen
    board2('\x1b[1;33;40m')

    print
    # Zug ausgeben
    if krw_f : pstr = "O-O"
    if grw_f : pstr = "O-O-O"
    print "Weiss   (" + str(gcnt+1) + "): " + '\x1b[1;33;40m' + zstr + '\x1b[0m' + " (" + pstr + ")"
    print "-----------------------------------------------"
    print

    # neues (eigenes) Brett auf altes uebertragen
    ptrans()

    # UCI-Board mit aktuellen Daten pushen
    board.push(move)

    if dbg: print(board)

    # Schwarz zieht
    # --------------------------------------------------------------
    command_b = engine_b.position(board, async_callback=True)
    command_b.result()
    command_b = engine_b.go(movetime=2000, async_callback=True)
    move = command_b.result().bestmove
    if move is None or board.result() != "*":
        if board.result() == "1/2-1/2":
            print("\nRemis.")
            break
        print("\nWeiss gewinnt!")
        break

    board.push(move)

    if dbg:
        print
        print(board)
        print

    # Figuren auf neuem Brett aktualisieren
    move_str = str(move)
    # auf Rochaden testen
    if move_str == krs or move_str == grs :
        # Eine Rochade wird durch den Zug des Koenigs definiert
        # Deshalb muss noch der Turm auf dem Brett nachgezogen werden
        s_iy = fy.index(move_str[1:2])
        s_ix = fx.index(move_str[0:1])
        p_m = parr[s_iy][s_ix]
        if p_m == "k" :
            # Rochade von Schwarz erkannt, schwarzen Turm nachziehen
            # Der rechte oder linke Turm stand dabei immer in Startaufstellung
            # Kleine Rochade
            if move_str == krs :
                # rechten Turm neuen Platz einnehmen lassen
                nparr[0][5] = "t"
                # Startplatz des rechten Turms loeschen
                nparr[0][7] = "."
                # Merker, um das spaeter anzuzeigen
                krs_f = True
            # Grosse Rochade
            if move_str == grs :
                # linken Turm neuen Platz einnehmen lassen
                nparr[0][3] = "t"
                # Startplatz des linken Turms loeschen
                nparr[0][0] = "."
                # Merker, um das spaeter anzuzeigen
                grs_f = True
    # normal weiter, bei Rochade wird hier nur noch der Koenig gezogen
    s_iy = fy.index(move_str[1:2])
    s_ix = fx.index(move_str[0:1])
    e_iy = fy.index(move_str[3:4])
    e_ix = fx.index(move_str[2:3])
    # Figur ermitteln
    p_m = parr[s_iy][s_ix]
    # Figur neuen Platz einnehmen lassen
    nparr[e_iy][e_ix] = p_m
    # Startplatz der Figur loeschen
    nparr[s_iy][s_ix] = "."

    # Zug zusammenbauen
    spl_str = str(fx[s_ix]) + str(fy[s_iy])
    epl_str = str(fx[e_ix]) + str(fy[e_iy])
    pstr = p_m + epl_str
    zstr = spl_str + epl_str
    # wenn Bauer zieht, dann Figurkennung entfernen
    if p_m == "B" or p_m == "b":
        pstr = epl_str
        zstr = spl_str + epl_str

    # Altes und neues Brett anzeigen
    board2('\x1b[1;36;40m')

    print
    # Zug ausgeben
    if krs_f : pstr = "o-o"
    if grs_f : pstr = "o-o-o"
    print "Schwarz (" + str(gcnt+1) + "): " + '\x1b[1;36;40m' + zstr + '\x1b[0m' + " (" + pstr + ")"
    print "-----------------------------------------------"
    print

    # neues Brett  auf altes uebertragen
    ptrans()

    # naechster Zug...
    gcnt += 1
    num_moves += 1

    # Schwarz hat gesetzt. Es muss ein neues Bild aufgenommen werden.
    # Aufnahme schwarzer Zug

    print "Schwarz per Hand nachziehen!"
    print "z - Zug gemacht                        q - Quit"
    print "-----------------------------------------------"
    menu_str = str(raw_input("Eingabe: "))
    while menu_str != "z" and menu_str != "q":
        menu_str = str(raw_input("Eingabe: "))
    if menu_str == "q":
        os.popen("sudo shutdown now")
 
    print

    if dbg: print "Zug aufnehmen..."
    envstr = "raspistill -w 2400 -h 1800 -o " + basedir + "zugs.jpg"
    os.popen(envstr)

    # Zuschneiden
    if dbg: print "Zuschneiden..."
    envstr = "convert " + basedir + "zugs.jpg" + " -crop 1400x1400+517+20 " + basedir + "zugs_crop.jpg"
    os.popen(envstr)

    # Entzerren
    if dbg: print "Entzerren..."
    envstr = "convert " + basedir + "zugs_crop.jpg" + " -distort barrel '0.0 -0.05 0.0' " + basedir + "zugs_dist.jpg"
    os.popen(envstr)

    # Bildkorrektur
    if dbg: print "Bildkorrektur..."
    envstr = "convert " + basedir + "zugs_dist.jpg" + " -modulate 100,30 -channel 'RGBA' -contrast-stretch 0.8% " + basedir + "start_icorr.jpg"
    os.popen(envstr)


print("Anzahl Zuege: %d ." % num_moves)
engine_b.quit()
print "-----------------------------------------------"
print

#------------- physical end ----------------------------------------------------------------------------
