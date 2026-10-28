"""Reading a SketchUp model (.skp) through SketchUp's own C library, headless (no SketchUp window, nothing installed).

SketchUp 2023's SketchUpAPI.dll (API 11) opens newer files too (status 1: "saved by a more recent version"). Only reads.

    m = Model(path)               the model, its top-level entities (m.top), materials, tags (layers), scenes
    m.defs[key]                   a definition (component or group; key = its pointer): own faces, children, bbox
    m.mesh(key)                   its own faces, triangulated: positions (inches, its own axes), triangles, each face's material
                                  (None: painted by the placement), its drawing element's entity (for the scenes' hidden lists)
    m.scene_hidden(name)          the entities a scene hides (pointers)
Units: SketchUp's inches. Transforms: 4x4 numpy, column vectors.
"""
import ctypes as C, os

import numpy as np

SU_DIR = os.environ.get("SKETCHUP_DIR", r"C:\Program Files\SketchUp\SketchUp 2023")
INCH = 0.0254


class Ref(C.Structure):
    _fields_ = [("ptr", C.c_void_p)]


class P3(C.Structure):
    _fields_ = [("x", C.c_double), ("y", C.c_double), ("z", C.c_double)]


class BB(C.Structure):
    _fields_ = [("a", P3), ("b", P3)]


class Xf(C.Structure):
    _fields_ = [("v", C.c_double * 16)]


class Color(C.Structure):
    _fields_ = [("r", C.c_ubyte), ("g", C.c_ubyte), ("b", C.c_ubyte), ("a", C.c_ubyte)]


def _lib():
    os.add_dll_directory(SU_DIR)
    S = C.CDLL(os.path.join(SU_DIR, "SketchUpAPI.dll"))
    for f in ("SUGroupToDrawingElement", "SUComponentInstanceToDrawingElement", "SUFaceToDrawingElement", "SUDrawingElementToEntity",
              "SUFaceToEntity", "SUEdgeToDrawingElement"):
        getattr(S, f).restype = C.c_void_p
    return S


class Model:
    def __init__(self, path):
        S = self.S = _lib()
        S.SUInitialize()
        self.m = Ref(); st = C.c_int(-1)
        r = S.SUModelCreateFromFileWithStatus(C.byref(self.m), os.fspath(path).encode("utf-8"), C.byref(st))
        if r != 0: raise RuntimeError(f"SketchUp could not open {path} (error {r})")
        self.status = st.value
        self._mat, self._tag = {}, {}
        e = Ref(); S.SUModelGetEntities(self.m, C.byref(e)); self.top_entities = e
        self.defs = {}
        self.top = self._entities(e, "top")

    # ---------- small helpers ----------
    def _str(self, fn, ref):
        S = self.S; s = Ref(); S.SUStringCreate(C.byref(s)); fn(ref, C.byref(s)); n = C.c_size_t(); S.SUStringGetUTF8Length(s, C.byref(n))
        buf = C.create_string_buffer(n.value + 1); c = C.c_size_t(); S.SUStringGetUTF8(s, n.value + 1, buf, C.byref(c)); S.SUStringRelease(C.byref(s))
        return buf.value.decode("utf-8", "replace")

    def _arr(self, numfn, getfn, ref, *pre):
        n = C.c_size_t(); numfn(ref, *pre, C.byref(n)); A = (Ref * n.value)(); c = C.c_size_t()
        if n.value: getfn(ref, *pre, n.value, A, C.byref(c))
        return list(A)

    @staticmethod
    def _xf(x):
        return np.array(x.v, dtype=np.float64).reshape(4, 4).T          # SketchUp's are column-major

    def material(self, ref):
        """(name, rgb, opacity) of a material pointer; textured ones by their texture's average colour"""
        if not ref.ptr: return None
        if ref.ptr in self._mat: return self._mat[ref.ptr]
        S = self.S; name = self._str(S.SUMaterialGetName, ref)
        col = Color(); S.SUMaterialGetColor(ref, C.byref(col)); rgb = (col.r, col.g, col.b)
        t = Ref()
        if S.SUMaterialGetTexture(ref, C.byref(t)) == 0 and t.ptr:
            a = Color()
            if S.SUTextureGetAverageColor(t, C.byref(a)) == 0: rgb = (a.r, a.g, a.b)
        use = C.c_bool(); op = C.c_double(1.0); S.SUMaterialGetUseOpacity(ref, C.byref(use)); S.SUMaterialGetOpacity(ref, C.byref(op))
        self._mat[ref.ptr] = out = (name, rgb, op.value if use.value else 1.0)
        return out

    def tag(self, de):
        S = self.S; l = Ref(); S.SUDrawingElementGetLayer(Ref(de), C.byref(l))
        if l.ptr not in self._tag: self._tag[l.ptr] = self._str(S.SULayerGetName, l) if l.ptr else "Layer0"
        return self._tag[l.ptr]

    def _placement(self, kind, r):
        """a child placement: (definition key, transform, tag, painted material, hidden, entity pointer, name)"""
        S = self.S
        if kind == "g":
            de = S.SUGroupToDrawingElement(r); ent = Ref(); S.SUGroupGetEntities(r, C.byref(ent)); d = Ref(); S.SUGroupGetDefinition(r, C.byref(d))
            x = Xf(); S.SUGroupGetTransform(r, C.byref(x)); name = self._str(S.SUGroupGetName, r)
        else:
            de = S.SUComponentInstanceToDrawingElement(r); d = Ref(); S.SUComponentInstanceGetDefinition(r, C.byref(d))
            ent = Ref(); S.SUComponentDefinitionGetEntities(d, C.byref(ent)); x = Xf(); S.SUComponentInstanceGetTransform(r, C.byref(x))
            name = self._str(S.SUComponentDefinitionGetName, d)
        hid = C.c_bool(); S.SUDrawingElementGetHidden(Ref(de), C.byref(hid)); mat = Ref(); S.SUDrawingElementGetMaterial(Ref(de), C.byref(mat))
        self._entities(ent, d.ptr, name)
        return (d.ptr, self._xf(x), self.tag(de), mat if mat.ptr else None, hid.value, S.SUDrawingElementToEntity(Ref(de)), name)

    def _entities(self, ent, key, name="top"):
        if key in self.defs: return self.defs[key]
        S = self.S
        d = self.defs[key] = {"key": key, "name": name, "ent": ent, "faces": self._arr(S.SUEntitiesGetNumFaces, S.SUEntitiesGetFaces, ent), "kids": []}
        b = BB(); S.SUEntitiesGetBoundingBox(ent, C.byref(b)); d["bbox"] = np.array([[b.a.x, b.a.y, b.a.z], [b.b.x, b.b.y, b.b.z]])
        d["kids"] = [self._placement("g", g) for g in self._arr(S.SUEntitiesGetNumGroups, S.SUEntitiesGetGroups, ent)] + \
                    [self._placement("i", i) for i in self._arr(S.SUEntitiesGetNumInstances, S.SUEntitiesGetInstances, ent)]
        return d

    # ---------- geometry ----------
    def mesh(self, key):
        """a definition's own faces: P (n,3 inches), T (m,3), per triangle: material pointer (0 = painted by the placement), the
        face's index; per face: (entity pointer, hidden)"""
        S = self.S; d = self.defs[key]
        if "mesh" in d: return d["mesh"]
        P, T, mat, fidx, fent = [], [], [], [], []; base = 0
        for fi, f in enumerate(d["faces"]):
            de = S.SUFaceToDrawingElement(f); hid = C.c_bool(); S.SUDrawingElementGetHidden(Ref(de), C.byref(hid))
            fent.append((S.SUFaceToEntity(f), hid.value))
            mh = Ref()
            if S.SUMeshHelperCreate(C.byref(mh), f) != 0: continue
            nv, nt = C.c_size_t(), C.c_size_t(); S.SUMeshHelperGetNumVertices(mh, C.byref(nv)); S.SUMeshHelperGetNumTriangles(mh, C.byref(nt))
            if nv.value and nt.value:
                V = (P3 * nv.value)(); c = C.c_size_t(); S.SUMeshHelperGetVertices(mh, nv.value, V, C.byref(c))
                I = (C.c_size_t * (nt.value * 3))(); S.SUMeshHelperGetVertexIndices(mh, nt.value * 3, I, C.byref(c))
                P.append(np.frombuffer(V, dtype=np.float64).reshape(-1, 3).copy())
                T.append(np.frombuffer(I, dtype=np.uint64).reshape(-1, 3).astype(np.int64) + base); base += nv.value
                fm = Ref(); S.SUFaceGetFrontMaterial(f, C.byref(fm))
                if not fm.ptr: S.SUFaceGetBackMaterial(f, C.byref(fm))
                if fm.ptr: self.material(fm)
                mat.append(np.full(nt.value, fm.ptr or 0, dtype=np.uint64)); fidx.append(np.full(nt.value, fi, dtype=np.int64))
            S.SUMeshHelperRelease(C.byref(mh))
        if P: out = (np.concatenate(P), np.concatenate(T), np.concatenate(mat), np.concatenate(fidx), fent)
        else: out = (np.zeros((0, 3)), np.zeros((0, 3), np.int64), np.zeros(0, np.uint64), np.zeros(0, np.int64), fent)
        d["mesh"] = out
        return out

    def edges(self, key):
        """a definition's own hard edges (not soft, not smooth, not hidden): (k, 2, 3) inches"""
        S = self.S; d = self.defs[key]; out = []
        for e in self._arr(S.SUEntitiesGetNumEdges, S.SUEntitiesGetEdges, d["ent"], C.c_bool(False)):
            soft, smooth, hid = C.c_bool(), C.c_bool(), C.c_bool()
            S.SUEdgeGetSoft(e, C.byref(soft)); S.SUEdgeGetSmooth(e, C.byref(smooth)); S.SUDrawingElementGetHidden(Ref(S.SUEdgeToDrawingElement(e)), C.byref(hid))
            if soft.value or smooth.value or hid.value: continue
            a, b = Ref(), Ref(); S.SUEdgeGetStartVertex(e, C.byref(a)); S.SUEdgeGetEndVertex(e, C.byref(b))
            p, q = P3(), P3(); S.SUVertexGetPosition(a, C.byref(p)); S.SUVertexGetPosition(b, C.byref(q))
            out.append(((p.x, p.y, p.z), (q.x, q.y, q.z)))
        return np.array(out, dtype=np.float64).reshape(-1, 2, 3)

    def scenes(self):
        S = self.S
        return [(self._str(S.SUSceneGetName, s), s) for s in self._arr(S.SUModelGetNumScenes, S.SUModelGetScenes, self.m)]

    def scene_hidden(self, name):
        S = self.S
        for n, s in self.scenes():
            if n == name: return {h.ptr for h in self._arr(S.SUSceneGetNumHiddenEntities, S.SUSceneGetHiddenEntities, s)}
        raise KeyError(name)

    def close(self):
        self.S.SUModelRelease(C.byref(self.m)); self.S.SUTerminate()
