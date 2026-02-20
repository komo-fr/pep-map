# PEP Map

## What is this?
**🐍PEP Map**: https://pep-map.onrender.com/


[PEP Map](https://pep-map.onrender.com/) is a web application that **visualizes citation relationships between PEPs** (Python Enhancement Proposals).

- **Timeline:** Citation relationships between PEPs in chronological order
- **Network:** Citation relationships between PEPs as a network graph **(coming soon)**

**Note:**
This project is a redesigned and reimplemented version of [pep_map_site](https://github.com/komo-fr/pep_map_site), originally built with Bokeh and PyScript.
It is now built using Dash.

## Timeline
Enter a PEP number in the text box on the left (e.g., 8).
The following information will be displayed in order of creation date:

- Which PEPs cite the selected PEP?
- Which PEPs does the selected PEP cite?

![](images/timeline.png)

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