#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import json
from PIL import Image
#######################
# Page configuration
st.set_page_config(
    page_title="Mwea Irrigation Scheme Irrigation Performance Indicators by Block Dashboard",
    page_icon="👈",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# CSS styling
st.markdown("""
<style>

[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}

[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}

[data-testid="stMetric"] {
    background-color: #1c1b1b;
    text-align: center;
    padding: 2px 0;
}

[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}

[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}

[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}
            
img[data-testid="stLogo"] {
            height: 4.5rem;
}

</style>
""", unsafe_allow_html=True)

#######################
# Load data
dfm = pd.read_csv(r'data/IPI_by_section_and_blocks_Mwea_Kenya.csv')
with open(r'data/Mwea_blocks.json') as response:
    geo = json.load(response)
dfm.columns = [x.replace('_', ' ') for x in dfm.columns]
logo_wide = r'data/logo_wide.png'
logo_small = r'data/logo_small.png'

IPA_description = {
    "beneficial fraction": "Beneficial fraction (BF) is the ratio of the water that is consumed as transpiration\
         compared to overall field water consumption (ETa). ${\\footnotesize BF = T_a/ET_a}$. \
         It is a measure of the efficiency of on farm water and agronomic practices in use of water for crop growth.",
    "crop water deficit": "crop water deficit (CWD) is measure of adequacy and calculated as the ration of seasonal\
        evapotranspiration to potential or reference evapotranspiration ${\\footnotesize CWD= ET_a/ET_p}$",
    "relative water deficit": "relative water deficit (RWD) is also a measure of adequacy which is 1 minus crop water\
          deficit ${\\footnotesize RWD= 1-ET_a/ET_p}$",
    "total seasonal biomass production": "total seasonal biomass production (TBP) is total biomass produced in tons. \
        ${\\footnotesize TBP = NPP * 22.222) / 1000}$",
    "seasonal yield": "seasonal yield is the yield in a season which is crop specific and calculated using \
        the TBP and yield factors such as moisture content, harvest index, light use efficiency correction \
            factor and above ground over total biomass production ratio (AOT) \
                ${\\footnotesize Yiled = TBP*HI*AOT*f_c/(1-MC)}$",
    "crop water productivity": "crop water productivity (CWP) is the seasonal yield per the amount of water \
        consumed in ${\\footnotesize kg/m^3}$"

}
# @st.cache_data(ttl=300)
def load_image(image_name: str) -> Image:
    """Displays an image.

    Parameters
    ----------
    image_name : str
        Local path of the image.

    Returns
    -------
    Image
        Image to be displayed.
    """
    return Image.open(image_name)
#######################
# Sidebar
with st.sidebar:
   
    # st.sidebar.image(load_image(logo_path), use_column_width=True)
    st.logo(load_image(logo_wide), size="large", link='https://www.un-ihe.org/', icon_image=load_image(logo_small))
    st.title('Mwea Irrigation Performance Indicators')
   
    year_list = list(dfm.year.unique())[::-1]
    indicator_list = list(dfm.columns.unique())[1:-2][::-1]
    
    selected_year = st.selectbox('Select a year', year_list)

    selected_indicator = st.selectbox('Select an indicator', indicator_list)
    st.write(IPA_description[selected_indicator])
   
    df_selected = dfm[dfm.year == selected_year][['section name', selected_indicator, "block"]]
    df_selected_sorted = df_selected.sort_values(by=selected_indicator, ascending=False)

#######################

# Plots

# Choropleth map
def make_Choroplethmapbox(geo, df, year, unit ):
    # Geographic Map
    col_name = df.columns[1]
    df['indicator'] = col_name
    fig = px.choropleth_mapbox(df,  # dataframe to plothangi veri seti
                                geojson=geo,  # the geolocation
                                locations=df['block'],
                                featureidkey="properties.block",
                                color=col_name,  
                                color_continuous_scale="Viridis",  #
                                range_color=(df[col_name].min(),
                                            df[col_name].max()),
                                
                                center={"lat": -0.69306, "lon":  37.35908},
                                mapbox_style="carto-darkmatter",  # mapbox style
                                template='plotly_dark',
                                zoom=10.7,  # zoom level
                                opacity=0.9,  # opacity
                                custom_data=[df['section name'],
                                            df[col_name], 
                                            df['block'],
                                            df['indicator']] ,
                                width=600, height=400,
                                )
    fig.update_layout(title=f"Mapa of {col_name} for year {year}",
                        # title_x=0.5  # Title position
                        )
    # colrbar configuration
    fig.update_layout(
                        # coloraxis_colorbar_x=0.95,
                        coloraxis_colorbar_title=f'{col_name} [{unit}]', 
                        coloraxis_colorbar_title_side="right",
                        coloraxis_colorbar_thickness=15,
                    )
    # hver template
    hovertemp = '<i style="color:white;">Section:</i><b> %{customdata[0]}</b><br>'
    hovertemp += '<i>Block:</i><b> %{customdata[2]}</b><br>'
    hovertemp += "%{customdata[3]}: %{customdata[1]:,.2f}<br>"
    fig.update_traces(hovertemplate=hovertemp)
    fig.update_layout(margin={"r":0, "l":0, "b":0})
    # fig.show()
    return fig
  
# histogram plot
def make_alt_chart(df, indicator, section):
    title = alt.TitleParams(f'Average {selected_indicator} per block for years'
                            f' {df.year.iloc[0]} to {df.year.iloc[-1]}', anchor='start')
    chart = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('block:N', axis=None),
        y=f'{indicator}:Q',
        color='block:N',
        column='year:N'
    ).properties(width=100, height=120).configure_legend(
        orient='bottom',
        columns=15
    )
    return chart


def format_number(num):
    return f"{num:.2f}"

# Calculation year-over-year difference in metrix
def calculate_idicator_difference(input_df, indicator, input_year):
  selected_year_data = input_df[input_df['year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
  selected_year_data['indicator_difference'] = selected_year_data[indicator].sub(previous_year_data[indicator], fill_value=0)
  return pd.concat([selected_year_data['block'], selected_year_data[indicator], selected_year_data.indicator_difference], axis=1).sort_values(by="indicator_difference", ascending=False)

#######################
# Dashboard Main Panel
col = st.columns((4.5, 1.0, 2), gap='medium')

with col[1]:
    st.markdown('###### Gains/Losses from previous year')

    input_df = dfm[['year', 'block', selected_indicator]]
    df_indicator_difference_sorted = calculate_idicator_difference(input_df, selected_indicator, selected_year)
 

    if selected_year > dfm['year'].min():
        first_block = df_indicator_difference_sorted['block'].iloc[0]
        first_block_indicator = format_number(df_indicator_difference_sorted[selected_indicator].iloc[0])
        first_block_delta = format_number(df_indicator_difference_sorted.indicator_difference.iloc[0])

        sec_name = dfm.loc[dfm['block'] == first_block, 'section name'].iloc[0]
        first_block = f'{first_block} in {sec_name}'
    else:
        first_block = '-'
        first_block_indicator = '-'
        first_block_delta = ''
    st.metric(label=first_block, value=first_block_indicator, delta=first_block_delta)

    if selected_year > dfm['year'].min():
        last_block = df_indicator_difference_sorted['block'].iloc[-1]
        last_block_indicator = format_number(df_indicator_difference_sorted[selected_indicator].iloc[-1])   
        last_block_delta = format_number(df_indicator_difference_sorted.indicator_difference.iloc[-1])  
        sec_name = dfm.loc[dfm['block'] == last_block, 'section name'].iloc[0]
        last_block = f'{last_block} in {sec_name}' 
    else:
        last_block = '-'
        last_block_indicator = '-'
        last_block_delta = ''
    st.metric(label=last_block, value=last_block_indicator, delta=last_block_delta)


with col[0]:
    st.markdown('###### Indicator Map and Chart')
    
    units = {'beneficial fraction':'-', 'crop water deficit': '-',
       'relative water deficit': '-', 'total seasonal biomass production': 'ton',
       'seasonal yield': 'ton/ha', 'crop water productivity': 'kg/m<sup>3</sup>'}

    choropleth = make_Choroplethmapbox(geo, df_selected, selected_year, units[selected_indicator] )
    st.plotly_chart(choropleth, use_container_width=True)

    st.write("")
    dfm_var = dfm[['year', selected_indicator,'section name', 'block']]
    for section in dfm_var['section name'].unique():
        df_section = dfm_var.loc[dfm_var['section name'] == section]
        chart = make_alt_chart(df_section, selected_indicator, section)
        st.altair_chart(chart, use_container_width=False)
    

with col[2]:
    st.markdown('###### Indictaor ranked')

    st.dataframe(df_selected_sorted,
                 column_order=("block", selected_indicator),
                 hide_index=True,
                 width=None,
                 column_config={
                    "block": st.column_config.TextColumn(
                        "Name",
                    ),
                    selected_indicator: st.column_config.ProgressColumn(
                        selected_indicator,
                        format="%.2f",
                        min_value=0,
                        max_value=max(df_selected_sorted[selected_indicator]),
                     )}
                 )
    
    with st.expander('About', expanded=False):
        st.write('''
            - Irrigation Performance Indicators are calcukated from data: [FAO WaPOR data](https://www.fao.org/in-action/remote-sensing-for-water-productivity/wapor-data/en).
            - :orange[**Gains/Losses**]: sections with high and low increase in the selected indicator from the previous year.
            - :orange[**Indicator ranked**]: shows the ranking of the section based on the selected indicator.
            ''')
