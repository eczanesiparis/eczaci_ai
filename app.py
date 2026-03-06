import streamlit as st
import os
from dotenv import load_dotenv
import re

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.chains.question_answering import load_qa_chain
from langchain.chains.llm import LLMChain

# --- 1. Başlangıç Ayarları ---
st.set_page_config(page_title="Eczacı AI Sohbet Asistanı", layout="wide")
st.title("💊 Eczacı AI Sohbet Asistanı")



@st.cache_resource
def kaynaklari_yukle():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key: st.error("OpenAI API anahtarı bulunamadı."); return None, None, None
    
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)
    try:
        sut_db = Chroma(persist_directory='chroma_db', embedding_function=embeddings)
    except Exception as e: st.error(f"SUT DB yüklenemedi: {e}"); sut_db = None
    try:
        prospektus_db = Chroma(persist_directory='prospektus_db', embedding_function=embeddings)
    except Exception as e: st.error(f"Prospektüs DB yüklenemedi: {e}"); prospektus_db = None
        
    llm = ChatOpenAI(model_name="gpt-5-mini", temperature=0, openai_api_key=api_key)
    
    return sut_db, prospektus_db, llm

sut_db, prospektus_db, llm = kaynaklari_yukle()

# --- 2. GÜNCELLENMİŞ GÖREV TANIMI ŞABLONLARI ---

# MAP AŞAMASI İÇİN GÖREV TANIMI (Daha Detaylı)
map_prompt_template = """
Sana aşağıda bir belgeden alınan bir metin parçası (CONTEXT) ve bir soru (QUESTION) verilecek.
Görevin, CONTEXT içinde QUESTION ile ilgili olan TÜM bilgileri (koşullar, dozlar, süreler, istisnalar, hasta grupları vb.) içeren DETAYLI bir özet çıkarmaktır.
HİÇBİR detayı atlamadığından emin ol.
Eğer CONTEXT içinde soruyla ilgili hiçbir bilgi yoksa, "Alakasız bilgi." diye cevap ver.
Kesinlikle kendi bilgini kullanma veya tahmin yürütme.

CONTEXT:
{context}

QUESTION:
{question}

Detaylı İlgili Bilgi Özeti:""" # Çıktı başlığı da güncellendi
MAP_PROMPT = PromptTemplate.from_template(map_prompt_template)

# REDUCE AŞAMASI İÇİN GÖREV TANIMI (Daha Detaylı)
combine_prompt_template = """
Sana bir sohbet geçmişi (chat_history), bir soru (question) ve bu soruya yanıt olabilecek bir dizi özetlenmiş metin (SUMMARIES) veriliyor.
Görevin, bu özetlerdeki HER BİR detayı kullanarak soruya EKSİKSİZ, kapsamlı, doğru ve anlaşılır bir final cevabı oluşturmaktır.
Cevabını oluştururken SADECE sana verilen SUMMARIES metinlerini kullan. Metin dışına ASLA çıkma.
Eğer SUMMARIES içinde yeterli bilgi yoksa veya sadece "Alakasız bilgi." içeriyorsa, "Verilen metinlerde bu soruya net bir cevap bulunmamaktadır." de.
Cevabını Türkçe, anlaşılır ve mümkünse maddeler halinde yaz.

CHAT HISTORY:
{chat_history}
QUESTION:
{question}
SUMMARIES:
{summaries}

Eksiksiz Nihai Cevap (Türkçe):""" # Çıktı başlığı da güncellendi
COMBINE_PROMPT = PromptTemplate.from_template(combine_prompt_template)

condense_question_template = "Sohbet geçmişi ve takip sorusu verildiğinde, onu tam bir soruya dönüştür.\n\nChat History:\n{chat_history}\nFollow Up Input: {question}\nStandalone question:"
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(condense_question_template)

# --- İlaç Bilgisi Genişletme Fonksiyonu ---
@st.cache_data
def ilac_bilgisini_genislet(_llm, ilac_adi):
    # ... (Bu fonksiyon aynı kalıyor) ...
    prompt = PromptTemplate.from_template(
        "'{ilac_adi}' ilacının Türkiye'deki yaygın bilinen etken maddesini ve ait olduğu ana farmakolojik sınıfı (örn: Statin, Antibiyotik, NSAİİ) kısa ve net bir şekilde söyle. Sadece etken madde ve sınıf adını ver, başka açıklama yapma. Örneğin: atorvastatin, Statin"
    )
    chain = LLMChain(llm=_llm, prompt=prompt)
    try:
        response = chain.invoke({"ilac_adi": ilac_adi})
        parts = response['text'].split(',')
        etken_madde = parts[0].strip() if len(parts) > 0 else None
        ilac_sinifi = parts[1].strip() if len(parts) > 1 else None
        return etken_madde, ilac_sinifi
    except Exception as e:
        print(f"İlaç bilgisi genişletme hatası: {e}")
        return None, None

def ilac_adi_tespit_et(soru):
     # ... (Bu fonksiyon aynı kalıyor) ...
     match = re.search(r'\b[A-Z][a-zA-Z-]+\b', soru)
     if match: return match.group(0)
     return None

# --- 3. Arayüz ---
if sut_db and prospektus_db and llm:
    tab1, tab2 = st.tabs(["⚕️ İlaç Asistanı Sohbeti", "📄 SUT Asistanı Sohbeti"])

    if "ilac_memory" not in st.session_state: st.session_state.ilac_memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')
    if "sut_memory" not in st.session_state: st.session_state.sut_memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True, output_key='answer')

    def create_conversational_chain(vectorstore, memory):
        question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
        # GÜNCELLENMİŞ görev tanımlarını doc_chain'e veriyoruz
        doc_chain = load_qa_chain(llm, chain_type="stuff")

        return ConversationalRetrievalChain(
            retriever=vectorstore.as_retriever(search_kwargs={"k": 4}), # k=10 belge getirmeye devam ediyoruz
            combine_docs_chain=doc_chain,
            question_generator=question_generator,
            memory=memory,
            rephrase_question=False
        )

    # --- İLAÇ ASİSTANI SOHBET SEKMESİ ---
    with tab1:
        st.header("İlaç Kullanma Talimatları Sohbeti")
        for msg in st.session_state.ilac_memory.chat_memory.messages:
            st.chat_message(msg.type).write(msg.content)

        ilac_chain = create_conversational_chain(prospektus_db, st.session_state.ilac_memory)

        if prompt := st.chat_input("İlaç hakkında bir soru sorun..."):
            st.chat_message("user").write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Düşünüyor..."):
                    try:
                        response = ilac_chain.invoke({"question": prompt})
                        st.write(response['answer'])
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")

    # --- SUT ASİSTANI SOHBET SEKMESİ (Sorgu Zenginleştirme ile) ---
    with tab2:
        st.header("Sağlık Uygulama Tebliği (SUT) Sohbeti")
        for msg in st.session_state.sut_memory.chat_memory.messages:
            st.chat_message(msg.type).write(msg.content)
            
        sut_chain = create_conversational_chain(sut_db, st.session_state.sut_memory) # Aynı sağlam zinciri kullanır

        if prompt := st.chat_input("SUT hakkında bir soru sorun..."):
            st.chat_message("user").write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Sorgu analiz ediliyor ve SUT taranıyor..."):
                    try:
                        tespit_edilen_ilac = ilac_adi_tespit_et(prompt)
                        enriched_query_terms = [] 
                        
                        if tespit_edilen_ilac:
                            st.info(f"'{tespit_edilen_ilac}' ilacı tespit edildi. Ek bilgi aranıyor...")
                            etken_madde, ilac_sinifi = ilac_bilgisini_genislet(llm, tespit_edilen_ilac)
                            if etken_madde: enriched_query_terms.append(etken_madde)
                            if ilac_sinifi: enriched_query_terms.append(ilac_sinifi)
                            if enriched_query_terms: st.info(f"Arama için ek terimler bulundu: {', '.join(enriched_query_terms)}")
                        
                        final_prompt = prompt
                        if enriched_query_terms:
                             final_prompt += f" ({', '.join(enriched_query_terms)} sınıfı kuralları dahil)"

                        response = sut_chain.invoke({"question": final_prompt})
                        
                        st.success("Cevap bulundu!")
                        st.write(response['answer'])
                        
                    except Exception as e:
                        st.error(f"Bir hata oluştu: {e}")
else:
    st.warning("Asistanı başlatmak için kaynaklar yüklenemedi.")