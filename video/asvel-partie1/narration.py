# -*- coding: utf-8 -*-
"""Narration de « ASVEL : la naissance d'une légende » — partie 1 (1948-1957).

Chaque phrase est un segment audio. Le montage se cale automatiquement sur la
durée réelle de chaque segment : déposer un enregistrement « voix/<id>.wav »
remplace la voix de synthèse provisoire pour ce segment.

pause = silence ajouté après le segment (en secondes).
tts   = variante d'écriture utilisée uniquement par la voix de synthèse.
"""

P_PHRASE = 0.35     # entre deux phrases d'un même paragraphe
P_PARA = 0.85       # entre deux paragraphes
P_SEQ = 1.8         # entre deux séquences

SEGMENTS = [
    # ── SÉQUENCE 1 — LA NAISSANCE DE L'ASVEL ──
    ("s1_01", "Pour comprendre le nom de l'ASVEL, il faut d'abord revenir aux deux associations qui lui ont donné naissance.", P_PARA),
    ("s1_02", "D'un côté, l'Association Sportive Villeurbannaise.", P_PHRASE),
    ("s1_03", "De l'autre, l'Éveil Lyonnais.", P_PARA),
    ("s1_04", "Elles possèdent chacune leur histoire.", P_PHRASE),
    ("s1_05", "L'une vient d'une tradition sportive laïque, l'autre de celle du patronage catholique.", P_PARA),
    ("s1_06", "Leurs dirigeants choisissent pourtant de réunir leurs forces.", P_PARA),
    ("s1_07", "Le vingt et un décembre mille neuf cent quarante-huit, cette fusion donne officiellement naissance à l'Association Sportive Villeurbanne Éveil Lyonnais.", P_PARA),
    ("s1_08", "Les initiales forment un nom : ASVEL.", P_PARA + 0.4),
    ("s1_09", "Pierre Millet devient le premier président du nouveau club.", P_PARA),
    ("s1_10", "Son histoire commune commence à peine.", P_PHRASE),
    ("s1_11", "Mais, sur le terrain, les résultats vont arriver immédiatement.", P_SEQ),

    # ── SÉQUENCE 2 — LES PREMIERS CHAMPIONS ──
    ("s2_01", "En mille neuf cent quarante-neuf, quelques mois après sa création, l'ASVEL remporte son premier championnat de France.", P_PARA),
    ("s2_02", "Le club vient de naître.", P_PHRASE),
    ("s2_03", "Il est déjà champion.", P_PARA),
    ("s2_04", "Au cœur de ces premières années, André Buffière joue un rôle essentiel.", P_PHRASE),
    ("s2_05", "Joueur, entraîneur et recruteur, il participe à la construction de l'équipe.", P_PARA),
    ("s2_06", "Autour de lui, le club rassemble des joueurs qui vont marquer cette première période.", P_PHRASE),
    ("s2_07", "Henri Grange rejoindra lui aussi les grandes figures des années cinquante.", P_PARA),
    ("s2_08", "Cette première victoire donne immédiatement du poids au nouveau club.", P_PARA),
    ("s2_09", "Mais une question se pose : l'ASVEL peut-elle recommencer ?", P_PARA),
    ("s2_10", "La réponse arrive dès l'année suivante.", P_PARA),
    ("s2_11", "En mille neuf cent cinquante, elle conserve son titre.", P_PARA),
    ("s2_12", "Deux championnats en deux ans.", P_PHRASE),
    ("s2_13", "Villeurbanne s'installe parmi les grandes forces du basket français.", P_SEQ),

    # ── SÉQUENCE 3 — LES TITRES S'ACCUMULENT ──
    ("s3_01", "En mille neuf cent cinquante-deux, Villeurbanne remporte un troisième championnat.", P_PARA),
    # découpé pour faire apparaître chaque année au moment où elle est prononcée
    ("s3_02a", "Puis viennent les titres de mille neuf cent cinquante-cinq,", 0.12),
    ("s3_02b", "cinquante-six", 0.08),
    ("s3_02c", "et cinquante-sept.", P_PARA),
    ("s3_03", "Sur ses neuf premières années d'existence, l'ASVEL compte donc six championnats de France.", P_PARA),
    ("s3_04", "Trois de ces titres sont remportés à la suite, entre mille neuf cent cinquante-cinq et mille neuf cent cinquante-sept.", P_PARA),
    ("s3_05", "Cette régularité distingue la première époque du club.", P_PHRASE),
    ("s3_06", "L'ASVEL réussit à revenir au sommet, année après année.", P_PARA),
    ("s3_07", "Chaque championnat renforce un palmarès encore jeune, mais déjà considérable.", P_PARA),
    ("s3_08", "Une première génération a donné à l'ASVEL une place nationale.", P_PHRASE),
    # 4 secondes de musique seule sur la frise complète
    ("s3_09", "Les suivantes auront désormais un héritage à prolonger.", 4.0 + P_SEQ),

    # ── SÉQUENCE 4 — LES PREMIÈRES COUPES DE FRANCE ──
    ("s4_01", "Le championnat ne résume pas tous les succès de ces premières années.", P_PARA),
    ("s4_02", "En mille neuf cent cinquante-trois, l'ASVEL remporte également la Coupe de France.", P_PARA),
    ("s4_03", "Elle gagne à nouveau cette compétition en mille neuf cent cinquante-sept, l'année où elle est aussi championne.", P_PARA),
    ("s4_04", "Le club réalise donc un doublé championnat–Coupe de France.", P_PARA,
     "Le club réalise donc un doublé, championnat, Coupe de France."),
    ("s4_05", "Au total, entre sa création et la fin de l'année mille neuf cent cinquante-sept, son équipe a remporté six championnats et deux Coupes de France.", P_PARA),
    ("s4_06", "Huit trophées nationaux en neuf ans.", P_PARA),
    ("s4_07", "Pour une association née en décembre mille neuf cent quarante-huit, le chemin parcouru est immense.", P_PHRASE),
    ("s4_08", "Ces victoires forment le premier socle du prestige de l'ASVEL.", P_SEQ),

    # ── SÉQUENCE 5 — UN HÉRITAGE À TRANSMETTRE ──
    ("s5_01", "Quand on raconte l'histoire de l'ASVEL, les images les plus récentes viennent souvent en premier : les finales à l'Astroballe, les campagnes européennes, les équipes que l'on a vues jouer soi-même.", P_PARA),
    ("s5_02", "Mais ces premières victoires rappellent que l'histoire du club s'écrivait déjà bien avant.", P_PARA),
    ("s5_03", "André Buffière, Henri Grange et les joueurs de ces premières générations ont installé Villeurbanne au sommet du championnat.", P_PARA),
    ("s5_04", "Ils ont donné aux équipes suivantes des références, des trophées et une réputation à défendre.", P_PARA),
    ("s5_05", "La suite ne sera pourtant pas une répétition des débuts.", P_PHRASE),
    ("s5_06", "Le club va évoluer, de nouveaux dirigeants vont arriver et d'autres joueurs vont prendre leur place.", P_PARA),
    ("s5_07", "Dans les années soixante, deux noms vont ouvrir une nouvelle grande période de l'ASVEL.", P_PARA + 0.3),
    ("s5_08", "Raphaël de Barros.", P_PARA + 0.2),
    ("s5_09", "Et Alain Gilles.", 0.0),
]


def segments():
    for s in SEGMENTS:
        sid, text, pause = s[:3]
        tts = s[3] if len(s) > 3 else text
        yield sid, text, pause, tts
