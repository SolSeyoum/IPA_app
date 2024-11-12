#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import json
from PIL import Image
from shapely.geometry import Polygon, mapping
from shapely.ops import unary_union
#######################
# Page configuration
st.set_page_config(
    page_title="Mwea Irrigation Scheme Irrigation Performance Indicators by Sections Dashboard",
    page_icon="📈🌿",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# CSS styling
# st.markdown("""
# <style>

# [data-testid="block-container"] {
#     padding-left: 2rem;
#     padding-right: 2rem;
#     padding-top: 1rem;
#     padding-bottom: 0rem;
#     margin-bottom: -7rem;
# }

# [data-testid="stVerticalBlock"] {
#     padding-left: 0rem;
#     padding-right: 0rem;
# }

# [data-testid="stMetric"] {
#     background-color: #1c1b1b;
#     text-align: center;
#     padding: 2px 0;
# }

# [data-testid="stMetricLabel"] {
#   display: flex;
#   justify-content: center;
#   align-items: center;
# }

# [data-testid="stMetricDeltaIcon-Up"] {
#     position: relative;
#     left: 38%;
#     -webkit-transform: translateX(-50%);
#     -ms-transform: translateX(-50%);
#     transform: translateX(-50%);
# }

# [data-testid="stMetricDeltaIcon-Down"] {
#     position: relative;
#     left: 38%;
#     -webkit-transform: translateX(-50%);
#     -ms-transform: translateX(-50%);
#     transform: translateX(-50%);
# }
            
# img[data-testid="stLogo"] {
#             height: 4.5rem;
# }

# </style>
# """, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .css-1jc7ptx, .e1ewe7hr3, .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_, .viewerBadge_link__1S137,
    .viewerBadge_text__1JaDK {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

#######################
# Load data
dfm = pd.read_csv(r'data/Mwea_IPA_stat_by_blocks.csv')
with open(r'data/Mwea_blocks.json') as response:
    geo = json.load(response)

# dfm.columns = [x.replace('_', ' ') for x in dfm.columns]
logo_wide = r'data/logo_wide.png'
logo_small = r'data/logo_small.png'

IPA_description = {
    "beneficial fraction": ":blue[Beneficial fraction (BF)] is the ratio of the water that is consumed as transpiration\
         compared to overall field water consumption (ETa). ${\\footnotesize BF = T_a/ET_a}$. \
         It is a measure of the efficiency of on farm water and agronomic practices in use of water for crop growth.",
    "crop water deficit": ":blue[crop water deficit (CWD)] is measure of adequacy and calculated as the ration of seasonal\
        evapotranspiration to potential or reference evapotranspiration ${\\footnotesize CWD= ET_a/ET_p}$",
    "relative water deficit": ":blue[relative water deficit (RWD)] is also a measure of adequacy which is 1 minus crop water\
          deficit ${\\footnotesize RWD= 1-ET_a/ET_p}$",
    "total seasonal biomass production": ":blue[total seasonal biomass production (TBP)] is total biomass produced in tons. \
        ${\\footnotesize TBP = (NPP * 22.222) / 1000}$",
    "seasonal yield": ":blue[seasonal yield] is the yield in a season which is crop specific and calculated using \
        the TBP and yield factors such as moisture content, harvest index, light use efficiency correction \
            factor and above ground over total biomass production ratio (AOT) \
                ${\\footnotesize Yiled = TBP*HI*AOT*f_c/(1-MC)}$",
    "crop water productivity": ":blue[crop water productivity (CWP)] is the seasonal yield per the amount of water \
        consumed in ${kg/m^3}$"
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

    st.logo(load_image(logo_wide), size="large", link='https://www.un-ihe.org/', icon_image=load_image(logo_small))
    st.title('Mwea Irrigation Performance Indicators')

    year_list = list(dfm.year.unique())[::-1]
    ll = list(dfm.columns.unique())[3:][::-1]
    indicator_lst = [' '.join(l.split('_')[:-1]) for l in ll]

    
    selected_year = st.selectbox('Select a year', year_list)
    indicator = st.selectbox('Select an indicator', set(indicator_lst))
    selected_indicator = f'{indicator.replace(' ', '_')}_mean'
    st.write(f'{IPA_description[indicator]}')
   
    df_selected = dfm[dfm.year == selected_year][['section_name', selected_indicator]]
    df_selected_sorted = df_selected.sort_values(by=selected_indicator, ascending=False)

    #aggregate by section
    df_section=df_selected_sorted.groupby('section_name').agg({selected_indicator:'mean'})#.rename(columns=d)
    df_section = df_section.sort_values(by=selected_indicator, ascending=False).reset_index()

#######################

# Plots

def indicator_title(indicator):
    stat_dict = {'std':'Standard deviation', 'min':'Minimum', 'max':'Maximum', 'mean':'Average'}
    lst = indicator.split('_')
    t1 = ' '.join(lst[:-1])
    t2 = f"{stat_dict[lst[-1]]} of {t1}" 
    return t1,t2

# merge block polygons to sections
def merge_blocks_to_sections(geo, df_section):
    new_features = []
    for i, name in enumerate(df_section.section_name):
        polygons = []
        to_combine = [f for f in geo["features"] if f["properties"]["section_name"]==name]
        # print(name)

        for feat in to_combine:
            lst = feat['geometry']['coordinates'][0]
            if isinstance(lst[0][0], list): # check if the geometry is 2d or 3d list
                lst = [e for sl in lst for e in sl]
            polygon = Polygon([ (coor[0], coor[1]) for coor in  lst ])
            polygons.append(polygon)

        new_geometry = mapping(unary_union(polygons)) # This line merges the polygones
        new_feature = dict(type='Feature', id=i, properties=dict(section_name=name),
                        geometry=dict(type=new_geometry['type'], 
                                        coordinates=new_geometry['coordinates']))
        new_features.append(new_feature)
    sections = dict(type='FeatureCollection', 
                    crs= dict(type='name', properties=dict(name='urn:ogc:def:crs:OGC:1.3:CRS84')), 
                    features=new_features)
    return sections

# Choropleth map
def make_Choroplethmapbox(geo, indicator, df, year, unit ):
  ylable, text = indicator_title(indicator)
  col_name = df.columns[0]
  df['indicator'] = ylable
  fig = px.choropleth_mapbox(df,  # dataframe to plothangi veri seti
                            geojson=geo,  # the geolocation
                            locations=df[col_name],
                            featureidkey=f"properties.{col_name}",
                            color=df[indicator],  
                            color_continuous_scale="Viridis",  #
                            range_color=(df[indicator].min(),
                                          df[indicator].max()),
                            center={"lat": -0.69306, "lon":  37.35908},
                            mapbox_style="carto-darkmatter",  # mapbox style
                            template='plotly_dark',
                            zoom=10.7,  # zoom level
                            opacity=0.9,  # opacity
                            custom_data=[df[col_name],
                                          df[indicator], 
                                          df['indicator']] ,
                              width=600, height=400,
                            )
  fig.update_layout(title=f"Map of {text} for year {year}",
                    title_x=0.5  # Title position
                    )
  # colrbar configuration
  fig.update_layout(
                      # coloraxis_colorbar_x=0.95,
                    coloraxis_colorbar_title=f'{ylable} [{unit}]', 
                    coloraxis_colorbar_title_side="right",
                    coloraxis_colorbar_thickness=15,
                  )
  # hver template
  hovertemp = '<i style="color:white;">Section:</i><b> %{customdata[0]}</b><br>'
  hovertemp += "%{customdata[2]}: %{customdata[1]:,.2f}<br>"
  fig.update_traces(hovertemplate=hovertemp)
  fig.update_layout(margin={"r":0, "l":0, "b":0})
  return fig

# histogram plot
def make_alt_chart(df,indicator):
    ylable, text = indicator_title(indicator)
    w = ylable.split()
    if(len(w)%2):
        w.append ("")
    ylable = [' '.join((w[2*i], w[2*i+1]))  for i in range(len(w)//2)]
    title = alt.TitleParams(f'Yearly {text} by section', anchor='middle')
    barchart = alt.Chart(df, title=title).mark_bar().encode(
        x=alt.X('section_name:N', axis=None),
        y=alt.Y(f'{indicator}:Q', title=ylable),
        color='section_name:N',
        column='year:N'
    ).properties(width=80, height=80).configure_legend(
        orient='bottom'
    )
    return barchart

def format_number(num):
    return f"{num:.2f}"

# Calculation year-over-year difference in metrix
def calculate_indicator_difference(input_df, indicator, input_year):
  selected_year_data = input_df[input_df['year'] == input_year].reset_index()
  previous_year_data = input_df[input_df['year'] == input_year - 1].reset_index()
  selected_year_data['indicator_difference'] = selected_year_data[indicator].sub(previous_year_data[indicator], fill_value=0)
  return pd.concat([selected_year_data['section_name'], selected_year_data[indicator], selected_year_data.indicator_difference], axis=1).sort_values(by="indicator_difference", ascending=False)


def history_df(df1, df2, idx_col):
    d2 = df1.pivot(index=idx_col, columns='year', values=selected_indicator).reset_index()
    d3 = df2.groupby(idx_col).agg({selected_indicator:'mean'}).reset_index()
    d4 = d3.merge(d2, on=idx_col, how = 'inner')
    d4[d4.columns[2:]]= d4[d4.columns[2:]].round(2)
    d4['history'] = d4[d4.columns[2:]].values.tolist()
    d4 = d4.drop(columns = d4.columns[2:-1])
    return d4.round(2)

#######################
# Dashboard Main Panel
col = st.columns((4, 1.0, 2.5), gap='medium')

with col[1]:
    st.markdown('###### Gains/Losses from previous year')

    input_df = dfm[['year','section_name', selected_indicator]]
    df_indicator_difference_sorted = calculate_indicator_difference(input_df, selected_indicator, selected_year)

    if selected_year > dfm['year'].min():
        first_section_name = df_indicator_difference_sorted['section_name'].iloc[0]
        first_section_name_indicator = format_number(df_indicator_difference_sorted[selected_indicator].iloc[0])
        first_section_name_delta = format_number(df_indicator_difference_sorted.indicator_difference.iloc[0])
    else:
        first_section_name = '-'
        first_section_name_indicator = '-'
        first_section_name_delta = ''
    st.metric(label=first_section_name, value=first_section_name_indicator, delta=first_section_name_delta)

    if selected_year > dfm['year'].min():
        last_first_section_name = df_indicator_difference_sorted['section_name'].iloc[-1]
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
       'seasonal yield': 'ton/ha', 'crop water productivity': 'kg/m<sup>3</sup>'}
    

    sections = merge_blocks_to_sections(geo, df_section)
    choropleth = make_Choroplethmapbox(sections,selected_indicator, df_section, selected_year, units[indicator] )
    st.plotly_chart(choropleth, use_container_width=True)

    st.write("")
    dfm_var = dfm[['year','section_name', selected_indicator]].groupby(['year','section_name'])
    dfm_var = dfm_var.agg({selected_indicator:'mean'}).reset_index()
    
    bar_chart = make_alt_chart(dfm_var, selected_indicator)
    st.altair_chart(bar_chart, use_container_width=False)
    

with col[2]:
    st.markdown('###### Indictaor ranked')
  
    ylable, text = indicator_title(selected_indicator)
    st.write(ylable)

    df = history_df(dfm_var, df_section, 'section_name')
    ymin = df.history.apply(lambda x: min(x)).min()
    ymax = df.history.apply(lambda x: max(x)).max()
    st.dataframe(df,
                 column_config={
                    "section_name": st.column_config.TextColumn(
                        "Name",
                    ),
                    selected_indicator: st.column_config.NumberColumn(
                    f"⭐{selected_year}",
                    help="value of the indicator for the selected year",
                    ),
                    "history": st.column_config.LineChartColumn(
                        "values since 2018", y_min=ymin, y_max=ymax,
                     help="value of the indicator for the years since 2018",   
                    )
                     },
                       hide_index=True,
                     
                 )
       
    with st.expander('About', expanded=True):
        st.write('''
            - Irrigation Performance Indicators are calcukated from data: [FAO WaPOR data](https://www.fao.org/in-action/remote-sensing-for-water-productivity/wapor-data/en).
            - :orange[**Gains/Losses**]: sections with high and low increase in the selected indicator from the previous year.
            - :orange[**Indicator ranked**]: shows the ranking of the section based on the selected indicator.
            ''')
