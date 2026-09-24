#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

export const CANVAS = Object.freeze({ x: 0, y: 0, w: 1920, h: 1080 });
export const SAFE_AREA = Object.freeze({ x: 148, y: 112, w: 1624, h: 856 });

export const STRUCTURE_LAYOUTS = Object.freeze({
  "BrandFocus.Cover.WithLogo": Object.freeze({
    fixedObjects: Object.freeze(["logo.top.standard"]),
    contentArea: Object.freeze({ x: 148, y: 240, w: 1624, h: 728 }),
  }),
  "BrandFocus.End.NoLogo": Object.freeze({
    fixedObjects: Object.freeze([]),
    contentArea: SAFE_AREA,
  }),
  "BrandFocus.End.WithLogo": Object.freeze({
    fixedObjects: Object.freeze(["logo.top.standard"]),
    contentArea: Object.freeze({ x: 148, y: 240, w: 1624, h: 728 }),
  }),
  "BrandFocus.LogoOnly": Object.freeze({
    fixedObjects: Object.freeze(["logo.center.focus"]),
    contentArea: null,
    allowNoMainGroup: true,
  }),
  "Section.NoLogo": Object.freeze({
    fixedObjects: Object.freeze([]),
    contentArea: SAFE_AREA,
  }),
  "Content.WithTitle": Object.freeze({
    fixedObjects: Object.freeze(["logo.top-right", "title.top"]),
    contentArea: Object.freeze({ x: 148, y: 240, w: 1624, h: 728 }),
  }),
  "Content.NoTitle.TenColumns": Object.freeze({
    fixedObjects: Object.freeze(["logo.top-right"]),
    contentArea: Object.freeze({ x: 148, y: 112, w: 1352, h: 856 }),
  }),
  "Content.NoTitle.FullWidth": Object.freeze({
    fixedObjects: Object.freeze(["logo.top-right"]),
    contentArea: Object.freeze({ x: 148, y: 240, w: 1624, h: 728 }),
  }),
});

const COLOR_IN_LAYOUT_ID =
  /(?:^|[._-])(blue|navy|cloud|white|black|dark|light|1677ff|082c5e|e0e5ec)(?:$|[._-])/i;

function cloneBox(box) {
  return box ? { x: box.x, y: box.y, w: box.w, h: box.h } : null;
}

function assertInteger(value, label) {
  if (!Number.isInteger(value)) {
    throw new Error(`${label} must be an integer LU; received ${value}`);
  }
}

function assertBox(box, label) {
  if (!box || typeof box !== "object") {
    throw new Error(`${label} must be an object`);
  }
  for (const key of ["x", "y", "w", "h"]) {
    assertInteger(box[key], `${label}.${key}`);
  }
  if (box.w <= 0 || box.h <= 0) {
    throw new Error(`${label} must have positive width and height`);
  }
}

function boxRight(box) {
  return box.x + box.w;
}

function boxBottom(box) {
  return box.y + box.h;
}

function sameBox(a, b) {
  return ["x", "y", "w", "h"].every((key) => a?.[key] === b?.[key]);
}

function within(inner, outer, tolerance = 0) {
  return (
    inner.x >= outer.x - tolerance &&
    inner.y >= outer.y - tolerance &&
    boxRight(inner) <= boxRight(outer) + tolerance &&
    boxBottom(inner) <= boxBottom(outer) + tolerance
  );
}

export function snapToGrid(value, grid = 8) {
  assertInteger(grid, "grid");
  if (grid <= 0) {
    throw new Error("grid must be positive");
  }
  return Math.round(value / grid) * grid;
}

export function getStructureLayout(layoutId) {
  if (typeof layoutId !== "string" || !layoutId) {
    throw new Error("structureLayout must be a non-empty string");
  }
  if (COLOR_IN_LAYOUT_ID.test(layoutId)) {
    throw new Error(
      `structureLayout "${layoutId}" contains a background/color term; keep backgroundStyle separate`,
    );
  }
  const layout = STRUCTURE_LAYOUTS[layoutId];
  if (!layout) {
    throw new Error(
      `Unknown structureLayout "${layoutId}". Use a registered layout or declare a reviewed custom layout.`,
    );
  }
  return {
    id: layoutId,
    fixedObjects: [...layout.fixedObjects],
    contentArea: cloneBox(layout.contentArea),
    allowNoMainGroup: Boolean(layout.allowNoMainGroup),
  };
}

export function unionBounds(elements) {
  if (!Array.isArray(elements) || elements.length === 0) {
    throw new Error("elements must contain at least one content element");
  }
  const boxes = elements.map((element, index) => {
    const box = element?.bounds ?? element;
    assertBox(box, `elements[${index}].bounds`);
    return box;
  });
  const x = Math.min(...boxes.map((box) => box.x));
  const y = Math.min(...boxes.map((box) => box.y));
  const right = Math.max(...boxes.map(boxRight));
  const bottom = Math.max(...boxes.map(boxBottom));
  return { x, y, w: right - x, h: bottom - y };
}

export function translateBounds(bounds, dx, dy) {
  assertBox(bounds, "bounds");
  assertInteger(dx, "dx");
  assertInteger(dy, "dy");
  return { x: bounds.x + dx, y: bounds.y + dy, w: bounds.w, h: bounds.h };
}

export function placeContentGroup({
  structureLayout,
  measuredBounds,
  alignment = "center",
  grid = 8,
  opticalShift = 0,
}) {
  const layout = getStructureLayout(structureLayout);
  if (!layout.contentArea) {
    throw new Error(`${structureLayout} does not provide a content area`);
  }
  assertBox(measuredBounds, "measuredBounds");
  assertInteger(opticalShift, "opticalShift");
  if (Math.abs(opticalShift) > 8 || opticalShift % grid !== 0) {
    throw new Error("opticalShift must be 0 or one grid step (±8 LU)");
  }

  const area = layout.contentArea;
  let rawY;
  if (alignment === "center") {
    rawY = area.y + (area.h - measuredBounds.h) / 2;
  } else if (alignment === "top") {
    rawY = area.y;
  } else if (alignment === "bottom") {
    rawY = boxBottom(area) - measuredBounds.h;
  } else {
    throw new Error(`Unsupported automatic alignment "${alignment}"`);
  }

  const y = snapToGrid(rawY, grid) + opticalShift;
  const offsetY = y - measuredBounds.y;
  const bounds = translateBounds(measuredBounds, 0, offsetY);
  return {
    bounds,
    offsetY,
    alignment,
    opticalShift,
    contentArea: cloneBox(area),
    centerDelta:
      bounds.y + bounds.h / 2 - (area.y + area.h / 2),
  };
}

export function createSlideAudit({
  slide,
  structureLayout,
  backgroundStyle,
  groups = [],
}) {
  assertInteger(slide, "slide");
  if (slide <= 0) {
    throw new Error("slide must be a positive integer");
  }
  if (typeof backgroundStyle !== "string" || !backgroundStyle.trim()) {
    throw new Error("backgroundStyle must be declared separately from structureLayout");
  }
  const layout = getStructureLayout(structureLayout);
  return {
    slide,
    structureLayout,
    backgroundStyle,
    fixedObjects: layout.fixedObjects,
    contentArea: layout.contentArea,
    groups,
  };
}

export function validateLayoutAudit(audit, { tolerance = 8 } = {}) {
  const errors = [];
  const results = [];

  if (!audit || typeof audit !== "object") {
    return { ok: false, errors: ["Audit root must be an object"], results };
  }
  if (audit.version !== 1) {
    errors.push(`version must be 1; received ${audit.version}`);
  }
  if (!Number.isInteger(audit.slideCount) || audit.slideCount <= 0) {
    errors.push("slideCount must be a positive integer");
  }
  if (!Array.isArray(audit.slides)) {
    errors.push("slides must be an array");
    return { ok: false, errors, results };
  }
  if (Number.isInteger(audit.slideCount) && audit.slides.length !== audit.slideCount) {
    errors.push(
      `slides length ${audit.slides.length} does not match slideCount ${audit.slideCount}`,
    );
  }

  const seenSlides = new Set();
  for (const [index, slide] of audit.slides.entries()) {
    const prefix = `slides[${index}]`;
    try {
      assertInteger(slide.slide, `${prefix}.slide`);
      if (seenSlides.has(slide.slide)) {
        errors.push(`${prefix}: duplicate slide number ${slide.slide}`);
      }
      seenSlides.add(slide.slide);

      const layout = getStructureLayout(slide.structureLayout);
      if (typeof slide.backgroundStyle !== "string" || !slide.backgroundStyle.trim()) {
        errors.push(`${prefix}: backgroundStyle is required`);
      }
      if (!sameBox(slide.contentArea, layout.contentArea)) {
        errors.push(
          `${prefix}: contentArea does not match structureLayout ${slide.structureLayout}`,
        );
      }
      if (
        JSON.stringify(slide.fixedObjects ?? []) !==
        JSON.stringify(layout.fixedObjects)
      ) {
        errors.push(
          `${prefix}: fixedObjects do not match structureLayout ${slide.structureLayout}`,
        );
      }

      const groups = slide.groups;
      if (!Array.isArray(groups)) {
        errors.push(`${prefix}: groups must be an array`);
        continue;
      }
      if (!layout.allowNoMainGroup && groups.length === 0) {
        errors.push(`${prefix}: at least one main content group is required`);
        continue;
      }
      if (layout.allowNoMainGroup && groups.length > 0) {
        errors.push(`${prefix}: ${slide.structureLayout} must not contain a main group`);
      }

      for (const [groupIndex, group] of groups.entries()) {
        const groupPrefix = `${prefix}.groups[${groupIndex}]`;
        if (typeof group.id !== "string" || !group.id.trim()) {
          errors.push(`${groupPrefix}: id is required`);
        }
        if (!["center", "top", "bottom", "custom"].includes(group.alignment)) {
          errors.push(`${groupPrefix}: unsupported alignment "${group.alignment}"`);
          continue;
        }
        if (group.alignment === "custom" && !group.reason?.trim()) {
          errors.push(`${groupPrefix}: custom alignment requires a functional reason`);
        }
        if (group.opticalShift) {
          if (
            !Number.isInteger(group.opticalShift) ||
            Math.abs(group.opticalShift) > tolerance
          ) {
            errors.push(
              `${groupPrefix}: opticalShift must be within ±${tolerance} LU`,
            );
          }
          if (!group.reason?.trim()) {
            errors.push(`${groupPrefix}: opticalShift requires a recorded reason`);
          }
        }

        let bounds;
        try {
          bounds = unionBounds(group.elements);
        } catch (error) {
          errors.push(`${groupPrefix}: ${error.message}`);
          continue;
        }
        if (!layout.contentArea) {
          errors.push(`${groupPrefix}: structure layout has no content area`);
          continue;
        }
        if (!within(bounds, layout.contentArea, tolerance)) {
          errors.push(`${groupPrefix}: content group exceeds the declared content area`);
        }

        const areaCenter = layout.contentArea.y + layout.contentArea.h / 2;
        const groupCenter = bounds.y + bounds.h / 2;
        const centerDelta = groupCenter - areaCenter;
        let alignmentDelta = 0;
        if (group.alignment === "center") {
          alignmentDelta = centerDelta;
        } else if (group.alignment === "top") {
          alignmentDelta = bounds.y - layout.contentArea.y;
        } else if (group.alignment === "bottom") {
          alignmentDelta = boxBottom(bounds) - boxBottom(layout.contentArea);
        }
        if (
          group.alignment !== "custom" &&
          Math.abs(alignmentDelta) > tolerance
        ) {
          errors.push(
            `${groupPrefix}: ${group.alignment} alignment delta ${alignmentDelta} LU exceeds ±${tolerance} LU`,
          );
        }
        results.push({
          slide: slide.slide,
          group: group.id,
          structureLayout: slide.structureLayout,
          backgroundStyle: slide.backgroundStyle,
          contentArea: cloneBox(layout.contentArea),
          usedBounds: bounds,
          alignment: group.alignment,
          centerDelta,
          alignmentDelta,
        });
      }
    } catch (error) {
      errors.push(`${prefix}: ${error.message}`);
    }
  }

  if (Number.isInteger(audit.slideCount)) {
    for (let slide = 1; slide <= audit.slideCount; slide += 1) {
      if (!seenSlides.has(slide)) {
        errors.push(`missing audit data for slide ${slide}`);
      }
    }
  }

  return { ok: errors.length === 0, errors, results };
}

export async function writeLayoutAudit(filePath, audit) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, `${JSON.stringify(audit, null, 2)}\n`);
}

async function main() {
  const args = process.argv.slice(2);
  const filePath = args[0] === "validate" ? args[1] : args[0];
  if (!filePath) {
    console.error("Usage: node scripts/ppt/layout_qa.mjs validate <layout-audit.json>");
    process.exitCode = 2;
    return;
  }
  const audit = JSON.parse(await fs.readFile(filePath, "utf8"));
  const result = validateLayoutAudit(audit);
  for (const item of result.results) {
    console.log(
      `[${Math.abs(item.alignmentDelta) <= 8 ? "PASS" : "FAIL"}] slide ${item.slide} ${item.group}: ` +
        `${item.alignment} delta=${item.alignmentDelta} LU, centerDelta=${item.centerDelta} LU`,
    );
  }
  if (!result.ok) {
    for (const error of result.errors) {
      console.error(`[ERROR] ${error}`);
    }
    process.exitCode = 1;
    return;
  }
  console.log(`Layout QA passed for ${audit.slideCount} slides.`);
}

const invokedPath = process.argv[1] ? pathToFileURL(path.resolve(process.argv[1])).href : "";
if (import.meta.url === invokedPath) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
