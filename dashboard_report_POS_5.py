import pandas as pd  # библиотека для анализа табличных данных
import plotly.express as px  # библиотека для построения интерактивных графиков
import streamlit as st  # библиотека для создания веб-приложений

# Загрузка данных из Excel с кэшированием, чтобы не перечитывать при каждом обновлении страницы
@st.cache_data
def load_data():
    df = pd.read_excel("Отчет_ПОС_кратко.xlsx")  # загрузка Excel-файла
    df['Дата поступления'] = pd.to_datetime(df['Дата поступления'], dayfirst=True, errors='coerce')  # преобразование строки в дату
    df['Год'] = df['Дата поступления'].dt.year  # извлечение года из даты
    df['Месяц'] = df['Дата поступления'].dt.month  # извлечение месяца из даты
    return df  # возвращаем обработанный датафрейм

df = load_data()  # загружаем данные через функцию

# Очистка поля "Организация исполнителя" от длинных формальных наименований
remove_phrases = [
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ ЛЕНИНГРАДСКОЙ ОБЛАСТИ",
    "ГОСУДАРСТВЕННОЕ КАЗЕННОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ ЛЕНИНГРАДСКОЙ ОБЛАСТИ",
    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ",
    "ЧАСТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ",
    "ЛЕНИНГРАДСКОЕ ОБЛАСТНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ",
    "АДМИНИСТРАЦИЯ МУНИЦИПАЛЬНОГО ОБРАЗОВАНИЯ",
    "ФЕДЕРАЛЬНОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ НАУКИ",
    "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ",
    "ГОСУДАРСТВЕННОЕ КАЗЕННОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ",
    "ЛЕНИНГРАДСКОЕ ОБЛАСТНОЕ ГОСУДАРСТВЕННОЕ ПРЕДПРИЯТИЕ",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ",
    "ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ ПРОФЕССИОНАЛЬНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ ЛЕНИНГРАДСКОЙ ОБЛАСТИ",
    "ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ УЧРЕЖДЕНИЕ ЗДРАВООХРАНЕНИЯ ЛЕНИНГРАДСКОЙ ОБЛАСТИ"
]
if 'Организация исполнителя' in df.columns:
    for phrase in remove_phrases:
        df['Организация исполнителя'] = df['Организация исполнителя'].str.replace(phrase, '', regex=False).str.strip()

# Боковая панель для выбора фильтра по годам, организациям, категориям и подкатегориям
st.sidebar.title("Фильтры")  # заголовок панели фильтров

# Фильтр по годам
selected_years = st.sidebar.multiselect(
    "Выберите год(ы)",  # подпись к фильтру
    sorted(df['Год'].dropna().unique()),  # список доступных лет без пропусков
    default=sorted(df['Год'].dropna().unique())  # по умолчанию выбраны все
)

# Фильтр по организациям исполнителя
if 'Организация исполнителя' in df.columns:
    all_orgs = sorted(df['Организация исполнителя'].dropna().unique())  # список всех уникальных организаций
    selected_orgs = st.sidebar.multiselect("Выберите организацию исполнителя", options=['Все'] + all_orgs, default=['Все'])  # выбор с возможностью выбрать "Все"
    if 'Все' in selected_orgs:
        selected_orgs = all_orgs  # если выбрано "Все", то выбираются все организации
else:
    selected_orgs = []  # если столбца нет, список пуст

# Фильтрация данных по выбранным фильтрам
filtered_df = df[df['Год'].isin(selected_years)]  # фильтрация по годам

if selected_orgs:
    filtered_df = filtered_df[filtered_df['Организация исполнителя'].isin(selected_orgs)]  # фильтрация по организациям

# Фильтр по категориям
if 'Категория' in df.columns:
    all_categories = sorted(df['Категория'].dropna().unique())  # список всех категорий
    selected_categories = st.sidebar.multiselect("Выберите категорию", options=['Все'] + all_categories, default=['Все'])  # фильтр с "Все"
    if 'Все' not in selected_categories:
        filtered_df = filtered_df[filtered_df['Категория'].isin(selected_categories)]  # фильтрация по выбранным категориям

# Фильтр по подкатегориям
if 'Подкатегория' in df.columns:
    all_subcategories = sorted(df['Подкатегория'].dropna().unique())  # список всех подкатегорий
    selected_subcategories = st.sidebar.multiselect("Выберите подкатегорию", options=['Все'] + all_subcategories, default=['Все'])  # фильтр с "Все"
    if 'Все' not in selected_subcategories:
        filtered_df = filtered_df[filtered_df['Подкатегория'].isin(selected_subcategories)]  # фильтрация по подкатегориям

# Определяем 10 самых частых "Фактов" обращений, исключая неконкретные
st.subheader("Динамика обращений по основным проблемам (ТОП-10)")  # заголовок секции
top_facts = filtered_df['Факт'].value_counts().drop(labels=['-', 'Иное', 'Другое'], errors='ignore').nlargest(10).index  # топ-10 фактов

top_df = filtered_df[filtered_df['Факт'].isin(top_facts)]  # фильтрация по этим фактам
top_data = top_df.groupby(['Год', 'Факт']).size().reset_index(name='Количество')  # подсчет количества по году и факту
fig = px.line(top_data, x='Год', y='Количество', color='Факт', markers=True)  # построение линейного графика
st.plotly_chart(fig)  # отображение график, key='plot_0')

# Анализ сезонности
st.subheader("Сезонность обращений по месяцам")
month_data = filtered_df.groupby('Месяц').size().reset_index(name='Количество')  # подсчет по месяцам
fig2 = px.bar(month_data, x='Месяц', y='Количество', labels={'Месяц': 'Месяц', 'Количество': 'Обращения'})  # построение столбчатой диаграммы
st.plotly_chart(fig2)  # отображение график, key='plot_1')

# Анализ по категориям
st.subheader("Динамика по категориям")
category_data = filtered_df.groupby(['Год', 'Категория']).size().reset_index(name='Количество')  # подсчет по годам и категориям
fig3 = px.line(category_data, x='Год', y='Количество', color='Категория', markers=True)  # построение графика
st.plotly_chart(fig3)  # отображени, key='plot_2')

# Анализ динамики обращений по категориям
st.subheader("Динамика по подкатегориям")
category_data = filtered_df.groupby(['Год', 'Подкатегория']).size().reset_index(name='Количество')
fig4 = px.line(category_data, x='Год', y='Количество', color='Подкатегория', markers=True)
st.plotly_chart(fig4, key='plot_3')

# Загрузка данных с сопоставлением фактов, принципов и критериев из внешнего файла
import os  # модуль для работы с файловой системой
if os.path.exists("Факты_и_критерии_4П.xlsx"):  # проверка наличия файла
    df_4p = pd.read_excel("Факты_и_критерии_4П.xlsx")  # загружаем Excel-файл с готовыми данными
else:
    df_4p = pd.DataFrame(columns=['Принцип 4П', 'Факт', 'Критерии'])  # создаём пустую таблицу, если файл не найден

# Количественная визуализация по принципам 4П
st.subheader("Количество жалоб по каждому принципу 4П")  # заголовок раздела

# Фильтрация таблицы df_4p по выбранным годам, организациям, категориям и подкатегориям
if not df_4p.empty:
    df_merged = df_4p.merge(filtered_df[['Факт', 'Год', 'Организация исполнителя', 'Категория', 'Подкатегория']], on='Факт', how='inner')
    principle_counts = df_merged['Принцип 4П'].value_counts().reset_index()
    principle_counts.columns = ['Принцип 4П', 'Количество жалоб']
    fig_p1 = px.bar(principle_counts, x='Принцип 4П', y='Количество жалоб', color='Принцип 4П')
    st.plotly_chart(fig_p1, key='plot_4')
else:
    st.info("Нет данных для отображения принципов 4П")  # отображение графика в интерфейсе


# Визуализация самых частых сочетаний факт + критерий + принцип с учетом фильтрации
st.subheader("Наиболее частые сочетания жалобы и критерия 4П")

# Объединение с фильтрованными данными для учета выбранных параметров
if not df_4p.empty:
    df_filtered_4p = df_4p.merge(
        filtered_df[['Факт', 'Год', 'Организация исполнителя', 'Категория', 'Подкатегория']],
        on='Факт', how='inner'
    )

    # Агрегация количества по каждой жалобе и критерию с учетом принципа
    fact_crit_counts = (
        df_filtered_4p.groupby(['Факт', 'Критерии', 'Принцип 4П'])
        .size()
        .reset_index(name='Количество')
    )

    # Выборка 20 наиболее частых
    fact_crit_top = fact_crit_counts.sort_values(by='Количество', ascending=False).head(20)

    # Визуализация
    fig_p2 = px.bar(
        fact_crit_top, x='Количество', y='Факт', color='Принцип 4П',
        orientation='h', hover_data=['Критерии'],
        title='Топ-20 жалоб с соответствующими критериями 4П'
    )
    st.plotly_chart(fig_p2, use_container_width=True, key="top20_filtered_graph")
else:
    st.info("Нет данных для отображения сочетаний жалоб и критериев 4П")
  # отображение графика в интерфейс, key='plot_5')
def classify_principle(text):
    if pd.isna(text):
        return []
    text = text.lower()
    matched = []
    for principle, keywords in principles_keywords.items():
        for kw in keywords:
            if kw in text:
                matched.append(principle)
                break
    return matched  # вернуть список принципов

# Сравнение количества обращений по годам и организациям
st.subheader("Сравнение обращений по годам и организациям")
if 'Организация исполнителя' in filtered_df.columns:
    org_year_data = filtered_df.groupby(['Год', 'Организация исполнителя']).size().reset_index(name='Количество')  # подсчет обращений
    fig5 = px.bar(org_year_data, x='Год', y='Количество', color='Организация исполнителя', barmode='group')  # график сравнения
    st.plotly_chart(fig5)  # отображени, key='plot_6')

# Завершающее пояснение
st.write("\n---\n")
st.markdown("**Разработано для анализа данных платформы обратной связи в целях оценки пациентоориентированности медицинской организации.")
