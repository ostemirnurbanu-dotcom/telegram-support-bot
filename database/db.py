import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

async def create_pool():
	return await asyncpg.create_pool(DATABASE_URL)

async def create_request(pool, telegram_id, name, phone, problem):
	await pool.execute(
		"""
		INSERT INTO requests (telegram_id, name, phone, problem)
		VALUES ($1, $2, $3, $4)
		""",
		telegram_id,
		name,
		phone,
		problem
	)

async def get_user_requests(pool, telegram_id):
	return await pool.fetch(
		"""
		SELECT id, problem, status, created_at
		FROM requests
		WHERE telegram_id = $1
		ORDER BY created_at DESC
		""",
		telegram_id
	)

async def get_user(pool, telegram_id):
	return await pool.fetchrow(
		"""
		SELECT id, telegram_id, name, role
		FROM users
		WHERE telegram_id = $1
		""",
		telegram_id
	)

async def create_user(pool, telegram_id, name):
	await pool.execute(
		"""
		INSERT INTO users (telegram_id, name)
		VALUES ($1, $2)
		ON CONFLICT (telegram_id) DO NOTHING
		""",
		telegram_id,
		name
	)

async def get_all_requests(pool):
	return await pool.fetch(
		"""
		SELECT id, name, phone, problem, status, created_at
		FROM requests
		ORDER BY created_at DESC
		"""
	)

async def get_requests_by_status(pool, status):
	return await pool.fetch(
		"""
		SELECT id, name, phone, problem, status, created_at
		FROM requests
		WHERE status = $1
		""",
		status
	)

async def update_request_status(pool, request_id, status):
	await pool.execute(
		"""
		UPDATE requests
		SET status = $1
		WHERE id = $2
		""",
		status,
		request_id
	)