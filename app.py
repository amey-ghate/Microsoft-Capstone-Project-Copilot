import os
import json
import random
import streamlit as st
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from streamlit_local_storage import LocalStorage
import streamlit.components.v1 as components

load_dotenv()

# Function to load all CSVs at a path and randomly select a specified number of them
def load_and_select_csvs(path, num_selected, rand_checkbox):
    csv_files = [file for file in os.listdir(path) if file.endswith('.csv')]
    if rand_checkbox:
        selected_csvs = random.sample(csv_files, num_selected)
    else:
        selected_csvs = csv_files[:num_selected]
    dataframes = []

    for csv_file in selected_csvs:
        csv_path = os.path.join(path, csv_file)
        try:
            dataframe = pd.read_csv(csv_path, sep='#')
            dataframes.append({"name": csv_file, "dataframe": dataframe})
        except pd.errors.ParserError as e:
            st.error(f"Error parsing CSV file '{csv_file}': {str(e)}")

    return dataframes

# Function to make API call and create heatmap
def make_openai_call(model_name, max_tokens, temperature, task, dataframe):
    task_name = task["task_name"]
    system_message = task["task_systemprompt"]

    openai_api_key = os.getenv('OPENAI_API_KEY')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',
    }

    messages = [
        {
            'role': 'task_systemprompt', 
            # FIXME: Update the way the table is appended to the task_systemprompt prompt
            'content': f"{system_message}\n{dataframe.to_markdown(index=False)}"
        }
    ]
    # print(f"messages\n{messages}")

    data = {
        'messages': messages,
        'model': model_name,
        'max_tokens': max_tokens,
        "temperature": temperature
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
    data = response.json()
    result = data['choices'][0]['message']['content']
    print(f"\ntask_name: {task_name}\nLLM result: {result}")

    return result

# Function to create heatmap
def make_other_call(task, dataframe):
    result = ''
    
    task_name = task["task_name"]

    if(task_name == "Row Counts"):
        result = str(dataframe.shape[0])
    
    if(task_name == "Column Counts"):
        result = str(dataframe.shape[1])
    
    if(task_name == "Table Shape"):
        result = str(dataframe.shape)
    
    if(task_name == "Table Bounds"):
        first_row = str(dataframe.iloc[0])
        last_row = str(dataframe.iloc[-1])
        result = first_row, last_row
        result = str(result)

    print(f"\ntask_name: {task_name}\nDF result: {result}")
    return result

# Streamlit App
def main():
    # Initial Stuff
    path = r'Data/CSVs'
    full_tasks = [
        {
            'task_text': 'Task 1: Row Counts',
            'task_name': 'Row Counts',
            'task_systemprompt': '',
        },
        {
            'task_text': 'Task 2: Column Counts',
            'task_name': 'Column Counts',
            'task_systemprompt': '',
        },
        {
            'task_text': 'Task 3: Table Shape',
            'task_name': 'Table Shape',
            'task_systemprompt': '',
        },
        {
            'task_text': 'Task 4: Table Bounds',
            'task_name': 'Table Bounds',
            'task_systemprompt': '',
        },
    ]
    
    localStorage = LocalStorage()
    
    # Initialize session state to store text area values
    if 'text_area_values' not in st.session_state:
        st.session_state.text_area_values = {}
        print(f"st.session_state.text_area_values: {st.session_state.text_area_values}")

    # Sidebar components
    st.sidebar.title('Microsoft Copilot Tests')

    username = st.sidebar.text_input('Username', help='Enter a username')
    modelname_dropdown = st.sidebar.selectbox('LLM Model', ['gpt-3.5-turbo', 'gpt-4-turbo-preview'], help='Select an LLM model')
    
    st.sidebar.header('Data Related')
    tablenum_slider = st.sidebar.slider('Tables to Load', min_value=1, max_value=10, value=2, help='Select number of tables to run tests on')
    table_append_type_dropdown = st.sidebar.selectbox('Table Append Type', ['Markdown', 'JSON', 'XML', 'Text'], index=0, help='Select a method of appending tables to the task_systemprompt prompt')
    rand_checkbox = st.sidebar.checkbox('Select random CSVs', help='Select to randomize cell indexes and values')

    # Task Stuff
    st.header('Tasks')
    # Dynamically create checkboxes for tasks and collect user responses
    st.sidebar.header('Task Related')
    task_checkboxes = {task['task_text']: st.sidebar.checkbox(task['task_text']) for task in full_tasks}

    # Initialize a list for selected tasks
    selected_tasks = []

    # Loop through each task, check if it was selected, and display a text area if it was
    for task in full_tasks:
        if task_checkboxes[task['task_text']]:
            # Show text area for the task and retrieve the value from session state
            key = f"task_text_area_{task['task_text']}"
            
            # FIXME: Retrieve the previous text value from session state
            # previous_text = localStorage.getItem(key)
            task['task_systemprompt'] = st.text_area(task['task_text'], "", key=key)
            print(f"key: {key}\nprevious_text: {previous_text}\ntask['task_systemprompt']: {task['task_systemprompt']}\n")
            
            # Save the text area value in session state
            localStorage.setItem(key, task['task_systemprompt'])
            
            # Add the task to the list of selected tasks
            selected_tasks.append(task)

    # Check if at least one task is selected and display an error message if not
    if not selected_tasks:
        st.error("Please select at least one task")
    
    # Check if at least one task is selected show button to run tests
    if selected_tasks:
        if st.button('Run Tasks'):
            st.header('Data')
            dataframes = load_and_select_csvs(path, tablenum_slider, rand_checkbox)
            st.text(f'Loaded {len(dataframes)} CSVs')

            st.header('Result')
            task_accuracies = {
                task["task_name"]: sum(
                    make_other_call(
                        task, 
                        dataframe["dataframe"]
                    ) 
                    == 
                    make_openai_call(
                        modelname_dropdown, 
                        256, 
                        0, 
                        task, 
                        dataframe["dataframe"]
                    )
                    for dataframe in dataframes
                ) / len(dataframes) * 100 
                for task in selected_tasks
            }
            [
                st.subheader(f"Task: {task_name} - Accuracy: {task_accuracy:.2f}%") 
                for task_name, task_accuracy in task_accuracies.items()
            ]
            st.markdown("---")

if __name__ == '__main__':
    main()