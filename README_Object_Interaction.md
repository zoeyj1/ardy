# Object Interaction Prototype (GenLARP)

A small Unity prototype that makes a character stand at an object and put both hands on it.
It's a test for the "character interacts with objects" part of GenLARP. Ardy generates the
body motion and doesn't know the object exists, so this adds the missing placement and
hand contact.

Tested in Unity 6.5 (6000.5.8f1) with the Animation Rigging package, using the Ardy
"walk_stop_turn" character (Mixamo-style X Bot rig) and a plain cube as the table.
Also tested by importing the package into a fresh Universal 3D project.
Not yet tested inside WorldGen_Unity.

## What it does
1. `MoveToStandPoint` moves the character to a marker in front of the object and faces it.
2. `InteractionBlend` fades two Two Bone IK constraints on and off, so the hands
   follow the animation normally and snap to the object only while interacting.

## What an object needs
Three empty child objects:
- `StandPoint`: where the character stands. Its forward (blue) arrow should point at the object.
- `HandAnchor_L` / `HandAnchor_R`: where each hand goes, on the object's surface.

Anchor rotation sets the hand direction. For this rig, flat palms facing down needed
R = (90, 90, 0) and L = (90, 0, -90). A different rig will need re-tuning.

## What a character needs
- Humanoid avatar and an Animator with a controller.
- Rig Builder with one Rig containing two Two Bone IK Constraints
  (Root = upper arm, Mid = forearm, Tip = hand, Target = the matching anchor).
- Scripts `MoveToStandPoint` (set Stand Point) and `InteractionBlend` (set Rig).

## Setup
1. Install the **Animation Rigging** package first (Window > Package Management > Package Manager > Unity Registry).
2. Import `GenLARP_ObjectInteraction.unitypackage` (Assets > Import Package > Custom Package).
3. Drag the Table prefab and the character prefab from `Assets/Prefabs` into a scene.
4. Prefabs can't remember scene objects, so assign these once per scene:
   - `MoveToStandPoint` > **Stand Point**: the `StandPoint` under the Table.
   - `Rig 1 > IK_RightHand` > Two Bone IK Constraint **Target**: `HandAnchor_R`.
   - `Rig 1 > IK_LeftHand` > Two Bone IK Constraint **Target**: `HandAnchor_L`.
5. Press Play and tick **Interacting** on `InteractionBlend` to test.

## Using it from code
Call `StartInteraction()` when the character reaches the object, and `StopInteraction()` to release.
Fade time is a field on `InteractionBlend` (default 0.6 s).

## Known limits
- Character is placed at the stand point instantly (no walking).
- Hand rotation values are specific to this rig.
- Body pose comes from the underlying clip (tested with an idle clip, not a dedicated
  "kneads dough" clip).
- No pick-up or carry, no character-to-character avoidance.
- Scene references (stand point, hand targets) must be reassigned after each import.

## Ideas for next steps
- Look up the stand point and hand anchors from the object at runtime, e.g. `Interact(table)`,
  so nothing needs hand-assigning.
- Auto-wire the rig for any humanoid.
- Pick up and carry (attach the object to the hand).
- Generate contact-specific Ardy prompts and test the full motion.
