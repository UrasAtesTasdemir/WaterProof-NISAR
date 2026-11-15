"""Textured navigation globe. Historical Earth context, never NISAR imagery."""
from pathlib import Path
import streamlit as st
from streamlit.components.v1 import declare_component
from src.i18n import t


def render_earth_globe(lat,lon,places):
    component=declare_component('waterproof_earth',path=str(Path(__file__).resolve().parents[1]/'assets/earth_globe'))
    picked=component(lat=float(lat),lon=float(lon),markers=places,hint=t('globe.hint'),
                     zoom_in=t('globe.zoom_in'),zoom_out=t('globe.zoom_out'),reset=t('globe.reset'),
                     label=t('globe.label'),error=t('globe.error'),default=None,key='ex_globe')
    st.caption(t('globe.source'))
    return picked
