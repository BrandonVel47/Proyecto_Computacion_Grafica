"""lib_bpy.py — utilidades de modelado compartidas por los scripts del proyecto."""
import math

import bpy
import bmesh
from mathutils import Matrix


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
