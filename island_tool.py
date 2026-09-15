"""Ile-chateau low-poly pour Maya 2026.

Copiez TOUT ce fichier dans Maya > Script Editor > Python, puis Execute All.
La fenetre s'ouvre automatiquement. Cliquez sur « Creer / reconstruire l'ile ».
Uniquement maya.cmds : aucun plugin ni fichier Blender n'est modifie.
"""

import math
import random

import maya.cmds as cmds

WINDOW = "fantasyIslandWindow"
ROOT = "fantasyIsland_GRP"
GROUPS = {
    "environment": "island_environment_GRP", "castle": "island_castle_GRP",
    "trees": "island_trees_GRP", "houses": "island_houses_GRP",
    "clouds": "island_clouds_GRP", "sheep": "island_sheep_GRP",
    "monsters": "island_monsters_GRP", "lights": "island_lights_GRP",
}

# Des positions composees sur les terrasses de l'ile, pas dans l'ocean.
TREE_POINTS = [(-9, -1), (-8, 3), (-7, -4), (-6, 5), (-5, -6),
               (-5, 1), (-4, 4), (-3, -5), (-2, 6), (-1, -7),
               (1, -7), (3, -6), (4, 5), (5, -4), (6, 3), (7, 0),
               (8, -2), (-8, 0), (7, 5), (-6, -5), (6, -5),
               (-3, 1), (3, 1), (-1, 5), (2, 6), (0, -5),
               (-9, 2), (8, 1), (-4, -2), (4, -2)]
HOUSE_POINTS = [(-4, 0), (-2, 2), (0, 3), (2, 2), (4, 0),
                (-3, -3), (0, -3), (3, -3), (-1, 5), (2, 5)]
SHEEP_POINTS = [(-5, 3), (-3, 4), (-1, 4), (1, 4), (3, 3),
                (-4, -4), (-2, -5), (0, -5), (2, -5), (4, -4),
                (-6, 0), (6, 0), (-3, 0), (3, 0), (0, 0)]
MONSTER_POINTS = [(-10, -4), (10, -4), (-8, 5), (8, 5),
                  (-10, 0), (10, 0), (-5, -7), (5, -7)]

# Couleurs deduites de la reference : bleu nuit, lavande, rose poudre et brun.
SEASONS = {
    "Printemps": {"leaf": (.42, .30, .38), "sky": (.34, .46, .58)},
    "Ete": {"leaf": (.20, .29, .27), "sky": (.27, .40, .54)},
    "Automne": {"leaf": (.48, .17, .14), "sky": (.40, .34, .47)},
    "Hiver": {"leaf": (.46, .29, .31), "sky": (.45, .48, .62)},
}


def ensure_group(name, parent=None):
    if not cmds.objExists(name):
        cmds.group(empty=True, name=name)
    if parent:
        old_parent = cmds.listRelatives(name, parent=True, fullPath=False) or []
        if old_parent != [parent]:
            cmds.parent(name, parent)
    return name


def clear_group(name):
    children = cmds.listRelatives(name, children=True, fullPath=True) or []
    if children:
        cmds.delete(children)


def material(name, colour):
    shader = name + "_MAT"
    shading_group = shader + "SG"
    if not cmds.objExists(shader):
        shader = cmds.shadingNode("lambert", asShader=True, name=shader)
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True,
                  name=shading_group)
        cmds.connectAttr(shader + ".outColor", shading_group + ".surfaceShader",
                         force=True)
    cmds.setAttr(shader + ".color", colour[0], colour[1], colour[2],
                 type="double3")
    return shader


def make(command, name, pos, scale, shader, parent, rotate=(0, 0, 0), **kwargs):
    """Cree une primitive, la colore, puis la range dans son groupe."""
    node = command(name=name, **kwargs)[0]
    cmds.xform(node, worldSpace=True, translation=pos, rotation=rotate)
    cmds.setAttr(node + ".scale", scale[0], scale[1], scale[2], type="double3")
    cmds.makeIdentity(node, apply=True, translate=False, rotate=False, scale=True)
    cmds.sets(node, edit=True, forceElement=shader + "SG")
    cmds.parent(node, parent)
    return node


def season():
    if cmds.control("seasonMenu", exists=True):
        return cmds.optionMenu("seasonMenu", query=True, value=True)
    return "Hiver"


def ellipsoid_top(x, z, cx, cy, cz, rx, ry, rz):
    value = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
    if value >= 1.0:
        return -1000.0
    return cy + ry * math.sqrt(1.0 - value)


def terrain_y(x, z):
    """La surface des 11 montagnes; evite les arbres et le chateau flottants."""
    surfaces = [
        ellipsoid_top(x, z, 0, 1.25, 0, 14.4, 2.2, 12.0),
        ellipsoid_top(x, z, -5.4, 3.1, -1.1, 5.8, 4.0, 5.6),
        ellipsoid_top(x, z, 4.8, 3.4, .7, 5.8, 4.7, 5.8),
        ellipsoid_top(x, z, 0, 6.5, .6, 4.9, 4.6, 4.2),
        ellipsoid_top(x, z, -8.3, 2.0, 2.6, 4.0, 2.3, 4.0),
        ellipsoid_top(x, z, 8.4, 2.0, -2.4, 4.2, 2.4, 4.0),
        ellipsoid_top(x, z, -2.7, 4.6, -4.4, 3.5, 2.8, 3.4),
        ellipsoid_top(x, z, 3.1, 4.9, -3.7, 3.5, 3.0, 3.5),
        ellipsoid_top(x, z, -5.8, 3.1, 4.7, 3.8, 2.7, 3.5),
        ellipsoid_top(x, z, 5.9, 3.4, 4.5, 3.7, 3.0, 3.6),
        ellipsoid_top(x, z, 0, 8.4, .6, 2.9, 2.4, 2.5),
    ]
    return max(.25, max(surfaces)) + .10


def make_materials():
    return {
        "ocean": material("island_ocean", (.015, .075, .29)),
        "deep_rock": material("island_deep_rock", (.075, .10, .18)),
        "blue_rock": material("island_blue_rock", (.16, .20, .36)),
        "violet_rock": material("island_violet_rock", (.30, .25, .40)),
        "lavender_rock": material("island_lavender_rock", (.54, .47, .60)),
        "snow_shadow": material("island_snow_shadow", (.60, .62, .78)),
        "snow": material("island_snow", (.93, .80, .80)),
        "snow_light": material("island_snow_light", (1.0, .89, .86)),
        "castle_stone": material("castle_stone", (.53, .38, .40)),
        "castle_dark": material("castle_dark_wood", (.13, .07, .11)),
        "castle_wood": material("castle_warm_wood", (.43, .22, .17)),
        "trunk": material("tree_trunk", (.19, .06, .08)),
        "cloud": material("cloud_cream", (.98, .86, .83)),
    }


def mountain(parent, index, data):
    x, y, z, sx, sy, sz, shader, rot = data
    make(cmds.polySphere, "island_mountain_%02d" % index, (x, y, z),
         (sx, sy, sz), shader, parent, rot, subdivisionsX=14, subdivisionsY=8)


def snow_cap(parent, index, x, z, y, sx, sy, sz, shader, rotation):
    make(cmds.polySphere, "island_snow_cap_%02d" % index, (x, y, z),
         (sx, sy, sz), shader, parent, rotation, subdivisionsX=12, subdivisionsY=7)


def create_shore_rocks(parent, mats):
    rng = random.Random(103)
    for index in range(36):
        angle = (math.pi * 2.0 * index / 36.0) + rng.uniform(-.08, .08)
        radius = rng.uniform(14.5, 18.2)
        x, z = math.cos(angle) * radius, math.sin(angle) * radius * .78
        size = rng.uniform(.5, 1.8)
        make(cmds.polySphere, "island_shore_rock_%02d" % index,
             (x, rng.uniform(-.25, .10), z),
             (size, size * rng.uniform(.22, .50), size * rng.uniform(.6, 1.4)),
             mats["deep_rock"] if index % 2 else mats["blue_rock"], parent,
             (rng.uniform(0, 50), rng.uniform(0, 360), rng.uniform(0, 50)),
             subdivisionsX=8, subdivisionsY=5)


def create_surface_fragments(parent, mats):
    """Des centaines de facettes petites: le corps n'est plus une grosse sphere lisse."""
    rng = random.Random(20260915)
    shades = (mats["deep_rock"], mats["blue_rock"], mats["violet_rock"], mats["lavender_rock"])
    for index in range(360):
        while True:
            x, z = rng.uniform(-13.8, 13.8), rng.uniform(-11.4, 11.4)
            if (x / 14.2) ** 2 + (z / 11.8) ** 2 < .96:
                break
        size = rng.uniform(.12, .48)
        make(cmds.polySphere, "island_facet_%03d" % index,
             (x, terrain_y(x, z) - rng.uniform(.04, .20), z),
             (size, size * rng.uniform(.18, .50), size * rng.uniform(.55, 1.5)),
             shades[index % len(shades)], parent,
             (rng.uniform(0, 65), rng.uniform(0, 360), rng.uniform(0, 65)),
             subdivisionsX=6, subdivisionsY=4)


def create_castle(parent, mats):
    """Petit chateau, ancre dans une terrasse enfouie dans le sommet."""
    # Une terrasse compacte est placee SOUS la surface : son bord disparait dans le roc.
    summit = terrain_y(0, .6)
    terrace_y = summit - .52
    make(cmds.polyCylinder, "castle_foundation", (0, terrace_y, .6),
         (2.20, .42, 1.95), mats["violet_rock"], parent, subdivisionsX=10)
    # Le haut visible de la fondation est le sol de tous les murs et tours.
    base = terrace_y + .42

    walls = [
        (0, -1.35, 1.18, .58, .14), (0, 1.78, 1.18, .58, .14),
        (-1.95, .20, .14, .58, 1.55), (1.95, .20, .14, .58, 1.55),
    ]
    for index, (x, z, sx, sy, sz) in enumerate(walls):
        make(cmds.polyCube, "castle_wall_%02d" % index, (x, base + sy, z),
             (sx, sy, sz), mats["castle_stone"], parent)
        for tooth in range(-3, 4):
            if index < 2:
                px, pz = x + tooth * .30, z
            else:
                px, pz = x, z + tooth * .30
            make(cmds.polyCube, "castle_merlon_%02d_%02d" % (index, tooth + 3),
                 (px, base + sy * 2 + .14, pz), (.09, .14, .09),
                 mats["castle_stone"], parent)

    towers = [(-1.95, -1.35, 2.25), (1.95, -1.35, 2.65),
              (-1.95, 1.78, 2.45), (1.95, 1.78, 2.15), (0, .45, 3.65)]
    for index, (x, z, height) in enumerate(towers):
        make(cmds.polyCylinder, "castle_tower_%02d" % index,
             (x, base + height / 2.0, z), (.42, height / 2.0, .42),
             mats["castle_stone"], parent, subdivisionsX=8)
        if index in (0, 3):
            for tooth in range(8):
                angle = tooth * math.pi * 2.0 / 8.0
                make(cmds.polyCube, "castle_tower_tooth_%02d_%02d" % (index, tooth),
                     (x + math.cos(angle) * .36, base + height + .13,
                      z + math.sin(angle) * .36), (.08, .13, .08),
                     mats["castle_stone"], parent)
        else:
            make(cmds.polyCone, "castle_roof_%02d" % index,
                 (x, base + height + .46, z), (.62, .58, .62),
                 mats["castle_dark"], parent, subdivisionsX=8)

    make(cmds.polyCube, "castle_keep", (0, base + 1.82, .45),
         (.75, 1.82, .66), mats["castle_stone"], parent)
    make(cmds.polyCone, "castle_keep_roof", (0, base + 4.10, .45),
         (1.03, .72, .88), mats["castle_dark"], parent, subdivisionsX=4)
    make(cmds.polyCube, "castle_gate", (0, base + .40, -1.50),
         (.30, .40, .04), mats["castle_dark"], parent)
    for x in (-.48, .48):
        make(cmds.polyCube, "castle_timber_%s" % str(x).replace("-", "n"),
             (x, base + 1.82, -1.47), (.07, 1.76, .03), mats["castle_wood"], parent)


def create_environment():
    parent = GROUPS["environment"]
    castle_parent = GROUPS["castle"]
    clear_group(parent)
    clear_group(castle_parent)
    mats = make_materials()

    make(cmds.polyCylinder, "island_ocean", (0, -.60, 0), (28, .30, 28),
         mats["ocean"], parent, subdivisionsX=64)

    parts = [
        (0, 1.25, 0, 14.4, 2.2, 12.0, mats["deep_rock"], (0, 0, 0)),
        (-5.4, 3.1, -1.1, 5.8, 4.0, 5.6, mats["blue_rock"], (0, 20, 13)),
        (4.8, 3.4, .7, 5.8, 4.7, 5.8, mats["violet_rock"], (0, -24, -12)),
        (0, 6.5, .6, 4.9, 4.6, 4.2, mats["blue_rock"], (0, 6, 0)),
        (-8.3, 2.0, 2.6, 4.0, 2.3, 4.0, mats["blue_rock"], (0, 8, 12)),
        (8.4, 2.0, -2.4, 4.2, 2.4, 4.0, mats["deep_rock"], (0, -12, -10)),
        (-2.7, 4.6, -4.4, 3.5, 2.8, 3.4, mats["lavender_rock"], (0, 18, 18)),
        (3.1, 4.9, -3.7, 3.5, 3.0, 3.5, mats["violet_rock"], (0, -15, -16)),
        (-5.8, 3.1, 4.7, 3.8, 2.7, 3.5, mats["violet_rock"], (0, 24, 10)),
        (5.9, 3.4, 4.5, 3.7, 3.0, 3.6, mats["blue_rock"], (0, -18, -12)),
        (0, 8.4, .6, 2.9, 2.4, 2.5, mats["lavender_rock"], (0, 0, 0)),
    ]
    for index, data in enumerate(parts):
        mountain(parent, index, data)

    # Cascades de neige/crevasses posees sur les pentes, inspirees de l'image.
    caps = [
        (-3.7, -3.8, 6.2, 2.4, .32, 2.9, mats["snow"], (0, 22, -38)),
        (3.6, -3.2, 7.0, 2.1, .35, 3.0, mats["snow_light"], (0, -18, 35)),
        (4.6, -.5, 7.35, 1.55, .30, 2.4, mats["snow"], (0, -15, 48)),
        (-1.5, 2.0, 9.5, 2.65, .38, 2.1, mats["snow_light"], (0, 14, 0)),
        (-6.0, 2.2, 4.6, 1.45, .22, 1.8, mats["snow_shadow"], (0, 25, -35)),
        (6.0, 3.8, 5.6, 1.25, .25, 1.6, mats["snow_shadow"], (0, -20, 30)),
    ]
    for index, cap in enumerate(caps):
        snow_cap(parent, index, *cap)

    create_surface_fragments(parent, mats)
    create_shore_rocks(parent, mats)
    create_castle(castle_parent, mats)


def add_tree_snow(parent, x, y, z, width):
    if season() != "Hiver":
        return
    snow = material("tree_snow", (1.0, .88, .86))
    make(cmds.polySphere, "tree_snow", (x, y, z), (width, .12, width * .82),
         snow, parent, subdivisionsX=8, subdivisionsY=5)


def create_tree(index, point):
    x, z = point
    y = terrain_y(x, z)
    parent = cmds.group(empty=True, name="island_tree_%02d_GRP" % index,
                        parent=GROUPS["trees"])
    trunk = material("tree_trunk", (.19, .06, .08))
    leaves = material("tree_foliage", SEASONS[season()]["leaf"])
    height = random.uniform(1.35, 2.6)
    style = random.choice(("pine", "pine", "round"))

    make(cmds.polyCylinder, "tree_%02d_trunk" % index,
         (x, y + height / 2.0, z), (.13, height / 2.0, .13), trunk, parent,
         subdivisionsX=6)
    if style == "pine":
        layers = ((height, 1.05), (height + .58, .74), (height + 1.08, .46))
        for layer, (offset, width) in enumerate(layers):
            make(cmds.polyCone, "tree_%02d_leaf_%02d" % (index, layer),
                 (x, y + offset, z), (width, .70, width), leaves, parent,
                 subdivisionsX=6)
            add_tree_snow(parent, x, y + offset + .35, z, width * .82)
    else:
        for layer in range(3):
            px = x + random.uniform(-.30, .30)
            py = y + height + .25 + layer * .32
            make(cmds.polySphere, "tree_%02d_leaf_%02d" % (index, layer),
                 (px, py, z), (.70, .52, .65), leaves, parent,
                 subdivisionsX=7, subdivisionsY=5)
            add_tree_snow(parent, px, py + .35, z, .60)


def create_house(index, point):
    x, z = point
    y = terrain_y(x, z)
    parent = cmds.group(empty=True, name="island_house_%02d_GRP" % index,
                        parent=GROUPS["houses"])
    size = random.uniform(.72, 1.10)
    wall = material("house_wall_%02d" % index,
                    random.choice(((.66, .44, .42), (.73, .55, .45), (.48, .49, .62))))
    roof = material("house_roof_%02d" % index,
                    random.choice(((.15, .08, .12), (.26, .10, .13), (.16, .18, .28))))
    wood = material("house_wood", (.23, .10, .08))
    make(cmds.polyCube, "house_%02d_body" % index, (x, y + size * .70, z),
         (size, size * .70, size * .78), wall, parent)
    make(cmds.polyCone, "house_%02d_roof" % index, (x, y + size * 1.62, z),
         (size * 1.34, size * .62, size * 1.10), roof, parent,
         (0, 45, 0), subdivisionsX=4)
    make(cmds.polyCube, "house_%02d_door" % index,
         (x, y + size * .32, z + size * .80), (size * .20, size * .32, .035),
         wood, parent)


def create_cloud(index):
    parent = cmds.group(empty=True, name="island_cloud_%02d_GRP" % index,
                        parent=GROUPS["clouds"])
    cloud = material("cloud_cream", (.98, .86, .83))
    x, y, z = random.uniform(-19, 19), random.uniform(11, 18), random.uniform(-12, 12)
    for part in range(random.randint(3, 6)):
        make(cmds.polySphere, "cloud_%02d_%02d" % (index, part),
             (x + (part - 2) * random.uniform(.5, 1.05),
              y + random.uniform(-.25, .35), z),
             (random.uniform(.55, 1.25), random.uniform(.28, .62),
              random.uniform(.45, .88)), cloud, parent,
             subdivisionsX=8, subdivisionsY=5)


def create_sheep(index, point):
    x, z = point
    y = terrain_y(x, z)
    parent = cmds.group(empty=True, name="island_sheep_%02d_GRP" % index,
                        parent=GROUPS["sheep"])
    wool, dark = material("sheep_wool", (.93, .82, .80)), material("sheep_dark", (.12, .06, .08))
    make(cmds.polySphere, "sheep_%02d_body" % index, (x, y + .44, z),
         (.55, .35, .36), wool, parent, subdivisionsX=8, subdivisionsY=5)
    make(cmds.polySphere, "sheep_%02d_head" % index, (x + .48, y + .50, z),
         (.18, .18, .18), dark, parent, subdivisionsX=7, subdivisionsY=5)


def create_monster(index, point):
    x, z = point
    y = terrain_y(x, z)
    parent = cmds.group(empty=True, name="island_monster_%02d_GRP" % index,
                        parent=GROUPS["monsters"])
    body, horn = material("monster_body", (.18, .08, .27)), material("monster_horn", (.75, .61, .53))
    make(cmds.polySphere, "monster_%02d_body" % index, (x, y + .75, z),
         (.65, .75, .50), body, parent, subdivisionsX=8, subdivisionsY=5)
    for horn_index, side in enumerate((-.28, .28)):
        make(cmds.polyCone, "monster_%02d_horn_%d" % (index, horn_index),
             (x + side, y + 1.55, z), (.16, .42, .16), horn, parent,
             subdivisionsX=6)


def rebuild_category(category, count):
    data = {
        "trees": (TREE_POINTS, create_tree), "houses": (HOUSE_POINTS, create_house),
        "clouds": (range(12), lambda index, point: create_cloud(index)),
        "sheep": (SHEEP_POINTS, create_sheep), "monsters": (MONSTER_POINTS, create_monster),
    }
    points, creator = data[category]
    clear_group(GROUPS[category])
    for index, point in enumerate(list(points)[:count]):
        creator(index, point)


def apply_season(value, *_unused):
    palette = SEASONS[value]
    material("tree_foliage", palette["leaf"])
    cmds.displayRGBColor("background", palette["sky"][0], palette["sky"][1], palette["sky"][2])
    if cmds.objExists(ROOT):
        create_environment()
        tree_count = cmds.intSliderGrp("treeSlider", query=True, value=True)
        rebuild_category("trees", tree_count)


def apply_time(value, *_unused):
    if not cmds.objExists("island_key_light"):
        return
    if value == "Nuit":
        cmds.setAttr("island_key_light.intensity", .38)
        cmds.setAttr("island_key_light.color", .26, .31, .62, type="double3")
        cmds.setAttr("island_fill_light.intensity", .10)
        cmds.displayRGBColor("background", .025, .035, .10)
    else:
        cmds.setAttr("island_key_light.intensity", 1.25)
        cmds.setAttr("island_key_light.color", 1.0, .72, .64, type="double3")
        cmds.setAttr("island_fill_light.intensity", .28)
        apply_season(season())


def create_lights():
    clear_group(GROUPS["lights"])
    key = cmds.directionalLight(name="island_key_light", rotation=(-42, -28, 0))
    fill = cmds.ambientLight(name="island_fill_light", intensity=.28)
    for light in (key, fill):
        transform = cmds.listRelatives(light, parent=True, fullPath=True) or [light]
        cmds.parent(transform[0], GROUPS["lights"])


def build_island(*_unused):
    if cmds.objExists(ROOT):
        cmds.delete(ROOT)
    root = cmds.group(empty=True, name=ROOT)
    for name in GROUPS.values():
        ensure_group(name, root)
    create_environment()
    create_lights()
    for category, control in (("trees", "treeSlider"), ("houses", "houseSlider"),
                              ("clouds", "cloudSlider"), ("sheep", "sheepSlider"),
                              ("monsters", "monsterSlider")):
        rebuild_category(category, cmds.intSliderGrp(control, query=True, value=True))
    apply_time(cmds.optionMenu("timeMenu", query=True, value=True))
    cmds.select(ROOT)


def update_slider(category, control, *_unused):
    if cmds.objExists(ROOT):
        rebuild_category(category, cmds.intSliderGrp(control, query=True, value=True))


def delete_island(*_unused):
    if cmds.objExists(ROOT):
        cmds.delete(ROOT)


def ui_section(label):
    cmds.text(label=label, align="left", font="smallBoldLabelFont", height=22)
    cmds.separator(style="in", height=6)


def show_ui():
    if cmds.window(WINDOW, exists=True):
        cmds.deleteUI(WINDOW)
    cmds.window(WINDOW, title="Ile-chateau fantasy | Maya 2026", sizeable=False,
                backgroundColor=(.10, .12, .20))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=7)
    cmds.text(label="✦  ILE-CHATEAU FANTASY  ✦", align="center",
              font="boldLabelFont", height=32, backgroundColor=(.22, .18, .32))
    cmds.text(label="Falaises de lavande · neige rose · forteresse", align="center",
              font="smallObliqueLabelFont", height=22)

    ui_section("  POPULATIONS")
    controls = (("treeSlider", "▲  Arbres", "trees", 30, 16),
                ("houseSlider", "⌂  Maisons", "houses", 10, 3),
                ("cloudSlider", "☁  Nuages", "clouds", 12, 6),
                ("sheepSlider", "●  Moutons", "sheep", 15, 5),
                ("monsterSlider", "◆  Monstres", "monsters", 8, 2))
    for control, label, category, maximum, default in controls:
        cmds.intSliderGrp(control, label=label, field=True, minValue=0,
                          maxValue=maximum, value=default,
                          columnWidth3=(105, 46, 180),
                          changeCommand=lambda unused, c=category, ui=control: update_slider(c, ui))

    ui_section("  AMBIANCE")
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(105, 190))
    cmds.text(label="✿  Saison", align="left", font="smallBoldLabelFont")
    cmds.optionMenu("seasonMenu", changeCommand=apply_season, backgroundColor=(.35, .27, .38))
    for value in SEASONS:
        cmds.menuItem(label=value)
    cmds.setParent("..")
    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(105, 190))
    cmds.text(label="◐  Moment", align="left", font="smallBoldLabelFont")
    cmds.optionMenu("timeMenu", changeCommand=apply_time, backgroundColor=(.20, .28, .42))
    cmds.menuItem(label="Jour")
    cmds.menuItem(label="Nuit")
    cmds.setParent("..")

    ui_section("  SCENE")
    cmds.iconTextButton(style="textOnly", label="✦  CREER / RECONSTRUIRE L'ILE  ✦",
                        height=42, font="boldLabelFont", command=build_island,
                        backgroundColor=(.30, .48, .42))
    cmds.iconTextButton(style="textOnly", label="✕  SUPPRIMER SEULEMENT L'ILE",
                        height=30, command=delete_island,
                        backgroundColor=(.40, .20, .25))
    cmds.text(label="Les symboles servent de logos ; aucun fichier image externe n'est necessaire.",
              align="center", font="smallObliqueLabelFont", height=24)
    cmds.showWindow(WINDOW)


show_ui()
