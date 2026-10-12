# Recovery with partial or missing styles

Manual review of the tested startup draft found the failure overlay inherited the
`.empty` component's margin and alignment. With the primary stylesheet absent,
background opening text and the skip link remained visible around the fixed panel.

The terminal recovery panel must cover the viewport independently of any loaded
stylesheet: remove the generic empty-state class, explicitly reset margin/box
sizing/borders/dimensions/alignment, use readable inline heading and paragraph
styles, and wrap diagnostic paths. Hide and inert the shell, sidebar and skip link
until the required genuine reload. Late assets cannot restore the hidden shell or
ready markers. Keep the existing named asset errors and focused reload action.

Verify normal startup still shows the requested roof, all API snapshot fallbacks,
static/schema/script/style stalls and late arrivals, plus native integrity recovery.
Manually inspect the missing-style and script-failure surfaces at phone widths.
Preserve component camera code/data unchanged and report earlier component proof
against its real head, rather than implying it was rerun on a new revision.
