# TODO: Using date.today() function for current date -- should the DB now() be
# used instead?

# Load Postgres PW
from dotenv import load_dotenv

# Env vars
import os

# Postgres connectivity
from sqlalchemy import (
    MetaData,
    case,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.exc import SQLAlchemyError

# Load environment vars (necessary for prod only)
load_dotenv()

POSTGRES_USR = os.environ.get("POSTGRES_USR")
POSTGRES_PW = os.environ.get("POSTGRES_PW")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT")
POSTGRES_SCHEMA = os.environ.get("POSTGRES_SCHEMA")

# Engine for DB transactions
# https://docs.sqlalchemy.org/en/20/tutorial/dbapi_transactions.html
engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USR}:{POSTGRES_PW}@localhost:{POSTGRES_PORT}/{POSTGRES_SCHEMA}"
)
# Load all schema tables as SQLAlchemy objects
# https://docs.sqlalchemy.org/en/20/core/reflection.html#reflecting-all-tables-at-once
metadata_obj = MetaData()
metadata_obj.reflect(bind=engine)
jammer_tbl = metadata_obj.tables["jammer"]
pomodoro_tbl = metadata_obj.tables["pomodoro"]
todo_tbl = metadata_obj.tables["todo"]


# Error handling
def raise_error(e):
    print("Error:", type(e))
    print("Msg:", e.args)
    raise e


# SELECT statements


# jammer table


def slct_jammer_info(email):
    try:
        stmt = select(
            jammer_tbl.c.jammer_id,
            jammer_tbl.c.email,
            jammer_tbl.c.jammer_pw,
            jammer_tbl.c.username,
        ).where(jammer_tbl.c.email == email)
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# Get password to check when changing
def slct_jammer_pw(jammer_id):
    try:
        stmt = select(jammer_tbl.c.jammer_pw).where(jammer_tbl.c.jammer_id == jammer_id)
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)


# Used to populate index
def slct_jammer_usr_sets(jammer_id):
    # Returns jammer_id, date_worked, daily_goal_hrs, daily_goal_hrs,
    # work_time_secs, & break_time_secs
    try:
        stmt = select(
            jammer_tbl.c.work_time_secs,
            jammer_tbl.c.break_time_secs,
            jammer_tbl.c.daily_goal_hrs,
        ).where(jammer_tbl.c.jammer_id == jammer_id)
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# todo table


def slct_todo_crnt_order(todo_id):
    try:
        stmt = select(todo_tbl.c.list_order).where(todo_tbl.c.todo_id == todo_id)
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def slct_todo_next_num(jammer_id):
    try:
        stmt = (
            select(todo_tbl.c.list_order)
            .where(todo_tbl.c.jammer_id == jammer_id, todo_tbl.c.is_complete == False)
            .order_by(todo_tbl.c.list_order.desc())
        )
        last_num = None
        with engine.connect() as conn:
            last_num = conn.execute(stmt).mappings().first()
        last_num = last_num["list_order"] if last_num else 0
        return last_num + 1
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def slct_todo_next_for_jammer(jammer_id):
    """Return first To Do in list for jammer"""
    try:
        stmt = (
            select(todo_tbl.c.todo_id, todo_tbl.c.todo_description)
            .where(todo_tbl.c.jammer_id == jammer_id, todo_tbl.c.is_complete == False)
            .order_by(todo_tbl.c.list_order)
        )
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def slct_todo_todos(jammer_id):
    try:
        stmt = (
            select(
                todo_tbl.c.todo_id,
                todo_tbl.c.list_order,
                todo_tbl.c.todo_description,
            )
            .where(todo_tbl.c.jammer_id == jammer_id, todo_tbl.c.is_complete == False)
            .order_by(todo_tbl.c.list_order)
        )
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().all()
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# pomodoro table


# Used to update user pomodoros on change
def slct_pomodoro_usr_cmplt_by_date(jammer_id, date):
    try:
        stmt = select(
            func.coalesce(
                select(func.sum(pomodoro_tbl.c.duration_secs))
                .join(jammer_tbl)
                .where(
                    jammer_tbl.c.jammer_id == jammer_id,
                    pomodoro_tbl.c.completed_date == date,
                )
                .scalar_subquery(),
                0,
            ).label("duration_secs")
        )
        with engine.connect() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# INSERT statements


# TODO: Refactor to use named dict of cols to insert instead -- won't have to
# program query that way
def insert_jammer(username, email, hashed_password):
    try:
        stmt = insert(jammer_tbl).values(
            email=email, jammer_pw=hashed_password, username=username
        )
        with engine.begin() as conn:
            return conn.execute(stmt).inserted_primary_key
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# Used when work Pomodoro complete
# TODO: Refactor to use named dict of cols to insert instead -- won't have to
# program query that way
def insert_pomodoro(jammer_id, completed_date, duration_secs):
    try:
        # TODO: Handle cases where User ID no longer exists???
        stmt = insert(pomodoro_tbl).values(
            jammer_id=jammer_id,
            completed_date=completed_date,
            duration_secs=duration_secs,
        )
        with engine.begin() as conn:
            return conn.execute(stmt).inserted_primary_key
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def insert_todo(jammer_id, todo_description):
    try:
        # Look up highest TODO number in list & increment if found, just use
        # "1" if not
        next_list_num = slct_todo_next_num(jammer_id)
        stmt = insert(todo_tbl).values(
            jammer_id=jammer_id,
            todo_description=todo_description,
            list_order=next_list_num,
        )
        with engine.begin() as conn:
            return conn.execute(stmt).inserted_primary_key
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# UPDATE statements


def updt_jammer_pw(jammer_id, new_password):
    try:
        stmt = (
            update(jammer_tbl)
            .where(jammer_tbl.c.jammer_id == jammer_id)
            .values(jammer_pw=new_password)
            .returning(jammer_tbl.c.jammer_id)
        )
        with engine.begin() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def updt_jammer_pom_sets(jammer_id, work_time, break_time, daily_goal_hrs):
    try:
        stmt = (
            update(jammer_tbl)
            .where(jammer_tbl.c.jammer_id == jammer_id)
            .values(
                work_time_secs=work_time,
                break_time_secs=break_time,
                daily_goal_hrs=daily_goal_hrs,
            )
            .returning(jammer_tbl.c.jammer_id)
        )
        with engine.begin() as conn:
            return conn.execute(stmt).mappings().first()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def updt_todo_cmplt_one(todo_id, completed_date):
    try:
        stmt = (
            update(todo_tbl)
            .where(todo_tbl.c.todo_id == todo_id)
            .values(is_complete=True, completed_date=completed_date, list_order=0)
        )
        with engine.begin() as conn:
            return conn.execute(stmt).mappings()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def updt_todo_cmplt_all(jammer_id, completed_date):
    try:
        stmt = (
            update(todo_tbl)
            .where(todo_tbl.c.jammer_id == jammer_id)
            .values(is_complete=True, completed_date=completed_date, list_order=0)
        )
        with engine.begin() as conn:
            return conn.execute(stmt).mappings()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def updt_todo_lst_ord(jammer_id, todo_id, new_position):
    try:
        valid_positions = ("first", "up", "down", "last")
        if new_position not in valid_positions:
            raise Exception("Invalid position submitted for To Do")

        # Current order of list item
        current_order = slct_todo_crnt_order(todo_id)
        current_order = int(current_order["list_order"]) if current_order else None
        # Last number of item in list + 1
        next_order = slct_todo_next_num(jammer_id)
        if not current_order or not next_order:
            raise Exception("Error fetching orders of list items")

        # Populate statements based on list orders
        match new_position:
            # Move target todo to first in list, those above it now below
            case "first":
                stmt = (
                    update(todo_tbl)
                    .where(
                        todo_tbl.c.jammer_id == jammer_id,
                    )
                    .values(
                        list_order=case(
                            (todo_tbl.c.list_order == current_order, 1),
                            (todo_tbl.c.list_order < current_order, todo_tbl.c.list_order + 1),
                            else_=todo_tbl.c.list_order
                        )
                    )
                )
            # Move target todo up one in list
            case "up":
                stmt = (
                    update(todo_tbl)
                    .where(
                        todo_tbl.c.jammer_id == jammer_id,
                    )
                    .values(
                        list_order=case(
                            (todo_tbl.c.list_order == current_order, current_order - 1),
                            (todo_tbl.c.list_order == current_order - 1, current_order),
                            else_=todo_tbl.c.list_order
                        )
                    )
                )
            # Move target todo down one in list
            case "down":
                stmt = (
                    update(todo_tbl)
                    .where(
                        todo_tbl.c.jammer_id == jammer_id,
                    )
                    .values(
                        list_order=case(
                            (todo_tbl.c.list_order == current_order, current_order + 1),
                            (todo_tbl.c.list_order == current_order + 1, current_order),
                            else_=todo_tbl.c.list_order
                        )
                    )
                )
            # Move target todo to last in list, those below now above
            case "last":
                stmt = (
                    update(todo_tbl)
                    .where(
                        todo_tbl.c.jammer_id == jammer_id,
                    )
                    .values(
                        list_order=case(
                            (todo_tbl.c.list_order == current_order, next_order - 1),
                            (todo_tbl.c.list_order > current_order, todo_tbl.c.list_order - 1),
                            else_=todo_tbl.c.list_order
                        )
                    )
                )
        # TODO: Why stmt always flagged as possibly unbound, even with null
        # check?
        with engine.begin() as conn:
            conn.execute(stmt)
            return
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


# DELETE statements
# Just used for test scripts right now


def delete_all():
    try:
        stmts = [
            delete(todo_tbl),
            delete(pomodoro_tbl),
            delete(jammer_tbl),
        ]
        with engine.begin() as conn:
            for s in stmts:
                conn.execute(s)
        return
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def delete_todo_all_incmplt(jammer_id):
    try:
        stmt = delete(todo_tbl).where(
            todo_tbl.c.jammer_id == jammer_id, todo_tbl.c.is_complete == False
        )
        with engine.begin() as conn:
            return conn.execute(stmt).mappings()
    except SQLAlchemyError as e:
        raise_error(e)
    except AttributeError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)


def delete_todo_one(todo_id):
    try:
        stmt = (
            delete(todo_tbl).where(todo_tbl.c.todo_id == todo_id)
        )
        with engine.begin() as conn:
            conn.execute(stmt)
            return
    except SQLAlchemyError as e:
        raise_error(e)
    except Exception as e:
        raise_error(e)
