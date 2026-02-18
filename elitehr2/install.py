import frappe


# def before_install():
#     frappe.db.set_value("Installed Application",{"app_name":"Elite_hr"},"is_setup_complete",0)
#     frappe.db.commit()
#     frappe.db.set_value("Installed Application",{"app_name":"frappe"},"is_setup_complete",0)
#     frappe.db.commit()
#     frappe.db.set_value("System Settings","System Settings","setup_complete",0)
#     frappe.db.commit()
#     frappe.clear_cache()

def after_install():
    # frappe.db.set_value("Installed Application",{"app_name":"frappe"},"is_setup_complete",0)
    frappe.db.set_value("System Settings","System Settings","language","ar")
    frappe.db.commit()

    # disallow_user_create_workspace()
    create_hr_role()
    create_admin_user()
    

    # frappe.db.set_default("desktop:setup_complete", 1)
    # frappe.db.set_value("System Settings", None, "setup_complete", 1)
    # frappe.db.commit()

# def disallow_user_create_workspace():
    # frappe.db.delete(
    #     "DocPerm",
    #         {
    #             "parent": "Workspace",
    #             "role": "Desk User"
    #         }
    # )
    # workspaces = frappe.get_all("Workspace", filters={"module": ["!=", "Elite Hr"]}, fields=["name"])
    # for ws in workspaces:
    #     frappe.db.set_value("Workspace", ws.name, "public", 0)
    # frappe.db.commit()

def create_hr_role():
    role_name = "Elite HR Admin"
    if not frappe.db.exists("Role", role_name):
        frappe.get_doc({
            "doctype": "Role",
            "role_name": role_name
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        print("Success Create Role: {role_name}")

def create_admin_user():
    email = "hradmin@company.local"
    password = "Admin@123!"
    role_name = "Elite HR Admin"
    module_name = "EliteHr"


    if not frappe.db.exists("User", email):
        user = frappe.get_doc({
            "doctype": "User",
            "email": email,
            "first_name": "HR Admin",
            "user_type": "System User",
            "enabled": 1,
            "send_welcome_email": 0,
            "new_password": password,
            "language": "ar"
            # "module_profile": profile_name
        })
        user.append("roles", {"role": role_name})
        user.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Success Create User: {email}")
        allow_only_specific_module(email, module_name)
        roles = [
            "Elitehr Branches",
            "Elitehr Employee",
            "Elitehr Attendance",
            "Elitehr Attendance Status",
            "Elitehr Tasks",
            "Elitehr Attachments",
            "Elitehr Deduction Levels",
            "Elitehr Deduction Rules",
            "Elitehr Late And Early Exit Rules",
            "Elitehr Attendance Rules",
            "Elitehr Shift Assign Tool",
            "Elitehr Shift Schedule Assign Tool",
            "Elitehr Shifts",
            "Elitehr Shift Schedule",
            "Elitehr Shifts Days",
            "Elitehr Attendance Correction Request",
            "Elitehr Leaves",
            "Elitehr Supply Contract",
            "Elitehr Resignations",
            "Elitehr Employment",
            "Elitehr Org Structure",
            "Eliteht Employee Contracts",
            "Elitehr Leave Policies",
            "Elitehr Short Leave Requests",
            "Elitehr Business Trip Request",
            "Elitehr Leave Policies Rules",
            "Elitehr Leave Policies",
            "Elitehr Employee Leaves Child Table",
            "Elitehr Extra Work",
            "Elitehr Projects",
            "Elitehr Team",
            "Eitehr Settings",
            "Elitehr Company",
            "Elitehr Users",
            "Elitehr Users",
            "Elite Themes",
            "Elitehr Fingerprint Sites",
            "Elitehr Security Settings",
            "Elitehr Requests"
        ]
        for r in roles:
            allow_role_read_doctype(role_name,r)

    else:
        print(f"User {email} exists.")


def allow_only_specific_module(email, allowed_module_name):
    if not frappe.db.exists("User", email):
        print(f"error: user not found {email}.")
        return

    user = frappe.get_doc("User", email)
    
    all_modules = [d.name for d in frappe.get_all("Module Def")]


    if allowed_module_name not in all_modules:
        print(f"error module not found: '{allowed_module_name}'.")
        print(f"avaliable modules:  {all_modules}")
        return

    user.set("block_modules", [])
    for module in all_modules:
        if module != allowed_module_name:
            user.append("block_modules", {
                "module": module
            })
    
    user.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache(user=email)
    print(f"Success link user {email} with only module : {allowed_module_name}")


def allow_role_read_doctype(role_name, doctype_name):
    # Check if permission already exists
    exists = frappe.db.exists(
        "DocPerm",
        {
            "parent": doctype_name,
            "role": role_name,
            "permlevel": 0
        }
    )

    if exists:
        print(f"Permission already exists: {role_name} -> {doctype_name}")
        return

    doc = frappe.get_doc("DocType", doctype_name)

    doc.append("permissions", {
        "role": role_name,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "permlevel": 0
    })

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache()

    print(f"Success: Role '{role_name}' can READ '{doctype_name}'")

def disallow_user_create_workspace():
    # 1️⃣ DocPerm
    doc_perms = frappe.get_all(
        "DocPerm",
        filters={
            "parent": "Workspace",
            "role": "Desk User"
        },
        fields=["name"]
    )

    for perm in doc_perms:
        frappe.db.set_value("DocPerm", perm.name, "create", 0)

    # 2️⃣ Custom DocPerm
    custom_perms = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "Workspace",
            "role": "Desk User"
        },
        fields=["name"]
    )
    for perm in custom_perms:
        frappe.db.set_value("Custom DocPerm", perm.name, "create", 0)
    

    frappe.db.commit()
    frappe.clear_cache()
    print("Success: Desk User cannot CREATE Workspace")
    
