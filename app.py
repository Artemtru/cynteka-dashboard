"""
Cynteka Dashboard - мониторинг заявок, счетов и доставок
"""
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from cynteka_api import CyntekaAPI

# Конфигурация страницы
st.set_page_config(
    page_title="Cynteka Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== TELEGRAM WEB APP AUTHENTICATION ==========
def check_telegram_auth():
    """Проверка авторизации из Telegram Web App"""
    query_params = st.query_params
    
    # Получаем параметры из URL (передаются ботом)
    tg_user_id = query_params.get("tg_user_id")
    tg_username = query_params.get("tg_username")
    
    # Белый список пользователей из .env
    allowed_users = os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
    
    # Если нет параметров Telegram — анонимный режим (для разработки)
    if not tg_user_id:
        if os.getenv("ALLOW_ANONYMOUS", "false").lower() == "true":
            st.sidebar.warning("⚠️ Режим разработки: авторизация отключена")
            return True
        else:
            st.error("❌ Доступ запрещён. Откройте дашборд через Telegram бота.")
            st.info("Для получения доступа напишите администратору.")
            st.stop()
            return False
    
    # Проверка прав доступа
    if allowed_users and tg_user_id not in allowed_users:
        st.error(f"❌ Доступ запрещён для пользователя `{tg_username}` (ID: `{tg_user_id}`).")
        st.info("Обратитесь к администратору для получения доступа.")
        st.stop()
        return False
    
    # Успешная авторизация — показываем инфо в сайдбаре
    st.sidebar.success(f"👤 {tg_username or f'User {tg_user_id}'}")
    return True

# Проверяем авторизацию перед загрузкой дашборда
check_telegram_auth()
# ====================================================

# Инициализация API
@st.cache_resource
def init_api():
    return CyntekaAPI()

api = init_api()

# Заголовок
st.title("📊 Cynteka Dashboard")
st.markdown("---")

# Боковая панель - фильтры
st.sidebar.header("Фильтры")

# Автообновление
auto_refresh = st.sidebar.checkbox("Автообновление (5 мин)", value=False)
if auto_refresh:
    st.sidebar.info("Обновление через 5 минут")

# Период
date_range = st.sidebar.date_input(
    "Период",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

# Фильтр по проектам
all_projects = api.get_projects()
selected_projects = st.sidebar.multiselect(
    "Проекты",
    options=all_projects,
    default=all_projects[:5] if len(all_projects) > 5 else all_projects
)

# Фильтр по сотрудникам
all_employees = api.get_employees()
selected_employees = st.sidebar.multiselect(
    "Ответственные",
    options=all_employees,
    default=[]
)

# Кнопка обновления
if st.sidebar.button("🔄 Обновить данные", use_container_width=True):
    st.cache_resource.clear()
    st.rerun()

# Получение данных
with st.spinner("Загрузка данных из Cynteka..."):
    requests_data = api.get_requests(
        date_from=date_range[0] if len(date_range) == 2 else None,
        date_to=date_range[1] if len(date_range) == 2 else None,
        projects=selected_projects,
        employees=selected_employees
    )
    
    invoices_data = api.get_invoices(
        date_from=date_range[0] if len(date_range) == 2 else None,
        date_to=date_range[1] if len(date_range) == 2 else None,
        projects=selected_projects
    )
    
    deliveries_data = api.get_deliveries(
        date_from=date_range[0] if len(date_range) == 2 else None,
        date_to=date_range[1] if len(date_range) == 2 else None,
        projects=selected_projects
    )

# Метрики верхнего уровня
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Всего заявок",
        len(requests_data),
        delta=f"+{len([r for r in requests_data if r['created_days_ago'] <= 7])} за неделю"
    )

with col2:
    in_progress = len([r for r in requests_data if r['status'] == 'В работе'])
    st.metric(
        "В работе",
        in_progress,
        delta=f"{round(in_progress/len(requests_data)*100, 1)}%" if requests_data else "0%"
    )

with col3:
    on_time = len([r for r in requests_data if r['closed_on_time']])
    total_closed = len([r for r in requests_data if r['status'] == 'Закрыта'])
    st.metric(
        "Закрыто в срок",
        on_time,
        delta=f"{round(on_time/total_closed*100, 1)}%" if total_closed else "0%"
    )

with col4:
    pending_invoices = len([i for i in invoices_data if i['status'] == 'На согласовании'])
    st.metric(
        "Счетов на согласовании",
        pending_invoices
    )

st.markdown("---")

# Основные вкладки
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Заявки по проектам",
    "💰 Счета на оплату",
    "🚚 Доставки",
    "👥 По сотрудникам"
])

# Вкладка 1: Заявки по проектам
with tab1:
    st.subheader("Заявки по проектам")
    
    if requests_data:
        # Группировка по проектам
        projects_summary = {}
        for req in requests_data:
            project = req['project']
            if project not in projects_summary:
                projects_summary[project] = {
                    'Всего': 0,
                    'В работе': 0,
                    'На согласовании': 0,
                    'Закрыто': 0,
                    'Закрыто в срок': 0,
                    'Просрочено': 0
                }
            
            projects_summary[project]['Всего'] += 1
            projects_summary[project][req['status']] = projects_summary[project].get(req['status'], 0) + 1
            
            if req['status'] == 'Закрыта':
                if req['closed_on_time']:
                    projects_summary[project]['Закрыто в срок'] += 1
            elif req.get('is_overdue'):
                projects_summary[project]['Просрочено'] += 1
        
        df_projects = pd.DataFrame(projects_summary).T
        df_projects = df_projects.fillna(0).astype(int)
        
        # Добавляем процент закрытия в срок
        df_projects['% в срок'] = df_projects.apply(
            lambda row: f"{round(row['Закрыто в срок']/row['Закрыто']*100, 1)}%" 
            if row['Закрыто'] > 0 else "—",
            axis=1
        )
        
        st.dataframe(
            df_projects,
            use_container_width=True,
            height=400
        )
        
        # График
        st.subheader("Статусы заявок по проектам")
        chart_data = df_projects[['В работе', 'На согласовании', 'Закрыто', 'Просрочено']].head(10)
        st.bar_chart(chart_data)
    else:
        st.info("Нет данных по заявкам за выбранный период")

# Вкладка 2: Счета на оплату
with tab2:
    st.subheader("Счета на согласовании")
    
    if invoices_data:
        # Фильтруем счета на согласовании
        pending = [i for i in invoices_data if i['status'] == 'На согласовании']
        
        if pending:
            df_invoices = pd.DataFrame(pending)
            
            # Выбор колонок для отображения
            display_columns = ['number', 'date', 'project', 'supplier', 'amount', 'days_pending']
            df_display = df_invoices[display_columns].copy()
            df_display.columns = ['№ счёта', 'Дата', 'Проект', 'Поставщик', 'Сумма ₽', 'Дней на согласовании']
            
            # Раскраска по времени
            def highlight_pending(val):
                if isinstance(val, (int, float)):
                    if val > 7:
                        return 'background-color: #ffcccc'  # Красный
                    elif val > 3:
                        return 'background-color: #fff4cc'  # Желтый
                return ''
            
            st.dataframe(
                df_display.style.applymap(highlight_pending, subset=['Дней на согласовании']),
                use_container_width=True,
                height=400
            )
            
            # Метрика просроченных
            overdue = len([i for i in pending if i['days_pending'] > 7])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Всего на согласовании", len(pending))
            with col2:
                st.metric("⚠️ Более 7 дней", overdue, delta="Требуют внимания")
            with col3:
                total_amount = sum([i['amount'] for i in pending])
                st.metric("Сумма на согласовании", f"{total_amount:,.0f} ₽")
        else:
            st.success("✅ Нет счетов на согласовании")
    else:
        st.info("Нет данных по счетам за выбранный период")

# Вкладка 3: Доставки
with tab3:
    st.subheader("Запланированные доставки")
    
    if deliveries_data:
        # Фильтруем только запланированные
        planned = [d for d in deliveries_data if d['status'] == 'Запланирована']
        
        if planned:
            df_deliveries = pd.DataFrame(planned)
            
            display_columns = ['date', 'project', 'address', 'supplier', 'items_count', 'responsible']
            df_display = df_deliveries[display_columns].copy()
            df_display.columns = ['Дата', 'Проект', 'Адрес', 'Поставщик', 'Позиций', 'Ответственный']
            
            st.dataframe(
                df_display,
                use_container_width=True,
                height=400
            )
            
            # Метрики
            col1, col2, col3 = st.columns(3)
            with col1:
                today = len([d for d in planned if d['is_today']])
                st.metric("Сегодня", today)
            with col2:
                this_week = len([d for d in planned if d['is_this_week']])
                st.metric("На этой неделе", this_week)
            with col3:
                st.metric("Всего запланировано", len(planned))
        else:
            st.info("Нет запланированных доставок")
    else:
        st.info("Нет данных по доставкам за выбранный период")

# Вкладка 4: По сотрудникам
with tab4:
    st.subheader("Статистика по сотрудникам")
    
    if requests_data:
        # Группировка по ответственным
        employee_summary = {}
        for req in requests_data:
            employee = req['responsible']
            if employee not in employee_summary:
                employee_summary[employee] = {
                    'Всего заявок': 0,
                    'В работе': 0,
                    'Закрыто': 0,
                    'Закрыто в срок': 0,
                    'Просрочено': 0
                }
            
            employee_summary[employee]['Всего заявок'] += 1
            
            if req['status'] == 'В работе':
                employee_summary[employee]['В работе'] += 1
            elif req['status'] == 'Закрыта':
                employee_summary[employee]['Закрыто'] += 1
                if req['closed_on_time']:
                    employee_summary[employee]['Закрыто в срок'] += 1
            
            if req.get('is_overdue'):
                employee_summary[employee]['Просрочено'] += 1
        
        df_employees = pd.DataFrame(employee_summary).T
        df_employees = df_employees.fillna(0).astype(int)
        
        # Добавляем эффективность
        df_employees['Эффективность %'] = df_employees.apply(
            lambda row: f"{round(row['Закрыто в срок']/row['Закрыто']*100, 1)}%" 
            if row['Закрыто'] > 0 else "—",
            axis=1
        )
        
        # Сортировка по количеству заявок в работе
        df_employees = df_employees.sort_values('В работе', ascending=False)
        
        st.dataframe(
            df_employees,
            use_container_width=True,
            height=400
        )
        
        # График топ-10 по загрузке
        st.subheader("Топ-10 по заявкам в работе")
        chart_data = df_employees[['В работе', 'Закрыто', 'Просрочено']].head(10)
        st.bar_chart(chart_data)
    else:
        st.info("Нет данных по сотрудникам за выбранный период")

# Футер
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"Последнее обновление: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
with col2:
    st.caption("Источник: Cynteka API")
with col3:
    if auto_refresh:
        st.caption("⏱️ Автообновление активно")

# Автообновление каждые 5 минут
if auto_refresh:
    import time
    time.sleep(300)
    st.rerun()
