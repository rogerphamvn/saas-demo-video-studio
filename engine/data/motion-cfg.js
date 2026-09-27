/* Project-specific motion layer (read by lib/motion-kit.js). Clip ids are keys of window.CUTS (data/cuts.json).
   With the sample data there is no footage, so transitions/pushes stay empty; drops still fire on GRID.drops. */
window.MOTION_CFG = {
  tilt: true,
  transitions: [],                           // e.g. [["e02", "flip"], ["e03", "push"]]  (flip | push | zoom | slab | drop)
  pushes: [],                                // e.g. [["e01", 1317, 409, 1.5, "e02", 1.28]]  (slot, x, y capture px, at bar, until clip, scale)
  drops: [[400, 560, "#6952E0"]],            // one [x, y, colour] per GRID.drops entry
};
