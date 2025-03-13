import asyncio
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app import User, Game, Highlight, Video, VideoSegment, Task, UserRole, TaskType, TaskStatus
from app.core import Base
from app.db import SQLAlchemyRepository, SQLAlchemyUnitOfWork
from app.db.crud import UserRepository


# Fixtures for the test session

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create an in-memory SQLite database engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    """Create a session factory for testing."""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return async_session


@pytest_asyncio.fixture
async def session(session_factory):
    """Get a session for testing."""
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def uow(session):
    """Get a unit of work for testing."""

    def session_provider():
        return session

    uow = SQLAlchemyUnitOfWork(session_provider)
    async with uow:
        yield uow


# Test data fixtures

@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    return User(
        username="testuser",
        password_hash="hashed_password",
        role=UserRole.USER,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_game():
    """Create a sample game for testing."""
    return Game(
        title="Test Game",
        event="Test Event",
        date=datetime.now(),
        white_player="White Player",
        black_player="Black Player",
        pgn_data="1. e4 e5 2. Nf3 Nc6",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_highlight():
    """Create a sample highlight for testing."""
    return Highlight(
        category="Tactic",
        start_move=10,
        end_move=15,
        importance_score=0.8,
        position_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        position_after="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
        description="Test highlight",
        detected_by="engine"
    )


@pytest.fixture
def sample_video():
    """Create a sample video for testing."""
    return Video(
        original_video_url="http://example.com/original.mp4",
        processed_video_url="http://example.com/processed.mp4",
        status="completed"
    )


@pytest.fixture
def sample_video_segment():
    """Create a sample video segment for testing."""
    return VideoSegment(
        start_time=10,
        end_time=20,
        sequence_order=1
    )


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        type=TaskType.GAME_ANALYSIS,
        status=TaskStatus.PENDING,
        game_id=1,
        user_id=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestModels:
    """Test cases for SQLModel models."""

    def test_user_model_init(self, sample_user):
        """Test that a User model can be initialized with correct values."""
        assert sample_user.username == "testuser"
        assert sample_user.password_hash == "hashed_password"
        assert sample_user.role == UserRole.USER
        assert sample_user.created_at is not None
        assert sample_user.updated_at is not None

    def test_game_model_init(self, sample_game):
        """Test that a Game model can be initialized with correct values."""
        assert sample_game.title == "Test Game"
        assert sample_game.event == "Test Event"
        assert sample_game.white_player == "White Player"
        assert sample_game.black_player == "Black Player"
        assert sample_game.pgn_data == "1. e4 e5 2. Nf3 Nc6"
        assert sample_game.created_at is not None
        assert sample_game.updated_at is not None

    def test_task_model_init(self, sample_task):
        """Test that a Task model can be initialized with correct values."""
        assert sample_task.type == TaskType.GAME_ANALYSIS
        assert sample_task.status == TaskStatus.PENDING
        assert sample_task.error_message is None
        assert sample_task.game_id == 1
        assert sample_task.user_id == 1
        assert sample_task.created_at is not None


class TestRepository:
    """Test cases for SQLAlchemyRepository."""

    @pytest.mark.asyncio
    async def test_create(self, session, sample_user):
        """Test creating a new record."""
        repo = SQLAlchemyRepository(session, User)
        created_user = await repo.create(sample_user)

        await session.commit()

        assert created_user.id is not None
        assert created_user.username == "testuser"
        assert created_user.role == UserRole.USER

    @pytest.mark.asyncio
    async def test_get(self, session, sample_user):
        """Test retrieving a record by ID."""
        repo = SQLAlchemyRepository(session, User)
        created_user = await repo.create(sample_user)
        await session.commit()

        retrieved_user = await repo.get(created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_all(self, session):
        """Test retrieving all records."""
        repo = SQLAlchemyRepository(session, User)

        # Create two users
        user1 = User(username="testuser1", password_hash="hash1", role=UserRole.USER)
        user2 = User(username="testuser2", password_hash="hash2", role=UserRole.MANAGER)

        await repo.create(user1)
        await repo.create(user2)

        await session.commit()

        users = await repo.get_all()

        assert len(users) >= 2
        assert any(u.username == "testuser1" for u in users)
        assert any(u.username == "testuser2" for u in users)

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, session):
        """Test retrieving filtered records."""
        repo = SQLAlchemyRepository(session, User)

        # Create users with different roles
        user1 = User(username="filter_user1", password_hash="hash1", role=UserRole.USER)
        user2 = User(username="filter_user2", password_hash="hash2", role=UserRole.MANAGER)

        await repo.create(user1)
        await repo.create(user2)

        # Filter by role
        managers = await repo.get_all(role=UserRole.MANAGER)

        assert any(u.username == "filter_user2" for u in managers)
        assert not any(u.username == "filter_user1" for u in managers)

    @pytest.mark.asyncio
    async def test_update(self, session, sample_user):
        """Test updating a record."""
        repo = SQLAlchemyRepository(session, User)
        created_user = await repo.create(sample_user)

        created_user.username = "updated_username"
        updated_user = await repo.update(created_user)

        await session.commit()

        assert updated_user.username == "updated_username"

        # Verify in the database
        retrieved_user = await repo.get(created_user.id)
        assert retrieved_user.username == "updated_username"

    @pytest.mark.asyncio
    async def test_delete(self, session):
        """Test deleting a record."""
        repo = SQLAlchemyRepository(session, User)
        user = User(username="delete_user", password_hash="hash", role=UserRole.USER)
        created_user = await repo.create(user)

        await session.commit()

        await repo.delete(created_user.id)

        await session.commit()

        retrieved_user = await repo.get(created_user.id)
        assert retrieved_user is None


class TestUserRepository:
    """Test cases specifically for UserRepository."""

    @pytest.mark.asyncio
    async def test_get_by_username(self, session, sample_user):
        """Test retrieving a user by username."""
        user_repo = UserRepository(session)
        sample_user.username = "unique_username"
        await user_repo.create(sample_user)

        retrieved_user = await user_repo.get_by_username("unique_username")

        assert retrieved_user is not None
        assert retrieved_user.username == "unique_username"
        assert retrieved_user.password_hash == "hashed_password"

    @pytest.mark.asyncio
    async def test_get_with_relationships(self, uow, sample_user, sample_game, sample_task):
        """Test retrieving a user with its relationships."""
        # Create user and flush to get the ID
        sample_user.username = "relationship_test_user"
        await uow.user.create(sample_user)
        await uow.session.flush()  # Ensure the user ID is available

        # Create game linked to user
        sample_game.user_id = sample_user.id
        await uow.game.create(sample_game)
        await uow.session.flush()  # Ensure the game ID is available

        # Create task linked to user and game
        sample_task.user_id = sample_user.id
        sample_task.game_id = sample_game.id
        await uow.task.create(sample_task)

        # Retrieve user with relationships
        retrieved_user = await uow.user.get(sample_user.id)

        assert len(retrieved_user.games) >= 1
        assert any(g.title == "Test Game" for g in retrieved_user.games)
        assert len(retrieved_user.tasks) >= 1


class TestUnitOfWork:
    """Test cases for SQLAlchemyUnitOfWork."""

    @pytest.mark.asyncio
    async def test_repositories_initialization(self, uow):
        """Test that repositories are initialized correctly."""
        assert uow.user is not None
        assert uow.game is not None
        assert uow.highlight is not None
        assert uow.video is not None
        assert uow.video_segment is not None
        assert uow.task is not None

    @pytest.mark.asyncio
    async def test_commit(self, session_factory):
        """Test that committing a transaction works."""
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            user = User(username="commit_test", password_hash="hash", role=UserRole.USER)
            await uow.user.create(user)
            await uow.commit()

            # Check that the user was created
            retrieved_user = await uow.user.get_by_username("commit_test")
            assert retrieved_user is not None

    @pytest.mark.asyncio
    async def test_rollback(self, session_factory):
        """Test that rolling back a transaction works."""
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            user = User(username="rollback_test", password_hash="hash", role=UserRole.USER)
            await uow.user.create(user)

            # Rollback before committing
            await uow.rollback()

            # The user should not be in the database
            retrieved_user = await uow.user.get_by_username("rollback_test")
            assert retrieved_user is None

    @pytest.mark.asyncio
    async def test_exception_handling(self, session_factory):
        """Test transaction rollback on exception."""
        try:
            async with SQLAlchemyUnitOfWork(session_factory) as uow:
                user = User(username="exception_test", password_hash="hash", role=UserRole.USER)
                await uow.user.create(user)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Start a new UoW to verify no user was saved
        async with SQLAlchemyUnitOfWork(session_factory) as uow:
            retrieved_user = await uow.user.get_by_username("exception_test")
            assert retrieved_user is None


class TestRelationships:
    """Test cases for SQLModel relationships."""

    @pytest.mark.asyncio
    async def test_user_game_relationship(self, uow, sample_user, sample_game):
        """Test the relationship between User and Game."""
        # Create user and game
        user = await uow.user.create(sample_user)
        await uow.session.flush()

        game = sample_game
        game.user_id = user.id
        game = await uow.game.create(game)
        await uow.session.flush()

        # Verify relationships
        retrieved_user = await uow.user.get(user.id)
        assert any(g.id == game.id for g in retrieved_user.games)

        retrieved_game = await uow.game.get(game.id)
        assert retrieved_game.user.id == user.id

    @pytest.mark.asyncio
    async def test_game_highlight_relationship(self, uow, sample_user, sample_game, sample_highlight):
        """Test the relationship between Game and Highlight."""
        # Setup
        user = await uow.user.create(sample_user)
        await uow.session.flush()
        game = sample_game
        game.user_id = user.id
        game = await uow.game.create(game)
        await uow.session.flush()

        highlight = sample_highlight
        highlight.game_id = game.id
        highlight = await uow.highlight.create(highlight)
        await uow.session.flush()

        # Verify relationships
        retrieved_game = await uow.game.get(game.id)
        assert any(h.id == highlight.id for h in retrieved_game.highlights)

        retrieved_highlight = await uow.highlight.get(highlight.id)
        assert retrieved_highlight.game.id == game.id

    @pytest.mark.asyncio
    async def test_task_relationships(self, uow, sample_user, sample_game):
        """Test task relationships with user and game."""
        # Setup
        user = await uow.user.create(sample_user)
        await uow.session.flush()
        game = sample_game
        game.user_id = user.id
        game = await uow.game.create(game)
        await uow.session.flush()

        task = Task(
            type=TaskType.GAME_ANALYSIS,
            status=TaskStatus.PENDING,
            game_id=game.id,
            user_id=user.id
        )
        task = await uow.task.create(task)
        await uow.session.flush()

        # Verify
        retrieved_user = await uow.user.get(user.id)
        assert any(t.id == task.id for t in retrieved_user.tasks)

        retrieved_game = await uow.game.get(game.id)
        assert any(t.id == task.id for t in retrieved_game.tasks)
