import asyncio
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Clan(Base):
    __tablename__ = 'clans'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("Member", back_populates="clan", cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = 'members'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    clan_id = Column(Integer, ForeignKey('clans.id'), nullable=False)
    rank = Column(String(50), default="Unknown")
    is_online = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    clan = relationship("Clan", back_populates="members")

class Database:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
    
    async def initialize(self):
        """Initialize the database and create tables"""
        # Check if DATABASE_URL is provided (for PostgreSQL on Render)
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # PostgreSQL for production (Render)
            # Fix the URL format if needed (Render sometimes uses postgres:// instead of postgresql://)
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            self.engine = create_engine(database_url, echo=False)
            print("Using PostgreSQL database for production")
        else:
            # SQLite for local development
            self.engine = create_engine('sqlite:///protanki_bot.db', echo=False)
            print("Using SQLite database for local development")
        
        # Create all tables
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get a database session"""
        return self.SessionLocal()
    
    async def add_clan(self, name: str) -> bool:
        """Add a new clan"""
        session = self.get_session()
        try:
            # Check if clan already exists
            existing_clan = session.query(Clan).filter(Clan.name == name).first()
            if existing_clan:
                return False
            
            new_clan = Clan(name=name)
            session.add(new_clan)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding clan: {e}")
            return False
        finally:
            session.close()
    
    async def get_clans(self) -> list:
        """Get all clans"""
        session = self.get_session()
        try:
            clans = session.query(Clan).all()
            return [(clan.id, clan.name) for clan in clans]
        finally:
            session.close()
    
    async def add_member(self, username: str, clan_id: int) -> bool:
        """Add a member to a clan"""
        session = self.get_session()
        try:
            # Check if member already exists in any clan
            existing_member = session.query(Member).filter(Member.username == username).first()
            if existing_member:
                return False
            
            # Check if clan exists
            clan = session.query(Clan).filter(Clan.id == clan_id).first()
            if not clan:
                return False
            
            new_member = Member(username=username, clan_id=clan_id)
            session.add(new_member)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error adding member: {e}")
            return False
        finally:
            session.close()
    
    async def get_clan_members(self, clan_id: int):
        """Get all members of a clan"""
        session = self.get_session()
        try:
            clan = session.query(Clan).filter(Clan.id == clan_id).first()
            if not clan:
                return None, []
            
            members = session.query(Member).filter(Member.clan_id == clan_id).all()
            return clan, members
        finally:
            session.close()
    
    async def get_all_members(self):
        """Get all members for monitoring"""
        session = self.get_session()
        try:
            members = session.query(Member).all()
            return members
        finally:
            session.close()
    
    async def update_member_status(self, username: str, rank: str, is_online: bool):
        """Update member status and rank"""
        session = self.get_session()
        try:
            member = session.query(Member).filter(Member.username == username).first()
            if member:
                member.rank = rank
                member.is_online = is_online
                member.last_updated = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error updating member status: {e}")
            return False
        finally:
            session.close()
    
    async def remove_clan(self, name: str) -> bool:
        """Remove a clan and all its members"""
        session = self.get_session()
        try:
            clan = session.query(Clan).filter(Clan.name == name).first()
            if clan:
                session.delete(clan)  # This will cascade delete all members
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            print(f"Error removing clan: {e}")
            return False
        finally:
            session.close()

# Global database instance
db = Database()
