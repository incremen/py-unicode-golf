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
    selector: 'node.chr-node',
    style: {
      'background-color': '#f5f5f5',
      'border-color': '#aaa',
      'border-width': 1,
      'border-style': 'dashed',
      'color': '#444',
      'font-size': '13px',
      'font-family': 'Courier New',
      'font-weight': 'bold',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'none',
      'shape': 'round-rectangle',
      'width': 'label',
      'height': 36,
      'padding': '8px',
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
      'label': 'data(strategy)',
      'font-family': 'Courier New',
      'font-size': '9px',
      'color': 'data(color)',
      'text-rotation': 'autorotate',
      'text-margin-y': -8,
    }
  }
];
