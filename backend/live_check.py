"""실기동 검증: 백엔드 API 엔드투엔드 시나리오 (SQLite 네이티브 기동 대상)."""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
STORE_ID = "11111111-1111-1111-1111-111111111111"

# Windows 콘솔 UTF-8 출력
sys.stdout.reconfigure(encoding="utf-8")


def call(method, path, body=None, token=None, session=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")  # 관리자 JWT
    if session:
        req.add_header("X-Session-Token", session)  # 테이블 세션 토큰
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


def ok(cond, msg):
    mark = "PASS" if cond else "FAIL"
    print(f"[{mark}] {msg}")
    if not cond:
        globals()["FAILED"] = True


FAILED = False

# 1. 관리자 로그인
st, r = call("POST", "/api/auth/admin-login",
             {"store_id": STORE_ID, "username": "admin", "password": "admin1234"})
ok(st == 200 and "access_token" in r, f"관리자 로그인 (status={st})")
admin_token = r.get("access_token")

# 2. 잘못된 비밀번호 거부
st, r = call("POST", "/api/auth/admin-login",
             {"store_id": STORE_ID, "username": "admin", "password": "wrong"})
ok(st == 401, f"잘못된 비밀번호 401 거부 (status={st})")

# 3. 테이블 생성 (재실행 시 이미 존재하면 허용)
st, r = call("POST", "/api/admin/tables",
             {"table_number": "1", "password": "table1234"}, token=admin_token)
ok(st in (200, 201, 409, 400), f"테이블 생성 (status={st})")

# 4. 테이블 로그인
st, r = call("POST", "/api/auth/table-login",
             {"store_id": STORE_ID, "table_number": "1", "password": "table1234"})
ok(st == 200 and "session_token" in r, f"테이블 로그인 (status={st})")
table_token = r.get("session_token")
table_id = r.get("table_id")

# 5. 메뉴 조회 (테이블 세션 토큰)
st, menus = call("GET", "/api/menus", session=table_token)
flat = []
if isinstance(menus, list):
    for c in menus:
        flat += c.get("menus", []) if isinstance(c, dict) else []
    if not flat and menus and "id" in menus[0]:
        flat = menus
ok(st == 200 and len(flat) >= 2, f"메뉴 조회 ({len(flat)}개 아이템, status={st})")
m1, m2 = flat[0], flat[1]
print(f"      예: {m1['name']} {m1['price']}원 / {m2['name']} {m2['price']}원")

# 6. 주문 생성
order_body = {
    "idempotency_key": "live-check-key-001",
    "items": [
        {"menu_id": m1["id"], "quantity": 2},
        {"menu_id": m2["id"], "quantity": 1},
    ],
}
st, order = call("POST", "/api/orders", order_body, session=table_token)
expected_total = m1["price"] * 2 + m2["price"] * 1
ok(st in (200, 201) and "id" in order, f"주문 생성 (status={st})")
order_id = order.get("id")
total = order.get("total_amount")
ok(total == expected_total, f"총액 불변식: {total} == {expected_total} (단가×수량 합)")

# 7. 멱등성: 같은 키 재요청 → 같은 주문
st, order2 = call("POST", "/api/orders", order_body, session=table_token)
ok(st in (200, 201) and order2.get("id") == order_id,
   f"멱등성: 동일 idempotency_key → 동일 주문 (id 일치={order2.get('id')==order_id})")

# 8. 관리자 대시보드에 주문 노출 (테이블별 요약: total_amount + recent_orders)
st, dash = call("GET", "/api/admin/dashboard", token=admin_token)
my_table = next((t for t in dash if t.get("table_id") == table_id), None) if isinstance(dash, list) else None
reflected = bool(my_table) and my_table.get("total_amount") == expected_total and len(my_table.get("recent_orders", [])) >= 1
ok(st == 200 and reflected, f"대시보드에 주문 반영 (total={my_table and my_table.get('total_amount')}, status={st})")

# 9. 주문 상태 전이 (OrderStatus enum 사용)
schema = json.load(urllib.request.urlopen(BASE + "/openapi.json"))
statuses = schema["components"]["schemas"]["OrderStatus"]["enum"]
print(f"      OrderStatus enum: {statuses}")
next_status = statuses[1]  # 접수 -> 준비중
st, r = call("PATCH", f"/api/admin/orders/{order_id}/status",
             {"status": next_status}, token=admin_token)
ok(st == 200, f"주문 상태 전이 -> '{next_status}' (status={st})")

# 10. 인증 없는 관리자 API 거부
st, r = call("GET", "/api/admin/dashboard")
ok(st in (401, 403), f"토큰 없는 관리자 API 거부 (status={st})")

print("\n=== 결과 ===")
print("전체 통과" if not FAILED else "일부 실패")
sys.exit(1 if FAILED else 0)
