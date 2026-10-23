"use strict";
/* Public-domain Natural Earth relief, projected through the map's actual camera.
 * Tint and limb lighting are cartographic styling; facility lights are separate data. */
const AtlasTerrain = (() => {
  const source = JSON.parse(
    document.getElementById("terrain-data")?.textContent || "{}",
  );
  const image = new Image();
  let pixels = null,
    width = 0,
    height = 0;
  image.onload = () => {
    const canvas = document.createElement("canvas");
    width = canvas.width = image.naturalWidth;
    height = canvas.height = image.naturalHeight;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    context.drawImage(image, 0, 0);
    pixels = context.getImageData(0, 0, width, height).data;
    // Tint once per source image, not once per pixel on every camera frame.
    for (let j = 0; j < pixels.length; j += 4) {
      const r = pixels[j],
        g = pixels[j + 1],
        b = pixels[j + 2];
      const ocean = b > r * 1.12 && b > g * 1.02,
        relief = (r * 0.27 + g * 0.58 + b * 0.15) / 255;
      if (ocean) {
        pixels[j] = 5;
        pixels[j + 1] = 13 + relief * 4;
        pixels[j + 2] = 23 + relief * 6;
      } else {
        const v = Math.pow(relief, 2.1);
        pixels[j] = 5 + v * 12;
        pixels[j + 1] = 16 + v * 23;
        pixels[j + 2] = 26 + v * 28;
      }
    }

    if (globe?.ua) globe.dirty = true;
  };
  image.onerror = () => {
    if (globe?.ua) globe.canvas.dataset.terrain = "unavailable";
  };
  function load() {
    if (!image.src)
      image.src =
        document.getElementById("atlas-terrain-image")?.src ||
        (source.path || "data/maps/terrain.webp") +
          "?v=" +
          (source.sha256 || "").slice(0, 12);
  }
  function paint(map) {
    load();
    if (!pixels) return false;
    const quality = map.drag ? 0.55 : 0.9;
    const w = Math.max(1, Math.round(map.w * quality)),
      h = Math.max(1, Math.round(map.h * quality));
    const key = JSON.stringify([
      w,
      h,
      map.flat,
      map.lat,
      map.lon,
      map.zoom,
      map.bounds,
    ]);
    if (map.terrainKey !== key) {
      const buffer = (map.terrainCanvas ||= document.createElement("canvas"));
      buffer.width = w;
      buffer.height = h;
      const context = buffer.getContext("2d"),
        output = context.createImageData(w, h),
        out = output.data;
      const rad = Math.PI / 180,
        sl = map.sl0,
        cl = map.cl0;
      if (map.flat) {
        // Mercator latitude is constant across a scanline. Reuse both axes.
        const columns = new Uint32Array(w),
          source32 = new Uint32Array(pixels.buffer),
          output32 = new Uint32Array(out.buffer);
        for (let x = 0; x < w; x++) {
          const lon =
            (map.mx + ((x + 0.5) / quality - map.cx) / map.scale) / rad;
          columns[x] = Math.min(
            width - 1,
            Math.floor((((((lon + 180) % 360) + 360) % 360) / 360) * width),
          );
        }
        for (let y = 0; y < h; y++) {
          const lat =
            (2 *
              Math.atan(
                Math.exp(map.my - ((y + 0.5) / quality - map.cy) / map.scale),
              ) -
              Math.PI / 2) /
            rad;
          const row =
            Math.max(
              0,
              Math.min(height - 1, Math.floor(((90 - lat) / 180) * height)),
            ) * width;
          for (let x = 0; x < w; x++)
            output32[y * w + x] = source32[row + columns[x]];
        }
      } else
        for (let y = 0; y < h; y++)
          for (let x = 0; x < w; x++) {
            const px = (x + 0.5) / quality,
              py = (y + 0.5) / quality,
              i = (y * w + x) * 4;
            const nx = (px - map.cx) / map.radius,
              ny = (map.cy - py) / map.radius,
              radiusSquared = nx * nx + ny * ny;
            if (radiusSquared >= 1) continue;
            const z = Math.sqrt(1 - radiusSquared),
              lat = Math.asin(ny * cl + z * sl) / rad,
              lon = map.lon + Math.atan2(nx, z * cl - ny * sl) / rad,
              light =
                0.42 +
                0.58 *
                  Math.pow(Math.max(0, z * 0.94 + ny * 0.19 - nx * 0.16), 0.6);
            const tx = Math.min(
              width - 1,
              Math.floor((((((lon + 180) % 360) + 360) % 360) / 360) * width),
            );
            const ty = Math.max(
              0,
              Math.min(height - 1, Math.floor(((90 - lat) / 180) * height)),
            );
            const j = (ty * width + tx) * 4,
              r = pixels[j],
              g = pixels[j + 1],
              b = pixels[j + 2];
            out[i] = r * light;
            out[i + 1] = g * light;
            out[i + 2] = b * light;
            out[i + 3] = 255;
          }
      context.putImageData(output, 0, 0);
      map.terrainKey = key;
    }
    map.ctx.drawImage(map.terrainCanvas, 0, 0, map.w, map.h);
    map.canvas.dataset.terrain = "natural-earth";
    return true;
  }
  return { paint, load, source };
})();
