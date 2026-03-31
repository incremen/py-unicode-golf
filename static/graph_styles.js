const CYTOSCAPE_STYLES = [
  {
    selector: 'node',
    style: {
      'background-color': '#2c3e50',
      'border-color': '#4a5568',
      'border-width': 2,
      'color': 'white',
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
    style: { 'border-color': '#2ecc71', 'border-width': 3 }
  },
  {
    selector: 'node.focused',
    style: { 'background-color': '#1a3a5c', 'border-color': '#5dade2', 'border-width': 3 }
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
      'text-background-color': '#12151e',
      'text-background-opacity': 0.85,
      'text-background-padding': '2px',
    }
  }
];
