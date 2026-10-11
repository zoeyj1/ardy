"""
Convert an Ardy .npz motion file into a .bvh file, using Ardy's
CoreSkeleton27 joint hierarchy (Mixamo-style naming).

Usage:
    python scripts/npz_to_bvh.py outputs/test1.npz outputs/test1.bvh
"""
import sys
import numpy as np

try:
    from scipy.spatial.transform import Rotation as R
except ImportError:
    sys.exit("Missing scipy. Install it first: pip install scipy")

from ardy.skeleton.definitions import CoreSkeleton27


def build_tree(names_with_parents):
    """Return {joint_name: [child_names]} and {joint_name: parent_name}."""
    children = {name: [] for name, _ in names_with_parents}
    parent_of = {}
    for name, parent in names_with_parents:
        parent_of[name] = parent
        if parent is not None:
            children[parent].append(name)
    return children, parent_of


def write_joint(f, name, children, parent_of, offsets, indent, order):
    """Recursively write one HIERARCHY node and record traversal order."""
    pad = "  " * indent
    tag = "ROOT" if parent_of[name] is None else "JOINT"
    f.write(f"{pad}{tag} {name}\n{pad}{{\n")
    ox, oy, oz = offsets[name]
    f.write(f"{pad}  OFFSET {ox:.6f} {oy:.6f} {oz:.6f}\n")
    if parent_of[name] is None:
        f.write(f"{pad}  CHANNELS 6 Xposition Yposition Zposition Xrotation Yrotation Zrotation\n")
    else:
        f.write(f"{pad}  CHANNELS 3 Xrotation Yrotation Zrotation\n")
    order.append(name)

    kids = children[name]
    if not kids:
        length = np.linalg.norm([ox, oy, oz])
        if length < 1e-6:
            ex, ey, ez = 0.0, 5.0, 0.0
        else:
            scale = max(length, 5.0)
            ex, ey, ez = (ox / length) * scale, (oy / length) * scale, (oz / length) * scale
        f.write(f"{pad}  End Site\n{pad}  {{\n{pad}    OFFSET {ex:.6f} {ey:.6f} {ez:.6f}\n{pad}  }}\n")
    else:
        for child in kids:
            write_joint(f, child, children, parent_of, offsets, indent + 1, order)
    f.write(f"{pad}}}\n")


def main(npz_path, bvh_path):
    data = np.load(npz_path, allow_pickle=True)
    local_rot_mats = data["local_rot_mats"]
    root_positions = data["root_positions"]
    fps = float(data["fps"])
    n_frames = local_rot_mats.shape[0]

    skel = CoreSkeleton27(load=True)
    names_with_parents = skel.bone_order_names_with_parents
    joint_names = [n for n, _ in names_with_parents]
    children, parent_of = build_tree(names_with_parents)

    neutral = skel.neutral_joints.cpu().numpy()
    name_to_idx = {n: i for i, n in enumerate(joint_names)}
    offsets = {}
    for name, parent in names_with_parents:
        j = neutral[name_to_idx[name]]
        if parent is None:
            offsets[name] = (0.0, 0.0, 0.0)
        else:
            p = neutral[name_to_idx[parent]]
            d = j - p
            offsets[name] = (float(d[0]), float(d[1]), float(d[2]))

    traversal_order = []
    with open(bvh_path, "w") as f:
        f.write("HIERARCHY\n")
        root_name = joint_names[skel.root_idx]
        write_joint(f, root_name, children, parent_of, offsets, 0, traversal_order)

        f.write("MOTION\n")
        f.write(f"Frames: {n_frames}\n")
        f.write(f"Frame Time: {1.0 / fps:.6f}\n")

        euler_by_joint = {}
        for name in traversal_order:
            idx = name_to_idx[name]
            mats = local_rot_mats[:, idx, :, :]
            eulers = R.from_matrix(mats).as_euler("XYZ", degrees=True)
            euler_by_joint[name] = eulers

        for t in range(n_frames):
            row = []
            for i, name in enumerate(traversal_order):
                if i == 0:
                    px, py, pz = root_positions[t]
                    row.extend([f"{px:.6f}", f"{py:.6f}", f"{pz:.6f}"])
                ex, ey, ez = euler_by_joint[name][t]
                row.extend([f"{ex:.6f}", f"{ey:.6f}", f"{ez:.6f}"])
            f.write(" ".join(row) + "\n")

    print(f"Wrote {bvh_path}: {n_frames} frames, {len(traversal_order)} joints.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python npz_to_bvh.py <input.npz> <output.bvh>")
    main(sys.argv[1], sys.argv[2])
