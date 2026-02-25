# PEP Map

## What is this?
**🐍PEP Map**: https://pep-map.onrender.com/


[PEP Map](https://pep-map.onrender.com/) is a web application that **visualizes citation relationships between PEPs** (Python Enhancement Proposals).

- **Timeline tab:**
    - Explore citation relationships between PEPs **on a chronological timeline**.
    - It helps you trace the history of PEPs related to the selected PEP.
- **Network tab (coming soon):**
    - Explore citation relationships between PEPs **as a network graph**.
    - It helps you understand the relationships between PEPs and identify influential ones.

**Note:**
This project is a redesigned and reimplemented version of [pep_map_site](https://github.com/komo-fr/pep_map_site), originally built with Bokeh and PyScript.
It is now built using Dash.

## Timeline
Enter a PEP number in the left text box (e.g., 8).   
The following information is displayed in creation date order:

- PEPs that cite the selected PEP
- PEPs cited by the selected PEP

![](images/timeline/timeline.png)

Enable the checkbox to show vertical lines for Python release dates.

![](images/timeline/checkbox.png)

Hover over a PEP data point on the timeline to see information about that PEP.   
Click the data point to open the official PEP document.

![](images/timeline/hover.png)

Select a range on the timeline to zoom in on that range.   
Click the home button (🏠) in the top-right corner of the timeline to reset the view.

![](images/timeline/zoom.gif)

## Network
(coming soon)

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
