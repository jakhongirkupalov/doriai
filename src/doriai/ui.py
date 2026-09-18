"""Streamlit sahifalari uchun umumiy yordamchilar (keshlangan yuklagichlar va vizuallar)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st
from rdkit.Chem import Draw

from doriai.chem.molecule import parse_smiles
from doriai.models.admet import ADMETPredictor
from doriai.repurposing.library import DrugLibrary

EXAMPLES = {
    "Aspirin": "CC(=O)Oc1ccccc1C(=O)O",
    "Ibuprofen": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
    "Sildenafil": "CCCc1nn(C)c2c1nc([nH]c2=O)-c1cc(ccc1OCC)S(=O)(=O)N1CCN(C)CC1",
    "Gefitinib (EGFR ingibitori)": "COc1cc2ncnc(Nc3ccc(F)c(Cl)c3)c2cc1OCCCN1CCOCC1",
    "Kurkumin (tabiiy birikma)": "COc1cc(/C=C/C(=O)CC(=O)/C=C/c2ccc(O)c(OC)c2)ccc1O",
}

DISCLAIMER = ("⚠️ DoriAI — tadqiqot uchun qaror qabul qilishni qo'llab-quvvatlovchi prototip. "
              "Bashoratlar laboratoriya va klinik tekshiruvni almashtirmaydi.")


def page_setup(title: str, icon: str = "💊") -> None:
    st.set_page_config(page_title=f"DoriAI · {title}", page_icon=icon, layout="wide")
    st.title(f"{icon} {title}")


@st.cache_resource(show_spinner="ADMET modellari yuklanmoqda...")
def get_predictor() -> ADMETPredictor:
    return ADMETPredictor()


@st.cache_resource(show_spinner="Dorilar kutubxonasi tayyorlanmoqda...")
def get_library() -> DrugLibrary:
    return DrugLibrary.load()


def mol_image(smiles: str, size=(420, 320)):
    mol = parse_smiles(smiles)
    return Draw.MolToImage(mol, size=size) if mol is not None else None


def score_gauge(score: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score, number={"suffix": " / 100"},
        title={"text": "DoriAI Score"},
        gauge={"axis": {"range": [0, 100]},
               "bar": {"color": "#1f77b4"},
               "steps": [{"range": [0, 50], "color": "#f8d7da"},
                         {"range": [50, 70], "color": "#fff3cd"},
                         {"range": [70, 100], "color": "#d4edda"}]},
    ))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=10))
    return fig


def smiles_input(key: str, default: str = "Aspirin") -> str:
    choice = st.selectbox("Namuna molekula", ["— o'zim kiritaman —", *EXAMPLES],
                          index=list(EXAMPLES).index(default) + 1, key=f"{key}_ex")
    value = EXAMPLES.get(choice, "")
    return st.text_input("SMILES", value=value, key=f"{key}_smi_{choice}",
                         help="Molekulaning matnli ifodasi. PubChem yoki ChEMBL'dan nusxa oling.")
