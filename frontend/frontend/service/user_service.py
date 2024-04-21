from ..repository.user_repository import select_all, select_user_by_email

def select_all_user_serice():
    users = select_all()
    print(users)
    return users

def selec_user_by_email_service(email: str):
    if(len(email) != 0):
        return select_user_by_email(email)
    else:
        return select_all()