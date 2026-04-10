# Brantsteele-style battle royale simulator.
# But with events chained logically.

import sqlite3
import nextcord
from nextcord.ext import commands
import random

from db_core import get_conn

database = get_conn()
cursor = database.cursor()



# br_players NO se dropea: preserva los nombres/géneros editados por el usuario
cursor.execute("DROP TABLE IF EXISTS br_stages;")
cursor.execute("DROP TABLE IF EXISTS br_sessions;")
cursor.execute("DROP TABLE IF EXISTS br_events;")
cursor.execute("DROP TABLE IF EXISTS br_weapons;")
cursor.execute("DROP TABLE IF EXISTS br_items;")
cursor.execute("DROP TABLE IF EXISTS br_genders;")
cursor.execute("""CREATE TABLE IF NOT EXISTS br_genders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gen TEXT NOT NULL,
    arti_defi TEXT NOT NULL,
    pron_pers TEXT NOT NULL,
    pron_suj TEXT NOT NULL,
    letter_a TEXT NOT NULL,
    letter_b TEXT NOT NULL
);""")
    # gen: femenino, masculino
    # arti_defi: la, el
    # pron_pers: la, lo
    # pron_suj: ella, él
    # letter_a: a, o
    # letter_b: a, e
cursor.execute("""CREATE TABLE IF NOT EXISTS br_players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE,
    gender_id INTEGER NOT NULL,
    UNIQUE (name, gender_id),
    FOREIGN KEY (gender_id) REFERENCES br_genders(id) ON DELETE CASCADE);""")
cursor.execute("""CREATE TABLE IF NOT EXISTS br_weapons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weapon_name TEXT NOT NULL,
    weapon_bonus INTEGER NOT NULL,
    weapon_kind INTEGER NOT NULL,
    UNIQUE (weapon_name));""")
    # Kind 1: Melee
    # Kind 2: Ranged
cursor.execute("""CREATE TABLE IF NOT EXISTS br_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL,
    item_value INTEGER NOT NULL DEFAULT 0,
    UNIQUE (item_name));""")
cursor.execute("""CREATE TABLE IF NOT EXISTS br_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_text TEXT NOT NULL,
    category INTEGER NOT NULL,
    alive INTEGER NOT NULL,
    dead INTEGER NOT NULL,
    weapon_id INTEGER,
    item_id INTEGER,
    FOREIGN KEY (weapon_id) REFERENCES br_weapons(id) ON DELETE SET NULL,
    FOREIGN KEY (item_id) REFERENCES br_items(id) ON DELETE SET NULL);""")
    # category 0: idle
    # category 1: kills
    # category 2: item pick up
    # category 3: practice
    # category 4: rest
    # category 5: item usage
cursor.execute("""CREATE TABLE IF NOT EXISTS br_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    players INTEGER NOT NULL,
    winner TEXT NOT NULL,
    UNIQUE (title));""")
cursor.execute("""CREATE TABLE IF NOT EXISTS br_stages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    stage_number INTEGER NOT NULL,
    stage_name TEXT NOT NULL,
    texts TEXT NOT NULL,
    UNIQUE (session_id, stage_number),
    FOREIGN KEY (session_id) REFERENCES br_sessions(id) ON DELETE CASCADE);""")
cursor.execute("""INSERT OR IGNORE INTO br_genders (id, gen, arti_defi, pron_pers, pron_suj, letter_a, letter_b) VALUES
               (1, 'Femenino', 'la', 'la', 'ella', 'a', 'a'),
               (2, 'Masculino', 'el', 'lo', 'él', 'o', 'e');""")
cursor.execute("""INSERT OR IGNORE INTO br_players (id, name, gender_id) VALUES
               (1, 'Player1', 1),
               (2, 'Player2', 2),
               (3, 'Player3', 1),
               (4, 'Player4', 2),
               (5, 'Player5', 1),
               (6, 'Player6', 2),
               (7, 'Player7', 1),
               (8, 'Player8', 2),
               (9, 'Player9', 1),
               (10, 'Player10', 2),
               (11, 'Player11', 1),
               (12, 'Player12', 2),
               (13, 'Player13', 1),
               (14, 'Player14', 2),
               (15, 'Player15', 1),
               (16, 'Player16', 2),
               (17, 'Player17', 1),
               (18, 'Player18', 2),
               (19, 'Player19', 1),
               (20, 'Player20', 2),
               (21, 'Player21', 1),
               (22, 'Player22', 2),
               (23, 'Player23', 1),
               (24, 'Player24', 2),
               (25, 'Player25', 1),
               (26, 'Player26', 2),
               (27, 'Player27', 1),
               (28, 'Player28', 2),
               (29, 'Player29', 1),
               (30, 'Player30', 2),
               (31, 'Player31', 1),
               (32, 'Player32', 2),
               (33, 'Player33', 1),
               (34, 'Player34', 2),
               (35, 'Player35', 1),
               (36, 'Player36', 2),
               (37, 'Player37', 1),
               (38, 'Player38', 2),
               (39, 'Player39', 1),
               (40, 'Player40', 2),
               (41, 'Player41', 1),
               (42, 'Player42', 2),
               (43, 'Player43', 1),
               (44, 'Player44', 2),
               (45, 'Player45', 1),
               (46, 'Player46', 2),
               (47, 'Player47', 1),
               (48, 'Player48', 2),
               (49, 'Player49', 1),
               (50, 'Player50', 2);""")
cursor.execute("""INSERT OR IGNORE INTO br_weapons (id, weapon_name, weapon_bonus, weapon_kind) VALUES
               (1, 'Cuchillo', 1, 1),
               (2, 'Daga', 1, 1),
               (3, 'Espada corta', 1, 1),
               (4, 'Garrote', 1, 1),
               (5, 'Hacha', 1, 1),
               (6, 'Hoz', 1, 1),
               (7, 'Machete', 1, 1),
               (8, 'Martillo', 1, 1),
               (9, 'Pala', 1, 1),
               (10, 'Espada larga', 2, 1),
               (11, 'Espada ropera', 2, 1),
               (12, 'Lanza', 2, 1),
               (13, 'Maza', 2, 1),
               (14, 'Tridente', 2, 1),
               (15, 'Arco corto', 2, 2),
               (16, 'Ballesta ligera', 2, 2),
               (17, 'Jabalina', 2, 2),
               (18, 'Resortera', 2, 2),
               (19, 'Arco largo', 3, 2),
               (20, 'Ballesta pesada', 3, 2);""")
cursor.execute("""INSERT OR IGNORE INTO br_items (id, item_name, item_value) VALUES
               (1, 'Kit de primeros auxilios', 3),
               (2, 'Comida completa', 3),
               (3, 'Cantimplora', 2),
               (4, 'Escudo', 2),
               (5, 'Comida simple', 1),
               (6, 'Medicamentos', 3),
               (7, 'Hierbas medicinales', 1);""")
cursor.execute("""INSERT OR IGNORE INTO br_events (id, event_text, category, alive, dead, weapon_id, item_id) VALUES
               -- Idle (1)
               (1, '**player__1** se mantuvo alerta en su escondite.', 0, 0, 0, NULL, NULL),

               -- Unarmed Kills (2-14)
               (2, '**player__1** empujó por un precipicio a **player__2**.', 1, 1, 1, NULL, NULL),
               (3, '**player__1** atravesó a **player__2** con una rama de árbol.', 1, 1, 1, NULL, NULL),
               (4, '**player__1** asfixió hasta la muerte a **player__2**.', 1, 1, 1, NULL, NULL),
               (5, '**player__1** le rompió el cuello a **player__2**.', 1, 1, 1, NULL, NULL),
               (6, '**player__1** le dio con una roca en la cabeza a **player__2**.', 1, 1, 1, NULL, NULL),
               (7, '**player__1** ahogó a **player__2** en un río.', 1, 1, 1, NULL, NULL),
               (8, '**player__1** le aplastó la tráquea a **player__2** en un combate.', 1, 1, 1, NULL, NULL),
               (9, '**player__2** murió desangrado al escapar de **player__1**.', 1, 1, 1, NULL, NULL),
               (10, '**player__1** mató a **player__2** tras rendirse.', 1, 1, 1, NULL, NULL),
               (11, '**player__1** mató a **player__2** mientras no veía.', 1, 1, 1, NULL, NULL),
               (12, '**player__1** mató a **player__2** en una emboscada.', 1, 1, 1, NULL, NULL),
               (13, '**player__1** dejó morir a **player__2** tras noquearl@ en un río.', 1, 1, 1, NULL, NULL),
               (14, '**player__1** asesinó a **player__2** mientras ést$ pedía piedad.', 1, 1, 1, NULL, NULL),

               -- Draws (15-16)
               (15, '**player__1** se desangró después de matar a **player__2**.', 1, 0, 2, NULL, NULL),
               (16, '**player__1** intentó empujar a **player__2** a un precipicio pero acabó cayendo también.', 1, 0, 2, NULL, NULL),

               -- Weapon Kills (17-116)
               (17, '**player__1** le cortó el cuello a **player__2** con su cuchillo.', 1, 1, 1, 1, NULL),
               (18, '**player__1** le apuñaló la espalda a **player__2** con su cuchillo.', 1, 1, 1, 1, NULL),
               (19, '**player__1** le apuñaló el estómago a **player__2** con su cuchillo.', 1, 1, 1, 1, NULL),
               (20, '**player__1** le apuñaló el hombro a **player__2** con su cuchillo.', 1, 1, 1, 1, NULL),
               (21, '**player__1** le apuñaló el cuello a **player__2** con su cuchillo.', 1, 1, 1, 1, NULL),
               (22, '**player__1** le cortó el cuello a **player__2** con su daga.', 1, 1, 1, 2, NULL),
               (23, '**player__1** le apuñaló la espalda a **player__2** con su daga.', 1, 1, 1, 2, NULL),
               (24, '**player__1** le apuñaló el estómago a **player__2** con su daga.', 1, 1, 1, 2, NULL),
               (25, '**player__1** le apuñaló el hombro a **player__2** con su daga.', 1, 1, 1, 2, NULL),
               (26, '**player__1** le apuñaló el cuello a **player__2** con su daga.', 1, 1, 1, 2, NULL),
               (27, '**player__1** le cortó el vientre a **player__2** con su espada corta.', 1, 1, 1, 3, NULL),
               (28, '**player__1** decapitó a **player__2** con su espada corta.', 1, 1, 1, 3, NULL),
               (29, '**player__1** le perforó el pecho a **player__2** con su espada corta.', 1, 1, 1, 3, NULL),
               (30, '**player__1** le atravesó el torso desde el hombro a **player__2** con su espada corta.', 1, 1, 1, 3, NULL),
               (31, '**player__1** le atravesó el cuello a **player__2** con su espada corta.', 1, 1, 1, 3, NULL),
               (32, '**player__1** le rompió el cráneo a **player__2** con su garrote.', 1, 1, 1, 4, NULL),
               (33, '**player__1** le rompió la caja torácica a **player__2** con su garrote.', 1, 1, 1, 4, NULL),
               (34, '**player__1** noqueó a **player__2** con su garrote y l@ dejó morir.', 1, 1, 1, 4, NULL),
               (35, '**player__1** le arrancó la mandíbula a **player__2** de un golpe con su garrote.', 1, 1, 1, 4, NULL),
               (36, '**player__1** le rompió las piernas a **player__2** con su garrote y l@ terminó de matar.', 1, 1, 1, 4, NULL),
               (37, '**player__1** decapitó a **player__2** con su hacha.', 1, 1, 1, 5, NULL),
               (38, '**player__1** le clavó un hacha en la cabeza a **player__2**.', 1, 1, 1, 5, NULL),
               (39, '**player__1** le atravesó el torso desde el hombro a **player__2** con su hacha.', 1, 1, 1, 5, NULL),
               (40, '**player__1** le clavó un hacha en la garganta a **player__2**.', 1, 1, 1, 5, NULL),
               (41, '**player__1** le rompió el cráneo a **player__2** con su hacha.', 1, 1, 1, 5, NULL),
               (42, '**player__1** le cortó el cuello a **player__2** con su hoz.', 1, 1, 1, 6, NULL),
               (43, '**player__1** le cortó el vientre a **player__2** con su hoz.', 1, 1, 1, 6, NULL),
               (44, '**player__1** le atravesó el torso desde el hombro a **player__2** con su hoz.', 1, 1, 1, 6, NULL),
               (45, '**player__1** le clavó la hoz en la cabeza a **player__2**.', 1, 1, 1, 6, NULL),
               (46, '**player__1** decapitó a **player__2** con su hoz.', 1, 1, 1, 6, NULL),
               (47, '**player__1** le cortó el vientre a **player__2** con su machete.', 1, 1, 1, 7, NULL),
               (48, '**player__1** decapitó a **player__2** con su machete.', 1, 1, 1, 7, NULL),
               (49, '**player__1** le clavó el machete en la cabeza a **player__2**.', 1, 1, 1, 7, NULL),
               (50, '**player__1** le atravesó el torso desde el hombro a **player__2** con su machete.', 1, 1, 1, 7, NULL),
               (51, '**player__1** le clavó un machete en la garganta a **player__2**.', 1, 1, 1, 7, NULL),
               (52, '**player__1** le rompió el cráneo a **player__2** con su martillo.', 1, 1, 1, 8, NULL),
               (53, '**player__1** le rompió la caja torácica a **player__2** con su martillo.', 1, 1, 1, 8, NULL),
               (54, '**player__1** noqueó a **player__2** con su martillo y l@ dejó morir.', 1, 1, 1, 8, NULL),
               (55, '**player__1** le arrancó la mandíbula a **player__2** de un golpe con su martillo.', 1, 1, 1, 8, NULL),
               (56, '**player__1** le rompió las piernas a **player__2** con su martillo y l@ terminó de matar.', 1, 1, 1, 8, NULL),
               (57, '**player__1** le rompió el cráneo a **player__2** con su pala.', 1, 1, 1, 9, NULL),
               (58, '**player__1** le clavó su pala en la garganta a **player__2**.', 1, 1, 1, 9, NULL),
               (59, '**player__1** noqueó a **player__2** con su pala y l@ dejó morir.', 1, 1, 1, 9, NULL),
               (60, '**player__1** le arrancó la mandíbula a **player__2** de un golpe con su pala.', 1, 1, 1, 9, NULL),
               (61, '**player__1** le rompió las piernas a **player__2** con su pala y l@ terminó de matar.', 1, 1, 1, 9, NULL),
               (62, '**player__1** le cortó el vientre a **player__2** con su espada larga.', 1, 1, 1, 10, NULL),
               (63, '**player__1** decapitó a **player__2** con su espada larga.', 1, 1, 1, 10, NULL),
               (64, '**player__1** le perforó el pecho a **player__2** con su espada larga.', 1, 1, 1, 10, NULL),
               (65, '**player__1** le atravesó el torso desde el hombro a **player__2** con su espada larga.', 1, 1, 1, 10, NULL),
               (66, '**player__1** le atravesó el cuello a **player__2** con su espada larga.', 1, 1, 1, 10, NULL),
               (67, '**player__1** le cortó el vientre a **player__2** con su espada ropera.', 1, 1, 1, 11, NULL),
               (68, '**player__1** le atravesó la cabeza a **player__2** con su espada ropera.', 1, 1, 1, 11, NULL),
               (69, '**player__1** le perforó el pecho a **player__2** con su espada ropera.', 1, 1, 1, 11, NULL),
               (70, '**player__1** le perforó el pulmón a **player__2** por la espalda con su espada ropera.', 1, 1, 1, 11, NULL),
               (71, '**player__1** le atravesó el cuello a **player__2** con su espada ropera.', 1, 1, 1, 11, NULL),
               (72, '**player__1** embistió a **player__2** contra un árbol con su lanza.', 1, 1, 1, 12, NULL),
               (73, '**player__1** le atravesó la cabeza a **player__2** con su lanza.', 1, 1, 1, 12, NULL),
               (74, '**player__1** le atravesó el pecho a **player__2** con su lanza.', 1, 1, 1, 12, NULL),
               (75, '**player__1** le atravesó el cuello a **player__2** con su lanza.', 1, 1, 1, 12, NULL),
               (76, '**player__1** ensartó a **player__2** con su lanza.', 1, 1, 1, 12, NULL),
               (77, '**player__1** le rompió el cráneo a **player__2** con su maza.', 1, 1, 1, 13, NULL),
               (78, '**player__1** le rompió la caja torácica a **player__2** con su maza.', 1, 1, 1, 13, NULL),
               (79, '**player__1** noqueó a **player__2** con su maza y l@ dejó morir.', 1, 1, 1, 13, NULL),
               (80, '**player__1** le arrancó la mandíbula a **player__2** de un golpe con su maza.', 1, 1, 1, 13, NULL),
               (81, '**player__1** le rompió las piernas a **player__2** con su maza y l@ terminó de matar.', 1, 1, 1, 13, NULL),
               (82, '**player__1** embistió a **player__2** contra un árbol con su tridente.', 1, 1, 1, 14, NULL),
               (83, '**player__1** le atravesó la cabeza a **player__2** con su tridente.', 1, 1, 1, 14, NULL),
               (84, '**player__1** le atravesó el pecho a **player__2** con su tridente.', 1, 1, 1, 14, NULL),
               (85, '**player__1** le atravesó el cuello a **player__2** con su tridente.', 1, 1, 1, 14, NULL),
               (86, '**player__1** ensartó a **player__2** con su tridente.', 1, 1, 1, 14, NULL),
               (87, '**player__1** le disparó una flecha en la garganta a **player__2** con su arco corto.', 1, 1, 1, 15, NULL),
               (88, '**player__1** le disparó dos flechas en la espalda a **player__2** con su arco corto.', 1, 1, 1, 15, NULL),
               (89, '**player__1** le disparó dos flechas en el pecho a **player__2** con su arco corto.', 1, 1, 1, 15, NULL),
               (90, '**player__1** le apuñaló el cuello a **player__2** con una flecha.', 1, 1, 1, 15, NULL),
               (91, '**player__1** le apuñaló el estómago a **player__2** con una flecha.', 1, 1, 1, 15, NULL),
               (92, '**player__1** le disparó una virote en la garganta a **player__2** con su ballesta ligera.', 1, 1, 1, 16, NULL),
               (93, '**player__1** le disparó dos virotes en la espalda a **player__2** con su ballesta ligera.', 1, 1, 1, 16, NULL),
               (94, '**player__1** le disparó dos virotes en el pecho a **player__2** con su ballesta ligera.', 1, 1, 1, 16, NULL),
               (95, '**player__1** le apuñaló el cuello a **player__2** con un virote.', 1, 1, 1, 16, NULL),
               (96, '**player__1** le apuñaló el estómago a **player__2** con un virote.', 1, 1, 1, 16, NULL),
               (97, '**player__1** clavó a **player__2** contra un árbol con su jabalina.', 1, 1, 1, 17, NULL),
               (98, '**player__1** le atravesó la cabeza a **player__2** con su jabalina.', 1, 1, 1, 17, NULL),
               (99, '**player__1** le atravesó el pecho a **player__2** con su jabalina.', 1, 1, 1, 17, NULL),
               (100, '**player__1** le atravesó el cuello a **player__2** con su jabalina.', 1, 1, 1, 17, NULL),
               (101, '**player__1** ensartó a **player__2** con su jabalina.', 1, 1, 1, 17, NULL),
               (102, '**player__1** le rompió la frente a **player__2** con su resortera.', 1, 1, 1, 18, NULL),
               (103, '**player__1** noqueó a **player__2** con un disparo en la nuca con su resortera.', 1, 1, 1, 18, NULL),
               (104, '**player__1** mató a **player__2** con múltiples disparos de su resortera.', 1, 1, 1, 18, NULL),
               (105, '**player__1** obliteró a **player__2** con su resortera.', 1, 1, 1, 18, NULL),
               (106, '**player__1** le rompió el cuello a **player__2** con su resortera.', 1, 1, 1, 18, NULL),
               (107, '**player__1** le disparó una flecha en la garganta a **player__2** con su arco largo.', 1, 1, 1, 19, NULL),
               (108, '**player__1** le disparó dos flechas en la espalda a **player__2** con su arco largo.', 1, 1, 1, 19, NULL),
               (109, '**player__1** le disparó dos flechas en el pecho a **player__2** con su arco largo.', 1, 1, 1, 19, NULL),
               (110, '**player__1** le apuñaló el cuello a **player__2** con una flecha.', 1, 1, 1, 19, NULL),
               (111, '**player__1** le apuñaló el estómago a **player__2** con una flecha.', 1, 1, 1, 19, NULL),
               (112, '**player__1** le disparó una virote en la garganta a **player__2** con su ballesta pesada.', 1, 1, 1, 20, NULL),
               (113, '**player__1** le disparó dos virotes en la espalda a **player__2** con su ballesta pesada.', 1, 1, 1, 20, NULL),
               (114, '**player__1** le disparó dos virotes en el pecho a **player__2** con su ballesta pesada.', 1, 1, 1, 20, NULL),
               (115, '**player__1** le apuñaló el cuello a **player__2** con un virote.', 1, 1, 1, 20, NULL),
               (116, '**player__1** le apuñaló el estómago a **player__2** con un virote.', 1, 1, 1, 20, NULL),

               -- Weapon Pick Ups (117-136)
               (117, '**player__1** tomó un cuchillo.', 2, 0, 0, 1, NULL),
               (118, '**player__1** tomó una daga.', 2, 0, 0, 2, NULL),
               (119, '**player__1** tomó una espada corta.', 2, 0, 0, 3, NULL),
               (120, '**player__1** tomó un garrote.', 2, 0, 0, 4, NULL),
               (121, '**player__1** tomó un hacha.', 2, 0, 0, 5, NULL),
               (122, '**player__1** tomó una hoz.', 2, 0, 0, 6, NULL),
               (123, '**player__1** tomó un machete.', 2, 0, 0, 7, NULL),
               (124, '**player__1** tomó un martillo.', 2, 0, 0, 8, NULL),
               (125, '**player__1** tomó una pala.', 2, 0, 0, 9, NULL),
               (126, '**player__1** tomó una espada larga.', 2, 0, 0, 10, NULL),
               (127, '**player__1** tomó una espada ropera.', 2, 0, 0, 11, NULL),
               (128, '**player__1** tomó una lanza.', 2, 0, 0, 12, NULL),
               (129, '**player__1** tomó una maza.', 2, 0, 0, 13, NULL),
               (130, '**player__1** tomó un tridente.', 2, 0, 0, 14, NULL),
               (131, '**player__1** tomó un arco corto y munición.', 2, 0, 0, 15, NULL),
               (132, '**player__1** tomó una ballesta ligera y munición.', 2, 0, 0, 16, NULL),
               (133, '**player__1** tomó una jabalina.', 2, 0, 0, 17, NULL),
               (134, '**player__1** tomó una resortera y munición.', 2, 0, 0, 18, NULL),
               (135, '**player__1** tomó un arco largo y munición.', 2, 0, 0, 19, NULL),
               (136, '**player__1** tomó una ballesta pesada y munición.', 2, 0, 0, 20, NULL),

               -- Weapon Loot from Corpse (137)
               (137, '**player__1** tomó /weapon/ del cuerpo de **player__2**.', 2, 0, 0, NULL, NULL),

               -- Item Pick Ups (138-144)
               (138, '**player__1** tomó un kit de primeros auxilios.', 2, 0, 0, NULL, 1),
               (139, '**player__1** tomó comida completa.', 2, 0, 0, NULL, 2),
               (140, '**player__1** tomó una cantimplora.', 2, 0, 0, NULL, 3),
               (141, '**player__1** tomó un escudo.', 2, 0, 0, NULL, 4),
               (142, '**player__1** recolectó frutas silvestres.', 2, 0, 0, NULL, 5),
               (143, '**player__1** tomó unos medicamentos.', 2, 0, 0, NULL, 6),
               (144, '**player__1** recolectó hierbas medicinales.', 2, 0, 0, NULL, 7),

               -- Practice (145-164)
               (145, '**player__1** pasó el tiempo practicando con su cuchillo.', 3, 0, 0, 1, NULL),
               (146, '**player__1** pasó el tiempo practicando con su daga.', 3, 0, 0, 2, NULL),
               (147, '**player__1** pasó el tiempo practicando con su espada corta.', 3, 0, 0, 3, NULL),
               (148, '**player__1** pasó el tiempo practicando con su garrote.', 3, 0, 0, 4, NULL),
               (149, '**player__1** pasó el tiempo practicando con su hacha.', 3, 0, 0, 5, NULL),
               (150, '**player__1** pasó el tiempo practicando con su hoz.', 3, 0, 0, 6, NULL),
               (151, '**player__1** pasó el tiempo practicando con su machete.', 3, 0, 0, 7, NULL),
               (152, '**player__1** pasó el tiempo practicando con su martillo.', 3, 0, 0, 8, NULL),
               (153, '**player__1** pasó el tiempo practicando con su pala.', 3, 0, 0, 9, NULL),
               (154, '**player__1** pasó el tiempo practicando con su espada larga.', 3, 0, 0, 10, NULL),
               (155, '**player__1** pasó el tiempo practicando con su espada ropera.', 3, 0, 0, 11, NULL),
               (156, '**player__1** pasó el tiempo practicando con su lanza.', 3, 0, 0, 12, NULL),
               (157, '**player__1** pasó el tiempo practicando con su maza.', 3, 0, 0, 13, NULL),
               (158, '**player__1** pasó el tiempo practicando con su tridente.', 3, 0, 0, 14, NULL),
               (159, '**player__1** pasó el tiempo practicando con su arco corto.', 3, 0, 0, 15, NULL),
               (160, '**player__1** pasó el tiempo practicando con su ballesta ligera.', 3, 0, 0, 16, NULL),
               (161, '**player__1** pasó el tiempo practicando con su jabalina.', 3, 0, 0, 17, NULL),
               (162, '**player__1** pasó el tiempo practicando con su resortera.', 3, 0, 0, 18, NULL),
               (163, '**player__1** pasó el tiempo practicando con su arco largo.', 3, 0, 0, 19, NULL),
               (164, '**player__1** pasó el tiempo practicando con su ballesta pesada.', 3, 0, 0, 20, NULL),

               -- Rest (165-167)
               (165, '**player__1** descansó en su escondite.', 4, 0, 0, NULL, NULL),
               (166, '**player__1** comió y recuperó energías.', 4, 0, 0, NULL, 2),
               (167, '**player__1** bebió su agua y recuperó energías.', 4, 0, 0, NULL, 3),

               -- Item Usage (168-171)
               (168, '**player__1** usó un kit de primeros auxilios para tratarse las heridas.', 5, 0, 0, NULL, 1),
               (169, '**player__1** llenó su cantimplora.', 5, 0, 0, NULL, 3),
               (170, '**player__1** se medicó la enfermedad.', 5, 0, 0, NULL, 6),
               (171, '**player__1** usó las hierbas medicinales para hacer unos medicamentos.', 5, 0, 0, NULL, 7);""")
database.commit()



class BRPaginatorView(nextcord.ui.View):
    def __init__(self, pages, total, build_embed_fn, author_id):
        super().__init__(timeout=300)
        self.pages = pages
        self.total = total
        self.build_embed = build_embed_fn
        self.author_id = author_id
        self.current = 0
        self._update_buttons()
    def _update_buttons(self):
        self.btn_prev.disabled = self.current == 0
        self.btn_next.disabled = self.current == self.total - 1
    @nextcord.ui.button(label="◀ Anterior", style=nextcord.ButtonStyle.secondary)
    async def btn_prev(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Solo quien inició el juego puede navegar.", ephemeral=True)
            return
        self.current = max(0, self.current - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(self.current), view=self)
    @nextcord.ui.button(label="Siguiente ▶", style=nextcord.ButtonStyle.secondary)
    async def btn_next(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Solo quien inició el juego puede navegar.", ephemeral=True)
            return
        self.current = min(self.total - 1, self.current + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(self.current), view=self)
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True



class db_battleroyale(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = get_conn()
        self.cursor = self.db.cursor()



    @nextcord.slash_command(name="brplayers")
    async def brplayers(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("""SELECT p.id, p.name, g.gen
                FROM br_players p
                JOIN br_genders g ON p.gender_id = g.id
                ORDER BY p.id ASC;""")
            rows = cursor.fetchall()
            if not rows:
                await interaction.followup.send("No hay jugadores registrados aún.")
                return
            lines = [f"- **{r[1]}** ({r[2]}; ID: {r[0]})" for r in rows]
            desc = "\n".join(lines)
            if len(desc) > 4000:
                desc = desc[:4000] + "\n…"
            embed = nextcord.Embed(
                title="**LISTA DE JUGADORES:**",
                description=desc,
                color=nextcord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")



    @nextcord.slash_command(name="breditplayer")
    async def breditplayer(self,
                        interaction: nextcord.Interaction,
                        id: int = nextcord.SlashOption(description="Player ID", required=True),
                        name: str = nextcord.SlashOption(description="New name for the player", required=False, default=None),
                        gender: str = nextcord.SlashOption(description="New gender for the player", required=False,
                                                            choices={"Femenino":"1",
                                                                    "Masculino":"2"})):
        await interaction.response.defer(ephemeral=False)
        try:
            cursor.execute("SELECT id FROM br_players WHERE id = ?;", (id,))
            if not cursor.fetchone():
                await interaction.followup.send(f"Jugador con ID {id} no encontrado.")
                return
            updates = []
            params = []
            if name:
                updates.append("name = ?")
                params.append(name)
            if gender:
                updates.append("gender_id = ?")
                params.append(gender)
            if not updates:
                await interaction.followup.send("No se proporcionaron campos para actualizar.")
                return
            params.append(id)
            cursor.execute(f"UPDATE br_players SET {', '.join(updates)} WHERE id = ?;", tuple(params))
            database.commit()
            await interaction.followup.send(f"Jugador (ID: {id}) actualizado correctamente.")
        except sqlite3.IntegrityError:
            await interaction.followup.send("Error: Ya existe un jugador con ese nombre y género.")
        except ValueError:
            await interaction.followup.send("ID inválido. Debe ser un número entero.")



    @nextcord.slash_command(name="brplay")
    async def brplay(self,
                     interaction: nextcord.Interaction,
                     title: str = nextcord.SlashOption(description="Título del juego", required=True),
                     players: int = nextcord.SlashOption(description="Cantidad de jugadores (Entre 2 a 50)", required=False, default=24)):
        await interaction.response.defer(ephemeral=False)
        try:
            if players < 2 or players > 50:
                await interaction.followup.send("La cantidad de jugadores debe estar entre 2 y 50.")
                return
            # 1. Cargar jugadores
            self.cursor.execute("""
                SELECT p.id, p.name, g.letter_a, g.letter_b
                FROM br_players p
                JOIN br_genders g ON p.gender_id = g.id
                ORDER BY p.id ASC
                LIMIT ?;
            """, (players,))
            pool = self.cursor.fetchall()
            if len(pool) < players:
                await interaction.followup.send("No hay suficientes jugadores registrados para esa cantidad.")
                return
            alive_players = [{"id": r[0], "name": r[1], "letter_a": r[2], "letter_b": r[3]} for r in pool]
            # 2. Cargar eventos
            self.cursor.execute("SELECT event_text FROM br_events WHERE category = 1 AND alive = 1 AND dead = 1 AND weapon_id IS NULL;")
            kill_events = [row[0] for row in self.cursor.fetchall()]
            self.cursor.execute("SELECT event_text, weapon_id FROM br_events WHERE category = 1 AND alive = 1 AND dead = 1 AND weapon_id IS NOT NULL;")
            weapon_kill_events = {}
            for row in self.cursor.fetchall():
                weapon_kill_events.setdefault(row[1], []).append(row[0])
            self.cursor.execute("SELECT event_text FROM br_events WHERE category = 1 AND alive = 0 AND dead = 2;")
            both_die_events = [row[0] for row in self.cursor.fetchall()]
            self.cursor.execute("SELECT event_text FROM br_events WHERE category = 0;")
            idle_events = [row[0] for row in self.cursor.fetchall()]
            self.cursor.execute("SELECT event_text, weapon_id FROM br_events WHERE category = 2 AND weapon_id IS NOT NULL;")
            weapon_events = [(row[0], row[1]) for row in self.cursor.fetchall()]
            weapon_events_by_weapon = {}
            weapon_article = {}
            for evt_text, wid in weapon_events:
                weapon_events_by_weapon.setdefault(wid, []).append(evt_text)
                parts = evt_text.split("tomó ", 1)
                if len(parts) > 1:
                    weapon_article[wid] = parts[1].rstrip('.').split(' ', 1)[0]
            self.cursor.execute("SELECT event_text, weapon_id FROM br_events WHERE category = 3;")
            practice_events_by_weapon = {}
            for row in self.cursor.fetchall():
                practice_events_by_weapon.setdefault(row[1], []).append(row[0])
            self.cursor.execute("SELECT id, event_text, item_id FROM br_events WHERE category = 2 AND item_id IS NOT NULL;")
            item_pickup_events = [(row[0], row[1], row[2]) for row in self.cursor.fetchall()]
            masacre_item_pickups = [(eid, et, iid) for eid, et, iid in item_pickup_events if eid in (138, 139, 140, 141, 143)]
            idle_item_pickups = [(eid, et, iid) for eid, et, iid in item_pickup_events if eid in (142, 143, 144)]
            self.cursor.execute("SELECT event_text FROM br_events WHERE category = 2 AND weapon_id IS NULL AND item_id IS NULL;")
            weapon_loot_templates = [row[0] for row in self.cursor.fetchall()]
            self.cursor.execute("SELECT id, event_text, item_id FROM br_events WHERE category = 4;")
            rest_events_raw = [(row[0], row[1], row[2]) for row in self.cursor.fetchall()]
            rest_events = [row[1] for row in rest_events_raw if row[2] is None]
            rest_event_by_id = {row[0]: row[1] for row in rest_events_raw}
            self.cursor.execute("SELECT id, event_text, item_id FROM br_events WHERE category = 5;")
            item_usage_events = {row[0]: (row[1], row[2]) for row in self.cursor.fetchall()}
            self.cursor.execute("SELECT id, item_name, item_value FROM br_items;")
            items_data = {row[0]: row[1] for row in self.cursor.fetchall()}
            self.cursor.execute("SELECT id, item_value FROM br_items;")
            items_value = {row[0]: row[1] for row in self.cursor.fetchall()}
            rest_item_table = []
            if 168 in item_usage_events:
                rest_item_table.append({"id": 168, "template": item_usage_events[168][0], "requires_item": 1, "requires_wounded": True, "remove": 1, "add": None, "cures": True})
            if 166 in rest_event_by_id:
                rest_item_table.append({"id": 166, "template": rest_event_by_id[166], "requires_item": 2, "requires_wounded": False, "remove": 2, "add": None, "cures": False})
            if 167 in rest_event_by_id:
                rest_item_table.append({"id": 167, "template": rest_event_by_id[167], "requires_item": 3, "requires_wounded": False, "remove": None, "add": None, "cures": False, "empties_cantimplora": True})
            if 169 in item_usage_events:
                rest_item_table.append({"id": 169, "template": item_usage_events[169][0], "requires_item": 3, "requires_wounded": False, "remove": None, "add": None, "cures": False, "fills_cantimplora": True})
            if 170 in item_usage_events:
                rest_item_table.append({"id": 170, "template": item_usage_events[170][0], "requires_item": 6, "requires_wounded": False, "remove": 6, "add": None, "cures": False, "requires_sick": True, "cures_sick": True})
            if 171 in item_usage_events:
                rest_item_table.append({"id": 171, "template": item_usage_events[171][0], "requires_item": 7, "requires_wounded": False, "remove": 7, "add": 6, "cures": False})
            idle_item_effects = {
                142: (None, 5),   # Recolectó frutas, recibe Comida simple
                143: (None, 6),   # Tomó medicamentos, recibe Medicamentos
                144: (None, 7),   # Recolectó hierbas, recibe Hierbas medicinales
            }
            self.cursor.execute("SELECT id, weapon_name, weapon_bonus, weapon_kind FROM br_weapons;")
            weapons_data = {row[0]: {"weapon_name": row[1], "weapon_bonus": row[2], "weapon_kind": row[3]} for row in self.cursor.fetchall()}
            # Probabilidades: Tiers de arma
            tier_weights = {(1,1): 0.4, (2,2): 0.3, (1,2): 0.2, (2,3): 0.1}
            weapon_tiers = {}
            for evt_text, wid in weapon_events:
                wd_t = weapons_data[wid]
                tier_key = (wd_t["weapon_kind"], wd_t["weapon_bonus"])
                weapon_tiers.setdefault(tier_key, []).append((evt_text, wid))
            available_tiers = [(tk, evts) for tk, evts in weapon_tiers.items() if tk in tier_weights]
            tier_keys = [tk for tk, _ in available_tiers]
            tier_w = [tier_weights[tk] for tk in tier_keys]
            if not kill_events:
                await interaction.followup.send("No hay eventos 1v1 (categoría 1) cargados.")
                return
            def genderize(text: str, letter_a: str, letter_b: str) -> str:
                return text.replace('@', letter_a).replace('$', letter_b)
            pages = []
            stage_number = 0
            kill_counts = {p["id"]: 0 for p in alive_players}  # kills por jugador
            wounded_ids = {}    # id, True si el jugador está herido
            recent_deaths = []  # muertes desde el último Tributos Caídos
            death_order = []    # lista total de IDs en orden de muerte
            all_players_map = {p["id"]: p for p in alive_players}
            player_weapons = {}  # id {"weapon_id", "weapon_name", "weapon_bonus", "weapon_kind"}
            player_practice = {}  # id {weapon_id: bonus}
            player_fatigue = {p["id"]: 0 for p in alive_players}  # puntos de fatiga (combate=2, demás=1)
            pending_weapon_swap = {}  # pid {"old_weapon": dict|None, "new_weapon": dict, "victim_name": str}
            dropped_weapons = []  # [{"weapon_id", "weapon_name", "weapon_bonus", "weapon_kind", "victim_name"}]
            player_weapon_kills = {}  # pid {weapon_id: count of weapon-event kills}
            player_items = {}  # pid [item_id, ...] (max 2 items)
            cantimplora_empty = {}  # pid, True si la cantimplora está vacía
            dropped_items = []  # [{"item_id", "item_name", "victim_name"}]
            wounded_duration = {}  # pid, eventos consecutivos herido sin descanso
            sick_ids = {}  # pid, True si el jugador está enfermo
            rest_cooldown = {}  # pid, eventos restantes sin poder descansar (ni sumar fatiga)
            weapon_def_article = {wid: ("la" if art == "una" else "el") for wid, art in weapon_article.items()}
            tired_labels = {1: "Cansad", 2: "Agotad"}
            tired_announce = {1: "está cansad", 2: "está agotad"}
            def get_tired_level(pid):
                f = player_fatigue.get(pid, 0)
                if f < 6:
                    return 0
                if f < 8:
                    return 1
                return 2
            def add_fatigue_and_check(player, text, points):
                pid = player["id"]
                old_level = get_tired_level(pid)
                player_fatigue[pid] = player_fatigue.get(pid, 0) + points
                new_level = get_tired_level(pid)
                if new_level > old_level and new_level >= 1:
                    text = text.rstrip('.') + f"; **{player['name']}** {tired_announce[new_level]}{player['letter_a']}."
                return text
            def get_effective_weapon_value(pid, weapon):
                if not weapon:
                    return 0
                return weapon["weapon_bonus"] + player_practice.get(pid, {}).get(weapon["weapon_id"], 0)
            def player_has_item(pid, item_id):
                return item_id in player_items.get(pid, [])
            def get_inventory_total(pid):
                """Total de objetos (items + arma). Máximo 2."""
                return len(player_items.get(pid, [])) + (1 if player_weapons.get(pid) else 0)
            def get_lowest_object(pid):
                """Devuelve (value, type, ref) del objeto con menor valor. type='item' o 'weapon'. Random si hay empate."""
                candidates = []
                for iid in player_items.get(pid, []):
                    candidates.append((items_value.get(iid, 0), "item", iid))
                weapon = player_weapons.get(pid)
                if weapon:
                    candidates.append((weapon["weapon_bonus"], "weapon", weapon))
                if not candidates:
                    return None
                min_val = min(c[0] for c in candidates)
                return random.choice([c for c in candidates if c[0] == min_val])
            def drop_object_to_ground(pid, obj_type, obj_ref):
                """Tira un objeto al suelo (dropped_items o dropped_weapons)."""
                if obj_type == "item":
                    iid = obj_ref
                    if iid in player_items.get(pid, []):
                        player_items[pid].remove(iid)
                    dropped_items.append({"item_id": iid, "item_name": items_data.get(iid, "?"), "victim_name": None})
                    if iid == 3:
                        cantimplora_empty.pop(pid, None)
                elif obj_type == "weapon":
                    w = obj_ref
                    dropped_weapons.append({"weapon_id": w["weapon_id"], "weapon_name": w["weapon_name"], "weapon_bonus": w["weapon_bonus"], "weapon_kind": w["weapon_kind"], "victim_name": None})
                    player_weapons.pop(pid, None)
            def can_acquire_item(pid, item_id):
                """¿El jugador puede adquirir este item (posiblemente tirando el de menor valor)?"""
                if get_inventory_total(pid) < 2:
                    return True
                new_value = items_value.get(item_id, 0)
                lowest = get_lowest_object(pid)
                return lowest is not None and new_value > lowest[0]
            def add_item(pid, item_id):
                """Añade item al inventario aplicando regla de 2 objetos. Tira el menor si es necesario."""
                if get_inventory_total(pid) >= 2:
                    new_value = items_value.get(item_id, 0)
                    lowest = get_lowest_object(pid)
                    if lowest is None or new_value <= lowest[0]:
                        return False
                    drop_object_to_ground(pid, lowest[1], lowest[2])
                player_items.setdefault(pid, []).append(item_id)
                return True
            def make_room_for_weapon(pid):
                """Tira el objeto con menor valor para hacer hueco a un arma (siempre, las armas tienen prioridad)."""
                if get_inventory_total(pid) < 2:
                    return
                lowest = get_lowest_object(pid)
                if lowest is None:
                    return
                drop_object_to_ground(pid, lowest[1], lowest[2])
            def remove_item(pid, item_id):
                inv = player_items.get(pid, [])
                if item_id in inv:
                    inv.remove(item_id)
            def update_wounded_duration(player, was_rest):
                """Actualiza duración de herida. Retorna texto de enfermedad si aplica."""
                pid = player["id"]
                if was_rest:
                    wounded_duration[pid] = 0
                    return ""
                if not wounded_ids.get(pid, False):
                    wounded_duration[pid] = 0
                    return ""
                if sick_ids.get(pid, False):
                    return "" # Enfermo
                wounded_duration[pid] = wounded_duration.get(pid, 0) + 1
                if wounded_duration[pid] >= 3:
                    sick_ids[pid] = True
                    return f"; **{player['name']}** se enfermó por sus heridas expuestas."
                return ""
            def finalize_event(actor, text, fatigue_points, events_out, is_rest=False):
                """Aplica fatiga, revisa enfermedad, y añade el texto a events_out."""
                pid = actor["id"]
                if is_rest:
                    player_fatigue[pid] = 0
                    update_wounded_duration(actor, True)
                else:
                    # Si tiene cooldown de comida/agua, no suma fatiga
                    if rest_cooldown.get(pid, 0) > 0:
                        rest_cooldown[pid] -= 1
                    else:
                        text = add_fatigue_and_check(actor, text, fatigue_points)
                    sick_text = update_wounded_duration(actor, False)
                    if sick_text:
                        text = text.rstrip('.') + sick_text
                events_out.append(f"• {text}")
            def resolve_pending_swap(player, is_combat):
                pid = player["id"]
                if pid not in pending_weapon_swap:
                    return ""
                info = pending_weapon_swap.pop(pid)
                if is_combat and random.random() < 0.20:  # Probabilidades: 20% de no swap en combate
                    dropped_weapons.append({"weapon_id": info["new_weapon"]["weapon_id"], "weapon_name": info["new_weapon"]["weapon_name"], "weapon_bonus": info["new_weapon"]["weapon_bonus"], "weapon_kind": info["new_weapon"]["weapon_kind"], "victim_name": info["victim_name"]})
                    if info["old_weapon"]:
                        player_weapons[pid] = info["old_weapon"]
                    else:
                        player_weapons.pop(pid, None)
                    return ""
                else:
                    if info["old_weapon"]:
                        dropped_weapons.append({"weapon_id": info["old_weapon"]["weapon_id"], "weapon_name": info["old_weapon"]["weapon_name"], "weapon_bonus": info["old_weapon"]["weapon_bonus"], "weapon_kind": info["old_weapon"]["weapon_kind"], "victim_name": None})
                    return ""
            def try_pickup_dropped(player):
                """Intenta recoger un arma del suelo. Devuelve el texto del evento de loot o None."""
                pid = player["id"]
                if not dropped_weapons:
                    return None
                current_eff = get_effective_weapon_value(pid, player_weapons.get(pid))
                best_idx = None
                best_eff = current_eff
                for i, dw in enumerate(dropped_weapons):
                    dw_eff = dw["weapon_bonus"] + player_practice.get(pid, {}).get(dw["weapon_id"], 0)
                    if dw_eff > best_eff:
                        best_eff = dw_eff
                        best_idx = i
                if best_idx is not None and random.random() < 0.50:  # Probabilidades: Pickup arma del suelo
                    picked = dropped_weapons.pop(best_idx)
                    old_w = player_weapons.get(pid)
                    if old_w:
                        dropped_weapons.append({"weapon_id": old_w["weapon_id"], "weapon_name": old_w["weapon_name"], "weapon_bonus": old_w["weapon_bonus"], "weapon_kind": old_w["weapon_kind"], "victim_name": None})
                    else:
                        make_room_for_weapon(pid)
                    picked_w = {"weapon_id": picked["weapon_id"], "weapon_name": picked["weapon_name"], "weapon_bonus": picked["weapon_bonus"], "weapon_kind": picked["weapon_kind"]}
                    player_weapons[pid] = picked_w
                    if picked["victim_name"]:
                        return build_weapon_loot_event(player, picked_w, picked["victim_name"])
                    else:
                        def_art = weapon_def_article.get(picked["weapon_id"], "el")
                        text = f"**{player['name']}** tomó {def_art} {picked['weapon_name'].lower()}."
                        return genderize(text, player["letter_a"], player["letter_b"])
                return None
            def build_weapon_loot_event(taker, weapon, victim_name):
                """Genera el texto del evento "tomó X del cuerpo de Y" usando la plantilla."""
                def_art = weapon_def_article.get(weapon["weapon_id"], "el")
                weapon_str = f"{def_art} {weapon['weapon_name'].lower()}"
                if weapon_loot_templates:
                    template = random.choice(weapon_loot_templates)
                else:
                    template = "**player__1** tomó /weapon/ del cuerpo de **player__2**."
                text = template.replace("player__1", taker["name"]).replace("player__2", victim_name).replace("/weapon/", weapon_str)
                text = genderize(text, taker["letter_a"], taker["letter_b"])
                return text
            def handle_weapon_loot(killer, victim):
                """Lógica de saqueo de arma. Devuelve el texto del evento de loot o None."""
                victim_w = player_weapons.get(victim["id"])
                if not victim_w:
                    return None
                killer_w = player_weapons.get(killer["id"])
                if not killer_w:
                    make_room_for_weapon(killer["id"])
                    player_weapons[killer["id"]] = victim_w.copy()
                    pending_weapon_swap[killer["id"]] = {"old_weapon": None, "new_weapon": victim_w.copy(), "victim_name": victim["name"]}
                    return build_weapon_loot_event(killer, victim_w, victim["name"])
                killer_eff = get_effective_weapon_value(killer["id"], killer_w)
                victim_w_eff = victim_w["weapon_bonus"] + player_practice.get(killer["id"], {}).get(victim_w["weapon_id"], 0)
                if victim_w_eff <= killer_eff:
                    dropped_weapons.append({"weapon_id": victim_w["weapon_id"], "weapon_name": victim_w["weapon_name"], "weapon_bonus": victim_w["weapon_bonus"], "weapon_kind": victim_w["weapon_kind"], "victim_name": victim["name"]})
                    return None
                old_weapon = killer_w.copy()
                player_weapons[killer["id"]] = victim_w.copy()
                pending_weapon_swap[killer["id"]] = {"old_weapon": old_weapon, "new_weapon": victim_w.copy(), "victim_name": victim["name"]}
                return build_weapon_loot_event(killer, victim_w, victim["name"])
            def handle_item_loot(killer, victim, text):
                """Killer saquea items del victim. Lo que no pueda cargar va a dropped_items."""
                victim_inv = player_items.get(victim["id"], []).copy()
                if not victim_inv:
                    return text
                for iid in victim_inv:
                    # Swap cantimplora vacía por llena
                    if iid == 3 and not cantimplora_empty.get(victim["id"], False) \
                            and player_has_item(killer["id"], 3) and cantimplora_empty.get(killer["id"], False):
                        cantimplora_empty[killer["id"]] = False
                        player_items.get(victim["id"], []).remove(iid)
                        text = text.rstrip('.') + f"; **{killer['name']}** cambió su cantimplora vacía por la llena del cuerpo de **{victim['name']}**."
                        continue
                    if add_item(killer["id"], iid):
                        item_name = items_data.get(iid, "?")
                        text = text.rstrip('.') + f"; **{killer['name']}** tomó {item_name.lower()} del cuerpo de **{victim['name']}**."
                        player_items.get(victim["id"], []).remove(iid)
                        if iid == 3 and cantimplora_empty.get(victim["id"], False):
                            cantimplora_empty[killer["id"]] = True
                for iid in player_items.get(victim["id"], []):
                    dropped_items.append({"item_id": iid, "item_name": items_data.get(iid, "?"), "victim_name": victim["name"]})
                player_items.pop(victim["id"], None)
                cantimplora_empty.pop(victim["id"], None)
                return text
            def try_pickup_dropped_items(player, text):
                """Intenta recoger un item del suelo durante idle."""
                pid = player["id"]
                if not dropped_items:
                    return text
                eligible = [(i, di) for i, di in enumerate(dropped_items) if can_acquire_item(pid, di["item_id"])]
                if eligible and random.random() < 0.50:  # Probabilidades: Pickup item del suelo
                    idx, picked = random.choice(eligible)
                    dropped_items.pop(idx)
                    if add_item(pid, picked["item_id"]):
                        if picked["victim_name"]:
                            text = text.rstrip('.') + f"; **{player['name']}** tomó {picked['item_name'].lower()} del cuerpo de **{picked['victim_name']}**."
                        else:
                            text = text.rstrip('.') + f"; **{player['name']}** encontró {picked['item_name'].lower()}."
                return text
            def get_stage_name(n):
                if n == 1:
                    return "La Masacre"
                phases = ["Mañana", "Tarde", "Noche"]
                idx = n - 2
                phase = phases[(idx + 1) % 3]
                day = (idx + 1) // 3 + 1
                return f"{phase} {day}"
            def build_summary(is_final=False):
                lines = []
                # Muertos recientes
                if recent_deaths:
                    lines.append("**Caídos:**")
                    for d in recent_deaths:
                        k = d["kills"]
                        victim_letter = d["victim_letter_a"]
                        kills_txt = f"{k} baja{'s' if k != 1 else ''}"
                        lines.append(f"- **{d['name']}**: {kills_txt}, asesinad{victim_letter} por *{d['killed_by']}* en *{d['stage']}*.")
                # Supervivientes
                if not is_final:
                    alive_ids = [p["id"] for p in alive_players]
                    if alive_ids:
                        lines.append("\n**Supervivientes:**")
                        for pid in alive_ids:
                            p = all_players_map[pid]
                            k = kill_counts[pid]
                            gear_parts = []
                            condition_parts = []
                            p_items = player_items.get(pid, [])
                            for iid in p_items:
                                gear_parts.append(items_data.get(iid, "?").lower())
                            weapon = player_weapons.get(pid)
                            if weapon:
                                practice_b = player_practice.get(pid, {}).get(weapon["weapon_id"], 0)
                                if practice_b > 0:
                                    gear_parts.append(f"{weapon['weapon_name'].lower()}, {practice_b} práctica{'s' if practice_b > 1 else ''}")
                                else:
                                    gear_parts.append(weapon["weapon_name"].lower())
                            if wounded_ids.get(pid, False):
                                condition_parts.append(f"herid{p['letter_a']}")
                            if sick_ids.get(pid, False):
                                condition_parts.append(f"enferm{p['letter_a']}")
                            t_lvl = get_tired_level(pid)
                            if t_lvl >= 1:
                                condition_parts.append(f"{tired_labels[t_lvl].lower()}{p['letter_a']}")
                            if gear_parts and condition_parts:
                                status_txt = f" ({', '.join(gear_parts)}; {', '.join(condition_parts)})"
                            elif gear_parts:
                                status_txt = f" ({', '.join(gear_parts)})"
                            elif condition_parts:
                                status_txt = f" ({', '.join(condition_parts)})"
                            else:
                                status_txt = ""
                            kills_txt = f"{k} baja{'s' if k != 1 else ''}."
                            lines.append(f"- **{p['name']}**{status_txt}: {kills_txt}")
                return "\n".join(lines)
            while len(alive_players) > 1:
                stage_number += 1
                stage_name = get_stage_name(stage_number)
                waiting = alive_players.copy()
                random.shuffle(waiting)
                events_out = []
                dead_ids = set()
                while waiting:
                    can_idle = bool(idle_events) and len(waiting) >= 1
                    can_kill = len(waiting) >= 2
                    can_weapon = bool(weapon_events) and len(waiting) >= 1 and stage_name == "La Masacre"
                    phase = stage_name.split()[0] if stage_name != "La Masacre" else None
                    max_practice = {"Noche": 1, "Tarde": 2, "Mañana": 3}.get(phase, 3) if phase else 3
                    has_armed = phase and any(
                        player_weapons.get(p["id"])
                        and player_practice.get(p["id"], {}).get(player_weapons[p["id"]]["weapon_id"], 0) < max_practice
                        and sum(player_practice.get(p["id"], {}).values()) < 3
                        for p in waiting
                    )
                    can_rest = phase and bool(rest_events) and len(waiting) >= 1
                    # Probabilidades base por stage (con practice)
                    base_probs = {
                        "Mañana":  {"kill": 0.23, "rest": 0.15, "idle": 0.47, "practice": 0.15},
                        "Tarde":   {"kill": 0.30, "rest": 0.10, "idle": 0.40, "practice": 0.20},
                        "Noche":   {"kill": 0.10, "rest": 0.60, "idle": 0.20, "practice": 0.10},
                    }
                    # Probabilidade base por stage (sin practice)
                    unarmed_probs = {
                        "Mañana":  {"kill": 0.23, "rest": 0.15, "idle": 0.62},
                        "Tarde":   {"kill": 0.30, "rest": 0.20, "idle": 0.50},
                        "Noche":   {"kill": 0.10, "rest": 0.70, "idle": 0.20},
                    }
                    weights = {}
                    if stage_name == "La Masacre":
                        # Probabilidades La Masacre
                        if can_idle: weights["idle"] = 0.25
                        if can_weapon: weights["weapon"] = 0.35
                        if can_kill: weights["kill"] = 0.40
                    else:
                        max_tired = max((get_tired_level(p["id"]) for p in waiting), default=0)
                        if has_armed:
                            w = base_probs[phase].copy()
                        else:
                            w = unarmed_probs[phase].copy()
                        # Probabilidades Finalistas
                        if len(alive_players) == 2 and can_kill:
                            w = {"kill": 0.50, "rest": 0.10, "practice": 0.20, "idle": 0.20}
                        # Probabilidades jugadores cansados/agotados
                        if max_tired >= 2:
                            w["rest"] = w.get("rest", 0) + 0.10
                            if "practice" in w:
                                w["practice"] = max(0, w["practice"] - 0.10)
                            else:
                                w["idle"] = max(0, w["idle"] - 0.10)
                        elif max_tired == 1:
                            w["rest"] = w.get("rest", 0) + 0.05
                            if "practice" in w:
                                w["practice"] = max(0, w["practice"] - 0.05)
                            else:
                                w["idle"] = max(0, w["idle"] - 0.05)
                        for act, prob in w.items():
                            if act == "kill" and not can_kill:
                                continue
                            if act == "rest" and not can_rest:
                                continue
                            if act == "practice" and not has_armed:
                                continue
                            if prob > 0:
                                weights[act] = prob
                    if not weights:
                        break
                    total_w = sum(weights.values())
                    roll = random.random() * total_w
                    cumulative = 0
                    action = list(weights.keys())[-1]
                    for act, w in weights.items():
                        cumulative += w
                        if roll < cumulative:
                            action = act
                            break
                    if action == "idle":
                        actor = waiting.pop()
                        resolve_pending_swap(actor, False)
                        idle_item_applied = False
                        if stage_name == "La Masacre":
                            text = f"**{actor['name']}** escapó de la Cornucopia."
                        else:
                            # Probabilidades: Idle como Item Pickup
                            idle_item_chance = 0.15
                            pid_idle = actor["id"]
                            idle_eligible = [
                                (eid, et, iid) for eid, et, iid in idle_item_pickups
                                if can_acquire_item(pid_idle, iid)
                            ]
                            # Rellenar cantimplora (Idle)
                            if player_has_item(pid_idle, 3) and cantimplora_empty.get(pid_idle, False) and 169 in item_usage_events:
                                idle_eligible.append((169, item_usage_events[169][0], 3))
                            if idle_eligible and random.random() < idle_item_chance:
                                evt_id, template, item_id = random.choice(idle_eligible)
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                                if evt_id == 169:
                                    cantimplora_empty[pid_idle] = False
                                else:
                                    remove_id, add_id = idle_item_effects.get(evt_id, (None, None))
                                    if remove_id is not None:
                                        remove_item(pid_idle, remove_id)
                                    if add_id is not None:
                                        add_item(pid_idle, add_id)
                                idle_item_applied = True
                            else:
                                template = random.choice(idle_events)
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                        if not idle_item_applied:
                            weapon_pickup_text = try_pickup_dropped(actor)
                            text = try_pickup_dropped_items(actor, text)
                        else:
                            weapon_pickup_text = None
                        finalize_event(actor, text, 1, events_out)
                        if weapon_pickup_text:
                            events_out.append(f"• {weapon_pickup_text}")
                    elif action == "weapon":
                        actor = waiting.pop()
                        resolve_pending_swap(actor, False)
                        # Probabilidades: Weapon Pick Up como Item Pick Up
                        item_pickup_chance = 0.20
                        pid_wp = actor["id"]
                        eligible_item_pickups = [
                            (eid, et, iid) for eid, et, iid in masacre_item_pickups
                            if can_acquire_item(pid_wp, iid)
                        ]
                        if eligible_item_pickups and random.random() < item_pickup_chance:
                            evt_id, template, item_id = random.choice(eligible_item_pickups)
                            text = template.replace("player__1", actor["name"])
                            text = genderize(text, actor["letter_a"], actor["letter_b"])
                            add_item(pid_wp, item_id)
                        else:
                            chosen_tier = random.choices(tier_keys, weights=tier_w, k=1)[0]
                            tier_idx = tier_keys.index(chosen_tier)
                            template, weapon_id = random.choice(available_tiers[tier_idx][1])
                            text = template.replace("player__1", actor["name"])
                            text = genderize(text, actor["letter_a"], actor["letter_b"])
                            wd = weapons_data[weapon_id]
                            player_weapons[pid_wp] = {"weapon_id": weapon_id, "weapon_name": wd["weapon_name"], "weapon_bonus": wd["weapon_bonus"], "weapon_kind": wd["weapon_kind"]}
                        finalize_event(actor, text, 1, events_out)
                    elif action == "practice":
                        eligible = [i for i, p in enumerate(waiting)
                                    if player_weapons.get(p["id"])
                                    and player_practice.get(p["id"], {}).get(player_weapons[p["id"]]["weapon_id"], 0) < max_practice
                                    and sum(player_practice.get(p["id"], {}).values()) < 3]
                        if eligible:
                            idx = random.choice(eligible)
                            actor = waiting.pop(idx)
                            resolve_pending_swap(actor, False)
                            weapon = player_weapons[actor["id"]]
                            templates = practice_events_by_weapon.get(weapon["weapon_id"], [])
                            if templates:
                                template = random.choice(templates)
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                                player_practice.setdefault(actor["id"], {})[weapon["weapon_id"]] = player_practice.get(actor["id"], {}).get(weapon["weapon_id"], 0) + 1
                            else:
                                template = random.choice(idle_events)
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                        else:
                            actor = waiting.pop()
                            resolve_pending_swap(actor, False)
                            template = random.choice(idle_events)
                            text = template.replace("player__1", actor["name"])
                            text = genderize(text, actor["letter_a"], actor["letter_b"])
                        finalize_event(actor, text, 1, events_out)
                    elif action == "rest":
                        actor = waiting.pop()
                        resolve_pending_swap(actor, False)
                        pid_rest = actor["id"]
                        # Cooldown de comida/bebida, no puede descansar, hacer idle
                        if rest_cooldown.get(pid_rest, 0) > 0:
                            template = random.choice(idle_events)
                            text = template.replace("player__1", actor["name"])
                            text = genderize(text, actor["letter_a"], actor["letter_b"])
                            weapon_pickup_text = try_pickup_dropped(actor)
                            finalize_event(actor, text, 1, events_out)
                            if weapon_pickup_text:
                                events_out.append(f"• {weapon_pickup_text}")
                        else:
                            # Eventos de descanso con item específico
                            applicable = [
                                entry for entry in rest_item_table
                                if player_has_item(pid_rest, entry["requires_item"])
                                and (not entry["requires_wounded"] or wounded_ids.get(pid_rest, False))
                                and (not entry.get("requires_sick") or sick_ids.get(pid_rest, False))
                                and (not entry.get("empties_cantimplora") or not cantimplora_empty.get(pid_rest, False))
                                and (not entry.get("fills_cantimplora") or cantimplora_empty.get(pid_rest, False))
                            ]
                            # Probabilidades: Usar un evento de item en descanso
                            if applicable and random.random() < 0.60:
                                chosen = random.choice(applicable)
                                template = chosen["template"]
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                                if chosen["remove"] is not None:
                                    remove_item(pid_rest, chosen["remove"])
                                if chosen["add"] is not None:
                                    add_item(pid_rest, chosen["add"])
                                if chosen["cures"]:
                                    wounded_ids.pop(pid_rest, None)
                                    wounded_duration.pop(pid_rest, None)
                                if chosen.get("cures_sick"):
                                    sick_ids.pop(pid_rest, None)
                                if chosen.get("empties_cantimplora"):
                                    cantimplora_empty[pid_rest] = True
                                if chosen.get("fills_cantimplora"):
                                    cantimplora_empty[pid_rest] = False
                                # Cooldown: comida, 3 eventos; bebida, 2 eventos; sin descanso ni fatiga
                                if chosen["id"] == 166:
                                    rest_cooldown[pid_rest] = 3
                                elif chosen["id"] == 167:
                                    rest_cooldown[pid_rest] = 2
                            else:
                                template = random.choice(rest_events)
                                text = template.replace("player__1", actor["name"])
                                text = genderize(text, actor["letter_a"], actor["letter_b"])
                            finalize_event(actor, text, 0, events_out, is_rest=True)
                    else:
                        p1 = waiting.pop()
                        p2 = waiting.pop()
                        resolve_pending_swap(p1, True)
                        resolve_pending_swap(p2, True)
                        w1 = wounded_ids.get(p1["id"], False)
                        w2 = wounded_ids.get(p2["id"], False)
                        s1 = sick_ids.get(p1["id"], False)
                        s2 = sick_ids.get(p2["id"], False)
                        w1_original, w2_original = w1, w2
                        # Combate: 1d6 + Weapon bonus + Practice - Cansancio - Wounded - Sick
                        bonus1 = player_weapons.get(p1["id"], {}).get("weapon_bonus", 0)
                        pw1_data = player_weapons.get(p1["id"])
                        if pw1_data:
                            bonus1 += player_practice.get(p1["id"], {}).get(pw1_data["weapon_id"], 0)
                        bonus1 -= get_tired_level(p1["id"])
                        if s1:
                            bonus1 -= 2
                        bonus2 = player_weapons.get(p2["id"], {}).get("weapon_bonus", 0)
                        pw2_data = player_weapons.get(p2["id"])
                        if pw2_data:
                            bonus2 += player_practice.get(p2["id"], {}).get(pw2_data["weapon_id"], 0)
                        bonus2 -= get_tired_level(p2["id"])
                        if s2:
                            bonus2 -= 2
                        tie_count = 0
                        while True:
                            roll1 = random.randint(1, 6) + bonus1 - (3 if w1 else 0)
                            roll2 = random.randint(1, 6) + bonus2 - (3 if w2 else 0)
                            if roll1 != roll2:
                                if roll1 > roll2:
                                    killer, victim = p1, p2
                                else:
                                    killer, victim = p2, p1
                                killer_weapon = player_weapons.get(killer["id"])
                                was_weapon_event = False
                                if killer_weapon and killer_weapon["weapon_id"] in weapon_kill_events and random.random() < 0.90:  # Probabilidades: Evento de arma en kill
                                    template = random.choice(weapon_kill_events[killer_weapon["weapon_id"]])
                                    was_weapon_event = True
                                else:
                                    template = random.choice(kill_events)
                                text = template.replace("player__1", killer["name"]).replace("player__2", victim["name"])
                                text = genderize(text, victim["letter_a"], victim["letter_b"])
                                # Estado del victim (cansad@/herid@)
                                victim_was_wounded_before = w1_original if victim["id"] == p1["id"] else w2_original
                                victim_tired_lvl = get_tired_level(victim["id"])
                                if victim_tired_lvl >= 1:
                                    tired_txt = f"{tired_labels[victim_tired_lvl]}{victim['letter_a']}"
                                    if victim_was_wounded_before:
                                        text = text.rstrip('.') + f"; **{victim['name']}** estaba {tired_txt.lower()} y herid{victim['letter_a']}."
                                    else:
                                        text = text.rstrip('.') + f"; **{victim['name']}** estaba {tired_txt.lower()}."
                                elif victim_was_wounded_before:
                                    text = text.rstrip('.') + f"; **{victim['name']}** había sido herid{victim['letter_a']} previamente."
                                # Player1 acabó herid@ en el enfrentamiento
                                killer_was_wounded_before = w1_original if killer["id"] == p1["id"] else w2_original
                                if wounded_ids.get(killer["id"], False) and not killer_was_wounded_before:
                                    text = text.rstrip('.') + f"; **{killer['name']}** acabó herid{killer['letter_a']} en el enfrentamiento."
                                # Player1 está acomodándose con su arma
                                if killer_weapon and was_weapon_event:
                                    wid = killer_weapon["weapon_id"]
                                    player_weapon_kills.setdefault(killer["id"], {})[wid] = player_weapon_kills.get(killer["id"], {}).get(wid, 0) + 1
                                    wk_count = player_weapon_kills[killer["id"]][wid]
                                    current_practice = player_practice.get(killer["id"], {}).get(wid, 0)
                                    if wk_count % 2 == 0 and current_practice < 3:
                                        player_practice.setdefault(killer["id"], {})[wid] = current_practice + 1
                                        text = text.rstrip('.') + f"; **{killer['name']}** está acomodándose con su {killer_weapon['weapon_name'].lower()}."
                                loot_event_text = handle_weapon_loot(killer, victim)
                                text = handle_item_loot(killer, victim, text)
                                finalize_event(killer, text, 2, events_out)
                                if loot_event_text:
                                    events_out.append(f"• {loot_event_text}")
                                dead_ids.add(victim["id"])
                                death_order.append(victim["id"])
                                wounded_ids.pop(victim["id"], None)
                                sick_ids.pop(victim["id"], None)
                                wounded_duration.pop(victim["id"], None)
                                kill_counts[killer["id"]] += 1
                                recent_deaths.append({
                                    "name": victim["name"],
                                    "killed_by": killer["name"],
                                    "victim_letter_a": victim["letter_a"],
                                    "stage": stage_name,
                                    "kills": kill_counts[victim["id"]]
                                })
                                break
                            else:
                                # Empate
                                tie_count += 1
                                first_tie = (tie_count == 1)
                                tie_shield_win = False
                                p1_shield = player_has_item(p1["id"], 4)
                                p2_shield = player_has_item(p2["id"], 4)
                                # Escudo, primer empate: Enfermo herido & Herido muere o sobrevive
                                def shield_save_sick(p, w_state):
                                    if not w_state:
                                        wounded_ids[p["id"]] = True
                                    return True
                                def shield_save_wounded():
                                    return random.random() >= 0.5 
                                if s1 and not s2:
                                    if first_tie and p1_shield:
                                        shield_save_sick(p1, w1)
                                        w1 = True
                                        tie_shield_win = True
                                        continue
                                    killer, victim = p2, p1
                                elif s2 and not s1:
                                    if first_tie and p2_shield:
                                        shield_save_sick(p2, w2)
                                        w2 = True
                                        tie_shield_win = True
                                        continue
                                    killer, victim = p1, p2
                                elif s1 and s2:
                                    # Ambos enfermos
                                    p1_saved = first_tie and p1_shield
                                    p2_saved = first_tie and p2_shield
                                    if p1_saved:
                                        shield_save_sick(p1, w1); w1 = True
                                    if p2_saved:
                                        shield_save_sick(p2, w2); w2 = True
                                    if p1_saved and p2_saved:
                                        tie_shield_win = True
                                        continue
                                    elif p1_saved:
                                        killer, victim = p1, p2
                                        tie_shield_win = True
                                    elif p2_saved:
                                        killer, victim = p2, p1
                                        tie_shield_win = True
                                    else:
                                        killer, victim = None, None
                                elif w1 and not w2:
                                    # Wounded vs sano: wounded muere
                                    if first_tie and p1_shield:
                                        if shield_save_wounded():
                                            tie_shield_win = True
                                            continue
                                        killer, victim = p2, p1
                                        tie_shield_win = True  # no hiere al oponente
                                    else:
                                        killer, victim = p2, p1
                                elif w2 and not w1:
                                    if first_tie and p2_shield:
                                        if shield_save_wounded():
                                            tie_shield_win = True
                                            continue
                                        killer, victim = p1, p2
                                        tie_shield_win = True
                                    else:
                                        killer, victim = p1, p2
                                elif w1 and w2:
                                    # Ambos wounded
                                    p1_saved = first_tie and p1_shield and shield_save_wounded()
                                    p2_saved = first_tie and p2_shield and shield_save_wounded()
                                    if p1_saved and p2_saved:
                                        tie_shield_win = True
                                        continue
                                    elif p1_saved:
                                        killer, victim = p1, p2
                                        tie_shield_win = True
                                    elif p2_saved:
                                        killer, victim = p2, p1
                                        tie_shield_win = True
                                    else:
                                        killer, victim = None, None
                                else:
                                    # Ambos sanos: verificar escudos
                                    if p1_shield != p2_shield:
                                        # Escudo protege: sólo el sin escudo se hiere → pierde
                                        tie_shield_win = True
                                        if p1_shield:
                                            wounded_ids[p2["id"]] = True
                                            w2 = True
                                            killer, victim = p1, p2
                                        else:
                                            wounded_ids[p1["id"]] = True
                                            w1 = True
                                            killer, victim = p2, p1
                                        # No continue: cae al bloque de resolución de kill
                                    else:
                                        # Ambos con escudo o sin escudo: se hieren y repiten
                                        w1, w2 = True, True
                                        wounded_ids[p1["id"]] = True
                                        wounded_ids[p2["id"]] = True
                                        # Armas a distancia pierden ventaja en desempate
                                        pw1 = player_weapons.get(p1["id"])
                                        if pw1 and pw1["weapon_kind"] == 2:
                                            bonus1 = 1 - get_tired_level(p1["id"])
                                        pw2 = player_weapons.get(p2["id"])
                                        if pw2 and pw2["weapon_kind"] == 2:
                                            bonus2 = 1 - get_tired_level(p2["id"])
                                        continue
                                if killer is not None:
                                    # Uno mata al otro (víctima estaba wounded)
                                    killer_weapon = player_weapons.get(killer["id"])
                                    was_weapon_event = False
                                    # Melee: 30% evento de arma; Ranged: siempre genérico
                                    if killer_weapon and killer_weapon["weapon_kind"] == 1 and killer_weapon["weapon_id"] in weapon_kill_events and random.random() < 0.50:  # Probabilidades: Evento de arma melee en desempate
                                        template = random.choice(weapon_kill_events[killer_weapon["weapon_id"]])
                                        was_weapon_event = True
                                    else:
                                        template = random.choice(kill_events)
                                    text = template.replace("player__1", killer["name"]).replace("player__2", victim["name"])
                                    text = genderize(text, victim["letter_a"], victim["letter_b"])
                                    # Víctima cansada en desempate
                                    victim_tired_lvl = get_tired_level(victim["id"])
                                    if victim_tired_lvl >= 1:
                                        tired_txt = f"{tired_labels[victim_tired_lvl]}{victim['letter_a']}"
                                        text = text.rstrip('.') + f"; **{victim['name']}** estaba {tired_txt.lower()}."
                                    if not tie_shield_win:
                                        text = text.rstrip('.') + f"; **{killer['name']}** acabó herid{killer['letter_a']} en el enfrentamiento."
                                        wounded_ids[killer["id"]] = True
                                    # Experiencia de combate con arma
                                    if killer_weapon and was_weapon_event:
                                        wid = killer_weapon["weapon_id"]
                                        player_weapon_kills.setdefault(killer["id"], {})[wid] = player_weapon_kills.get(killer["id"], {}).get(wid, 0) + 1
                                        wk_count = player_weapon_kills[killer["id"]][wid]
                                        current_practice = player_practice.get(killer["id"], {}).get(wid, 0)
                                        if wk_count % 2 == 0 and current_practice < 3:
                                            player_practice.setdefault(killer["id"], {})[wid] = current_practice + 1
                                            text = text.rstrip('.') + f"; **{killer['name']}** está acomodándose con su {killer_weapon['weapon_name'].lower()}."
                                    loot_event_text = handle_weapon_loot(killer, victim)
                                    text = handle_item_loot(killer, victim, text)
                                    finalize_event(killer, text, 2, events_out)
                                    if loot_event_text:
                                        events_out.append(f"• {loot_event_text}")
                                    dead_ids.add(victim["id"])
                                    death_order.append(victim["id"])
                                    wounded_ids.pop(victim["id"], None)
                                    sick_ids.pop(victim["id"], None)
                                    wounded_duration.pop(victim["id"], None)
                                    kill_counts[killer["id"]] += 1
                                    recent_deaths.append({
                                        "name": victim["name"],
                                        "killed_by": killer["name"],
                                        "victim_letter_a": victim["letter_a"],
                                        "stage": stage_name,
                                        "kills": kill_counts[victim["id"]]
                                    })
                                else:
                                    # Ambos mueren
                                    if both_die_events:
                                        template = random.choice(both_die_events)
                                    else:
                                        template = random.choice(kill_events)
                                    text = template.replace("player__1", p1["name"]).replace("player__2", p2["name"])
                                    text = genderize(text, p2["letter_a"], p2["letter_b"])
                                    events_out.append(f"• {text}")
                                    kill_counts[p1["id"]] += 1
                                    kill_counts[p2["id"]] += 1
                                    # Armas e items de ambos van a dropped
                                    for p in [p1, p2]:
                                        pw = player_weapons.get(p["id"])
                                        if pw:
                                            dropped_weapons.append({"weapon_id": pw["weapon_id"], "weapon_name": pw["weapon_name"], "weapon_bonus": pw["weapon_bonus"], "weapon_kind": pw["weapon_kind"], "victim_name": p["name"]})
                                        for iid in player_items.get(p["id"], []):
                                            dropped_items.append({"item_id": iid, "item_name": items_data.get(iid, "?"), "victim_name": p["name"]})
                                        player_items.pop(p["id"], None)
                                        cantimplora_empty.pop(p["id"], None)
                                    dead_ids.add(p1["id"])
                                    dead_ids.add(p2["id"])
                                    death_order.append(p1["id"])
                                    death_order.append(p2["id"])
                                    wounded_ids.pop(p1["id"], None)
                                    wounded_ids.pop(p2["id"], None)
                                    sick_ids.pop(p1["id"], None)
                                    sick_ids.pop(p2["id"], None)
                                    wounded_duration.pop(p1["id"], None)
                                    wounded_duration.pop(p2["id"], None)
                                    recent_deaths.append({
                                        "name": p1["name"],
                                        "killed_by": p2["name"],
                                        "victim_letter_a": p1["letter_a"],
                                        "stage": stage_name,
                                        "kills": kill_counts[p1["id"]]
                                    })
                                    recent_deaths.append({
                                        "name": p2["name"],
                                        "killed_by": p1["name"],
                                        "victim_letter_a": p2["letter_a"],
                                        "stage": stage_name,
                                        "kills": kill_counts[p2["id"]]
                                    })
                                break
                # Quitar muertos de alive_players
                alive_players = [p for p in alive_players if p["id"] not in dead_ids]
                # Página de la ronda
                stage_text = "\n".join(events_out) if events_out else "No hubo eventos."
                pages.append((stage_name, stage_text))
                # Todos muertos, salir del bucle
                if len(alive_players) == 0:
                    break
                # Tributos Caídos después de cada Tarde
                if stage_name.startswith("Tarde") and len(alive_players) > 1:
                    day_num = stage_name.split()[-1]
                    pages.append((f"Tributos Caídos {day_num}", build_summary()))
                    recent_deaths.clear()
            # 4. Guardar sesión y stages en bd
            winner_name = alive_players[0]["name"] if len(alive_players) == 1 else "-"
            self.cursor.execute("""
                INSERT INTO br_sessions (title, players, winner)
                VALUES (?, ?, ?);
            """, (title, players, winner_name))
            session_id = self.cursor.lastrowid
            # 5) Tributos Caídos final + Página del ganador
            if recent_deaths:
                final_day = (stage_number - 2 + 1) // 3 + 1 if stage_number > 1 else 1
                pages.append((f"Tributos Caídos {final_day}", build_summary(is_final=True)))
                recent_deaths.clear()
            if len(alive_players) == 1:
                winner = alive_players[0]
                winner_kills = kill_counts[winner["id"]]
                extras_parts = []
                if sick_ids.get(winner["id"], False):
                    extras_parts.append(f"Enferm{winner['letter_a']}")
                elif wounded_ids.get(winner["id"], False):
                    extras_parts.append(f"Herid{winner['letter_a']}")
                w_tired_lvl = get_tired_level(winner["id"])
                if w_tired_lvl >= 1:
                    extras_parts.append(f"{tired_labels[w_tired_lvl]}{winner['letter_a']}")
                w_items = player_items.get(winner["id"], [])
                if w_items:
                    w_item_names = [items_data.get(iid, "?") for iid in w_items]
                    w_items_prefix = "Con" if not extras_parts else "con"
                    extras_parts.append(f"{w_items_prefix} {', '.join(w_item_names).lower()}")
                winner_weapon = player_weapons.get(winner["id"])
                if winner_weapon:
                    prefix = "Con" if not extras_parts else "con"
                    practice_b = player_practice.get(winner["id"], {}).get(winner_weapon["weapon_id"], 0)
                    if practice_b > 0:
                        extras_parts.append(f"{prefix} {winner_weapon['weapon_name'].lower()}, {practice_b} práctica{'s' if practice_b > 1 else ''}")
                    else:
                        extras_parts.append(f"{prefix} {winner_weapon['weapon_name'].lower()}")
                extras_txt = "; ".join(extras_parts) if extras_parts else "Ninguno"
                pages.append(("Ganador", f"¡**{winner_name}** ha ganado el Battle Royale!\n- **Bajas:** {winner_kills}\n- **Extras:** {extras_txt}"))
            else:
                pages.append(("Ganador", "Nadie sobrevivió el Battle Royale."))
            # Página de clasificación
            all_ids = list(all_players_map.keys())
            def rank_key(pid):
                kills = kill_counts[pid]
                if pid in death_order:
                    survival = death_order.index(pid)
                else:
                    survival = len(death_order)
                return (-kills, -survival)
            all_ids.sort(key=rank_key)
            rank_lines = []
            for pos, pid in enumerate(all_ids, start=1):
                p = all_players_map[pid]
                k = kill_counts[pid]
                kills_txt = f"{k} baja{'s' if k != 1 else ''}"
                rank_lines.append(f"{pos}. **{p['name']}**: {kills_txt}")
            pages.append(("Clasificación", "\n".join(rank_lines)))
            for i, (sn, st) in enumerate(pages, start=1):
                self.cursor.execute("""
                    INSERT INTO br_stages (session_id, stage_number, stage_name, texts)
                    VALUES (?, ?, ?, ?);
                """, (session_id, i, sn, st))
            self.db.commit()
            # 6) Enviar embed
            total = len(pages)
            def build_embed(page_index: int) -> nextcord.Embed:
                page_name, page_text = pages[page_index]
                if page_name == "Ganador":
                    header = f"**{title} — Ganador**"
                else:
                    header = f"**{title} — {page_name}**"
                desc = page_text
                if len(desc) > 4000:
                    desc = desc[:4000] + "\n…"
                embed = nextcord.Embed(title=header, description=desc, color=nextcord.Color.red())
                embed.set_footer(text=f"Página {page_index + 1}/{total}")
                return embed
            view = BRPaginatorView(pages, total, build_embed, interaction.user.id)
            await interaction.followup.send(embed=build_embed(0), view=view)
        except sqlite3.IntegrityError:
            await interaction.followup.send("Error: Ya existe un juego con ese título.")
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")



    @nextcord.slash_command(name="brsessions")
    async def brsessions(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            self.cursor.execute("""
                SELECT s.id, s.title, s.winner, s.players, COUNT(st.id) as pages
                FROM br_sessions s
                LEFT JOIN br_stages st ON s.id = st.session_id
                GROUP BY s.id
                ORDER BY s.id DESC;
            """)
            rows = self.cursor.fetchall()
            if not rows:
                await interaction.followup.send("No hay sesiones registradas aún.")
                return
            page_size = 10
            pages = []
            for i in range(0, len(rows), page_size):
                chunk = rows[i:i + page_size]
                lines = [f"- **{r[1]}** (ID {r[0]}): {r[3]} jugadores; {r[4]} páginas." for r in chunk]
                pages.append("\n".join(lines))
            total = len(pages)
            def build_embed(page_index: int) -> nextcord.Embed:
                desc = pages[page_index]
                if len(desc) > 4000:
                    desc = desc[:4000] + "\n…"
                embed = nextcord.Embed(
                    title="**Sesiones de Battle Royale**",
                    description=desc,
                    color=nextcord.Color.blue()
                )
                embed.set_footer(text=f"Página {page_index + 1}/{total}")
                return embed
            if total == 1:
                await interaction.followup.send(embed=build_embed(0))
            else:
                pages_tuples = [(str(i), p) for i, p in enumerate(pages)]
                view = BRPaginatorView(pages_tuples, total, build_embed, interaction.user.id)
                await interaction.followup.send(embed=build_embed(0), view=view)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")



    @nextcord.slash_command(name="brreplay")
    async def brreplay(self,
                       interaction: nextcord.Interaction,
                       search: str = nextcord.SlashOption(description="ID o título de la sesión", required=True)):
        await interaction.response.defer(ephemeral=False)
        try:
            if search.isdigit():
                self.cursor.execute("SELECT id, title, winner FROM br_sessions WHERE id = ?;", (int(search),))
            else:
                self.cursor.execute("SELECT id, title, winner FROM br_sessions WHERE title = ? COLLATE NOCASE;", (search,))
            session = self.cursor.fetchone()
            if not session:
                await interaction.followup.send(f"Sesión '{search}' no encontrada.")
                return
            session_id = session[0]
            session_title = session[1]
            self.cursor.execute("""
                SELECT stage_name, texts
                FROM br_stages
                WHERE session_id = ?
                ORDER BY stage_number ASC;
            """, (session_id,))
            stages = self.cursor.fetchall()
            if not stages:
                await interaction.followup.send("Esta sesión no tiene datos de rondas.")
                return
            pages = [(r[0], r[1]) for r in stages]
            total = len(pages)
            def build_embed(page_index: int) -> nextcord.Embed:
                page_name, page_text = pages[page_index]
                if page_name == "Ganador":
                    header = f"**{session_title} — Ganador**"
                else:
                    header = f"**{session_title} — {page_name}**"
                desc = page_text
                if len(desc) > 4000:
                    desc = desc[:4000] + "\n…"
                embed = nextcord.Embed(title=header, description=desc, color=nextcord.Color.red())
                embed.set_footer(text=f"Página {page_index + 1}/{total}")
                return embed
            view = BRPaginatorView(pages, total, build_embed, interaction.user.id)
            await interaction.followup.send(embed=build_embed(0), view=view)
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")



    @nextcord.slash_command(name="brresetplayer")
    async def brresetplayer(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=False)
        try:
            self.cursor.execute("SELECT COUNT(*) FROM br_players;")
            total = self.cursor.fetchone()[0]
            for i in range(1, total + 1):
                gender_id = 1 if i % 2 == 1 else 2
                self.cursor.execute("UPDATE br_players SET name = ?, gender_id = ? WHERE id = ?;", (f"Player{i}", gender_id, i))
            self.db.commit()
            await interaction.followup.send(f"Se restauraron {total} jugadores a sus valores por defecto (Player1-Player{total}).")
        except Exception as e:
            await interaction.followup.send(f"Ocurrió un error: {e}")



def setup(bot):
    bot.add_cog(db_battleroyale(bot))