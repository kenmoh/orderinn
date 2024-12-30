from fastapi import HTTPException, status
from appwrite.exception import AppwriteException
from appwrite.id import ID
from appwrite.role import Role
from appwrite.permission import Permission


from app.schemas.user_schemas import (
    CreateMembershipSchema,
    CreateUserSchema,
    CreateteamSchema,
    UpdateMembershipSchema,
)
from app.utils import appwrite


def create_company_team(company_id: str):
    """
    Create teams for a company with different roles.

    Args:
        company_id (str): The ID of the company for which to create teams.
    """

    roles = ["owner", "manager", "chef", "waiter", "laundry-attendant"]

    for role in roles:
        team_name = f"{role}-{company_id}"
        appwrite.team.create(team_id=ID.unique(),
                             name=team_name, roles=["owner"])


def get_users():
    try:
        return appwrite.user.list()
    except AppwriteException as e:
        return e.message


def create_company_user(data: CreateUserSchema):
    try:
        new_user = appwrite.account.create(
            ID.unique(),
            email=data.email,
            password=data.password,
            name=data.name,
        )

        new_user = appwrite.user.update_labels(
            new_user["$id"], labels=["company"])
        create_company_team(new_user["$id"])

        return new_user

    except AppwriteException as e:
        return e.message


def create_guest_user(data: CreateUserSchema):
    try:
        new_user = appwrite.account.create(
            ID.unique(),
            email=data.email,
            password=data.password,
            name=data.name or None,
        )

        new_user = appwrite.user.update_labels(
            new_user["$id"], labels=["guest"])
        return new_user
    except AppwriteException as e:
        return e.message


def create_team(teamData: CreateteamSchema):
    teams = appwrite.team.list()
    for team in teams.get('teams'):
        if team.get('name') == teamData.name:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail='A team with this name already exists.')
    try:
        return appwrite.team.create(team_id=ID.unique(), name=teamData.name)
    except AppwriteException as e:
        return e.message


def create_team_member(company_id: str, member: CreateMembershipSchema):

    # return appwrite.team.create_membership(
    #     team_id=member.team_id,
    #     name=member.name,
    #     email=member.email,
    #     roles=[f'waiter-{company_id}'],
    # )

    try:
        if member.team_name == f'manager-{company_id}':
            return appwrite.team.create_membership(
                team_id=member.team_id,
                name=member.name,
                email=member.email,
                roles=[f'manager-{company_id}'],
            )
        elif member.team_name == f'chef-{company_id}':
            return appwrite.team.create_membership(
                team_id=member.team_id,
                name=member.name,
                email=member.email,
                roles=[f'chef-{company_id}'],
            )
        elif member.team_name == f'water-{company_id}':
            return appwrite.team.create_membership(
                team_id=member.team_id,
                name=member.name,
                email=member.email,
                roles=[f'waiter-{company_id}'],
            )
        elif member.team_name == f'laundry-attendant-{company_id}':
            return appwrite.team.create_membership(
                team_id=member.team_id,
                name=member.name,
                email=member.email,
                roles=[f'laundry-attendant-{company_id}'],
            )
    except AppwriteException as e:
        return e.message


def update_team_member_role(
    team_id: str, company_id: str, membership_id: str, role: UpdateMembershipSchema
):
    try:
        if role.permission == f"manager-{company_id}":
            return appwrite.team.update_membership(
                team_id=team_id,
                membership_id=membership_id,
                roles=[
                    Permission.read(Role.team(f"manager-{company_id}")),
                    Permission.create(Role.team(f"manager-{company_id}")),
                    Permission.update(Role.team(f"manager-{company_id}")),
                ],
            )
        elif role.permission == f"chef-{company_id}":
            return appwrite.team.update_membership(
                team_id=team_id,
                membership_id=membership_id,
                roles=[
                    Permission.read(Role.team(f"chef-{company_id}")),
                    Permission.update(Role.team(f"chef-{company_id}")),
                ],
            )
        elif role.permission == f"waite-{company_id}":
            return appwrite.team.update_membership(
                team_id=team_id,
                membership_id=membership_id,
                roles=[
                    Permission.read(Role.team(f"waiter-{company_id}")),
                    Permission.update(Role.team(f"waiter-{company_id}")),
                ],
            )
        elif role.permission == f"laundry-attendant-{company_id}":
            return appwrite.team.update_membership(
                team_id=team_id,
                membership_id=membership_id,
                roles=[
                    Permission.read(
                        Role.team(f"laundry-attendant-{company_id}")),
                    Permission.update(
                        Role.team(f"laundry-attendant-{company_id}")),
                ],
            )
    except AppwriteException as e:
        return e.message


def get_membership(team_id: str, membership_id: str):
    try:
        return appwrite.team.get_membership(
            team_id=team_id, membership_id=membership_id
        )

    except AppwriteException as e:
        return e.message


def get_teams():
    try:
        return appwrite.team.list()
    except AppwriteException as e:
        return e.message


def get_company_teams(company_id: str):
    try:
        teams = appwrite.team.list().get("teams")
        return [team for team in teams if team["name"].split("-")[-1] == company_id]
    except AppwriteException as e:
        return e.message
