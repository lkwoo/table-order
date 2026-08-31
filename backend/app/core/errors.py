"""U0 Core - 표준 오류 (business-rules §7).

422 검증 / 401 인증 / 403 타매장 / 404 없음 / 409 중복·전이위반 / 500
"""
from fastapi import HTTPException, status


def unauthorized(msg: str = "인증에 실패했습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)


def forbidden(msg: str = "권한이 없습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)


def not_found(msg: str = "리소스를 찾을 수 없습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)


def conflict(msg: str = "충돌이 발생했습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)


def unprocessable(msg: str = "요청을 처리할 수 없습니다.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=msg)
