# bmeg to cytoscape

Generates sif file and associated tables for import into cytoscape.


## instructions

```
$ python3 schema_to_cytoscape.py
```

The app reads bmeg, so you will need credentials in `~/.bmeg_credentials.json`

```
>>> edge_labels.json
>>> node_labels.json
```

Note that the graph rendered by `https://bmeg.io/meta/schema.json` will be used.

* File->Import->Import Network from file `<graph_name>.sif`
* File->Import->Table from file `<graph_name>_edges.tsv` `<graph_name>_nodes.tsv`

## gotchas

* There are timeouts in bmeg, so there will be missing `count` fields in `edge_labels.json`. You will need to find and edit them manually.

* We have a large number of publications, edit the node_labels file to adjust.
