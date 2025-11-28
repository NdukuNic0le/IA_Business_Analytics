import json
with open('../../data/raw/donor_segmentation_matrix.json', 'r') as f:
    donors_data = json.load(f)
    
# Print the first donor to see the structure
print(json.dumps(donors_data[0], indent=2))