const CYTOSCAPE_STYLES = [
  {
    selector: 'node',
    style: {
      'background-color': '#d8d8d8',
      'border-color': '#333',
      'border-width': 2,
      'color': '#222',
      'label': 'data(label)',
      'font-family': 'Courier New',
      'font-size': '13px',
      'text-valign': 'center',
      'text-halign': 'center',
      'width': 46,
      'height': 46,
    }
  },
  {
    selector: 'node.expanded',
    style: { 'border-color': '#333', 'border-width': 2, 'background-color': '#c8c8c8' }
  },
  {
    selector: 'node.focused',
    style: { 'background-color': '#d8d8d8', 'border-color': '#306998', 'border-width': 3 }
  },
  {
    selector: 'node#s',
    style: {
      'background-color': '#1a1a2e',
      'border-color': '#306998',
      'border-width': 3,
      'color': '#FFD43B',
      'font-size': '16px',
      'font-weight': 'bold',
      'width': 52,
      'height': 52,
    }
  },
  {
    selector: 'node.chr-node',
    style: {
      'background-color': '#FFD43B',
      'border-color': '#e6b800',
      'border-width': 3,
      'border-style': 'solid',
      'color': '#1a1200',
      'font-size': '22px',
      'font-family': 'Courier New',
      'font-weight': 'bold',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'none',
      'shape': 'round-rectangle',
      'width': 'label',
      'height': 52,
      'padding': '14px',
      'shadow-blur': 18,
      'shadow-color': '#FFD43B',
      'shadow-opacity': 0.7,
      'shadow-offset-x': 0,
      'shadow-offset-y': 0,
    }
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': 'data(color)',
      'target-arrow-color': 'data(color)',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': '',
    }
  },
  {
    selector: 'edge[strategy = "chr"]',
    style: {
      'width': 3,
      'line-style': 'dashed',
      'line-dash-pattern': [8, 4],
      'target-arrow-shape': 'triangle',
      'arrow-scale': 1.6,
    }
  },
  {
    selector: 'edge.hovered',
    style: { 'width': 3 }
  }
];
