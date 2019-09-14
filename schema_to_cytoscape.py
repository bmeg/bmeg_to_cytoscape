"""Transforms bmeg schema to cytoscape."""
import os
import requests
from attrdict import AttrDict
import gripql
from collections import defaultdict
import json
import click

class GripHelper():
    def __init__(self, bmeg_url, bmeg_graph, bmeg_credential_file):
        # Set up connection to server and create graph handle
        conn = gripql.Connection(bmeg_url, credential_file=bmeg_credential_file)
        self.O = conn.graph(bmeg_graph)  # noqa E741

    def edge_label_count(self, name):
        return list(self.O.query().E().hasLabel(name).count())[0].count

    def edge_count(self, edge):
        count_list = []
        try:
            count_list = list(self.O.query().V().hasLabel(edge["from"]).outE(edge.label).count())
        except Exception as e:
            print(f'timeout? {edge} {e}')
            return None
        return count_list[0].count

    def node_count(self, name):
        return list(self.O.query().V().hasLabel(name).count())[0].count


def validate(schema):
    expected_keys = ['graph', 'vertices', 'edges']
    for expected_key in expected_keys:
        assert expected_key in schema, f'{expected_key} not found'
    return AttrDict(schema)

# def to_sif(schema):
#     return [f'{edge["from"]} {edge.label} {edge.to}' for edge in schema.edges]

def to_sif(edge_labels):
    return [f'{edge["from"]} {edge.label} {edge.to}' for edge in edge_labels]

def to_sif_with_counts(schema, grip):
    return [f'{edge["from"]} {edge.label} {edge.to} {grip.edge_label_count(edge.label)}' for edge in schema.edges]


def init(url):
    schema = requests.get(f'{url}/meta/schema.json').json()
    schema = validate(schema)
    bmeg_url = f'{url}/api'
    # setup credentials
    bmeg_graph = schema.graph
    print(f'bmeg_graph:{bmeg_graph}')
    bmeg_credential_file = os.path.expanduser('~/.bmeg_credentials.json')
    grip = GripHelper(bmeg_url, bmeg_graph, bmeg_credential_file)
    return schema, grip


def create_edge_labels(schema, grip):
    edge_labels = defaultdict(list)
    for e in [AttrDict({'label':edge.label, 'edge': edge })  for edge in schema.edges]:
        edge_labels[e.label].append(e.edge)

    unique_edge_labels = [k for k, v  in edge_labels.items() if len(v) == 1]

    for label in unique_edge_labels:
        edge = edge_labels[label][0]
        sif = f'{edge["from"]} {edge.label} {edge.to}'
        count = grip.edge_label_count(label)
        edge.count = count
        print(f'{sif} {count}')

    duplicate_edge_labels = [k for k, v  in edge_labels.items() if len(v) > 1]
    for label in duplicate_edge_labels:
        for edge in edge_labels[label]:
            sif = f'{edge["from"]} {edge.label} {edge.to}'
            count = grip.edge_count(edge)
            edge.count = count
            print(f'{sif} {count}')


    with open('edge_labels.json','w') as output:
        flattened_edge_labels = [item for sublist in edge_labels.values() for item in sublist]
        json.dump(flattened_edge_labels, output)


def create_node_labels(edge_labels, grip):
    labels = set([edge["from"] for edge in edge_labels] + [edge["to"] for edge in edge_labels])
    node_labels = {}
    for label in labels:
        node_labels[label] = grip.node_count(label)
    with open('node_labels.json','w') as output:
        json.dump(node_labels, output)
    return node_labels

@click.command()
@click.option('--url', default='https://bmeg.io', help='Base url')
def main(url):
    schema, grip = init(url)

    if not os.path.exists('edge_labels.json'):
        create_edge_labels(schema, grip)

    with open('edge_labels.json') as input:
        edge_labels = json.load(input)
        edge_labels = [AttrDict(e) for e in edge_labels]

    if not os.path.exists('node_labels.json'):
        create_node_labels(edge_labels, grip)

    with open('node_labels.json') as input:
        node_labels = json.load(input)

    print(f'# read edge_labels: {len(edge_labels)}')
    print(f'# read node_labels: {len(node_labels)}')

    with open(f'{grip.O.graph}.sif','w') as output:
        output.write('\n'.join(sorted(to_sif(edge_labels))))
    print(f'# wrote {grip.O.graph}.sif')

    with open(f'{grip.O.graph}_nodes.tsv','w') as output:
        output.write('\t'.join(['label', 'size']))
        output.write('\n')
        for k, v in node_labels.items():
            output.write(f'{k}\t{v}\n')
    print(f'# wrote {grip.O.graph}_nodes.tsv')

    with open(f'{grip.O.graph}_edges.tsv','w') as output:
        output.write('\t'.join(['label', 'size']))
        output.write('\n')
        for edge in edge_labels:
            output.write(f'{edge["from"]} ({edge.label}) {edge.to}\t{edge.count}\n')
    print(f'# wrote {grip.O.graph}_edges.tsv')

if __name__ == '__main__':
    main()
