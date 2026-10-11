# scripts/npz_to_bvh.py

Converts an Ardy motion file (.npz) into a BVH skeleton animation that Blender can import.

**Run (from the repo root):**
python scripts/npz_to_bvh.py outputs/test1.npz outputs/test1.bvh

**Needs:** the `ardy` package installed, and `pip install scipy`.
**Output:** a .bvh with Ardy's 27-joint Mixamo-style skeleton.
Full pipeline (Blender, Unity): see docs/ARDY_SETUP.md