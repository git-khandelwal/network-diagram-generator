import streamlit as st
import json
import yaml
import pandas as pd
import google.generativeai as genai
import networkx as nx
import matplotlib.pyplot as plt
import ast
import os
from dotenv import load_dotenv
from helper_ import classify_device, compare_adjacency_lists, extract_json_from_markdown
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO

load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)

st.title("Network File Processor")
st.write("Upload a JSON/YAML file")

uploaded_file = st.file_uploader("Choose a file", type=["json", "yaml", "yml"])

icons = {
    'server': os.path.join(os.getcwd(), 'icons', 'file-server.png'),
    'router': os.path.join(os.getcwd(), 'icons', 'router.png'),
    'pc': os.path.join(os.getcwd(), 'icons', 'pc.png'),
    'switch': os.path.join(os.getcwd(), 'icons', 'switch.png'),
    'other': os.path.join(os.getcwd(), 'icons', 'cloud.png')
}

if uploaded_file is not None:
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'json':
            data = json.load(uploaded_file)
            file_type = "JSON"
        elif file_extension in ('yaml', 'yml'):
            data = yaml.safe_load(uploaded_file)
            file_type = "YAML"
        else:
            st.error("Unsupported file type. Please upload a JSON or YAML file.")
            st.stop()
            
        st.success(f"{file_type} file loaded successfully!")
        
        dummy_processed = {
            "filename": uploaded_file.name,
            "file_type": file_type,
            "data": data
        }
        
        tab1, tab2, tab3, tab4 = st.tabs(["Raw Data", "Processed Data", "Graph", "Graph Analysis"])
        
        with tab1:
            st.subheader("Original Data")
            
            if isinstance(data, list) and data and isinstance(data[0], dict):
                # If it's a list of dictionaries, show as dataframe
                st.write(f"File contains a list with {len(data)} items")
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True)
            elif isinstance(data, dict):
                # If it's a dictionary, show as JSON
                st.write("File contains a dictionary structure")
                st.json(data)
            else:
                # For other data types
                st.write("File contains data of type:", type(data).__name__)
                st.code(str(data))
        
        with tab2:
            st.subheader("Processed Data")
            st.write("Adjacency List:")
            
            processed_json = json.dumps(dummy_processed, indent=2)

            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content([processed_json, """You are a network configuration parser. I will provide you with a network configuration file. 
                                                Your task is to analyze the configuration and generate an adjacency list representing the network topology.
                                                The adjacency list should be formatted as a JSON object, where:
                                                * Each key represents a network node (e.g., a router, switch, or server).
                                                * Each value is a list of nodes that are directly connected to the key node.

                                                Please provide the output in the following JSON format:
                                                ```json
                                                {"node1": ["node2", "node3"], "node2": ["node1", "node4"], ...}```"""])

            st.info(f"{response.text}")
            
            adjacency_orig = ast.literal_eval(extract_json_from_markdown(response.text))
            st.download_button(
                label="Download Data",
                data=processed_json,
                file_name=f"processed_{uploaded_file.name}",
                mime="application/json"
            )
        
        with tab3:
            st.subheader("Network Graph")
            
            g = nx.Graph()

            start_index = response.text.find("```json") + len("```json")
            end_index = response.text.find("```", start_index)
            json_string = response.text[start_index:end_index].strip()
            

            for node, neighbors in ast.literal_eval(json_string).items():
                for neighbor in neighbors:
                    g.add_edge(node, neighbor)

            device_types = {device: classify_device(device) for device in ast.literal_eval(json_string)}

            pos = nx.spring_layout(g)

            # Clear any existing plots and set figure size
            plt.clf()
            plt.figure(figsize=(10, 10))
            plt.margins(0.2)

            nx.draw_networkx_edges(g, pos)

            label_pos = {}
            for node, (x, y) in pos.items():
                if node in device_types:
                    if device_types[node] == 'server':
                        offset = 0.14
                    elif device_types[node] == 'router':
                        offset = 0.10
                    elif device_types[node] == 'switch':
                        offset = 0.09
                    elif device_types[node] == 'pc':
                        offset = 0.14
                    else:
                        offset = 0.10  # Default offset for other known devices
                else:
                    offset = 0.10  # Default offset for unknown devices
                
                label_pos[node] = (x, y - offset)

            for device, connections in ast.literal_eval(json_string).items():
                x, y = pos[device]
                img = plt.imread(icons[device_types[device]])
                imagebox = OffsetImage(img, zoom=0.1)
                ab = AnnotationBbox(imagebox, (x, y), frameon=False)
                plt.gca().add_artist(ab)
                for connected_device in connections:
                    if connected_device not in device_types:
                        x, y = pos[connected_device]
                        img = plt.imread(icons["other"])
                        imagebox = OffsetImage(img, zoom=0.1)
                        ab = AnnotationBbox(imagebox, (x, y), frameon=False)
                        plt.gca().add_artist(ab)

            # Draw labels using the offset positions
            nx.draw_networkx_labels(g, label_pos, font_size=8)
            st.pyplot(plt)

        with tab4:
            st.subheader("Graph Analysis")
            
            # Get the current figure
            fig = plt.gcf()
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
            buf.seek(0)
    
            image_data = {'mime_type': 'image/png', 'data': buf.getvalue()}
            
            model = genai.GenerativeModel('gemini-2.0-flash')

            response_2 = model.generate_content([image_data, """Please analyze the provided image, which depicts a network diagram. Extract the nodes (devices) and the connections between them. Represent this information as an adjacency list in JSON format.
                                                Specifically, for each node (device) in the diagram(Which can be a router, switch, server or a pc), create a key-value pair in the JSON object. The key should be the node's identifier (e.g., "node1", "serverA", "routerX"). The value should be a list containing the identifiers of all nodes directly connected to that node, including external nodes such as "Internet", "ISP", or "Backup".
                                                The desired output format is as follows (example):
                                                ```json
                                                {"node1": ["node2", "node3", "Internet"], "node2": ["node1", "node4"], "node3": ["node1"], "node4": ["node2", "Backup"], "Server1": ["R2", "ISP"], "R2": ["Server1"]}```"""])

            st.write("### Network Analysis")

            adjacency_output = ast.literal_eval(extract_json_from_markdown(response_2.text))

            external_keywords = ['isp', 'backup', 'internet', 'printer', 'cloud', 'wan', "firewall"]
            filtered_data = {}
            
            for node, neighbors in adjacency_output.items():
                # Skip nodes that match external keywords
                if any(keyword in node.lower() for keyword in external_keywords):
                    continue
                filtered_data[node] = neighbors
                
            st.info(f"```json\n{json.dumps(filtered_data, indent=2)}\n```")
            st.image(buf, caption="Original Graph")
            st.write("Matching with Original Graph?", compare_adjacency_lists(filtered_data, adjacency_orig))

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")