import frappe


def after_uninstall():
    """Called when the app is uninstalled from a site.

    We want to clean up artifacts that were created during install.  At a
    minimum the administrative user that we create for demo/initial setup
    should be removed so that the site doesn't retain a stale user.
    """
    delete_admin_user()
    delete_hr_role()



def delete_admin_user():
    email = "hradmin@company.local"
    if frappe.db.exists("User", email):
        try:
            frappe.delete_doc("User", email, force=True)
            frappe.db.commit()
            frappe.clear_cache(user=email)
            print(f"Success: removed user {email} during uninstall")
        except Exception as e:
            frappe.log_error(f"Failed to delete user {email} on uninstall: {e}",
                             "elitehr2.uninstall.delete_admin_user")
    else:
        print(f"User {email} not present, nothing to delete")


def delete_hr_role():
    """Optionally remove the custom role we created during install."""
    role_name = "Elite HR Admin"
    if frappe.db.exists("Role", role_name):
        try:
            frappe.delete_doc("Role", role_name, force=True)
            frappe.db.commit()
            print(f"Success: removed role {role_name} during uninstall")
        except Exception as e:
            frappe.log_error(f"Failed to delete role {role_name} on uninstall: {e}",
                             "elitehr2.uninstall.delete_hr_role")
    else:
        print(f"Role {role_name} not present, nothing to delete")
