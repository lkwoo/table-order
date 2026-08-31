# U7-frontend — 코드 요약

React 18 + TypeScript + Vite. 고객/관리자 두 영역.

## 구조 (`frontend/`)
- 설정: `package.json`, `vite.config.ts`(`/api`·`/health` 프록시, `VITE_PROXY_TARGET` 지원, SSE 스트리밍), tsconfig, `index.html`, `src/main.tsx`, `src/App.tsx`(`/customer/*`, `/admin/*`), `Dockerfile`.
- 공유(`src/shared/`): `api.ts`(타입드 호출, Bearer/X-Session-Token/Idempotency-Key, 3회 재시도), `auth.ts`, `sse.ts`(EventSource `?token=`, 자동 재연결 + 스냅샷 콜백), `ui.tsx`/`ui.css`(버튼 ≥50px, StatusBadge 색상), `types.ts`(단방향 전이).
- 고객(`src/customer/`): CustomerAuthContext, CartContext(localStorage, 수량 1~99), useOrderStream; 뷰 TableLogin, MenuList+MenuDetailModal, CartDrawer, OrderConfirm, OrderSubmit+OrderSuccess(5초 카운트다운), OrderHistory(SSE 실시간).
- 관리자(`src/admin/`): AdminAuthContext, useDashboardStream(오프라인 배너 + 스냅샷 리페치 + 3초 신규 주문 하이라이트); 뷰 AdminLogin, Dashboard(TableCard 그리드), TableOrderDetailPanel(단방향 상태 컨트롤, 삭제/세션종료 확인), TableSetupModal(비밀번호 4~10), OrderHistoryModal(all/today/yesterday), MenuManagementView(가격 1,000~100,000, 순서 up/down).

## 규칙
- 모든 상호작용 요소에 `data-testid`(`{component}-{role}` 규칙).
- 상태 배지 색상: 대기중 `#F5A623`, 준비중 `#2D7FF9`, 완료 `#27AE60`.
- REST/SSE 계약은 백엔드와 `code-generation-plan.md` 계약을 준수.
