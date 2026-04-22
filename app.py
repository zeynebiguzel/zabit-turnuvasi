import streamlit as st
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Zabıta Turnuvası Maçkolik", layout="wide")

# Maçkolik Tarzı Tasarım Dokunuşları (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTable { background-color: white; border-radius: 10px; }
    .grup-baslik { 
        background-color: #0e1133; 
        color: white; 
        padding: 10px; 
        border-radius: 5px;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 Zabıta Dairesi Başkanlığı Futbol Turnuvası")

# VERİ YÜKLEME VE HESAPLAMA MOTORU
def verileri_hazirla():
    dosya = 'turnuva_verileri.xlsx'
    takimlar = pd.read_excel(dosya, sheet_name='Sheet1')
    fikstur = pd.read_excel(dosya, sheet_name='fikstür')
    
    # Temizlik
    takimlar['Takım'] = takimlar['Takım'].str.strip()
    fikstur['Ev_Sahibi'] = fikstur['Ev_Sahibi'].str.strip()
    fikstur['Deplasman'] = fikstur['Deplasman'].str.strip()
    
    # Sıfırlama
    takimlar[['O', 'G', 'B', 'M', 'AG', 'YG', 'AV', 'P']] = 0
    
    # Hesaplama
    oynanan = fikstur.dropna(subset=['Ev_Skor', 'Dep_Skor'])
    for _, mac in oynanan.iterrows():
        ev, dep = mac['Ev_Sahibi'], mac['Deplasman']
        ev_g, dep_g = int(mac['Ev_Skor']), int(mac['Dep_Skor'])
        
        e_idx = takimlar[takimlar['Takım'] == ev].index[0]
        d_idx = takimlar[takimlar['Takım'] == dep].index[0]
        
        takimlar.at[e_idx, 'O'] += 1
        takimlar.at[d_idx, 'O'] += 1
        takimlar.at[e_idx, 'AG'] += ev_g
        takimlar.at[e_idx, 'YG'] += dep_g
        takimlar.at[d_idx, 'AG'] += dep_g
        takimlar.at[d_idx, 'YG'] += ev_g
        
        if ev_g > dep_g:
            takimlar.at[e_idx, 'G'] += 1; takimlar.at[e_idx, 'P'] += 3; takimlar.at[d_idx, 'M'] += 1
        elif dep_g > ev_g:
            takimlar.at[d_idx, 'G'] += 1; takimlar.at[d_idx, 'P'] += 3; takimlar.at[e_idx, 'M'] += 1
        else:
            takimlar.at[e_idx, 'B'] += 1; takimlar.at[d_idx, 'B'] += 1
            takimlar.at[e_idx, 'P'] += 1; takimlar.at[d_idx, 'P'] += 1
            
    takimlar['AV'] = takimlar['AG'] - takimlar['YG']
    return takimlar, fikstur

# Uygulamayı Başlat
try:
    guncel_takimlar, df_fikstur = verileri_hazirla()
    
    # Sekmeler (Tabs)
    tab1, tab2, tab3 = st.tabs(["📊 CANLI PUAN DURUMU", "📅 FİKSTÜR VE SKORLAR", "🔥 SON 16"])

    with tab1:
        # Grupları 2'li yan yana gösterelim
        gruplar = sorted(guncel_takimlar['Grup'].unique())
        for i in range(0, len(gruplar), 2):
            col1, col2 = st.columns(2)
            for j, col in enumerate([col1, col2]):
                if i + j < len(gruplar):
                    g = gruplar[i+j]
                    with col:
                        st.markdown(f'<div class="grup-baslik">GRUP {g}</div>', unsafe_allow_html=True)
                        grup_df = guncel_takimlar[guncel_takimlar['Grup'] == g].sort_values(by=['P', 'AV', 'AG'], ascending=False)
                        # İndeks numarasını gizleyerek Maçkolik gibi gösterelim
                        st.dataframe(grup_df[['Takım', 'O', 'G', 'B', 'M', 'P', 'AV']], use_container_width=True, hide_index=True)

    with tab2:
        st.write("### Turnuva Maç Programı")
        secili_grup = st.selectbox("Filtrelemek istediğiniz grubu seçin:", ["Hepsi"] + gruplar)
        
        filtreli_fikstur = df_fikstur if secili_grup == "Hepsi" else df_fikstur[df_fikstur['Grup'] == secili_grup]
        
        # Fikstür görünümü
        st.table(filtreli_fikstur[['Grup', 'Ev_Sahibi', 'Ev_Skor', 'Dep_Skor', 'Deplasman', 'Maç Tarihi']])

    with tab3:
        st.info("Grup maçları tamamlandığında, her grubun ilk 2 takımı otomatik olarak buraya düşecek.")

except Exception as e:
    st.error(f"Hata: {e}")
    st.info("Lütfen Excel dosyanızın 'fikstür' ve 'Sheet1' sayfalarının doğru olduğundan emin olun.")
