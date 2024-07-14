import streamlit as st
import altair as alt
import pandas as pd
import ast
import json
from actions_and_services import load_services_data, get_services, get_suggested_actions
from collections import defaultdict
import requests
from integrate import parse_inputs, features_finder, calculate_risk_scores, get_life_data, get_life_expectancy_risks, get_health_data, get_health_risks

st.set_page_config(layout="wide")

# Set the background color to black
st.markdown(
    """
    <style>
        
        footer {
            padding-top: 0.1; /* Reduce the top padding of the footer */
        }   
        header {
            margin-bottom: 0.1; /* Reduce the bottom margin of the header */
        }
        [data-testid="stApp"]{
            background-image: url("https://s7d1.scene7.com/is/image/wbcollab/Health_Background_Nov21");
            opacity: 0.9;
            color: white; /* Set text color to white */
            font-size: 27px;
        }
        [data-testid="stWidgetLabel"]{
            font-size= 5rem;
            font-style: bold;
            text-align: center;
        }
        [data-testid="stMarkdownContainer"] p {
            text-align: center;
        }
        [data-testid="stMarkdownContainer"] p {
            font-size: 19px !important;
            
        }
        [data-testid="stExpander"]{
            font-size= 3rem;
            font-style: bold;
        }
        .big-font {
            font-size: 2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Streamlit app
def main():
    st.markdown("<h1 style='text-align: center;'>Risk Calculator</h1>", unsafe_allow_html=True)
    # second title with a slight smaller font
    st.markdown('<head><link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"></head>', unsafe_allow_html=True)
    # 
    st.markdown("<h3 style='text-align: center;'>Enter your details</h3>", unsafe_allow_html=True)
    
    inputs_name = ['zip_code', 'age', 'address', 'income', 'gender', 'race', 'veteran_status', 'education']
    # Create 8 input fields for the user to enter values in 4 columns and 2 rows 
    # ending 4 input_name will be of dropdown type
    
    # storing inputs in a dictionary
    inputs = {}
    
    for i in range(0, 4, 4):
        columns = st.columns(4)
        for j, (column, input_name) in enumerate(zip(columns, inputs_name[i:i + 4])):
            with column:
                
                input_value = st.text_input(f"{input_name.capitalize()}", key=input_name, value="")
            
                inputs[input_name] = input_value
                # st.markdown("<h5 style='text-align: center;'>"+input_value+"</h5>", unsafe_allow_html=True)
    
    for i in range(4, len(inputs_name), 4):
        columns = st.columns(4)
        for j, (column, input_name) in enumerate(zip(columns, inputs_name[i:i + 4])):
            with column:
                if input_name=="gender":
                    input_value = st.selectbox(f"{input_name.capitalize()}", key=input_name, options=["","Male","Female"])
                    inputs[input_name] = input_value
                    # st.markdown("<h5 style='text-align: center;'>"+input_value+"</h5>", unsafe_allow_html=True)
                if input_name=="race":
                    input_value=st.selectbox(f"{input_name.capitalize()}", key=input_name, options=["","White", "Black", "Asian", "Hispanic", "Others"])
                    inputs[input_name] = input_value
                    # st.markdown("<h5 style='text-align: center;'>"+input_value+"</h5>", unsafe_allow_html=True)
                if input_name=="veteran_status":
                    input_value = st.selectbox(f"{input_name.capitalize()}", key=input_name, options=["","Yes", "No"])
                    inputs[input_name] = input_value
                    # st.markdown("<h5 style='text-align: center;'>"+input_value+"</h5>", unsafe_allow_html=True)
                if input_name=="education":
                    input_value = st.selectbox(f"{input_name.capitalize()}", key=input_name, options=["","Less than high school", "Post Secondary", "Professional Degree"])
                    inputs[input_name] = input_value
    
    
    parse_data=parse_inputs(inputs)
    feature_data=features_finder(**parse_data)
    # print(feature_data)
    calculate_risks,valid_variable_cnt, category_risks, cluster_risks = calculate_risk_scores(feature_data)
    
    # print(inputs)           
    # Button to trigger risk calculation
    if st.button("Calculate Risks"):
        # Calculate risks based on the input values
        risks = inputs
        
        # Display risks in 2 columns and rows
        display_risks(risks,category_risks, cluster_risks,calculate_risks,inputs)

# Function to calculate risks based on input values
def calculate_risksssss(inputs):
    # Replace this with your own risk calculation logic
    risks = [input_value for input_value in inputs]
    return risks

import streamlit as st

# Function to display risks in 2 columns and 6 rows
def display_risks(risks,category_risks, cluster_risks,calculate_risks,inputs):
    # Calculate the number of rows and columns
    num_rows = 6
    num_columns = 2
    risk_names=['Educational Challenges','Social Environmental Risk','Lifestyle','Transportation Risk','Technology Access Risk','Food Security','Housing Challenges','Climate Risk','Disease Risk','financial Risk','healthcare access risk']
    # risk_names2=['Educational Challenges','Social Environmental Risk','Lifestyle','Transportation Risk','Technology Access Risk','Food Security','Housing Challenges','Climate Risk','Disease Risk','financial risk','healthcare access risk']
    st.markdown("<h2 style='text-align: center;'>Risk ScoreCard</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'></h3>", unsafe_allow_html=True)
    icons_names=['fa fa-address-book','fas fa-user-friends','fas fa-glass-cheers','fa fa-truck','fas fa-laptop','fas fa-bread-slice','fas fa-house-user','fas fa-heartbeat','fas fa-water','fas fa-money-bill-wave','fas fa-briefcase-medical']
    headings=['Educational Challenges','Social Environmental Risk','Lifestyle Risk','Transportation Risk','Technology Access Risk','Food Security','Housing Challenges Risk','Climate Risk','Disease Risk','Financial Risk','Healthcare Access Risk']

    risk_action_df=pd.read_csv('risk_actions.csv')
    # get_suggested_actions,services=get_suggested_actions(risk,clusters,risk_action_df,94501)
    # Display all 11 risks in 2 columns and 6 rows along with their name from risk_names
    # print get_suggested_actions corresponding to each risk_names 
    # suggestions is of format {'risk_name': 'suggestions'}
    
    for i in range(0, len(risk_names), num_columns):
        row_risks = risk_names[i:i + num_columns]
        row_names = risk_names[i:i + num_columns]
        headings_names=headings[i:i + num_columns]
        # row_names2=risk_names2[i:i + num_columns]
        columns = st.columns(num_columns)
        count=0
        for j, (column, risk) in enumerate(zip(columns, row_risks)):
            with column:
                # if row_names[j]=="healthcare access risk":
                if category_risks[row_names[j]]=="High":
                    st.markdown(
                        """
                        <div style="display: flex; align-items: center;">
                            <i class="{icon}" style="color: white; font-size: 2rem; margin-right: 12rem;"></i>
                            <h5 style="text-align: center; margin: 0;">{risk_name}</h5>
                            <div>
                                <img src="{image_source}" style="width: 20px; height: 20px; margin-left: 5px; margin-top: -21px">
                            </div>
                        </div>
                        
                        """.format(icon=icons_names[i + j], risk_name=headings_names[j]+" : "+category_risks[row_names[j]], image_source="https://raw.githubusercontent.com/Manas2593/battery/master/c.png"),
                        unsafe_allow_html=True
                    ) 
                if category_risks[row_names[j]]=="Medium":
                    st.markdown(
                        """
                        <div style="display: flex; align-items: center;">
                            <i class="{icon}" style="color: white; font-size: 2rem; margin-right: 12rem;"></i>
                            <h5 style="text-align: center; margin: 0;">{risk_name}</h5>
                            <div>
                                <img src="{image_source}" style="width: 20px; height: 20px; margin-left: 5px; margin-top: -21px">
                            </div>
                        </div>
                        
                        """.format(icon=icons_names[i + j], risk_name=headings_names[j]+" : "+category_risks[row_names[j]], image_source="https://raw.githubusercontent.com/Manas2593/battery/master/b.png"),
                        unsafe_allow_html=True
                    )  
                if category_risks[row_names[j]]=="Low":
                    st.markdown(
                        """
                        <div style="display: flex; align-items: center;">
                            <i class="{icon}" style="color: white; font-size: 2rem; margin-right: 12rem;"></i>
                            <h5 style="text-align: center; margin: 0;">{risk_name}</h5>
                            <div style="height: fit-content">
                                <img src="{image_source}" style="width: 20px; height: 30px; margin-left: 5px;margin-top: 0px; margin-top: -21px">
                            </div>
                        </div>
                        
                        """.format(icon=icons_names[i + j], risk_name=headings_names[j]+" : "+category_risks[row_names[j]], image_source="https://raw.githubusercontent.com/Manas2593/battery/master/a.png"),
                        unsafe_allow_html=True
                    ) 
                # else :
                #     st.markdown(
                #         """
                #         <div style="display: flex; align-items: center;">
                #             <i class="{icon}" style="color: white; font-size: 2rem; margin-right: 12rem;"></i>
                #             <h5 style="text-align: center; margin: 0;">{risk_name}</h5>
                #         </div>
                #         """.format(icon=icons_names[i + j], risk_name=row_names[j]+" : "+category_risks[row_names[j]]),
                #         unsafe_allow_html=True
                #     )
                clusters=[]
                # sub cluster
                row_count_subrisk = 0
                with st.expander("View Risk Distribution"):
                    chart_row = st.columns(3)
                    # print("\n category_risk\n",category_risks)
                    # print("\n category_risk\n",category_risks[row_names2[j]])
                    sub_cluster_risk = calculate_risks[row_names[j]]
                    for a in sub_cluster_risk:
                        if row_count_subrisk==3:
                            row_count_subrisk=0
                        if cluster_risks[a] == "Medium":
                            with chart_row[row_count_subrisk]:
                                st.write(make_donut(50, "Risk", "orange", f"{cluster_risks[a]}"))
                                st.markdown("<h7 style='text-align: center;'>"+a+"</h7>", unsafe_allow_html=True)
                                clusters.append(a)
                                row_count_subrisk+=1
                                
                        if cluster_risks[a] == "High":
                            with chart_row[row_count_subrisk]:
                                st.write(make_donut(100, "Risk", "red", f"{cluster_risks[a]}"))
                                st.markdown("<h7 style='text-align: center;'>"+a+"</h7>", unsafe_allow_html=True)
                                clusters.append(a)
                                row_count_subrisk+=1
                    # Display donut chart for each risk
                    # with chart_row[0]:
                    #     st.write(make_donut(50, "Risk", "red"))
                    # with chart_row[1]:
                    #     st.write(make_donut(70, "Risk", "green"))
                    
                # print("\n\n clusters \n\n",clusters)
                with st.expander("Suggested Actions"):
                    # adding a suggestions dropdown with some suggestions in bullet points
                    risk=risk_names[i+j]

                    # printing in bullet point list form
                    if count==0:
                        for cluster in clusters:
                            get_suggested_action,services=get_suggested_actions(risk,clusters,risk_action_df,inputs['zip_code'])
                            # print("\n\n get_suggested_action \n\n",get_suggested_action)
                            # st.write(get_suggested_action)
                            # printing in bullet point list form
                            st.markdown("<h5>"+cluster+" Risk</h5>", unsafe_allow_html=True)
                            to_print="<h6>"+get_suggested_action[cluster]+"</h6>"
                            st.markdown(to_print, unsafe_allow_html=True)
                            # st.markdown(get_suggested_action[cluster])
                        count+=1
                # putting keys of services in clusters
                
                
                # print("clusters",clusters)
                with st.expander("Services"):
                    # adding a suggestions dropdown with some suggestions in bullet points
                    # risk='Transportation Risk'
                    # clusters=['Transportation Services']
                    # printing in bullet point list form
                    get_suggested_action,services=get_suggested_actions(risk,clusters,risk_action_df,inputs['zip_code'])
                    # print("services",services)
                    keys_set=[]
                    if services is not None:
                        for key in services.keys():
                            if services[key] is not None: 
                                keys_set.append(key)
                        
                        for key_value in keys_set:
                                
                                # st.write(services[cluster])
                                # printing in bullet point list form
                                # print(services)
                                # to_print="<ul><li>"+services[cluster]+"</li></ul>"
                                # st.markdown(to_print, unsafe_allow_html=True
                                # )
                                
                            st.markdown(key_value)
                                # services[cluster] is [['string','string'],['string','string']] , want to concatenate all strings and print
                            
                            # print("\n services \n",services)
                            for service in services[key_value]:
                                    # combining all strings
                                final_service=', '.join(service)
                                    # final_service=""
                                    # for s in service:
                                    #     final_service+=s
                                    # final_service="<h9>"+final_service+"</h9>"
                                st.markdown(
                                    """
                                    <div style="display: flex; align-items: center;">
                                        <h6 style="text-align: center; margin: 0;">{risk_name}</h6>
                                    </div>
                                    """.format(risk_name=final_service),
                                    unsafe_allow_html=True
                                )
                                    
                            st.markdown("<h5 style='text-align: center;'></h5>", unsafe_allow_html=True)
                                    # st.markdown(final_service, unsafe_allow_html=True)
                                # st.markdown(services[cluster])
              
                    # get_suggested_action,services=get_suggested_actions(risk,clusters,risk_action_df,94501)
                    
                    # with st.expander("Suggested Actions"):
                    #     st.write(get_suggested_action)
                    
                     
                
        # putting a blank space between the rows
        st.markdown("<h3 style='text-align: center;'> </h3>", unsafe_allow_html=True)
        
        
    with st.expander("Life Expectancy"):
        
            
                    # adding a suggestions dropdown with some suggestions in bullet points
        get_data=get_life_data(inputs['zip_code'])
        get_life_data_=get_life_expectancy_risks(get_data)
        
        if len(get_life_data_)>0:
                    # printing in bullet point list form
                    # st.markdown("<h5>Life Expectancy</h5>", unsafe_allow_html=True)
            # printing nested list in bullet point form
            st.markdown("<h6>Life Expectancy Risks found in age groups:</h6>", unsafe_allow_html=True)
            
            for life_data_ in get_life_data_:
                to_print="<li>"+str(life_data_).replace("[", "").replace("]", "")+"</li>"
                st.markdown(to_print, unsafe_allow_html=True)
            
        else:
            to_print="<ul><li>No major Life Expectancy risk</li></ul>" 
            st.markdown(to_print, unsafe_allow_html=True)
    
    with st.expander("Disease Risks"):
        
            
                    # adding a suggestions dropdown with some suggestions in bullet points
        get_data_=get_health_data(inputs['zip_code'])
        get_health_data_=get_health_risks(get_data_)
        # print("\n\n health \n\n", get_health_data_)
        
        # if get_health_data_ is not empty then print the health risks
       
        if len(get_health_data_)==0:
                    # printing in bullet point list form
                    # st.markdown("<h5>Life Expectancy</h5>", unsafe_allow_html=True)
            # printing nested list in bullet point form
            to_print="<ul><li>No major Health risk</li></ul>" 
            st.markdown(to_print, unsafe_allow_html=True) 
            
        else:
            
            st.markdown("<h6>Health Risks found:</h6>", unsafe_allow_html=True)           
            for health_data_ in get_health_data_:
                to_print="<li>"+health_data_+"</li>"
                st.markdown(to_print, unsafe_allow_html=True)

        

def make_donut(input_response, input_text, input_color, input_show):
    if input_color == 'blue':
        chart_color = ['#29b5e8', '#155F7A']
    if input_color == 'green':
        chart_color = ['#27AE60', '#12783D']
    if input_color == 'orange':
        chart_color = ['#F39C12', '#875A12']
    if input_color == 'red':
        chart_color = ['#E74C3C', '#781F16']
    
    source = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100-input_response, input_response]
    })
    source_bg = pd.DataFrame({
        "Topic": ['', input_text],
        "% value": [100, 0]
    })
    
    plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
        theta="% value",
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=130, height=130)
    
    text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=25, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_show}'))
    plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
        theta="% value",
        color=alt.Color("Topic:N",
                        scale=alt.Scale(
                            domain=[input_text, ''],
                            range=chart_color),
                        legend=None),
    ).properties(width=130, height=130)
    
    layer_chart = (plot_bg + plot + text).properties(background="transparent")
    return layer_chart

if __name__ == "__main__":
    main()
