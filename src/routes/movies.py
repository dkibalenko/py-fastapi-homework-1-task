from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from database import get_db, MovieModel
from schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number to fetch"),
    per_page: int = Query(
        10,
        ge=1,
        le=20,
        description="Number of movies to fetch per page"
    )
):
    offset = (page - 1) * per_page

    total_items = await db.scalar(select(func.count()).select_from(MovieModel))

    result = await db.execute(
        select(MovieModel).offset(offset).limit(per_page)
    )
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    
    total_pages = (total_items + per_page - 1) // per_page

    # Generate pagination links
    base_url = "/api/v1/theater/movies/"
    prev_page = f"{base_url}?page={page - 1}&per_page={per_page}" \
        if page > 1 else None
    next_page = f"{base_url}?page={page + 1}&per_page={per_page}" \
        if page < total_pages else None

    # Return the response with pagination metadata
    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def read_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )

    return movie
