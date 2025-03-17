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

load_dotenv()
api_key = os.getenv("API_KEY")
genai.configure(api_key=api_key)

st.title("Network File Processor")
st.write("Upload a JSON/YAML file")

uploaded_file = st.file_uploader("Choose a file", type=["json", "yaml", "yml"])

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
        
        tab1, tab2, tab3 = st.tabs(["Raw Data", "Processed Data", "Graph"])
        
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
            # response = model.generate_content([processed_json, "This is a network configuration file. Return the output in the form of adjacency list."])
            response = model.generate_content([processed_json, """You are a network configuration parser. I will provide you with a network configuration file. Your task is to analyze the configuration and generate an adjacency list representing the network topology.
The adjacency list should be formatted as a JSON object, where:
* Each key represents a network node (e.g., a router, switch, or server).
* Each value is a list of nodes that are directly connected to the key node.

Please provide the output in the following JSON format:
```json
{"node1": ["node2", "node3"], "node2": ["node1", "node4"], ...}"""])

            
            st.info(f"{response.text}")
            
            st.download_button(
                label="Download Data",
                data=processed_json,
                file_name=f"processed_{uploaded_file.name}",
                mime="application/json"
            )
        
        with tab3:
            st.subheader("Network Graph")
            
            g = nx.Graph()
            print(response.text)

            start_index = response.text.find("```json") + len("```json")
            end_index = response.text.find("```", start_index)
            json_string = response.text[start_index:end_index].strip()
            
            print(json_string)
            
            for node, neighbors in ast.literal_eval(json_string).items():
                for neighbor in neighbors:
                    g.add_edge(node, neighbor)
            plt.figure(figsize=(6, 4))
            nx.draw(g, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=14)
            st.pyplot(plt)

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")