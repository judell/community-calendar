#!/usr/bin/env node
/**
 * analyze-xmlui-props.js
 *
 * Analyzes XMLUI component documentation to report which common/universal props
 * are documented for each component.
 *
 * Universal props in XMLUI (available on all visual components):
 * - when: Conditional rendering (documented in Fragment.md)
 * - id: Component identifier
 * - tooltip: Hover text (documented in Tooltip.md)
 * - tooltipMarkdown: Markdown tooltip
 * - tooltipOptions: Tooltip configuration
 *
 * Usage:
 *   node analyze-xmlui-props.js <path-to-xmlui-docs>
 *   node analyze-xmlui-props.js --generate-snippet
 *
 * Examples:
 *   node analyze-xmlui-props.js ~/xmlui-mcp/docs/content/components
 *   node analyze-xmlui-props.js --generate-snippet > universal-props.md
 */

const fs = require('fs');
const path = require('path');

// Universal props that should be available on all visual components
const UNIVERSAL_PROPS = [
  { name: 'when', description: 'Conditional rendering. When the expression evaluates to false, the component is not rendered.', source: 'https://docs.xmlui.org/components/Fragment' },
  { name: 'id', description: 'A unique identifier for referencing the component programmatically via methods or other components.', source: null },
  { name: 'tooltip', description: 'Plain text displayed when hovering over the component.', source: 'https://docs.xmlui.org/components/Tooltip' },
  { name: 'tooltipMarkdown', description: 'Markdown-formatted text displayed when hovering over the component.', source: 'https://docs.xmlui.org/components/Tooltip' },
  { name: 'tooltipOptions', description: 'Configuration options for tooltip appearance and behavior (position, delay, etc.).', source: 'https://docs.xmlui.org/components/Tooltip' }
];

// Common props shared by many (but not all) components
const COMMON_PROPS = [
  'enabled',
  'onClick',
  'onContextMenu',
  'initialValue',
  'value',
  'onDidChange'
];

function parseMarkdownProps(content) {
  const props = new Set();

  // Look for ### `propName` patterns in Properties section
  const propsMatch = content.match(/## Properties[\s\S]*?(?=## Events|## Exposed|## Styling|$)/i);
  if (!propsMatch) return props;

  const propsSection = propsMatch[0];
  const propMatches = propsSection.matchAll(/### `([^`]+)`/g);

  for (const match of propMatches) {
    props.add(match[1]);
  }

  return props;
}

function analyzeComponent(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const name = path.basename(filePath, '.md');

  const documentedProps = parseMarkdownProps(content);

  // Check which universal props are documented
  const universalStatus = {};
  for (const prop of UNIVERSAL_PROPS) {
    universalStatus[prop.name] = documentedProps.has(prop.name);
  }

  // Check which common props are documented
  const commonStatus = {};
  for (const prop of COMMON_PROPS) {
    commonStatus[prop] = documentedProps.has(prop);
  }

  return {
    name,
    documentedProps: Array.from(documentedProps),
    universalStatus,
    commonStatus,
    hasNoProps: content.includes('This component does not have any properties')
  };
}

function findComponentFiles(docsDir) {
  const files = [];

  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.name.endsWith('.md') && !entry.name.startsWith('_')) {
        files.push(fullPath);
      }
    }
  }

  walk(docsDir);
  return files;
}

function generateUniversalPropsSnippet() {
  console.log('## Universal Properties [#universal-properties]\n');
  console.log('The following properties are available on all visual components:\n');

  for (const prop of UNIVERSAL_PROPS) {
    console.log(`### \`${prop.name}\` [#${prop.name}]\n`);
    console.log(`${prop.description}\n`);
    if (prop.source) {
      console.log(`See [${prop.name} documentation](${prop.source}) for details.\n`);
    }
  }

  console.log('---\n');
  console.log('*These properties can be used on any visual component without being explicitly listed in the component\'s Properties section.*\n');
}

function generateReport(components) {
  console.log('# XMLUI Component Props Analysis\n');
  console.log('## Universal Props Coverage\n');
  console.log('These props are available on ALL visual components but may not be documented:\n');
  console.log('| Component | when | id | tooltip | tooltipMarkdown | tooltipOptions |');
  console.log('|-----------|------|-----|---------|-----------------|----------------|');

  for (const comp of components) {
    if (comp.hasNoProps) continue; // Skip components with no props

    const row = [
      comp.name,
      comp.universalStatus.when ? '✓' : '-',
      comp.universalStatus.id ? '✓' : '-',
      comp.universalStatus.tooltip ? '✓' : '-',
      comp.universalStatus.tooltipMarkdown ? '✓' : '-',
      comp.universalStatus.tooltipOptions ? '✓' : '-'
    ];
    console.log(`| ${row.join(' | ')} |`);
  }

  console.log('\n## Summary\n');

  // Count how many components document each universal prop
  const counts = {};
  for (const prop of UNIVERSAL_PROPS) {
    counts[prop.name] = components.filter(c => !c.hasNoProps && c.universalStatus[prop.name]).length;
  }

  const visualComponents = components.filter(c => !c.hasNoProps).length;

  console.log(`Total visual components analyzed: ${visualComponents}\n`);
  console.log('Universal prop documentation coverage:');
  for (const [prop, count] of Object.entries(counts)) {
    const pct = ((count / visualComponents) * 100).toFixed(1);
    console.log(`  - ${prop}: ${count}/${visualComponents} (${pct}%)`);
  }

  console.log('\n## Recommendation\n');
  console.log('Since `when`, `id`, `tooltip`, `tooltipMarkdown`, and `tooltipOptions` are');
  console.log('universal props available on all visual components, they should either:\n');
  console.log('1. **Create a "Universal Properties" reference page** that documents these once');
  console.log('2. **Auto-inject a section** into each component doc linking to the reference');
  console.log('3. **Add a note** to the component overview page listing universal props\n');
  console.log('Run with `--generate-snippet` to get markdown for a Universal Properties section.\n');
  console.log('### Sources:');
  console.log('- `when`: https://docs.xmlui.org/components/Fragment');
  console.log('- `tooltip*`: https://docs.xmlui.org/components/Tooltip');
}

// Main
const args = process.argv.slice(2);

if (args.includes('--generate-snippet')) {
  generateUniversalPropsSnippet();
  process.exit(0);
}

if (args.includes('--help') || args.includes('-h')) {
  console.log('analyze-xmlui-props.js - Analyze XMLUI component documentation\n');
  console.log('Usage:');
  console.log('  node analyze-xmlui-props.js <path-to-docs>   Analyze component docs');
  console.log('  node analyze-xmlui-props.js --generate-snippet   Generate universal props markdown');
  console.log('  node analyze-xmlui-props.js --help   Show this help\n');
  console.log('Universal props (available on all visual components):');
  for (const prop of UNIVERSAL_PROPS) {
    console.log(`  - ${prop.name}: ${prop.description}`);
  }
  process.exit(0);
}

const docsDir = args[0];
if (!docsDir) {
  console.error('Usage: node analyze-xmlui-props.js <path-to-xmlui-docs>');
  console.error('       node analyze-xmlui-props.js --generate-snippet');
  console.error('\nExample: node analyze-xmlui-props.js ~/xmlui-mcp/docs/content/components');
  process.exit(1);
}

if (!fs.existsSync(docsDir)) {
  console.error(`Directory not found: ${docsDir}`);
  process.exit(1);
}

const componentFiles = findComponentFiles(docsDir);
console.error(`Found ${componentFiles.length} component files\n`);

const components = componentFiles.map(f => analyzeComponent(f));
components.sort((a, b) => a.name.localeCompare(b.name));

generateReport(components);
