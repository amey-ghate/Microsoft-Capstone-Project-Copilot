import os
import random
import streamlit as st
import requests
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# Function to make API call and create heatmap
def make_openai_call(model_name, max_tokens, temperature, system_message, dataframes):
    openai_api_key = os.getenv('OPENAI_API_KEY')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openai_api_key}',
    }

    messages = [
        {
            'role': 'system', 
            # FIXME: Update the way the table is appended to the system prompt
            'content': f"{system_message}\n{dataframes[0].to_markdown(index=False)}"
        }
    ]
    print(f"messages\n{messages}")

    data = {
        'messages': messages,
        'model': model_name,
        'max_tokens': max_tokens,
        "temperature": temperature
    }

    response = requests.post('https://api.openai.com/v1/chat/completions', json=data, headers=headers)
    result = response.json()
    print(f"result\n{result}")

    data = result['choices'][0]['message']['content']
    return data

# Function to create heatmap
def make_other_call(model_name, max_tokens, temperature, system_message):
    # Create heatmap using seaborn
    df = pd.DataFrame(data)
    sns.heatmap(df, annot=True, cmap='viridis')
    plt.title('Heatmap')
    st.pyplot()

    return df

# Function to load all CSVs at a path and randomly select a specified number of them
def load_and_select_csvs(path, num_selected):
    csv_files = [file for file in os.listdir(path) if file.endswith('.csv')]
    selected_csvs = random.sample(csv_files, num_selected)
    dataframes = []

    for csv_file in selected_csvs:
        csv_path = os.path.join(path, csv_file)
        try:
            dataframe = pd.read_csv(csv_path)
            dataframes.append(dataframe)
        except pd.errors.ParserError as e:
            st.error(f"Error parsing CSV file '{csv_file}': {str(e)}")

    return dataframes
    
# Function to create dataframe data
def create_dataframe_data(dataframes):
    dataframe_data_list = []
    for dataframe in dataframes:
        dataframe_data = {
            "df": dataframe,
            "row_count": dataframe.shape[0],
            "col_count": dataframe.shape[1],
            "size": dataframe.size
        }
        dataframe_data_list.append(dataframe_data)
    return dataframe_data_list

# Streamlit App
def main():
    st.sidebar.title('Microsoft Copilot Tests')

    # Sidebar components
    username = st.sidebar.text_input('Username', help='Enter a username')
    modelname_dropdown = st.sidebar.selectbox('Dropdown', ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo-preview'], help='Select an LLM model')
    tablenum_slider = st.sidebar.slider('\# of Tables to Test', min_value=1, max_value=20, value=2, help='Select number of tables to run tests on')
    rand_checkbox = st.sidebar.checkbox('Randomize Checkbox', help='Select to randomize cell indexes and values')

    # Main panel components
    st.header('SUC System Prompts')
    systemprompts_0 = st.text_area('Row Counts')
    systemprompts_1 = st.text_area('Column Counts')
    # systemprompts_2 = st.text_area('Table Size')
    # systemprompts_3 = st.text_area('Table Bounds')
    # systemprompts_4 = st.text_area('Merged Cells Index')
    # systemprompts_5 = st.text_area('Cell Data Retrieval (& Vice-Versa)')
    # systemprompts_6 = st.text_area('Column & Row Retrieval')
    system_prompts = [
        systemprompts_0,
        systemprompts_1
        # systemprompts_2,
        # systemprompts_3,
        # systemprompts_4,
        # systemprompts_5,
        # systemprompts_6
    ]
    
    path = r'Data/CSVs'
    dataframes = load_and_select_csvs(path, tablenum_slider)
    print(f"dataframes.length: {len(dataframes)}")
    df_data = create_dataframe_data(dataframes)
    print(f"df_data.length: {len(df_data)}")

    # Button to trigger API call
    if st.button('Run Test'):
        st.header('Results')
        for i, system_prompt in enumerate(system_prompts, start=0):
            response = make_openai_call(modelname_dropdown, 256, 0, system_prompt, dataframes)
            st.subheader(f"Result for System Prompt {i}:")
            st.write(f"System Prompt: {system_prompts[i]}")
            st.write(f"Response: {response}")
            st.markdown("---")

# Run the app
if __name__ == '__main__':
    main()
