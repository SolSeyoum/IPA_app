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
    background-color: #393939;
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

</style>
""", unsafe_allow_html=True)


#######################
# Load data
dfm = pd.read_csv(r'data/IPI_by_section_and_blocks_Mwea_Kenya.csv')
# shp_file = r'data\Mwea.json'
with open(r'data/Mwea_blocks.json') as response:
    geo = json.load(response)
# shdf = gpd.read_file(shp_file ,crs="EPSG:32737")
# shdf.columns = [x.replace('_', ' ') for x in shdf.columns]
dfm.columns = [x.replace('_', ' ') for x in dfm.columns]
logo_path = r'data/logo.png'

IPA_description = {
     "beneficial fraction": "beneficial fraction (BF) is a measure of efficiency and calculated as the ratio of sum of transpiration to evapotranspiration.",
    "crop water deficit": "crop water deficit (CWD) is measure of adequacy and calculated as the ration of seasonal evapotranspiration to potential or reference evapotranspiration",
    "relative water deficit": "relative water deficit (RWD) is also a measure of adequacy which is 1 minus crop water deficit",
    "total seasonal biomass production": "total seasonal biomass production (TBP) is total biomass produced in tons",
    "seasonal yield": "seasonal yield is the yield in a season which is crop specific and calculated using the TBP and yield factors such as moisture content, harvest index, light use efficiency correction factor and above ground over total biomass production ratio (AOT)",
    "crop water productivity": "crop water productivity (CWP) is the seasonal yield per the amount of water consumed in kg/m3"

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

    st.sidebar.image(load_image(logo_path), use_column_width=True)
    st.title('Mwea Irrigation Performance Indicators')

    
    year_list = list(dfm.year.unique())[::-1]
    indicator_list = list(dfm.columns.unique())[1:-2][::-1]
    # indicator_list = [l.replace('_',' ') for l in indicator_list]
    
    selected_year = st.selectbox('Select a year', year_list)

    selected_indicator = st.selectbox('Select an indicator', indicator_list)

    # if (selected_indicator == 'crop water productivity'):
    st.write(IPA_description[selected_indicator])
   

    # selected_indicator = selected_indicator.replace(' ', '_')

    # df_selected = dfm[dfm.year == selected_year][['section name', selected_indicator]]
    df_selected = dfm[dfm.year == selected_year][['section name', selected_indicator, "block"]]
    df_selected_sorted = df_selected.sort_values(by=selected_indicator, ascending=False)

    # color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis']
    # selected_color_theme = st.selectbox('Select a color theme', color_theme_list)


#######################

# Plots

# def get_merged_df(dft, shdf):
#     df_merged  = shdf.merge(dft, on='section name', how='left')
#     gdf = gpd.GeoDataFrame(df_merged)
#     return gdf

# gdf = get_merged_df(df_selected_sorted, shdf)

# Choropleth map
def make_Choroplethmapbox(geodata, df_selected, year, unit ):
    # Geographic Map
    col_name = df_selected.columns[1]
    
    fig = go.Figure(
        go.Choroplethmapbox(
            geojson=geodata,
            locations=df_selected['block'],
            featureidkey="properties.block",
            z=df_selected[col_name],
            colorscale="Viridis",
            colorbar=dict(title=f'{col_name} [{unit}]', title_side="right",  x= 0.95, thickness=12,
                        ),

        )
    )

    fig.update_layout(
        template='plotly_dark',
        mapbox_style="carto-darkmatter",
        mapbox_zoom=10.5,
        mapbox_center={"lat": -0.69306, "lon":  37.35908},
        width=400,
        height=400,
        title=f"Mapa of {col_name} for year {year}",
    )

    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
    fig.update_layout(geo_bgcolor='rgba(0,0,0,0)')
    # fig.show()
    return fig


# histogram plot
def make_lat_chart(df, indicator, section):
    title = alt.TitleParams(f'Yearly {indicator} by block for {section}', anchor='middle')
    chart = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('block:N', axis=None),
        y=f'{indicator}:Q',
        color='block:N',
        column='year:N'
    ).properties(width=100, height=120)
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
        first_section_name = df_indicator_difference_sorted['block'].iloc[0]
        first_section_name_indicator = format_number(df_indicator_difference_sorted[selected_indicator].iloc[0])
        first_section_name_delta = format_number(df_indicator_difference_sorted.indicator_difference.iloc[0])
    else:
        first_section_name = '-'
        first_section_name_indicator = '-'
        first_section_name_delta = ''
    st.metric(label=first_section_name, value=first_section_name_indicator, delta=first_section_name_delta)

    if selected_year > dfm['year'].min():
        last_first_section_name = df_indicator_difference_sorted['block'].iloc[-1]
        last_section_name_indicator = format_number(df_indicator_difference_sorted[selected_indicator].iloc[-1])   
        last_section_name_delta = format_number(df_indicator_difference_sorted.indicator_difference.iloc[-1])   
    else:
        last_first_section_name = '-'
        last_section_name_indicator = '-'
        last_section_name_delta = ''
    st.metric(label=last_first_section_name, value=last_section_name_indicator, delta=last_section_name_delta)


with col[0]:
    st.markdown('###### Indicator Map and Chart')
    
    units = {'beneficial fraction':'-', 'crop water deficit': '-',
       'relative water deficit': '-', 'total seasonal biomass production': 'ton',
       'seasonal yield': 'ton/ha', 'crop water productivity': 'kg/m^3'}

    choropleth = make_Choroplethmapbox(geo, df_selected, selected_year, units[selected_indicator] )
    # choropleth = make_choropleth(df_selected_year, 'states_code', 'population', selected_color_theme)
    st.plotly_chart(choropleth, use_container_width=True)


    dfm_var = dfm[['year', selected_indicator,'section name', 'block']]
    for section in dfm_var['section name'].unique():
        df_section = dfm_var.loc[dfm_var['section name'] == section]
        chart = make_lat_chart(df_section, selected_indicator, section)
        st.altair_chart(chart, use_container_width=False)

    # dfm_var = dfm[['year', selected_indicator,'section name']]
    # dfm_var = dfm_var.pivot(index='year', columns='section name', values=selected_indicator)

    # dfm_var = dfm[['year', selected_indicator,'section name']]
    
    # bar_chart = make_barchart(dfm_var, selected_indicator)
    # # bar_chart = plot_df(dfm_var, selected_indicator)
    
    # # heatmap = make_heatmap(dfm, 'year', 'states', 'population', selected_color_theme)
    # st.altair_chart(bar_chart, use_container_width=False)
    

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
