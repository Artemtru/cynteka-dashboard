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
col1, col2, col3, col4, col5 = st.columns(5)

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
        delta=f"{round(in_progress/len(requests_data)*100)}%" if requests_data else "0%"
    )

with col3:
    on_time = len([r for r in requests_data if r['closed_on_time']])
    total_closed = len([r for r in requests_data if r['status'] == 'Закрыта'])
    st.metric(
        "Эффективность",
        f"{round(on_time/total_closed*100)}%" if total_closed else "—",
        delta=f"{on_time}/{total_closed} в срок"
    )

with col4:
    overdue = len([r for r in requests_data if r.get('is_overdue')])
    color = "🔴" if overdue > 5 else "🟡" if overdue > 0 else "🟢"
    st.metric(
        "Просрочено",
        f"{color} {overdue}",
        delta="Требуют внимания" if overdue > 0 else "Всё в порядке",
        delta_color="inverse" if overdue > 0 else "normal"
    )

with col5:
    pending_invoices = len([i for i in invoices_data if i['status'] == 'На согласовании'])
    urgent_invoices = len([i for i in invoices_data if i['status'] == 'На согласовании' and i['days_pending'] > 7])
    st.metric(
        "Счётов на согласовании",
        pending_invoices,
        delta=f"⚠️ {urgent_invoices} >7 дней" if urgent_invoices > 0 else "✅ Без задержек"
    )

st.markdown("---")

# Основные вкладки
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 По ответственным",
    "📊 По проектам",
    "💰 Счета на оплату",
    "🚚 Доставки",
    "📈 Эффективность"
])

# Вкладка 1: По ответственным (главная для руководителя)
with tab1:
    st.subheader("📊 Эффективность работы по ответственным")
    
    if requests_data:
        # Группировка по ответственным с детальной статистикой
        employee_summary = {}
        employee_details = {}  # Для детализации по проектам
        
        for req in requests_data:
            employee = req['responsible']
            project = req['project']
            
            if employee not in employee_summary:
                employee_summary[employee] = {
                    'Всего заявок': 0,
                    'В работе': 0,
                    'Закрыто': 0,
                    'Закрыто в срок': 0,
                    'Просрочено': 0,
                    'На согласовании': 0
                }
                employee_details[employee] = []
            
            employee_summary[employee]['Всего заявок'] += 1
            
            if req['status'] == 'В работе':
                employee_summary[employee]['В работе'] += 1
            elif req['status'] == 'Закрыта':
                employee_summary[employee]['Закрыто'] += 1
                if req['closed_on_time']:
                    employee_summary[employee]['Закрыто в срок'] += 1
            elif req['status'] == 'На согласовании':
                employee_summary[employee]['На согласовании'] += 1
            
            if req.get('is_overdue'):
                employee_summary[employee]['Просрочено'] += 1
            
            # Сохраняем детали для раскрытия
            employee_details[employee].append({
                'Проект': project,
                'Статус': req['status'],
                'Создана': req.get('created_date', '—'),
                'Дней в работе': req.get('days_in_progress', 0)
            })
        
        df_employees = pd.DataFrame(employee_summary).T
        df_employees = df_employees.fillna(0).astype(int)
        
        # Добавляем эффективность и рейтинг
        df_employees['Эффективность %'] = df_employees.apply(
            lambda row: round(row['Закрыто в срок']/row['Закрыто']*100, 1) 
            if row['Закрыто'] > 0 else 0,
            axis=1
        )
        
        # Сортировка: сначала по просроченным (убывание), потом по эффективности (убывание)
        df_employees = df_employees.sort_values(['Просрочено', 'Эффективность %'], ascending=[False, False])
        
        # Цветовая индикация эффективности
        def color_efficiency(val):
            if isinstance(val, (int, float)):
                if val >= 90:
                    return 'background-color: #d4edda; color: #155724'  # Зелёный
                elif val >= 75:
                    return 'background-color: #fff3cd; color: #856404'  # Жёлтый
                elif val > 0:
                    return 'background-color: #f8d7da; color: #721c24'  # Красный
            return ''
        
        def color_overdue(val):
            if isinstance(val, (int, float)) and val > 0:
                return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
            return ''
        
        # Отображаем таблицу с подсветкой
        styled_df = df_employees.style\
            .applymap(color_efficiency, subset=['Эффективность %'])\
            .applymap(color_overdue, subset=['Просрочено'])
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=500
        )
        
        st.markdown("---")
        
        # Детализация по выбранному сотруднику
        st.subheader("🔍 Детализация по сотруднику")
        selected_employee = st.selectbox(
            "Выберите сотрудника:",
            options=list(employee_summary.keys()),
            index=0
        )
        
        if selected_employee:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("В работе", employee_summary[selected_employee]['В работе'])
            with col2:
                st.metric("Закрыто в срок", employee_summary[selected_employee]['Закрыто в срок'])
            with col3:
                st.metric("Просрочено", employee_summary[selected_employee]['Просрочено'])
            with col4:
                eff = round(employee_summary[selected_employee]['Закрыто в срок'] / 
                           max(employee_summary[selected_employee]['Закрыто'], 1) * 100, 1)
                st.metric("Эффективность", f"{eff}%")
            
            # Таблица заявок сотрудника
            st.markdown("**Заявки:**")
            df_details = pd.DataFrame(employee_details[selected_employee])
            
            # Группировка по проектам
            project_counts = df_details.groupby('Проект').size().to_dict()
            df_details['Заявок в проекте'] = df_details['Проект'].map(project_counts)
            
            st.dataframe(
                df_details,
                use_container_width=True,
                height=300
            )
        
        st.markdown("---")
        
        # График распределения нагрузки
        st.subheader("📊 Распределение нагрузки (топ-10)")
        chart_data = df_employees[['В работе', 'Просрочено', 'На согласовании']].head(10)
        st.bar_chart(chart_data)
        
    else:
        st.info("Нет данных по заявкам за выбранный период")

# Вкладка 2: По проектам
with tab2:
    st.subheader("📊 Заявки по проектам")
    
    if requests_data:
        # Группировка по проектам с детализацией по ответственным
        projects_summary = {}
        project_employees = {}  # Кто работает над проектом
        
        for req in requests_data:
            project = req['project']
            employee = req['responsible']
            
            if project not in projects_summary:
                projects_summary[project] = {
                    'Всего': 0,
                    'В работе': 0,
                    'На согласовании': 0,
                    'Закрыто': 0,
                    'Закрыто в срок': 0,
                    'Просрочено': 0
                }
                project_employees[project] = set()
            
            projects_summary[project]['Всего'] += 1
            project_employees[project].add(employee)
            
            if req['status'] == 'В работе':
                projects_summary[project]['В работе'] += 1
            elif req['status'] == 'Закрыта':
                projects_summary[project]['Закрыто'] += 1
                if req['closed_on_time']:
                    projects_summary[project]['Закрыто в срок'] += 1
            elif req['status'] == 'На согласовании':
                projects_summary[project]['На согласовании'] += 1
            
            if req.get('is_overdue'):
                projects_summary[project]['Просрочено'] += 1
        
        df_projects = pd.DataFrame(projects_summary).T
        df_projects = df_projects.fillna(0).astype(int)
        
        # Добавляем количество ответственных
        df_projects['Ответственных'] = [len(project_employees[proj]) for proj in df_projects.index]
        
        # Процент закрытия в срок
        df_projects['% в срок'] = df_projects.apply(
            lambda row: f"{round(row['Закрыто в срок']/row['Закрыто']*100, 1)}%" 
            if row['Закрыто'] > 0 else "—",
            axis=1
        )
        
        # Сортировка по количеству просроченных
        df_projects = df_projects.sort_values('Просрочено', ascending=False)
        
        st.dataframe(
            df_projects,
            use_container_width=True,
            height=500
        )
        
        st.markdown("---")
        
        # Детализация по выбранному проекту
        st.subheader("🔍 Детализация проекта")
        selected_project = st.selectbox(
            "Выберите проект:",
            options=list(projects_summary.keys())
        )
        
        if selected_project:
            st.markdown(f"**Ответственные:** {', '.join(project_employees[selected_project])}")
            
            # Заявки проекта по ответственным
            project_reqs = [r for r in requests_data if r['project'] == selected_project]
            proj_emp_stats = {}
            
            for req in project_reqs:
                emp = req['responsible']
                if emp not in proj_emp_stats:
                    proj_emp_stats[emp] = {'В работе': 0, 'Закрыто': 0, 'Просрочено': 0}
                
                if req['status'] == 'В работе':
                    proj_emp_stats[emp]['В работе'] += 1
                elif req['status'] == 'Закрыта':
                    proj_emp_stats[emp]['Закрыто'] += 1
                
                if req.get('is_overdue'):
                    proj_emp_stats[emp]['Просрочено'] += 1
            
            df_proj_emp = pd.DataFrame(proj_emp_stats).T
            st.dataframe(df_proj_emp, use_container_width=True)
        
        # График статусов по проектам
        st.subheader("Статусы заявок по проектам (топ-10)")
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

# Вкладка 5: Эффективность (аналитика для руководителя)
with tab5:
    st.subheader("📈 Аналитика эффективности отдела")
    
    if requests_data:
        # Общие метрики эффективности
        st.markdown("### 🎯 Ключевые показатели")
        
        total_requests = len(requests_data)
        closed_requests = len([r for r in requests_data if r['status'] == 'Закрыта'])
        closed_on_time = len([r for r in requests_data if r['status'] == 'Закрыта' and r['closed_on_time']])
        overdue_requests = len([r for r in requests_data if r.get('is_overdue')])
        in_progress = len([r for r in requests_data if r['status'] == 'В работе'])
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Общая эффективность",
                f"{round(closed_on_time/max(closed_requests, 1)*100, 1)}%",
                delta="Закрыто в срок"
            )
        
        with col2:
            completion_rate = round(closed_requests/total_requests*100, 1)
            st.metric(
                "Скорость закрытия",
                f"{completion_rate}%",
                delta=f"{closed_requests}/{total_requests}"
            )
        
        with col3:
            overdue_rate = round(overdue_requests/max(in_progress, 1)*100, 1)
            color = "🔴" if overdue_rate > 20 else "🟡" if overdue_rate > 10 else "🟢"
            st.metric(
                "Просрочено в работе",
                f"{color} {overdue_rate}%",
                delta=f"{overdue_requests} заявок"
            )
        
        with col4:
            avg_per_employee = round(total_requests / len(set([r['responsible'] for r in requests_data])), 1)
            st.metric(
                "Средняя нагрузка",
                f"{avg_per_employee}",
                delta="заявок/сотрудник"
            )
        
        with col5:
            active_employees = len(set([r['responsible'] for r in requests_data if r['status'] == 'В работе']))
            st.metric(
                "Активных сотрудников",
                active_employees,
                delta=f"из {len(set([r['responsible'] for r in requests_data]))}"
            )
        
        st.markdown("---")
        
        # Проблемные зоны
        st.markdown("### ⚠️ Требуют внимания")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 Сотрудники с просрочками:**")
            
            emp_overdue = {}
            for req in requests_data:
                if req.get('is_overdue'):
                    emp = req['responsible']
                    emp_overdue[emp] = emp_overdue.get(emp, 0) + 1
            
            if emp_overdue:
                sorted_overdue = sorted(emp_overdue.items(), key=lambda x: x[1], reverse=True)[:5]
                for emp, count in sorted_overdue:
                    st.markdown(f"- **{emp}**: {count} просроченных")
            else:
                st.success("✅ Нет просроченных заявок")
        
        with col2:
            st.markdown("**📊 Проекты с низкой эффективностью (<75%):**")
            
            project_efficiency = {}
            for req in requests_data:
                if req['status'] == 'Закрыта':
                    proj = req['project']
                    if proj not in project_efficiency:
                        project_efficiency[proj] = {'closed': 0, 'on_time': 0}
                    project_efficiency[proj]['closed'] += 1
                    if req['closed_on_time']:
                        project_efficiency[proj]['on_time'] += 1
            
            low_efficiency_projects = []
            for proj, stats in project_efficiency.items():
                if stats['closed'] >= 3:  # Минимум 3 закрытых заявки
                    eff = stats['on_time'] / stats['closed'] * 100
                    if eff < 75:
                        low_efficiency_projects.append((proj, eff, stats['closed']))
            
            if low_efficiency_projects:
                sorted_projects = sorted(low_efficiency_projects, key=lambda x: x[1])[:5]
                for proj, eff, closed in sorted_projects:
                    st.markdown(f"- **{proj}**: {round(eff, 1)}% ({closed} заявок)")
            else:
                st.success("✅ Все проекты с эффективностью >75%")
        
        st.markdown("---")
        
        # Динамика по времени (если есть данные о датах)
        st.markdown("### 📅 Динамика создания заявок")
        
        # Группировка по неделям
        weekly_stats = {}
        for req in requests_data:
            created_days = req.get('created_days_ago', 0)
            week = created_days // 7
            week_label = f"Неделя {week}" if week == 0 else f"-{week} нед"
            
            if week_label not in weekly_stats:
                weekly_stats[week_label] = 0
            weekly_stats[week_label] += 1
        
        if weekly_stats:
            df_weekly = pd.DataFrame(list(weekly_stats.items()), columns=['Период', 'Заявок'])
            df_weekly = df_weekly.sort_values('Период')
            st.bar_chart(df_weekly.set_index('Период'))
        
        st.markdown("---")
        
        # Топ по эффективности
        st.markdown("### 🏆 Рейтинг эффективности")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🥇 Лучшие сотрудники (>90% в срок):**")
            
            top_employees = []
            for req in requests_data:
                emp = req['responsible']
                if emp not in [e[0] for e in top_employees]:
                    emp_reqs = [r for r in requests_data if r['responsible'] == emp]
                    closed = [r for r in emp_reqs if r['status'] == 'Закрыта']
                    
                    if len(closed) >= 5:  # Минимум 5 закрытых
                        on_time = len([r for r in closed if r['closed_on_time']])
                        eff = on_time / len(closed) * 100
                        
                        if eff >= 90:
                            top_employees.append((emp, eff, len(closed)))
            
            if top_employees:
                sorted_top = sorted(top_employees, key=lambda x: x[1], reverse=True)[:5]
                for i, (emp, eff, closed) in enumerate(sorted_top, 1):
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
                    st.markdown(f"{medal} **{emp}**: {round(eff, 1)}% ({closed} заявок)")
            else:
                st.info("Недостаточно данных (минимум 5 закрытых заявок)")
        
        with col2:
            st.markdown("**⚡ Самые загруженные сотрудники:**")
            
            workload = {}
            for req in requests_data:
                if req['status'] == 'В работе':
                    emp = req['responsible']
                    workload[emp] = workload.get(emp, 0) + 1
            
            if workload:
                sorted_workload = sorted(workload.items(), key=lambda x: x[1], reverse=True)[:5]
                for emp, count in sorted_workload:
                    bar = "█" * min(count, 20)
                    st.markdown(f"- **{emp}**: {bar} {count}")
            else:
                st.info("Нет заявок в работе")
    
    else:
        st.info("Нет данных по заявкам за выбранный период")

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
