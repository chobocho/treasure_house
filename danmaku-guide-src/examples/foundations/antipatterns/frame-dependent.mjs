// #region frame-dependent
export function move(renderFrames) {
  let x = 0;
  for (let frame = 0; frame < renderFrames; frame++) x += 4;
  return x;
}
// #endregion
