# Ardy Setup Guide for GenLARP

How to generate character motion with Ardy and get it playing on a character in Unity.

## The pipeline at a glance

1. **Ardy** generates a motion from a text prompt (`.npz` file). *Needs a GPU.*
2. **`npz_to_bvh.py`** converts the `.npz` into a `.bvh` skeleton animation.
3. **Blender + Rokoko** retarget that motion onto a character (X Bot).
4. **Blender** exports the animated character as an `.fbx`.
5. **Unity** imports the `.fbx` and plays the animation.

Only Step 1 needs a GPU. Steps 3 to 5 run on a normal laptop. If you want to skip generation, use the sample files in the shared handoff folder (see "Where things live") and start at Step 3.

**Status:** Steps 1 to 5 are verified in a blank Unity project (`genlarp-ardy-test`). They are **not yet tested inside a WorldGen_Unity scene**. See Step 6.

### Terms used in this guide

- **BVH**: a standard motion-capture file: a skeleton plus its movement over time.
- **Retargeting**: copying a motion from one skeleton onto a different character's skeleton.
- **Humanoid / Avatar (Unity)**: Unity's system for mapping any human-shaped skeleton onto a standard set of bones. The Avatar is the mapping asset Unity generates.
- **Animator Controller (Unity)**: an asset that decides which animation clip plays on a character.

---

## Where things live

| Item | Location |
|---|---|
| Code (fork of NVIDIA's Ardy) | https://github.com/zoeyj1/ardy, branch `ardy-bvh-export` |
| Converter script | `scripts/npz_to_bvh.py` |
| Lightning AI studio | `ardy-test` (L4 GPU), under zoeyj-org / ai-powered-social-game-project. Only needed for Step 1. Andy can skip it by using test1.bvh from the shared folder. |
| Sample files (`test1.npz`, `test1.bvh`, `.blend`, `.fbx`, Unity package) | https://drive.google.com/drive/folders/1WOCgwDtRh6U--dVyJ_KIx6dLdjMls_qB?usp=sharing |

---

## Prerequisites

- **GPU with 17 GB+ VRAM** for Step 1 (an L4 24 GB on Lightning AI works, about $0.79/hr). A Kaggle T4 is not enough.
- **Blender 4.2.23 LTS.** Do not use a newer version: 4.4+ (and 5.2.1, which we tried) breaks the Rokoko add-on. You can install 4.2 LTS alongside a newer Blender.
- **Rokoko add-on v1.4.3 (Studio Live).** https://www.rokoko.com/integrations/blender Install it in Blender via Edit → Preferences → Add-ons → Install from Disk, then enable it.
- **A Mixamo account** (free Adobe account) to download the X Bot character.
- **Unity 6.5 (6000.5.8f1).**

---

## Step 1: Generate motion with Ardy

On the Lightning studio, in a terminal:

```bash
cd ~/ardy
python scripts/generate.py "a person walks forward and waves" --model core --duration 5.0 --output outputs/test1
```

**You should see:** a file `outputs/test1.npz`.

Optional preview: `python scripts/visualize.py outputs/test1.npz`

---

## Step 2: Convert .npz to .bvh

```bash
pip install scipy        # first time only
python scripts/npz_to_bvh.py outputs/test1.npz outputs/test1.bvh
```

**You should see:** `Wrote outputs/test1.bvh: N frames, 27 joints.`

Download `test1.bvh` to your computer (right-click it in the Lightning file explorer).

*Note: the script needs the `ardy` package installed and must be run from the repo root. Joint names are Mixamo-style (`mixamorig:` prefix), which is why Step 3 maps automatically.*

---

## Step 3: Retarget in Blender

### Set up the scene

1. Open Blender 4.2.23. Choose File → New → General, then delete the default cube.
2. File → Import → Motion Capture (.bvh), and pick `test1.bvh`. In the Transform options use Mode = XYZ Euler and Scale = 1.000 on all axes.
3. Get the X Bot: on mixamo.com, sign in, open the Characters tab, search "X Bot", and download as **FBX Binary (.fbx)** with **T-pose**. In Blender, File → Import → FBX and pick that file.

**You should see:** a bare skeleton (`test1`) and the X Bot character (`Armature`).

### Retarget

1. In the 3D viewport, press **N** and open the **Rokoko** tab. Expand **Retargeting**.
2. Set **Source** = `test1` and **Target** = `Armature`.
3. Click **Rebuild Bone List**. It fills in automatically. Only `Spine1` and the two `*HandEnd` bones stay blank, and that is expected (see Appendix A).
4. Set **Use Pose** = Rest, leave **Auto Scale** off, and click **Retarget Animation**.

**You should see:** the X Bot walking and waving when you scrub the timeline.

### Check the timeline length

The scene's **End** frame must cover the whole animation (ours is 130). If the clip looks cut off in Unity, raise End and export again.

### Clean up before export

1. In the Outliner, change the display mode to **Blender File** and expand **Actions**.
2. Delete every action except the retargeted one (it is named something like `test1 Retarget`). This removes the Mixamo animation (`mixamo.com|Layer0`) that came with the X Bot.
3. Switch the Outliner back to **View Layer**. Check that `Armature` → Animation still shows the action. If it is empty, assign it in a Dope Sheet → Action Editor.
4. Delete the `test1` skeleton (select it, press **X**).
5. Save the `.blend`. genlarp_retarget_v3.blend in Ardy Handoff Google Drive

---

## Step 4: Export FBX from Blender

1. In Object Mode, select only `Armature`, `Beta_Surface` and `Beta_Joints`.
2. File → Export → FBX (.fbx) and use these settings (taken from our working export):

| Section | Setting |
|---|---|
| Include | Limit to **Selected Objects** on. Object Types: **Armature** and **Mesh** |
| Transform | Scale 1.00, Apply Scalings = **FBX All**, Forward = **-Z Forward**, Up = **Y Up**, Apply Unit on, Use Space Transform on, Apply Transform off |
| Armature | Primary Bone Axis = Y, Secondary = X, Armature FBX Node Type = Null, Only Deform Bones off, **Add Leaf Bones off** |
| Animation | Animation on, **Key All Bones** on, **NLA Strips** off, **All Actions** off, **Force Start/End Keying** on, Sampling Rate 1.00, Simplify 1.00 |

**You should see:** an `.fbx` file saved where you chose.

---

## Step 5: Import into Unity

1. Drag the `.fbx` into `Assets/Characters`.
2. Select it, open the **Rig** tab, set **Animation Type = Humanoid**, and click **Apply**. Click **Configure** to check that no bones are red.
3. Open the **Animation** tab. There should be **one clip**. In our export it is called **`Scene`** (about 4.3 s, 30 FPS, frames 1 to 130). Tick **Loop Time**, then click **Apply**.
   - To rename the clip, click it in the Clips list and edit the name field below. This is optional.
4. Create an Animator Controller (right-click in Project → Create → Animator Controller). Open it, then drag the clip from inside the FBX (expand the FBX with its arrow) onto the graph. It becomes the orange default state.
   - Drag the **clip** (triangle icon). Not the FBX, and not the Avatar.
5. Drag the FBX into the scene Hierarchy. On the root object's **Animator** component, set **Controller** to your controller and **Avatar** to the one generated from the FBX.
6. Press **Play**.

**You should see:** the character walking and waving in a loop.

---

## Step 6: Next, integration into WorldGen_Unity (for Andy)

Not done yet. Suggested approach:

1. Import the FBX, its Avatar and the controller into the WorldGen_Unity project.
2. Check **Apply Root Motion** on the Animator and the clip's root transform settings, so the character doesn't drift or float.
3. Check that the character stands on the generated terrain.

### Open questions for Andy

- Bone mapping is per-character. Should we **pre-retarget one fixed character**, or **retarget at runtime** for whatever character WorldGen_Unity produces?
- Which character will WorldGen_Unity spawn? That decides how much mapping work is needed.

### Suggested next experiments

- A second prompt (for example "a person sits down and stretches").
- A different target character, to see how reusable the pipeline is.

---

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| Rokoko errors with `'Action' object has no attribute 'fcurves'` | You are on Blender 4.4 or newer. Use 4.2 LTS. |
| Character stays in a T-pose in Play Mode | Wrong clip in the controller state, no controller on the Animator, or no Avatar. Check all three. |
| Wrong or extra animation plays | The Mixamo action was exported too. Delete extra actions in Blender and export again with All Actions off. |
| Animation cut short | Blender's End frame is too low. Raise it and re-export. |
| Red SerializedObject error in Unity's status bar | Usually a harmless editor glitch. Check whether it returns after you assign the clip. |
| Lost `.blend` file | Rebuild it from the `.bvh`, and keep a backup in the shared drive. |

---

## Appendix A: Bone mapping (target → source)

Captured from the Rokoko "Rebuild Bone List" panel. The list matched automatically, with no manual edits.

| Target bone | Source bone | Notes |
|---|---|---|
| Hips | mixamorig:Hips | auto |
| Spine | mixamorig:Spine | auto |
| Spine1 | (none) | Target has 4 spine bones, the source has 3. Safe to leave blank for a walk or wave. |
| Spine2 | mixamorig:Spine1 | auto (shifted) |
| Spine3 | mixamorig:Spine2 | auto (shifted) |
| Neck, Head | mixamorig:Neck, mixamorig:Head | auto |
| Right and Left Shoulder / Arm / ForeArm / Hand | matching mixamorig bones | auto |
| Right and Left HandThumb1 | matching mixamorig bones | auto |
| RightHandEnd, LeftHandEnd | (none) | Expected: tip bones need no rotation data. |
| Right and Left UpLeg / Leg / Foot / ToeBase | matching mixamorig bones | auto |

Mapping works automatically here because the source bones use the same `mixamorig:` names as the X Bot. A different target character will need the bone list reviewed and fixed by hand.

---

*Verified end to end on: 10/11/26 by Zoey Ji*