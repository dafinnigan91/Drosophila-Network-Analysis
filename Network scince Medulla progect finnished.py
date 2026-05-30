import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
from collections import Counter
import math  
import random
import sys
import os
import time

random.seed(42) # Set seed for reproducibility
input_path = "C:/Users/david/OneDrive/Desktop/Drosophila medula/drosophila_medulla_1.graphml"
MF = nx.read_graphml("C:/Users/david/OneDrive/Desktop/Drosophila medula/drosophila_medulla_1.graphml")
Edges = nx.to_pandas_edgelist(MF)
output_dir = os.path.dirname(input_path)
# Save edges to CSV
Edges = pd.DataFrame([{'source': u,'target': v,**d } for u, v, d in MF.edges(data=True)]) # Convert to DataFrame

edges_csv_path = os.path.join(output_dir, "medulla_edges.csv")
Edges.to_csv(edges_csv_path, index=False)

# Save nodes to CSV
Nodes = pd.DataFrame.from_dict(dict(MF.nodes(data=True)), orient='index') # Convert to DataFrame
Nodes.index.name = 'node_id'
Nodes.reset_index(inplace=True)
nodes_csv_path = os.path.join(output_dir, "medulla_nodes.csv")
Nodes.to_csv(nodes_csv_path, index=False)

print(f"Saved edge list to: {edges_csv_path}")
print(f"Saved node list to: {nodes_csv_path}")

Edges = pd.read_csv(edges_csv_path)
Nodes = pd.read_csv(nodes_csv_path)

edges_with_src = pd.merge(Edges,Nodes[['node_id', 'name']], how='left', left_on='source', right_on='node_id').rename(columns={'name': 'source_name'}).drop(columns=['node_id']) # Merge to get source names

# Merge to get target names
edges_named = pd.merge(edges_with_src,Nodes[['node_id', 'name']],how='left',left_on='target',right_on='node_id').rename(columns={'name': 'target_name'}).drop(columns=['node_id']) # Merge to get target names

edges_weighted = (edges_named.groupby(['source', 'target', 'source_name', 'target_name']).size().reset_index(name='weight')) # Group by source and target to get weights


edges_weighted.to_csv("C:/Users/david/OneDrive/Desktop/Drosophila medula/medulla_edges_weighted.csv", index=False) # Save the merged DataFrame to CSV

print("Merged file saved as medulla_edges_weighted.csv")
print(edges_weighted.head(5))

Medulla = nx.from_pandas_edgelist(edges_weighted,source='source',target='target',edge_attr='weight',create_using=nx.DiGraph()) # Create directed graph from DataFrame

labels = dict(zip(edges_weighted['source'], edges_weighted['source_name'])) # Create a dictionary for labels
nx.set_node_attributes(Medulla, labels, name='label')

# pos = nx.spring_layout(Medulla, k=0.5)  # Position nodes using spring layout

######################################################################################

num_nodes = Medulla.number_of_nodes() # Get number of nodes
num_edges = Medulla.number_of_edges() # Get number of edges
print(f"Number of nodes: {num_nodes}")
print(f"Number of edges: {num_edges}")

density = nx.density(Medulla) # Calculate density
print(f"Density: {density:.4f}")

avg_degree = sum(dict(Medulla.degree()).values()) / num_nodes #claculate the average degree
print(f"Average degree: {avg_degree:.4f}")

avg_in = sum(dict(Medulla.in_degree()).values()) / num_nodes # calculte the average in-degree
print(f"Average in-degree: {avg_in:.4f}")

avg_out = sum(dict(Medulla.out_degree()).values()) / num_nodes # calculate the average out-degree
print(f"Average out-degree: {avg_out:.4f}")

assortativity = nx.degree_assortativity_coefficient(Medulla) #calculate the assortativity coefficient
print(f"Assortativity: {assortativity:.4f}")

for node in Medulla.nodes: # Assign the neuron type based on the label
    label = Medulla.nodes[node].get('label', None)
    if isinstance(label, str):
        # Extract first word before any space as the type
        Medulla.nodes[node]['type'] = label.split()[0]
    else:
        # Fallback type if label missing
        Medulla.nodes[node]['type'] = 'Unknown'
        
assort_by_type = nx.attribute_assortativity_coefficient(Medulla, attribute='type') # Calculate assortativity based neuron type
print(f"Assortativity by neuron type: {assort_by_type:.4f}")

clustering = nx.average_clustering(Medulla.to_undirected()) # Clustering coefficient for undirected 
print(f"Average clustering coefficient: {clustering:.4f}")

wcc = list(nx.weakly_connected_components(Medulla)) # Find weakly connected components
print(f"Number of weakly connected components: {len(wcc)}") 

largest_wcc = Medulla.subgraph(max(wcc, key=len)).copy() # Get the largest weakly connected component
print(f"Size of largest weakly connected component: {len(largest_wcc)}")

largest_undirected = largest_wcc.to_undirected() # Convert to undirected for further analysis

diameter = nx.diameter(largest_undirected) # find the diameter of the largest weakly connected component
print(f"Diameter: {diameter}")

# Average shortest path length
avg_path = nx.average_shortest_path_length(largest_undirected) #find the average shortest path length
print(f"Average shortest path length: {avg_path:.2f}")

####################################################################################

degree_data = [] # a list to store degree data which will be converted to a dictionary
for node in Medulla.nodes():
    deg = Medulla.degree(node)
    in_deg = Medulla.in_degree(node)
    out_deg = Medulla.out_degree(node)
    ntype = Medulla.nodes[node].get('type', 'Unknown')
    label = Medulla.nodes[node].get('label', node)  # fallback to ID if label missing
    degree_data.append({
        'node': node,
        'label': label,
        'type': ntype,
        'degree': deg,
        'in_degree': in_deg,
        'out_degree': out_deg
    })

df_degrees = pd.DataFrame(degree_data)
K = 20 # Select top-k by degree
topk_nodes = df_degrees.sort_values(by='degree', ascending=False).head(K) # Select top-k nodes by degree
topk_ids = topk_nodes['node'].tolist() 
topk_labels = topk_nodes['label'].tolist() # retreave the labels of the top-k nodes 

adj_matrix_labelled = pd.DataFrame(0, index=topk_labels, columns=topk_labels) # Build adjacency matrix with labels
for i, u in enumerate(topk_ids): 
    for j, v in enumerate(topk_ids):
        if Medulla.has_edge(u, v):
            weight = Medulla[u][v].get('weight', 1) # Default weight is 1 if not specified
            adj_matrix_labelled.iloc[i, j] = weight # Fill the adjacency matrix with weights

plt.figure(figsize=(10, 8)) # Plot the adjacency matrix for top-k neurons
sns.heatmap(adj_matrix_labelled, cmap="YlGnBu", annot=True, fmt='d')
plt.title(f"Adjacency Heatmap of Top {K} High-Degree Neurons (Labeled)")
plt.xlabel("Target Neuron (Label)")
plt.ylabel("Source Neuron (Label)")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()
#####################################################################################################
target_label = adj_matrix_labelled.sum(axis=0).idxmax() # Get the label of the most targeted neuron
label_to_node = {Medulla.nodes[n].get('label', str(n)): n for n in Medulla.nodes} # Create the mapping from label to node ID
target_node = label_to_node.get(target_label) # Get the node ID of the most targeted neuron

in_edges = [(u, Medulla[u][target_node].get('weight', 1)) for u in Medulla.predecessors(target_node)] # Input: top 20 predecessors by edge weight
top_in = sorted(in_edges, key=lambda x: x[1], reverse=True)[:20]
top_in_nodes = [u for u, _ in top_in]

out_edges = [(v, Medulla[target_node][v].get('weight', 1)) for v in Medulla.successors(target_node)] # Output: top 20 successors by edge weight
top_out = sorted(out_edges, key=lambda x: x[1], reverse=True)[:20]
top_out_nodes = [v for v, _ in top_out]

selected_nodes = top_in_nodes + [target_node] + top_out_nodes # Build combined subgraph for the most targeted neuron
inout_subgraph = Medulla.subgraph(selected_nodes)
plt.figure(figsize=(10, 8))
pos = nx.spring_layout(inout_subgraph, seed=42)
node_colors = ['red' if n == target_node else ('skyblue' if n in top_in_nodes else 'lightgreen') for n in inout_subgraph.nodes] # Color nodes based on their type
node_labels = {n: Medulla.nodes[n].get('label', str(n)) for n in inout_subgraph.nodes}
nx.draw(inout_subgraph, pos, with_labels=True, labels=node_labels,
        node_color=node_colors, edge_color='gray', node_size=80, font_size=10, arrows=True, width=0.5)
plt.title(f"Input/Output Subgraph of Top 20 Connections for {target_label}") # plot the subgraph for the most targeted neuron
plt.tight_layout()
plt.show()

betweenness_centrality = nx.betweenness_centrality(Medulla)

target_label = adj_matrix_labelled.sum(axis=0).idxmax() # Get the label of the most targeted neuron from earlier
label_to_node = {Medulla.nodes[n].get('label', str(n)): n for n in Medulla.nodes}
target_node = label_to_node.get(target_label)

target_betweenness = betweenness_centrality.get(target_node, 0) # Report the betweenness centrality of the target neuron
target_label, target_betweenness
print (f"Betweenness centrality of {target_label}: {target_betweenness:.4f}")
in_degree = Medulla.in_degree(target_node)
print (f"In-degree of {target_label}: {in_degree}")
out_degree = Medulla.out_degree(target_node)
print (f"Out-degree of {target_label}: {out_degree}")
Medulla.nodes['n1472'].get('type')

neuron_type = Medulla.nodes['n1472'].get('type')
print (f"Neuron type of {target_label}: {neuron_type}")

##############################################################################################

lengths_dictionary = dict(nx.all_pairs_shortest_path_length(largest_wcc)) #get the shortest path lengths
all_lengths = []
for src in lengths_dictionary: 
    for tgt, length in lengths_dictionary[src].items():
        if src != tgt:
            all_lengths.append(length) # Exclude self-loops

if all_lengths: # Compute basic statistics for shortest path lengths
    avg_length = sum(all_lengths) / len(all_lengths)
    max_length = max(all_lengths)
    min_length = min(all_lengths)
    print(f"Average shortest path length (excluding self-loops): {avg_length:.2f}")
    print(f"Maximum shortest path length (excluding self-loops): {max_length}")
    print(f"Minimum shortest path length (excluding self-loops): {min_length}")
else:
    print("No valid shortest path lengths found.")
   
length_counts = Counter(all_lengths)

total_paths = sum(length_counts.values()) 
probs = [count / total_paths for count in length_counts.values()] # Calculate probabilities for each path length

path_entropy = -sum(p * math.log2(p) for p in probs if p > 0) # Calculate path entropy
print(f"Path entropy (excluding self-loops): {path_entropy:.4f}")

lengths_dict = dict(nx.all_pairs_shortest_path_length(largest_wcc))# Create a dictionary of all pairs shortest path lengths
all_lengths = [] 
for src in lengths_dict:
    for tgt, length in lengths_dict[src].items():
        if src != tgt:
            all_lengths.append(length)

length_counts = Counter(all_lengths) # Count frequencies
total_paths = sum(length_counts.values())
P_len = [count / total_paths for count in length_counts.values()]

# Path entropy
path_entropy = -sum(p * math.log2(p) for p in P_len if p > 0)

#######################################################################################
G = largest_wcc.to_undirected()

C = nx.average_clustering(G) # Clustering and path length for your medulla network
L = nx.average_shortest_path_length(G)

n = G.number_of_nodes() # Match size and density for random graph
m = G.number_of_edges()
p = 2 * m / (n * (n - 1))  # Edge probability for random graph

random_graph = nx.gnp_random_graph(n, p, seed=42) # Generate comparable Erdős–Rényi random graph
C_rand = nx.average_clustering(random_graph)
L_rand = nx.average_shortest_path_length(random_graph)

print(f"C: {C:.4f}")
print(f"C_rand: {C_rand:.4f}")
print(f"L: {L:.4f}")
print(f"L_rand: {L_rand:.4f}")
print(f"Small-world coefficient (σ):", (C / C_rand) / (L / L_rand)) # calculate the Small-world coefficient σ

Medulla.remove_edges_from(nx.selfloop_edges(Medulla)) # Remove self-loops for k-core analysis
core_numbers = nx.core_number(Medulla)
core_df = pd.DataFrame.from_dict(core_numbers, orient='index', columns=['core_number']) # Create a DataFrame for analysis
core_df['label'] = core_df.index.map(lambda n: Medulla.nodes[n].get('label', str(n)))
core_df = core_df.sort_values(by='core_number', ascending=False)

plt.figure(figsize=(8, 5))# Plot the core number distribution
core_df['core_number'].value_counts().sort_index().plot(kind='bar', color='steelblue')
plt.title("Distribution of K-Core Numbers in Medulla Network")
plt.xlabel("Core Number (k)")
plt.ylabel("Number of Neurons") 
plt.tight_layout()
plt.show()

max_core = core_df['core_number'].max() # Get top-core nodes
top_core_nodes = core_df[core_df['core_number'] == max_core]
print(f"Top {len(top_core_nodes)} nodes in the largest core (k={max_core}):")
print(top_core_nodes.head(10))

degrees = [d for _, d in Medulla.degree()] # calculate the degree entropy 
degree_counts = Counter(degrees)
total_nodes = sum(degree_counts.values())
P_k = [count / total_nodes for count in degree_counts.values()]
degree_entropy = -sum(p * math.log2(p) for p in P_k if p > 0)
print(f"Degree entropy: {degree_entropy:.4f} bits")

