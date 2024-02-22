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
def load_and_select_csvs(path, num_selected, rand_csv_checkbox):
    csv_files = [file for file in os.listdir(path) if file.endswith('.csv')]
    if rand_csv_checkbox:
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
    print(f'openai_api_key: {openai_api_key}')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',
    }
    print(f'headers: {headers}')

    messages = [
        {
            'role': 'system', 
            # FIXME: Update the way the table is appended to the task_systemprompt prompt
            'content': f"{system_message}\n{dataframe.to_markdown(index=False)}"
        }
    ]
    # print(f"messages\n{messages}")

    data = {
        'messages': messages,
        'model': model_name,
        'max_tokens': max_tokens,
        "temperature": temperature,
        'seed': 48
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
    result = response.json()
    print(f"result: {result}")
    result_text = result['choices'][0]['message']['content']
    print(f"\ntask_name: {task_name}\nLLM result: {result_text}")

    return result_text

# Function to create heatmap
def make_other_call(rand_index_checkbox, task, dataframe):
    result = ''
    
    task_name = task["task_name"]

    if(task_name == "Task 1: Row Counts"):
        result = str(dataframe.shape[0])
    
    if(task_name == "Task 2: Column Counts"):
        result = str(dataframe.shape[1])
    
    if(task_name == "Task 3: Table Shape"):
        result = str(dataframe.shape)
    
    if(task_name == "Task 4: Table Bounds"):
        first_row = str(dataframe.iloc[0])
        last_row = str(dataframe.iloc[-1])
        result = first_row, last_row
        result = str(result)
    
    if(task_name == "Task 5: Cell Lookup"):
        if not rand_index_checkbox:
            middle_row = 1
            middle_col = 1
            
            result = dataframe.iloc[middle_row, middle_col]
        else:
            random_row = np.random.randint(0, dataframe.shape[0])
            random_col = np.random.randint(0, dataframe.shape[1])
            
            result = dataframe.iloc[random_row, random_col]
    
    if(task_name == "Task 6: Reverse Cell Lookup"):
        if not rand_index_checkbox:
            indices = np.where(dataframe == value_to_find)
            
            if len(indices[0]) > 0 and len(indices[1]) > 0:
                result = (int(indices[0][0]), int(indices[1][0]))
            else:
                result = None
        else:
            random_row = np.random.randint(0, dataframe.shape[0])
            random_col = np.random.randint(0, dataframe.shape[1])
            
            result = dataframe.iloc[random_row, random_col]
    
    if(task_name == "Task 7: Row Retrieval"):
        result = ''
    
    if(task_name == "Task 8: Column Retrieval"):
        result = ''
    
    if(task_name == "Task 9: Merged Cell Index"):
        result = ''
    
    if(task_name == "Task 10: Table Data Info"):
        result = ''

    print(f"\ntask_name: {task_name}\nDF result: {result}")
    return result

# Streamlit App
def main():
    # Initial Stuff
    path = r'Data/CSVs'
    full_tasks = [
        {
            'task_name': 'Task 1: Row Counts',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 2: Column Counts',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 3: Table Shape',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 4: Table Bounds',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 5: Cell Lookup',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 6: Reverse Cell Lookup',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 7: Row Retrieval',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 8: Column Retrieval',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 9: Merged Cell Index',
            'task_systemprompt': '',
        },
        {
            'task_name': 'Task 10: Table Data Info',
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
    rand_csv_checkbox = st.sidebar.checkbox('Select random CSVs', help='Select to randomize CSV selected')
    rand_index_checkbox = st.sidebar.checkbox('Select random index for a CSV', help='Select to randomize cell indexes and values')

    if 'selected_dataframes' not in st.session_state:
        st.session_state.selected_dataframes = None
    if 'toggle_states' not in st.session_state:
        st.session_state.toggle_states = {}

    # Check if at least one task is selected and display the "Load Data" button
    st.header('Data')
    if st.button('Load Data'):
        st.session_state.selected_dataframes = load_and_select_csvs(path, tablenum_slider, rand_csv_checkbox)
        st.session_state.toggle_states = {df['name']: False for df in st.session_state.selected_dataframes}

    if st.session_state.selected_dataframes:
        st.text(f'Loaded {len(st.session_state.selected_dataframes)} CSVs')
        for idx, df in enumerate(st.session_state.selected_dataframes):
            # Button to toggle dataframe visibility
            btn_key = f"df_btn_{idx}"
            if st.button(f"{df['name']}", key=btn_key):
                # Toggle the visibility state
                st.session_state.toggle_states[df['name']] = not st.session_state.toggle_states.get(df['name'], False)
            
            # Check the current toggle state and display/hide the dataframe accordingly
            if st.session_state.toggle_states.get(df['name'], False):
                st.dataframe(df['dataframe'])
                # Task Stuff
    
    st.header('Tasks')
    st.sidebar.header('Task Related')
    task_checkboxes = {task['task_name']: st.sidebar.checkbox(task['task_name']) for task in full_tasks}

    # Initialize a list for selected tasks
    selected_tasks = []

    # Loop through each task, check if it was selected, and display a text area if it was
    for task in full_tasks:
        if task_checkboxes[task['task_name']]:
            # Show text area for the task and retrieve the value from session state
            key = f"task_name_area_{task['task_name']}"
            
            # FIXME: Retrieve the previous text value from session state
            # previous_text = localStorage.getItem(key)
            task['task_systemprompt'] = st.text_area(task['task_name'], "", key=key)
            print(f"key: {key}\ntask['task_systemprompt']: {task['task_systemprompt']}\n")
            
            # Save the text area value in session state
            localStorage.setItem(key, task['task_systemprompt'])
            
            # Add the task to the list of selected tasks
            selected_tasks.append(task)
            
    if not selected_tasks:
        st.error("Please select at least one task")

    if selected_tasks and st.button('Run Tasks'):
        st.header('Result')
        for task in selected_tasks:
            task_name = task["task_name"]
            task_matches = 0
            for dataframe in st.session_state.selected_dataframes:
                match = make_other_call(
                            rand_index_checkbox,
                            task, 
                            dataframe["dataframe"]
                        ) == make_openai_call(
                            modelname_dropdown, 
                            256, 
                            0, 
                            task, 
                            dataframe["dataframe"]
                        )
                task_matches += match
            
            # Determine the color based on whether the number of matches equals the number of dataframes
            color = "green" if task_matches == len(st.session_state.selected_dataframes) else "red"

            # Display the task name, number of matches, and total dataframes
            st.markdown(f"<span title='{', '.join(df['name'] for df in st.session_state.selected_dataframes)}'>{task_name}</span> - <span style='color: {color};'>{task_matches}/{len(st.session_state.selected_dataframes)}</span>", unsafe_allow_html=True)

if __name__ == '__main__':
    main()