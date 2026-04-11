# Polaris TKAnimation Format Import/Export for Blender
This add-on allows you to import and export Tekken 8 custom animation binaries to Blender.
It's still very experimental and has many issues to fix.

## Goals
Enable the import and export of TEKKEN 8 animation binaries.
First, Tekken 8 consists of five categories of animations as follows:
- Fullbody
- Hand
- Facial
- Swing
- Camera
- Extra

Each category has a different target to animate.

The animation encoding formats are categorized as follows:
 - FBF (Frame By Frame)
 - KEF (Keyframed)
 - MIXED (mixed - KEF/FBF)

## Issues to Resolve
TK6/7/TTT2 share almost the same animation format.
However, TK8 has a different structure.

We need to complete a conversion tool between the legacy formats and the TK8 format.