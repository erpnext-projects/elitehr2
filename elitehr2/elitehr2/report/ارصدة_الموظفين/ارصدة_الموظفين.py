# Copyright (c) 2026, Mohamed Elgohary and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data



def get_columns():
    return [
        "Employee:Link/Elitehr Employee:150",
        "Employee Name:Data:180",
        "Leave Type:Data:150",
        "Allowed Days:Float:120",
        "Used Days:Float:120",
        "Percentage %:Percent:120",
    ]



def get_data(filters):
    data = []

    employees = frappe.get_all(
        "Elitehr Employee",
        filters={"name": filters.employee} if filters.get("employee") else {},
        fields=["name", "employee_name"]
    )

    for emp in employees:
        doc = frappe.get_doc("Elitehr Employee", emp.name)

        for l in doc.table_leaves:

            used_days = frappe.db.sql("""
                SELECT SUM(days)
                FROM `tabElitehr Leaves`
                WHERE employee=%s
                AND type=%s
                AND status='مكتمل'
            """, (emp.name, l.leave))[0][0] or 0

            percentage = (used_days / int(l.days)) * 100 if l.days else 0

            data.append([
                emp.name,
                emp.employee_name,
                l.leave_name or l.leave,
                l.days,
                used_days,
                round(percentage, 2)
            ])

    return data


@frappe.whitelist()
def get_leave_summary():
    data = []
    employees = frappe.get_all("Elitehr Employee", fields=["name", "employee_name"])

    for emp in employees:
        doc = frappe.get_doc("Elitehr Employee", emp.name)
        for l in doc.table_leaves:
            used_days = frappe.db.sql("""
                SELECT SUM(days) FROM `tabElitehr Leaves`
                WHERE employee=%s AND type=%s AND status='مكتمل'
            """, (emp.name, l.leave))[0][0] or 0

            allowed = float(l.days) if l.days else 0
            percentage = round((used_days / allowed) * 100, 2) if allowed > 0 else 0

            data.append({
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "leave_type": l.leave_name or l.leave,
                "allowed_days": allowed,
                "used_days": used_days,
                "percentage": percentage
            })
    return data