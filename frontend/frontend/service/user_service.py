from ..repository.user_repository import select_all

def select_all_user_serice():
    users = select_all()
    print(users)
    return users