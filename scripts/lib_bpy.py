"""lib_bpy.py — utilidades de modelado compartidas por los scripts del proyecto."""
import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

# Rotación en Z que orienta un texto (o letrero plano) hacia cada dirección del espacio,
# después de pararlo con 90° en X. Ver text().
FACING = {'-Y': 0.0, '+Y': math.pi, '+X': math.pi / 2, '-X': -math.pi / 2}


def fresh_collection(name, parent):
    """Crea una colección o la vacía si ya existe (los scripts se pueden repetir)."""
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    else:
        for o in list(col.objects):
            bpy.data.objects.remove(o, do_unlink=True)
    return col


def _add(name, bm, center, col):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = center
    col.objects.link(obj)
    return obj


def box(name, size, center, col):
    """Caja con la escala aplicada a los vértices (UV consistentes)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    return _add(name, bm, center, col)


def pipe(name, radius, length, center, col, segments=8):
    """Tubo orientado a lo largo de X (8 lados por defecto, low-poly)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                          radius1=radius, radius2=radius, depth=length)
    bmesh.ops.rotate(bm, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'), verts=bm.verts)
    return _add(name, bm, center, col)


def cylinder(name, radius, depth, center, col, segments=16, axis='Z'):
    """Cilindro con su eje en Z (o en X / Y con `axis`)."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    if axis != 'Z':
        eje = 'Y' if axis == 'X' else 'X'
        bmesh.ops.rotate(bm, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.pi / 2, 3, eje), verts=bm.verts)
    return _add(name, bm, center, col)


def tube_between(name, p0, p1, radius, col, segments=8):
    """Tubo recto entre dos puntos: pasamanos, cables tensos, soportes."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments,
                          radius1=radius, radius2=radius, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix()
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts)
    return _add(name, bm, (p0 + p1) / 2, col)


def blob(name, rx, ry, center, col, seed=0, sides=16):
    """Polígono plano de borde irregular (charcos)."""
    rng = random.Random(seed)
    bm = bmesh.new()
    verts = []
    for i in range(sides):
        a = 2 * math.pi * i / sides
        f = rng.uniform(0.7, 1.15)
        verts.append(bm.verts.new((math.cos(a) * rx * f, math.sin(a) * ry * f, 0)))
    bm.faces.new(verts)
    return _add(name, bm, center, col)


def _curve_to_mesh(tmp, name, col):
    """Convierte un objeto curva/texto en malla para tratarlo como cualquier otro objeto."""
    dg = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    data = tmp.data
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(data)
    mesh.name = name
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def text(name, body, size, loc, facing, col, align='CENTER'):
    """Texto plano parado frente a `facing` ('-Y', '+Y', '+X' o '-X'), convertido a malla.
    El texto de Blender vive en su plano XY; 90° en X lo para y la rotación en Z lo orienta."""
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body, cu.size = body, size
    cu.align_x, cu.align_y = align, 'CENTER'
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    col.objects.link(tmp)
    obj = _curve_to_mesh(tmp, name, col)
    obj.location = loc
    obj.rotation_euler = (math.pi / 2, 0, FACING[facing])
    return obj


def cable(name, points, radius, col):
    """Cable flexible: curva Bezier por los puntos dados, con grosor, convertida a malla."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions, cu.bevel_depth, cu.bevel_resolution = '3D', radius, 1
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(points) - 1)
    for bp, co in zip(sp.bezier_points, points):
        bp.co = co
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    tmp = bpy.data.objects.new(name + "_tmp", cu)
    col.objects.link(tmp)
    return _curve_to_mesh(tmp, name, col)


def repeat(obj, count, dx, dy=0.0, dz=0.0):
    """Array: un solo objeto con `count` copias separadas (dx, dy, dz)."""
    m = obj.modifiers.new("Repetir", 'ARRAY')
    m.use_relative_offset = False
    m.use_constant_offset = True
    m.constant_offset_displace = (dx, dy, dz)
    m.count = count


def anchor(name, loc, col):
    """Empty que marca dónde va un elemento de otro script."""
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = 'ARROWS'
    o.location = loc
    col.objects.link(o)


def anchor_location(name):
    """Posición de un empty ANCLA_* creado por 01_geometria_base.py."""
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"No existe {name}: ejecuta primero 01_geometria_base.py")
    return obj.location.copy()
