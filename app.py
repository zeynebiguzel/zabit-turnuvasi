import streamlit as st
import pandas as pd

# 1. Sayfa Ayarları
st.set_page_config(page_title="Zabıta Turnuvası Maçkolik", layout="wide")

# 2. Gelişmiş Maçkolik Tasarımı (CSS)
st.markdown("""
    <style>
    .main { background-color: #f2f2f2; }
    .grup-baslik { 
        background-color: #ffffff; color: #333; padding: 10px; 
        border-left: 5px solid #00a65a; border-radius: 3px;
        font-weight: bold; margin-bottom: 5px; box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
    }
    .fikstur-tarih {
        background-color: #eeeeee; padding: 5px 15px;
        font-weight: bold; font-size: 14px; color: #555;
        margin-top: 15px; border-radius: 5px;
    }
    .mac-kart {
        background-color: white; padding: 10px;
        border-bottom: 1px solid #ddd; display: flex;
        align-items: center; justify-content: center;
    }
    .takim-isim { flex: 1; text-align: center; font-weight: 500; }
    .skor-kutu { 
        background-color: #f9f9f9; padding: 5px 15px; 
        border-radius: 5px; font-weight: bold; min-width: 60px; text-align: center;
        border: 1px solid #eee; margin: 0 20px;
    }
    .ms-etiket {
        background-color: #333; color: white; padding: 2px 8px;
        font-size: 12px; border-radius: 3px; margin-right: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Yardımcı Fonksiyonlar
def renklendir_siralam(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    styles.iloc[0:2, :] = 'background-color: #d4edda;' 
    return styles

def verileri_hazirla():
    try:
        sheet_id = "1PDX2QyGBvqkdtVEhZSxop-8azj1LeDv78G6zR4X1ZAw"
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        takimlar = pd.read_excel(sheet_url, sheet_name='Sheet1')
        fikstur = pd.read_excel(sheet_url, sheet_name='fikstür')
        takimlar['Takım'] = takimlar['Takım'].str.strip()
        fikstur['Ev_Sahibi'] = fikstur['Ev_Sahibi'].str.strip()
        fikstur['Deplasman'] = fikstur['Deplasman'].str.strip()
        takimlar[['O', 'G', 'B', 'M', 'AG', 'YG', 'AV', 'P']] = 0
        oynanan = fikstur.dropna(subset=['Ev_Skor', 'Dep_Skor'])
        for _, mac in oynanan.iterrows():
            ev, dep = mac['Ev_Sahibi'], mac['Deplasman']
            ev_g, dep_g = int(mac['Ev_Skor']), int(mac['Dep_Skor'])
            e_idx = takimlar[takimlar['Takım'] == ev].index[0]
            d_idx = takimlar[takimlar['Takım'] == dep].index[0]
            takimlar.at[e_idx, 'O'] += 1; takimlar.at[d_idx, 'O'] += 1
            takimlar.at[e_idx, 'AG'] += ev_g; takimlar.at[e_idx, 'YG'] += dep_g
            takimlar.at[d_idx, 'AG'] += dep_g; takimlar.at[d_idx, 'YG'] += ev_g
            if ev_g > dep_g:
                takimlar.at[e_idx, 'G'] += 1; takimlar.at[e_idx, 'P'] += 3; takimlar.at[d_idx, 'M'] += 1
            elif dep_g > ev_g:
                takimlar.at[d_idx, 'G'] += 1; takimlar.at[d_idx, 'P'] += 3; takimlar.at[e_idx, 'M'] += 1
            else:
                takimlar.at[e_idx, 'B'] += 1; takimlar.at[d_idx, 'B'] += 1
                takimlar.at[e_idx, 'P'] += 1; takimlar.at[d_idx, 'P'] += 1
        takimlar['AV'] = takimlar['AG'] - takimlar['YG']
        return takimlar, fikstur
    except Exception as e:
        st.error(f"Google Sheets bağlantı hatası: {e}")
        return None, None

# 4. Uygulama Başlangıcı
st.title("Zabıta Dairesi Başkanlığı Turnuvası")
guncel_takimlar, df_fikstur = verileri_hazirla()

if guncel_takimlar is not None:
    tab1, tab2, tab3 = st.tabs(["PUAN DURUMU", "FİKSTÜR", "SON 16"])

    with tab1:
        gruplar = sorted(guncel_takimlar['Grup'].unique())
        for i in range(0, len(gruplar), 2):
            c1, c2 = st.columns(2)
            for j, col in enumerate([c1, c2]):
                if i + j < len(gruplar):
                    g = gruplar[i+j]
                    with col:
                        st.markdown(f'<div class="grup-baslik">GRUP {g}</div>', unsafe_allow_html=True)
                        g_df = guncel_takimlar[guncel_takimlar['Grup'] == g].sort_values(by=['P', 'AV', 'AG'], ascending=False).reset_index(drop=True)
                        g_df.index += 1
                        st.dataframe(
                            g_df[['Takım', 'O', 'G', 'B', 'M', 'P', 'AV']].style.apply(renklendir_siralam, axis=None),
                            use_container_width=True,
                            hide_index=False
                        )
                        st.caption(" 🟢 Son 16 turuna yükselir.")

    with tab2:
        # Tarih formatını Gün.Ay.Yıl şekline getiriyoruz
        df_fikstur['Maç Tarihi'] = pd.to_datetime(df_fikstur['Maç Tarihi'], errors='coerce').dt.strftime('%d.%m.%Y')
        tarihler = df_fikstur['Maç Tarihi'].dropna().unique()

        for tarih in tarihler:
            st.markdown(f'<div class="fikstur-tarih">{tarih}</div>', unsafe_allow_html=True)
            gunun_maclari = df_fikstur[df_fikstur['Maç Tarihi'] == tarih]
            
            for _, mac in gunun_maclari.iterrows():
                ev_skor = int(mac['Ev_Skor']) if pd.notna(mac['Ev_Skor']) else None
                dep_skor = int(mac['Dep_Skor']) if pd.notna(mac['Dep_Skor']) else None
                skor_metni = f"{ev_skor} - {dep_skor}" if ev_skor is not None else "v"
                ms_durumu = "MS" if ev_skor is not None else "--"
                
                st.markdown(f"""
                    <div class="mac-kart">
                        <span class="ms-etiket">{ms_durumu}</span>
                        <div class="takim-isim" style="text-align:right;">{mac['Ev_Sahibi']}</div>
                        <div class="skor-kutu">{skor_metni}</div>
                        <div class="takim-isim" style="text-align:left;">{mac['Deplasman']}</div>
                    </div>
                """, unsafe_allow_html=True)

    with tab3:
        st.write("### Genel Puan Durumu")
        genel_tablo = guncel_takimlar.sort_values(by=['P', 'AV', 'AG'], ascending=False).reset_index(drop=True)
        genel_tablo.index += 1

        def genel_renklendir(df):
            styles = pd.DataFrame('', index=df.index, columns=df.columns)
            styles.iloc[0:16, :] = 'background-color: #d4edda;'
            return styles

        st.dataframe(
            genel_tablo[['Takım', 'Grup', 'O', 'G', 'B', 'M', 'P', 'AV']].style.apply(genel_renklendir, axis=None),
            use_container_width=True,
            hide_index=False
        )
        st.success("Yeşil bölgedeki takımlar bir üst tura yükselir.")

        st.write("---")
        st.write("### Otomatik Eşleşmeler")
        ilk_ikiler = {}
        for g in gruplar:
            siralam_grup = guncel_takimlar[guncel_takimlar['Grup'] == g].sort_values(by=['P', 'AV', 'AG'], ascending=False).reset_index(drop=True)
            if len(siralam_grup) >= 2:
                ilk_ikiler[g] = {'birinci': siralam_grup.iloc[0]['Takım'], 'ikinci': siralam_grup.iloc[1]['Takım']}

        if len(ilk_ikiler) >= 2:
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"A1: {ilk_ikiler.get('A', {'birinci': 'A1'})['birinci']} vs B2: {ilk_ikiler.get('B', {'ikinci': 'B2'})['ikinci']}")
                st.info(f"C1: {ilk_ikiler.get('C', {'birinci': 'C1'})['birinci']} vs D2: {ilk_ikiler.get('D', {'ikinci': 'D2'})['ikinci']}")
            with c2:
                st.info(f"B1: {ilk_ikiler.get('B', {'birinci': 'B1'})['birinci']} vs A2: {ilk_ikiler.get('A', {'ikinci': 'A2'})['ikinci']}")
                st.info(f"D1: {ilk_ikiler.get('D', {'birinci': 'D1'})['birinci']} vs C2: {ilk_ikiler.get('C', {'ikinci': 'C2'})['ikinci']}")
