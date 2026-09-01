# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

from elitehr2.api import get_employees_leave_summary
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import  flt, getdate, date_diff
from elitehr2.elitehr2.doctype.elitehr_employee_checkin.elitehr_employee_checkin import get_month_from_and_end_based_on_closing_day , get_attendance_penalty
class ElitehrFinalsettlement(Document):
    def validate(self):
        self.calculate_settlement()
        
    def calculate_settlement(self):
        self.set_loan_balance()
        self.set_advance_salary()
        self.set_remaining_vacation_days()
        self.calculate_vacation_allowance()
        self.calculate_years_of_service()
        self.calculate_end_of_service_reward()
        self.calculate_totals()
    
        
    def set_loan_balance(self):
        """حساب رصيد السلف المقبولة وتثبيته في حقل loan_balance"""
        if not self.employee:
            self.loan_balance = 0
            return

        # جلب مجموع ميزانية السلف المقبولة للموظف
        total_loans = frappe.db.sql("""
            SELECT SUM(budget)
            FROM `tabElitehr Requests`
            WHERE type = 'ADVANCE_SALARY'
            AND status = 'Approved'
            AND employee = %s
        """, (self.employee,))[0][0] or 0.0

        self.loan_balance = flt(total_loans)
        
    def set_advance_salary(self):
        if self.last_day_of_work:
            self.remaining_days_salary = current_month_salary(date=self.last_day_of_work) or 0
        else:
            self.remaining_days_salary = 0
    
    def set_remaining_vacation_days(self):
        # الاجازات المتبقية
        # الاجازة السنوية والاعتيادية فقط
        if not self.employee or not self.last_day_of_work:
            self.remaining_vacation_days = 0
            self.vacation_allowance = 0
            return
        
        last_day = getdate(self.last_day_of_work)
        current_year = last_day.year
        previous_year = current_year - 1
    
        #  جلب البيانات من دالة  API
        current_summary = get_employees_leave_summary(self.employee, year=current_year) or []
        previous_summary = get_employees_leave_summary(self.employee, year=previous_year) or []

        # حساب الرصيد المرحل أوتوماتيكياً (المتبقي من السنة السابقة)
        carried_over = 0.0
        for prev_item in previous_summary:
            leave_name = (prev_item.get("leave_name") or "").lower()
            if "annual" in leave_name or "سنو" in leave_name or "اعتياد" in leave_name:
                carried_over += flt(prev_item.get("avilable", 0))
        
        
        # حساب عدد الأيام من 1 يناير حتى تاريخ نهاية الخدمة
        jan_1 = getdate(f"{last_day.year}-01-01")
        days_from_jan_1 = date_diff(last_day, jan_1) + 1  # شاملاً يوم النهاية
        
        net_remaining_balance = 0.0
        total_used_days = 0.0
        total_current_entitlement = 0.0
        total_used_days = 0.0
        
        for item in current_summary:
            leave_name = (item.get("leave_name") or "").lower()
            # فلترة وتجميع الإجازات السنوية/الاعتيادية فقط
            if "annual" in leave_name or "سنو" in leave_name or "اعتياد" in leave_name:
                annual_days = flt(item.get("days", 0))         # الرصيد السنوي
                used_days = flt(item.get("used_days", 0))       # الأيام المستهلكة
                
                # الاستحقاق النسبي عن السنة الحالية[cite: 1]
                total_current_entitlement += (annual_days / 365.0) * days_from_jan_1
                total_used_days += used_days
                
        # 3. صافي الرصيد المتبقي = (استحقاق السنة الحالية + المرحل) - المستهلك[cite: 1]
        net_remaining_balance = (total_current_entitlement + carried_over) - total_used_days

        self.remaining_vacation_days = max(0, round(net_remaining_balance, 2))
        
    # رصيد الاجازات المتبقية
    def calculate_vacation_allowance(self):
        if self.net_salary and self.remaining_vacation_days:
            # أجر اليوم = الراتب / 30
            daily_salary = flt(self.net_salary) / 30.0
            self.vacation_allowance = round(daily_salary * flt(self.remaining_vacation_days), 2)
        else:
            self.vacation_allowance = 0.0
            
    def calculate_years_of_service(self):
        if self.date_of_appointment and self.last_day_of_work:
            # حساب الأيام وقسمتها على 365 بناءً على القواعد المعتمدة
            days = date_diff(self.last_day_of_work, self.date_of_appointment)
            self.years_of_service = round(days / 365.0, 2)
        else:
            self.years_of_service = 0.0
            
    
    def calculate_end_of_service_reward(self):

        if not self.net_salary or not self.years_of_service or not self.type_of_termination_of_service:
            self.end_of_service_reward = 0.0
            return

        company_country = frappe.db.get_single_value("Elitehr Company", "country")
        frappe.log(f"company_country: {company_country}")

        daily_salary = flt(self.net_salary) / 30.0
        years = flt(self.years_of_service)
        
        # الحساب الأساسي: نصف شهر لأول 5 سنوات، وشهر كامل لما زاد
        if years <= 5:
            base_reward = years * 15 * daily_salary
        else:
            base_reward = (5 * 15 * daily_salary) + ((years - 5) * 30 * daily_salary)
            
        final_reward = base_reward
        
        # === قانون العمل المصري ===
        if company_country in ["Egypt", "مصر"]:
            # الاستقالة / انتهاء العقد = صفر
            if self.type_of_termination_of_service in ["Contract Expiration", "Resignation"]:
                final_reward = 0.0
            # استحقاق سن الستين (التقاعد) أو الإغلاق الاقتصادي = 100%
            elif self.type_of_termination_of_service in ["Retirement"]:
                final_reward = base_reward
        else:
            # === نظام العمل السعودي (الافتراضي للخليج) ===
            # 1. إنهاء من المنشأة / انتهاء عقد / تقاعد: 100% كاملة
            if self.type_of_termination_of_service in ["Contract Expiration", "Retirement"]:
                final_reward = base_reward

            # 2. استقالة الموظف (المادة 85): تطبيق نسب الاستحقاق
            elif self.type_of_termination_of_service == "Resignation":
                if years < 2:
                    final_reward = 0.0                            # أقل من سنتين: 0%
                elif 2 <= years < 5:
                    final_reward = base_reward / 3.0              # من سنتين إلى أقل من 5 سنوات: ثلث المكافأة (33.3%)
                elif 5 <= years < 10:
                    final_reward = (base_reward * 2.0) / 3.0      # من 5 إلى أقل من 10 سنوات: ثلثا المكافأة (66.6%)
                else:
                    final_reward = base_reward                    # 10 سنوات فأكثر: 100% كاملة
                
        self.end_of_service_reward = round(final_reward, 2)
        
    def calculate_totals(self):
        total_disbursements = (
            flt(self.vacation_allowance) +
            flt(self.remaining_days_salary) +
            flt(self.end_of_service_reward) +
            flt(self.additional_bonuses) +
            flt(self.other_benefits)
        )

        total_deductions = (
            flt(self.loan_balance) +
            flt(self.credit_balance) +
            flt(self.other_discounts)
        )

        self.net_settlement = round(total_disbursements - total_deductions, 2)




def current_month_salary(date): 
    from_date, to_date = get_month_from_and_end_based_on_closing_day(date)
    payroll = frappe.db.get_value(
        "Elitehr Payroll",
        {
        "date": ["between",[from_date,to_date]],
        "status": "Approved"
        },
        "net_salary"
    )
    
    if not payroll:
        frappe.throw(_("No approved payroll found for the specified date."))
        
    return payroll