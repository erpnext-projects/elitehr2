import frappe
from frappe.auth import LoginManager


@frappe.whitelist(allow_guest=True)
def login(username, password):

    login_manager = LoginManager()
    login_manager.authenticate(username, password)
    login_manager.post_login()

    user = frappe.get_doc("User", frappe.session.user)

    # Always refresh api_key and api_secret on login
    user.api_key = frappe.generate_hash(length=15)
    user.api_secret = frappe.generate_hash(length=15)
    user.save(ignore_permissions=True)

    api_secret = user.get_password("api_secret")

    access_token = f"{user.api_key}:{api_secret}"

    return {
        "access_token": access_token,
        "user": user.name,
        "full_name": user.full_name
    }


@frappe.whitelist()
def logout():

    user = frappe.session.user
    user_doc = frappe.get_doc("User", user)

    user_doc.api_key = None
    user_doc.api_secret = None
    user_doc.save(ignore_permissions=True)

    frappe.sessions.clear_sessions(user=user)
    frappe.local.login_manager.logout()
    return {
        "message": "Logged out successfully"
    }