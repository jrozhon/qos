import { defineMermaidSetup } from '@slidev/types'

/**
 * Mermaid diagrams are slide chrome, not syntax highlighting, so they follow
 * the palette (VSB-STYLE.md R3).
 *
 * Nodes carry a light tint of the university green rather than sitting bare on
 * white. Manual 1.5 sanctions flat tints of the brand colour as background
 * fields, so this is in-style — what it forbids is tinting the *logo* (R4).
 * #EBF8F7 is an 8 % tint of #00A499 over white.
 *
 * Edges are straight rather than curved: this is infrastructure, and the
 * orthogonal read is both more technical and easier to follow at the back of
 * a lecture hall.
 */
export default defineMermaidSetup(() => ({
  theme: 'base',

  themeVariables: {
    fontFamily: "'Drive', 'Carlito', 'Calibri', system-ui, sans-serif",
    fontSize: '16px',

    // nodes — 8 % green tint with a full-strength keyline
    primaryColor: '#EBF8F7',
    primaryBorderColor: '#00A499',
    primaryTextColor: '#0F2E2B',
    secondaryColor: '#E9F9FC',
    secondaryBorderColor: '#05C3DE',   // FEI, keyline only (R5)
    secondaryTextColor: '#0F2E2B',
    tertiaryColor: '#FFFFFF',
    tertiaryBorderColor: '#00736B',
    tertiaryTextColor: '#0F2E2B',
    mainBkg: '#EBF8F7',
    nodeBorder: '#00A499',
    nodeTextColor: '#0F2E2B',

    // subgraph clusters — a quieter ground so grouping reads before content
    clusterBkg: '#F6FAFA',
    clusterBorder: '#05C3DE',
    titleColor: '#00736B',

    // edges
    lineColor: '#00A499',
    textColor: '#0F2E2B',
    edgeLabelBackground: '#FFFFFF',

    // sequence diagrams
    actorBkg: '#EBF8F7',
    actorBorder: '#00A499',
    actorTextColor: '#0F2E2B',
    actorLineColor: '#9FD9D4',
    signalColor: '#00736B',
    signalTextColor: '#0F2E2B',
    labelBoxBkgColor: '#EBF8F7',
    labelBoxBorderColor: '#00A499',
    labelTextColor: '#0F2E2B',
    loopTextColor: '#0F2E2B',
    noteBkgColor: '#E9F9FC',
    noteBorderColor: '#05C3DE',
    noteTextColor: '#0F2E2B',
    activationBkgColor: '#00A499',
    activationBorderColor: '#00736B',
  },

  /**
   * Slidev renders mermaid inside a ShadowRoot (`<ShadowRoot class="mermaid">`
   * in @slidev/client), so stylesheet rules in style.css never reach the
   * diagram. Anything beyond themeVariables has to travel through themeCSS,
   * which mermaid injects into the SVG's own <style> inside that shadow tree.
   */
  themeCSS: `
    /* R24 - hard edges everywhere, including sequence actors and notes */
    rect, .label-container, .cluster rect, .actor, .note {
      rx: 0 !important;
      ry: 0 !important;
    }

    /* Enough weight to read from the back of a lecture hall */
    .flowchart-link, .messageLine0, .messageLine1 { stroke-width: 1.8px; }
    .node rect, .node circle, .node polygon, .node path { stroke-width: 1.6px; }
    .cluster rect { stroke-width: 1.2px; }
    .actor { stroke-width: 1.6px; }

    /* Lifelines stay quiet so the messages carry the diagram */
    .actor-line { stroke-dasharray: 3 4; stroke-width: 1px; }

    /* Edge labels sit on a white chip so they never collide with a line */
    .edgeLabel { font-size: 13px; line-height: 1.3; }
    .edgeLabel foreignObject > div, .edgeLabel span.edgeLabel { padding: 1px 5px; }

    /* Cluster titles read as labels, not headings */
    .cluster-label { font-size: 13px; letter-spacing: 0.06em; font-weight: 700; }

    /* Message text sits clear of its arrow */
    .messageText { font-size: 13px; dominant-baseline: auto; }
  `,

  flowchart: {
    curve: 'linear',
    nodeSpacing: 42,
    rankSpacing: 56,
    padding: 14,
    useMaxWidth: true,
    htmlLabels: true,
  },

  sequence: {
    actorMargin: 64,
    boxMargin: 12,
    noteMargin: 12,
    messageMargin: 40,
    mirrorActors: false,
    useMaxWidth: true,
  },
}))
