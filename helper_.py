def classify_device(device_name):
    device_name = device_name.lower()
    if 'server' in device_name:
        return 'server'
    elif ('r' in device_name and device_name[1:].isdigit()) or 'router' in device_name:  # R1, R2, etc.
        return 'router'
    elif ('sw' in device_name and device_name[2:].isdigit()) or 'switch' in device_name:  # SW1, SW2, etc.
        return 'switch'
    elif 'pc' in device_name:
        return 'pc'
    else:
        return 'other'
    

def compare_adjacency_lists(adj_list1, adj_list2):
    if adj_list1.keys() != adj_list2.keys():
        return False

    for node, neighbors1 in adj_list1.items():
        neighbors2 = adj_list2[node]
        if sorted(neighbors1) != sorted(neighbors2):  # Compare sorted lists
            return False

    return True


def extract_json_from_markdown(text):
    start_index = text.find("```json")
    if start_index == -1:
        return None  # No JSON block found

    start_index += len("```json")
    end_index = text.find("```", start_index)
    if end_index == -1:
        return None  # Closing backticks not found

    json_string = text[start_index:end_index].strip()
    return json_string
