"""U3 Order - 고객 주문 라우터 (세션 토큰)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import SessionContext, get_current_session
from app.order import service
from app.order.schemas import OrderCreate, OrderOut

router = APIRouter(prefix="/api/orders", tags=["order"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreate, ctx: SessionContext = Depends(get_current_session)):
    return service.create_order(ctx, body.idempotency_key, body.items)


@router.get("", response_model=list[OrderOut])
def list_orders(ctx: SessionContext = Depends(get_current_session), db: Session = Depends(get_db)):
    return service.list_current_orders(db, ctx)
