"""lib_materiales.py — constructor de materiales PBR procedurales (nodos de Blender).

Todas las texturas usan las coordenadas de OBJETO (en metros, porque la escala está
aplicada a los vértices): la densidad de textura es la misma en toda la estación y no
hace falta desenvolver UV en geometría de cajas.
"""
import math

import bpy


def _rgba(c):
    return tuple(c) if len(c) == 4 else (*c, 1.0)


class Mat:
    """Envoltorio mínimo para armar un material con Principled BSDF."""

    def __init__(self, name, surface=True):
        self.mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.node('ShaderNodeOutputMaterial')
        self.coord = self.node('ShaderNodeTexCoord').outputs['Object']
        self.bsdf = None
        if surface:
            self.bsdf = self.node('ShaderNodeBsdfPrincipled')
            self.link(self.bsdf.outputs['BSDF'], self.out.inputs['Surface'])

    def node(self, kind):
        return self.nt.nodes.new(kind)

    def link(self, a, b):
        self.nt.links.new(a, b)

    def set(self, name, value):
        """Asigna un valor fijo o conecta un socket a una entrada del Principled."""
        sock = self.bsdf.inputs[name]
        if isinstance(value, bpy.types.NodeSocket):
            self.link(value, sock)
        elif isinstance(value, (tuple, list)):
            sock.default_value = _rgba(value)
        else:
            sock.default_value = value

    def mapping(self, scale=(1, 1, 1), rotation=(0, 0, 0)):
        n = self.node('ShaderNodeMapping')
        n.inputs['Scale'].default_value = scale
        n.inputs['Rotation'].default_value = rotation
        self.link(self.coord, n.inputs['Vector'])
        return n.outputs['Vector']

    def noise(self, scale, detail=5.0, vec=None):
        n = self.node('ShaderNodeTexNoise')
        n.inputs['Scale'].default_value = scale
        n.inputs['Detail'].default_value = detail
        self.link(vec or self.coord, n.inputs['Vector'])
        return n.outputs['Fac']

    def voronoi(self, scale):
        n = self.node('ShaderNodeTexVoronoi')
        n.inputs['Scale'].default_value = scale
        self.link(self.coord, n.inputs['Vector'])
        return n.outputs['Distance']

    def ramp(self, fac, stops):
        """ColorRamp: stops = [(posición, color), ...] en orden ascendente."""
        n = self.node('ShaderNodeValToRGB')
        el = n.color_ramp.elements
        el[0].position, el[0].color = stops[0][0], _rgba(stops[0][1])
        el[1].position, el[1].color = stops[1][0], _rgba(stops[1][1])
        for pos, col in stops[2:]:
            e = el.new(pos)
            e.color = _rgba(col)
        self.link(fac, n.inputs['Fac'])
        return n.outputs['Color']

    def mix(self, fac, a, b):
        n = self.node('ShaderNodeMix')
        n.data_type = 'RGBA'
        self.link(fac, n.inputs[0])
        for idx, val in ((6, a), (7, b)):
            if isinstance(val, bpy.types.NodeSocket):
                self.link(val, n.inputs[idx])
            else:
                n.inputs[idx].default_value = _rgba(val)
        return n.outputs[2]

    def bump(self, height, strength=0.3, dist=0.02):
        n = self.node('ShaderNodeBump')
        n.inputs['Strength'].default_value = strength
        n.inputs['Distance'].default_value = dist
        self.link(height, n.inputs['Height'])
        self.set('Normal', n.outputs['Normal'])

    def grime(self, scale=1.2):
        """Máscara de suciedad (0 = limpio, ~0.6 = sucio)."""
        return self.ramp(self.noise(scale, 6),
                         [(0.42, (0, 0, 0)), (0.68, (0.6, 0.6, 0.6))])


# ---------------------------------------------------------------- materiales
def concreto(name, base=(0.5, 0.48, 0.45), wet=False):
    m = Mat(name)
    manchas, fino = m.noise(1.5, 6), m.noise(30, 8)
    dark = tuple(c * 0.35 for c in base)
    light = tuple(min(c * 1.15, 1.0) for c in base)
    m.set('Base Color', m.ramp(manchas, [(0.38, dark), (0.5, base), (0.62, light)]))
    if wet:   # charcos: zonas muy lisas junto a zonas mate
        m.set('Roughness', m.ramp(manchas, [(0.45, (0.12,) * 3), (0.55, (0.7,) * 3)]))
    else:
        m.set('Roughness', m.ramp(fino, [(0.3, (0.75,) * 3), (0.7, (0.95,) * 3)]))
    m.bump(fino, 0.35, 0.02)
    return m.mat


def pintura(name, color, rough=0.3, wear_at=0.55):
    """Pintura descascarada: el color base se rompe en zonas oscuras y mate."""
    m = Mat(name)
    mask, fino = m.noise(5, 10), m.noise(40, 6)
    dirt = tuple(c * 0.2 for c in color)
    m.set('Base Color', m.ramp(mask, [(wear_at - 0.05, color), (wear_at + 0.07, dirt)]))
    m.set('Roughness', m.ramp(mask, [(wear_at - 0.05, (rough,) * 3), (wear_at + 0.07, (0.85,) * 3)]))
    m.bump(fino, 0.15, 0.01)
    return m.mat


def metal_oxidado(name, steel=(0.5, 0.5, 0.52), rust=(0.22, 0.09, 0.03)):
    m = Mat(name)
    mask, fino = m.noise(3, 8), m.noise(35, 6)
    m.set('Base Color', m.ramp(mask, [(0.45, steel), (0.6, rust)]))
    m.set('Metallic', m.ramp(mask, [(0.45, (1, 1, 1)), (0.6, (0.1, 0.1, 0.1))]))
    m.set('Roughness', m.ramp(mask, [(0.45, (0.35,) * 3), (0.6, (0.85,) * 3)]))
    m.bump(fino, 0.3, 0.01)
    return m.mat


def acero(name):
    m = Mat(name)
    m.set('Base Color', (0.72, 0.72, 0.74))
    m.set('Metallic', 1.0)
    m.set('Roughness', m.ramp(m.noise(40, 4), [(0.3, (0.25,) * 3), (0.7, (0.45,) * 3)]))
    return m.mat


def mate(name, color, rough=0.6):
    m = Mat(name)
    m.set('Base Color', color)
    m.set('Roughness', rough)
    return m.mat


def marmol(name):
    """Losetas de mármol pulido, irregulares, con suciedad que las vuelve mates."""
    m = Mat(name)
    b = m.node('ShaderNodeTexBrick')
    for k, v in (('Color1', (0.36, 0.29, 0.23, 1)), ('Color2', (0.17, 0.14, 0.12, 1)),
                 ('Mortar', (0.6, 0.58, 0.55, 1)), ('Mortar Size', 0.012),
                 ('Brick Width', 0.9), ('Row Height', 0.5), ('Bias', 0.0), ('Scale', 1.0)):
        b.inputs[k].default_value = v
    m.link(m.mapping(), b.inputs['Vector'])
    grime = m.grime(1.2)
    m.set('Base Color', m.mix(grime, b.outputs['Color'], (0.04, 0.035, 0.03)))
    m.set('Roughness', m.ramp(grime, [(0.0, (0.1,) * 3), (0.6, (0.6,) * 3)]))
    m.bump(b.outputs['Fac'], 0.2, 0.004)
    return m.mat


def travertino(name):
    """Paneles verticales de travertino de 0.6 m (se proyectan en el plano X-Z)."""
    m = Mat(name)
    b = m.node('ShaderNodeTexBrick')
    b.offset = 0.0
    for k, v in (('Color1', (0.62, 0.50, 0.38, 1)), ('Color2', (0.52, 0.41, 0.30, 1)),
                 ('Mortar', (0.05, 0.04, 0.03, 1)), ('Mortar Size', 0.008),
                 ('Brick Width', 0.6), ('Row Height', 2.4), ('Scale', 1.0)):
        b.inputs[k].default_value = v
    m.link(m.mapping(rotation=(math.pi / 2, 0, 0)), b.inputs['Vector'])
    grime = m.grime(0.8)
    m.set('Base Color', m.mix(grime, b.outputs['Color'], (0.07, 0.05, 0.035)))
    m.set('Roughness', m.ramp(m.noise(20, 5), [(0.3, (0.35,) * 3), (0.7, (0.6,) * 3)]))
    return m.mat


def balasto(name):
    m = Mat(name)
    piedras = m.voronoi(70)
    m.set('Base Color', m.ramp(piedras, [(0.0, (0.03, 0.03, 0.03)), (0.5, (0.22, 0.21, 0.20))]))
    m.set('Roughness', 0.9)
    m.bump(piedras, 1.0, 0.1)
    return m.mat


def emision(name, color, strength):
    """Material emisivo. El nodo se llama 'Emision' para poder animar su 'Strength'."""
    m = Mat(name, surface=False)
    e = m.node('ShaderNodeEmission')
    e.name = 'Emision'
    e.inputs['Color'].default_value = _rgba(color)
    e.inputs['Strength'].default_value = strength
    m.link(e.outputs['Emission'], m.out.inputs['Surface'])
    return m.mat


def cristal_interior(name):
    """Ventanas del vagón: oscuras con un resplandor tenue de las luces interiores."""
    m = Mat(name)
    m.set('Base Color', (0.02, 0.02, 0.02))
    m.set('Roughness', 0.05)
    m.set('Emission Color', (0.8, 0.75, 0.45))
    m.set('Emission Strength', 0.6)
    return m.mat


def niebla(name):
    """Volumen de niebla con densidad irregular (zonas más espesas y más claras)."""
    m = Mat(name, surface=False)
    v = m.node('ShaderNodeVolumePrincipled')
    v.inputs['Color'].default_value = (0.8, 0.85, 0.9, 1)
    v.inputs['Anisotropy'].default_value = 0.4
    dens = m.ramp(m.noise(0.15, 3), [(0.4, (0.004,) * 3), (0.6, (0.03,) * 3)])
    m.link(dens, v.inputs['Density'])
    m.link(v.outputs['Volume'], m.out.inputs['Volume'])
    return m.mat
