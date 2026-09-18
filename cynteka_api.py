"""
Модуль для работы с Cynteka API
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class CyntekaAPI:
    """Клиент для работы с Cynteka API"""
    
    def __init__(self):
        self.base_url = os.getenv('CYNTEKA_API_URL', 'https://anvaz.cynteka.ru/core')
        self.api_token = os.getenv('CYNTEKA_API_TOKEN')
        
        if not self.api_token:
            raise ValueError(
                "CYNTEKA_API_TOKEN не найден в .env файле. "
                "Получите токен у администратора Cynteka или в техподдержке: "
                "8-800-333-84-60, help@cynteka.ru"
            )
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Выполнить GET запрос к API"""
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_projects(self) -> List[str]:
        """
        Получить список проектов
        
        TODO: Реализовать реальный запрос к API после получения токена
        Пока возвращается заглушка для тестирования интерфейса
        """
        # Заглушка
        return [
            "Сокольники - Монолит",
            "Сокольники - ВОР",
            "Альфа-Групп Офис",
            "Склад Химки",
            "Проект Восток"
        ]
    
    def get_employees(self) -> List[str]:
        """
        Получить список сотрудников
        
        TODO: Реализовать реальный запрос к API
        """
        # Заглушка
        return [
            "Иванов И.И.",
            "Петров П.П.",
            "Сидоров С.С.",
            "Кузнецов К.К.",
            "Михайлов М.М."
        ]
    
    def get_requests(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        projects: Optional[List[str]] = None,
        employees: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Получить заявки
        
        TODO: Реализовать реальный запрос к API
        Endpoint: /api/requests или /api/applications
        
        Параметры:
        - date_from: начало периода
        - date_to: конец периода
        - projects: фильтр по проектам
        - employees: фильтр по ответственным
        
        Возвращает список заявок с полями:
        - id: ID заявки
        - number: номер заявки
        - project: проект
        - status: статус (В работе, На согласовании, Закрыта, Отклонена)
        - responsible: ответственный сотрудник
        - created_date: дата создания
        - deadline: срок закрытия
        - closed_date: дата закрытия (если закрыта)
        - closed_on_time: закрыта в срок (bool)
        - is_overdue: просрочена (bool)
        """
        # Заглушка для тестирования интерфейса
        statuses = ['В работе', 'На согласовании', 'Закрыта']
        projects_list = projects if projects else self.get_projects()
        employees_list = employees if employees else self.get_employees()
        
        requests_data = []
        for i in range(50):
            created = datetime.now() - timedelta(days=i)
            deadline = created + timedelta(days=14)
            is_closed = i % 3 == 0
            closed_date = created + timedelta(days=10) if is_closed else None
            
            requests_data.append({
                'id': i + 1,
                'number': f'REQ-2026-{i+1:04d}',
                'project': projects_list[i % len(projects_list)],
                'status': 'Закрыта' if is_closed else statuses[i % 2],
                'responsible': employees_list[i % len(employees_list)],
                'created_date': created.isoformat(),
                'created_days_ago': i,
                'deadline': deadline.isoformat(),
                'closed_date': closed_date.isoformat() if closed_date else None,
                'closed_on_time': (closed_date < deadline) if (is_closed and closed_date) else False,
                'is_overdue': not is_closed and datetime.now() > deadline
            })
        
        return requests_data
    
    def get_invoices(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        projects: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Получить счета
        
        TODO: Реализовать реальный запрос к API
        Endpoint: /api/invoices
        
        Возвращает список счетов с полями:
        - id: ID счёта
        - number: номер счёта
        - date: дата счёта
        - project: проект
        - supplier: поставщик
        - amount: сумма
        - status: статус (На согласовании, Оплачен, Отклонён)
        - days_pending: дней на согласовании
        """
        # Заглушка
        projects_list = projects if projects else self.get_projects()
        suppliers = ['ООО "Строймаркет"', 'ИП Васильев', 'ООО "Техснаб"', 'ООО "МегаТорг"']
        
        invoices_data = []
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            days_pending = i
            
            invoices_data.append({
                'id': i + 1,
                'number': f'INV-{i+1:05d}',
                'date': date.strftime('%d.%m.%Y'),
                'project': projects_list[i % len(projects_list)],
                'supplier': suppliers[i % len(suppliers)],
                'amount': (i + 1) * 15000,
                'status': 'На согласовании' if i < 15 else 'Оплачен',
                'days_pending': days_pending if i < 15 else 0
            })
        
        return invoices_data
    
    def get_deliveries(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        projects: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Получить доставки
        
        TODO: Реализовать реальный запрос к API
        Endpoint: /api/deliveries
        
        Возвращает список доставок с полями:
        - id: ID доставки
        - date: дата доставки
        - project: проект
        - address: адрес доставки
        - supplier: поставщик
        - items_count: количество позиций
        - responsible: ответственный
        - status: статус (Запланирована, Выполнена, Отменена)
        """
        # Заглушка
        projects_list = projects if projects else self.get_projects()
        addresses = ['Офис, ул. Ленина 1', 'Склад, ул. Складская 10', 'Объект Восток', 'Склад Химки']
        suppliers = ['ООО "Строймаркет"', 'ИП Васильев', 'ООО "Техснаб"']
        employees_list = self.get_employees()
        
        deliveries_data = []
        for i in range(20):
            delivery_date = datetime.now() + timedelta(days=i)
            
            deliveries_data.append({
                'id': i + 1,
                'date': delivery_date.strftime('%d.%m.%Y'),
                'project': projects_list[i % len(projects_list)],
                'address': addresses[i % len(addresses)],
                'supplier': suppliers[i % len(suppliers)],
                'items_count': (i % 10) + 1,
                'responsible': employees_list[i % len(employees_list)],
                'status': 'Запланирована',
                'is_today': i == 0,
                'is_this_week': i < 7
            })
        
        return deliveries_data
