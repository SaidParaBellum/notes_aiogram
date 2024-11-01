from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

from app.database import async_session_maker


class Base(DeclarativeBase):
    @classmethod
    async def get_all(cls):
        async with async_session_maker() as session:
            query=select(cls)
            result=await session.execute(query)

            return result.scalars().all()

    @classmethod
    async def update(cls,record_id,**data):
        async with async_session_maker() as session:
            query=update(cls).values(**data).filter_by(id=record_id).returning(cls)

            result=await  session.execute(query)
            await session.commit()
            return result.scalar_one()

    @classmethod
    async def delete(cls,filters):
        async with async_session_maker() as session:
            query=delete(cls).filter(filters)
            await session.execute(query)
            await session.commit()


    @classmethod
    async def filter(cls,filters):
        async with async_session_maker() as session:
            query=select(cls).filter(filters)
            result= await session.execute(query)
            return result.scalars().all()


    @classmethod
    async def first(cls,filters):
        async with async_session_maker() as session:
            query=select(cls).filter(filters).limit(1)
            result=await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def pagginate(cls, page, limit, filters=None):
        async with async_session_maker() as session:
            query = select(cls).limit(limit).offset((page - 1) * limit)
            if filters:
                query = query.filter(filters)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def create(cls, **data):
        async with async_session_maker() as session:
            query=cls(**data)
            session.add(query)
            await session.commit()
            return query