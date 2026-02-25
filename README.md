# PEP Map

## What is this?
**🐍PEP Map**: https://pep-map.onrender.com/


[PEP Map](https://pep-map.onrender.com/) is a web application that **visualizes citation relationships between PEPs** (Python Enhancement Proposals).

- **Timeline tab:**
    - Explore citation relationships between PEPs **on a chronological timeline**.
    - It helps you trace the history of PEPs related to the selected PEP.
- **Network tab:**
    - Explore citation relationships between PEPs **as a network graph**.
    - It helps you understand the relationships between PEPs and identify influential ones.

![](images/pepmap_overview.png)

**Note:**
This project is a redesigned and reimplemented version of [pep_map_site](https://github.com/komo-fr/pep_map_site), originally built with Bokeh and PyScript.
It is now built using Dash.

## Timeline tab
### Viewing Citation History
Enter a PEP number in the left text box (e.g., 8).   
The following information is displayed in creation date order:

- PEPs that cite the selected PEP
- PEPs cited by the selected PEP

![](images/timeline/timeline.png)

Enable the checkbox to show vertical lines for Python release dates.

![](images/timeline/checkbox.png)

### Interaction
Hover over a PEP data point on the timeline to see information about that PEP.   
Click the data point to open the official PEP document.

![](images/timeline/hover.png)

Select a range on the timeline to zoom in on that range.   
Click the home button (🏠) in the top-right corner of the timeline to reset the view.

![](images/timeline/zoom.gif)

## Network tab
### Viewing Citation Structure
The network graph reveals structural patterns in PEP citation relationships.
- Nodes represent PEPs.
- Edges represent citation relationships.
- Larger nodes indicate higher connectivity based on the selected metric.

You may notice that PEPs naturally form clusters around specific themes, such as governance, documentation, type hints, or packaging.
These clusters represent groups of closely related PEPs.
Highly connected nodes tend to appear near the center of the graph, indicating influential or widely referenced PEPs.

![](images/network/network_introduction.png)

Enter a PEP number in the text box on the left (e.g., 8), or click a node in the network graph.
The selected PEP and its citation connections will be highlighted in the network graph.

- **Orange edges:** Other PEPs cite the selected PEP.
- **Blue edges:** The selected PEP cites other PEPs.

![](images/network/network.png)

### Reset selection
Click the `Reset selection` button to clear the current node selection.

![](images/network/reset.png)

### Change node size
You can change the node size using the following four metrics:
- `in-degree`: The number of PEPs that cite the selected PEP. PEPs with a high in-degree are widely referenced and often influential.
- `out-degree`: The number of PEPs that the selected PEP cites. PEPs with a high out-degree tend to reference many other PEPs and may serve as integrative or coordinating proposals.
- `degree`: The sum of in-degree and out-degree.
- `constant`: All nodes are displayed with the same size.

If the selected metric is 0, the node is displayed with a default minimum size.

![](images/network/node_size.png)

### Zoom and Pan
- **Zoom:** Use the mouse wheel (or pinch gestures) to zoom in and out.
- **Pan:** Click and drag the background to move the entire graph.

![](images/network/zoom.gif)
![](images/network/move.gif)

### Node Interaction
Drag a node to reposition it manually.

![](images/network/move_node.gif)

## Local environment setup

```
$ python -m venv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
```

```
(venv) $ python app.py
```

To enable debug mode (hot reload, interactive error display):

```
(venv) $ DEBUG=true python app.py
```
