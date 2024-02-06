import os
import random
import streamlit as st
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv

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
            dataframe = pd.read_csv(csv_path)
            dataframes.append(dataframe)
        except pd.errors.ParserError as e:
            st.error(f"Error parsing CSV file '{csv_file}': {str(e)}")

    return dataframes

# Function to make API call and create heatmap
def make_openai_call(model_name, max_tokens, temperature, task, dataframe):
    task_name = task["task_name"]
    system_message = task["system"]

    openai_api_key = os.getenv('OPENAI_API_KEY')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',
    }

    messages = [
        {
            'role': 'system', 
            # FIXME: Update the way the table is appended to the system prompt
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
    print(f"\ntask_name: {task_name}\nresult: {result}")

    return result

# Function to create heatmap
def make_other_call(task, dataframe):
    output_str = ''
    
    task_name = task["task_name"]

    if(task_name == "Row Counts"):
        output_str = str(dataframe.shape[0])
    
    if(task_name == "Column Counts"):
        output_str = str(dataframe.shape[1])
    
    if(task_name == "Table Size"):
        output_str = str(dataframe.size)
    
    if(task_name == "Table Bounds"):
        first_row = str(dataframe.iloc[0])
        last_row = str(dataframe.iloc[-1])
        result = first_row, last_row
        output_str = str(result)

    print(f"\ntask_name: {task_name}\noutput_str: {output_str}")
    return output_str

# Streamlit App
def main():
    # Sidebar components
    st.sidebar.title('Microsoft Copilot Tests')

    username = st.sidebar.text_input('Username', help='Enter a username')
    modelname_dropdown = st.sidebar.selectbox('LLM Model', ['gpt-3.5-turbo', 'gpt-4-turbo-preview'], help='Select an LLM model')
    
    st.sidebar.header('Data Related')
    tablenum_slider = st.sidebar.slider('Tables to Load', min_value=1, max_value=10, value=2, help='Select number of tables to run tests on')
    table_append_type_dropdown = st.sidebar.selectbox('Table Append Type', ['Markdown', 'JSON', 'XML', 'Text'], index=0, help='Select a method of appending tables to the system prompt')
    rand_checkbox = st.sidebar.checkbox('Select random CSVs', help='Select to randomize cell indexes and values')

    st.sidebar.header('Task Related')
    task1_checkbox = st.sidebar.checkbox('Task 1: Row Counts')
    task2_checkbox = st.sidebar.checkbox('Task 2: Column Counts')
    task3_checkbox = st.sidebar.checkbox('Task 3: Table Size')
    task4_checkbox = st.sidebar.checkbox('Task 4: Table Bounds')

    # Data Stuff
    path = r'Data/CSVs'

    # Task Stuff
    st.header('Tasks')
    full_tasks = [
        {
            'task_text': 'Task 1: Row Counts',
            'task_name': 'Row Counts',
            'system': '',
        },
        {
            'task_text': 'Task 2: Column Counts',
            'task_name': 'Column Counts',
            'system': '',
        },
        {
            'task_text': 'Task 3: Table Size',
            'task_name': 'Table Size',
            'system': '',
        },
        {
            'task_text': 'Task 4: Table Bounds',
            'task_name': 'Table Bounds',
            'system': '',
        },
    ]
    # Initialize a list for selected tasks
    selected_tasks = []

    # Check if at least one task is selected and update the system prompts
    if task1_checkbox:
        full_tasks[0]["system"] = st.text_area(full_tasks[0]["task_text"])
        selected_tasks.append(full_tasks[0])

    if task2_checkbox:
        full_tasks[1]["system"] = st.text_area(full_tasks[1]["task_text"])
        selected_tasks.append(full_tasks[1])

    if task3_checkbox:
        full_tasks[2]["system"] = st.text_area(full_tasks[2]["task_text"])
        selected_tasks.append(full_tasks[2])

    if task4_checkbox:
        full_tasks[3]["system"] = st.text_area(full_tasks[3]["task_text"])
        selected_tasks.append(full_tasks[3])

    # Check if at least one task is selected and display an error message if not
    if not selected_tasks:
        st.error("Please select at least one task")
    
    if st.button('Run Tasks'):
        st.header('Data')
        dataframes = load_and_select_csvs(path, tablenum_slider, rand_checkbox)
        st.text(f'Loaded {len(dataframes)} CSVs')

        st.header('Result')
        task_accuracies = {
            task["task_name"]: sum(
                make_other_call(
                    task, 
                    dataframe
                ) 
                == 
                make_openai_call(
                    modelname_dropdown, 
                    256, 
                    0, 
                    task, 
                    dataframe
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

        # st.header('Output')
        # task_accuracies = {}
        # for i, task in enumerate(selected_tasks, start=0):
        #     # print(f"{i} - {task}\n")
            
        #     task_system_prompt = task["system"]
        #     task_name = task["task_name"]

        #     correct_count = 0  # Counter for correct responses

        #     for j, dataframe in enumerate(dataframes, start=0):
        #         # print(f"{j} - {dataframe}\n")

        #         response = make_openai_call(modelname_dropdown, 256, 0, task_system_prompt, dataframe)
        #         actual = make_other_call(task_name, dataframe)

        #         match = actual == int(response)

        #         # st.subheader(f"System Prompt #{i} on CSV #{j}:")
        #         # st.write(f"Task Name: {task_name}")
        #         # st.write(f"System Prompt: {task_system_prompt}")
        #         # st.write(f"Response: {response}")
        #         # st.write(f"Actual: {actual}")
        #         # st.write(f"Match: {match}")

        #         if match:
        #             correct_count += 1

        #     # Calculate accuracy percentage
        #     task_accuracy = (correct_count / len(dataframes)) * 100
        #     task_accuracies[task_name] = task_accuracy

        # st.header('Final')
        # for task_name, task_accuracy in task_accuracies.items():
        #     st.subheader(f"Task: {task_name} - Accuracy: {task_accuracy:.2f}%")
        # st.markdown("---")

if __name__ == '__main__':
    main()