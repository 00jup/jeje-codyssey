// ==========================================
// 스마트스토어 AI 비서 — 통합 바닐라 앱 스크립트
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    // 앱 상태
    let currentConversationId = null;
    let cachedDataList = [];

    // DOM 요소 캐싱
    const elements = {
        // 서버 상태
        statusDot: document.getElementById("statusDot"),
        statusText: document.getElementById("statusText"),
        btnConfigApi: document.getElementById("btnConfigApi"),
        btnRefreshAll: document.getElementById("btnRefreshAll"),

        // 요약 위젯
        summaryPeriod: document.getElementById("summaryPeriod"),
        summaryCount: document.getElementById("summaryCount"),
        summaryTotal: document.getElementById("summaryTotal"),
        summaryAverage: document.getElementById("summaryAverage"),
        summaryTrendBadge: document.getElementById("summaryTrendBadge"),
        summaryMax: document.getElementById("summaryMax"),
        summaryMaxDate: document.getElementById("summaryMaxDate"),

        // 탭
        tabChatBtn: document.getElementById("tabChatBtn"),
        tabDataBtn: document.getElementById("tabDataBtn"),
        chatPanel: document.getElementById("chatPanel"),
        dataPanel: document.getElementById("dataPanel"),

        // 대화 히스토리
        btnNewChat: document.getElementById("btnNewChat"),
        conversationList: document.getElementById("conversationList"),

        // 채팅
        chatMessages: document.getElementById("chatMessages"),
        typingIndicator: document.getElementById("typingIndicator"),
        chatForm: document.getElementById("chatForm"),
        chatInput: document.getElementById("chatInput"),
        btnSendChat: document.getElementById("btnSendChat"),
        chipButtons: document.querySelectorAll(".chip-btn"),

        // 데이터 관리
        tableDataCount: document.getElementById("tableDataCount"),
        dataTableBody: document.getElementById("dataTableBody"),
        btnOpenAddModal: document.getElementById("btnOpenAddModal"),

        // 모달
        dataModal: document.getElementById("dataModal"),
        modalTitle: document.getElementById("modalTitle"),
        dataForm: document.getElementById("dataForm"),
        editDataId: document.getElementById("editDataId"),
        inputDate: document.getElementById("inputDate"),
        inputValue: document.getElementById("inputValue"),
        inputMemo: document.getElementById("inputMemo"),
        btnCloseModal: document.getElementById("btnCloseModal"),
        btnCancelModal: document.getElementById("btnCancelModal"),
    };

    // ==========================================
    // 1. 초기화 및 서버 헬스체크 (Render 콜드스타트 대비)
    // ==========================================
    async function checkServerHealth() {
        elements.statusDot.className = "status-dot warming";
        elements.statusText.textContent = "서버 연결 확인 중...";

        try {
            await api.checkHealth();
            elements.statusDot.className = "status-dot online";
            elements.statusText.textContent = "서버 정상 연결";
        } catch (err) {
            elements.statusDot.className = "status-dot warming";
            elements.statusText.textContent = "서버 깨우는 중 (약 30초 소요 가능)";
            // 3초 후 재시도
            setTimeout(checkServerHealth, 3000);
        }
    }

    async function initApp() {
        checkServerHealth();
        await Promise.allSettled([
            loadSummary(),
            loadConversations(),
            loadDataList()
        ]);
    }

    // ==========================================
    // 2. 데이터 요약 (Summary) 렌더링
    // ==========================================
    async function loadSummary() {
        try {
            const summary = await api.getSummary();
            renderSummary(summary);
        } catch (err) {
            console.error("요약 정보 로드 실패:", err);
        }
    }

    function renderSummary(summary) {
        if (!summary) return;

        elements.summaryPeriod.textContent = summary.period || "기록 없음";
        elements.summaryCount.textContent = `기록된 데이터: ${summary.count || 0}일`;

        const m = summary.metrics || {};
        elements.summaryTotal.textContent = `${(m.total || 0).toLocaleString()}원`;
        elements.summaryAverage.textContent = `${(m.average || 0).toLocaleString()}원`;

        // 트렌드 뱃지 스타일 적용
        const trend = summary.trend || "안정";
        elements.summaryTrendBadge.textContent = trend;
        if (trend.includes("상승")) {
            elements.summaryTrendBadge.className = "trend-badge up";
        } else if (trend.includes("하락")) {
            elements.summaryTrendBadge.className = "trend-badge down";
        } else {
            elements.summaryTrendBadge.className = "trend-badge neutral";
        }

        if (m.max_date && m.max_date !== "-") {
            elements.summaryMax.textContent = `${(m.max || 0).toLocaleString()}원`;
            elements.summaryMaxDate.textContent = `최고일: ${m.max_date}`;
        } else {
            elements.summaryMax.textContent = "- 원";
            elements.summaryMaxDate.textContent = "최고일: -";
        }
    }

    // ==========================================
    // 3. 대화 세션 (Conversations) 관리
    // ==========================================
    async function loadConversations() {
        try {
            const convs = await api.getConversations();
            renderConversationList(convs);
        } catch (err) {
            console.error("대화 목록 로드 실패:", err);
        }
    }

    function renderConversationList(convs) {
        elements.conversationList.innerHTML = "";
        if (!convs || convs.length === 0) {
            const emptyLi = document.createElement("li");
            emptyLi.style.padding = "12px";
            emptyLi.style.color = "var(--text-muted)";
            emptyLi.style.fontSize = "12px";
            emptyLi.textContent = "저장된 대화가 없습니다.";
            elements.conversationList.appendChild(emptyLi);
            return;
        }

        convs.forEach(conv => {
            const li = document.createElement("li");
            li.className = `conversation-item ${conv.id === currentConversationId ? "active" : ""}`;
            li.dataset.id = conv.id;

            const titleSpan = document.createElement("span");
            titleSpan.className = "conversation-title";
            titleSpan.textContent = conv.title || "대화 세션";
            titleSpan.title = conv.title || "";

            const delBtn = document.createElement("button");
            delBtn.className = "btn-delete-conv";
            delBtn.innerHTML = "&times;";
            delBtn.title = "대화 삭제";
            delBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                if (confirm(`'${conv.title}' 대화를 삭제하시겠습니까?`)) {
                    await api.deleteConversation(conv.id);
                    if (currentConversationId === conv.id) {
                        startNewChat();
                    }
                    await loadConversations();
                }
            });

            li.appendChild(titleSpan);
            li.appendChild(delBtn);

            li.addEventListener("click", () => {
                loadConversationDetail(conv.id);
            });

            elements.conversationList.appendChild(li);
        });
    }

    async function loadConversationDetail(convId) {
        try {
            const conv = await api.getConversation(convId);
            currentConversationId = conv.id;
            
            // 사이드바 활성 스타일
            document.querySelectorAll(".conversation-item").forEach(el => {
                el.classList.toggle("active", el.dataset.id === convId);
            });

            // 채팅 메시지 다시 렌더링
            renderChatHistory(conv.messages || []);

            // 채팅 탭으로 이동
            switchTab("chat");
        } catch (err) {
            alert(`대화 불러오기 실패: ${err.message}`);
        }
    }

    function startNewChat() {
        currentConversationId = null;
        document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
        elements.chatMessages.innerHTML = `
            <div class="chat-bubble assistant">
              안녕하세요! 스마트스토어 AI 매출 분석 비서입니다. 🏪<br>
              매장의 최근 실적이나 트렌드, 최고/최저 매출에 대해 무엇이든 물어보세요!
              <div class="chat-bubble-time">AI 비서</div>
            </div>
        `;
        switchTab("chat");
    }

    function renderChatHistory(messages) {
        elements.chatMessages.innerHTML = "";
        if (!messages || messages.length === 0) {
            startNewChat();
            return;
        }

        messages.forEach(msg => {
            appendMessageBubble(msg.role, msg.content, msg.timestamp);
        });
        scrollChatToBottom();
    }

    function appendMessageBubble(role, content, timestamp) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble ${role === "user" ? "user" : "assistant"}`;
        
        // 텍스트 내용
        const textNode = document.createElement("div");
        textNode.textContent = content;
        bubble.appendChild(textNode);

        // 시간 표시
        const timeDiv = document.createElement("div");
        timeDiv.className = "chat-bubble-time";
        timeDiv.textContent = role === "user" ? "나" : "AI 비서";
        bubble.appendChild(timeDiv);

        elements.chatMessages.appendChild(bubble);
        scrollChatToBottom();
    }

    function scrollChatToBottom() {
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }

    // ==========================================
    // 4. AI 채팅 발송 로직
    // ==========================================
    async function handleSendMessage(messageText) {
        const text = (messageText || elements.chatInput.value).trim();
        if (!text) return;

        // 사용자 말풍선 추가
        appendMessageBubble("user", text, new Date().toISOString());
        elements.chatInput.value = "";

        // UI 로딩 표시
        elements.typingIndicator.style.display = "inline-flex";
        elements.btnSendChat.disabled = true;
        scrollChatToBottom();

        try {
            const res = await api.chat(text, currentConversationId);
            currentConversationId = res.conversation_id;

            // AI 답변 렌더링
            appendMessageBubble("assistant", res.reply, new Date().toISOString());

            // 요약 위젯 스냅샷 갱신
            if (res.summary) {
                renderSummary(res.summary);
            }

            // 대화 목록 갱신
            await loadConversations();
        } catch (err) {
            appendMessageBubble("assistant", `오류가 발생했습니다: ${err.message}`, new Date().toISOString());
        } finally {
            elements.typingIndicator.style.display = "none";
            elements.btnSendChat.disabled = false;
            elements.chatInput.focus();
        }
    }

    // ==========================================
    // 5. 시계열 데이터 관리 (CRUD)
    // ==========================================
    async function loadDataList() {
        try {
            cachedDataList = await api.getDataList();
            renderDataTable(cachedDataList);
            elements.tableDataCount.textContent = `${cachedDataList.length}건`;
        } catch (err) {
            console.error("데이터 목록 로드 실패:", err);
        }
    }

    function renderDataTable(data) {
        elements.dataTableBody.innerHTML = "";
        if (!data || data.length === 0) {
            elements.dataTableBody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align: center; color: var(--text-muted); padding: 32px;">
                        등록된 매출 데이터가 없습니다.
                    </td>
                </tr>
            `;
            return;
        }

        // 최신 날짜순 내림차순 정렬 표시
        const sorted = [...data].sort((a, b) => b.date.localeCompare(a.date));

        sorted.forEach(item => {
            const tr = document.createElement("tr");

            tr.innerHTML = `
                <td style="font-weight: 600;">${item.date}</td>
                <td style="color: var(--primary); font-weight: 700;">${(item.value || 0).toLocaleString()}원</td>
                <td>${escapeHtml(item.memo || "-")}</td>
                <td>
                    <div class="action-btn-group">
                        <button class="btn-sm-edit" data-id="${item.id}">수정</button>
                        <button class="btn-sm-del" data-id="${item.id}">삭제</button>
                    </div>
                </td>
            `;

            // 수정 버튼 이벤트
            tr.querySelector(".btn-sm-edit").addEventListener("click", () => {
                openEditModal(item);
            });

            // 삭제 버튼 이벤트
            tr.querySelector(".btn-sm-del").addEventListener("click", async () => {
                if (confirm(`[${item.date}] 매출 데이터(${item.value.toLocaleString()}원)를 삭제하시겠습니까?`)) {
                    try {
                        await api.deleteData(item.id);
                        await Promise.all([loadDataList(), loadSummary()]);
                    } catch (err) {
                        alert(`삭제 실패: ${err.message}`);
                    }
                }
            });

            elements.dataTableBody.appendChild(tr);
        });
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // 모달 관리
    function openAddModal() {
        elements.modalTitle.textContent = "새 매출 데이터 추가";
        elements.editDataId.value = "";
        elements.inputDate.value = new Date().toISOString().split("T")[0];
        elements.inputValue.value = "";
        elements.inputMemo.value = "";
        elements.dataModal.classList.add("open");
        elements.inputDate.focus();
    }

    function openEditModal(item) {
        elements.modalTitle.textContent = "매출 데이터 수정";
        elements.editDataId.value = item.id;
        elements.inputDate.value = item.date;
        elements.inputValue.value = item.value;
        elements.inputMemo.value = item.memo || "";
        elements.dataModal.classList.add("open");
        elements.inputValue.focus();
    }

    function closeModal() {
        elements.dataModal.classList.remove("open");
    }

    async function handleSaveData(e) {
        e.preventDefault();
        const id = elements.editDataId.value;
        const payload = {
            date: elements.inputDate.value,
            value: parseInt(elements.inputValue.value, 10),
            memo: elements.inputMemo.value.trim()
        };

        try {
            if (id) {
                await api.updateData(id, payload);
            } else {
                await api.createData(payload);
            }
            closeModal();
            await Promise.all([loadDataList(), loadSummary()]);
        } catch (err) {
            alert(`저장 실패: ${err.message}`);
        }
    }

    // ==========================================
    // 6. 탭 전환 및 유틸리티
    // ==========================================
    function switchTab(tabName) {
        if (tabName === "chat") {
            elements.tabChatBtn.classList.add("active");
            elements.tabDataBtn.classList.remove("active");
            elements.chatPanel.classList.add("active");
            elements.dataPanel.classList.remove("active");
        } else {
            elements.tabChatBtn.classList.remove("active");
            elements.tabDataBtn.classList.add("active");
            elements.chatPanel.classList.remove("active");
            elements.dataPanel.classList.add("active");
        }
    }

    // ==========================================
    // 7. 이벤트 리스너 등록
    // ==========================================
    // 탭 전환
    elements.tabChatBtn.addEventListener("click", () => switchTab("chat"));
    elements.tabDataBtn.addEventListener("click", () => switchTab("data"));

    // 새 대화 버튼
    elements.btnNewChat.addEventListener("click", startNewChat);

    // 채팅 폼 전송
    elements.chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleSendMessage();
    });

    // 추천 칩 클릭
    elements.chipButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.dataset.query;
            handleSendMessage(query);
        });
    });

    // 데이터 추가 모달 버튼
    elements.btnOpenAddModal.addEventListener("click", openAddModal);
    elements.btnCloseModal.addEventListener("click", closeModal);
    elements.btnCancelModal.addEventListener("click", closeModal);
    elements.dataForm.addEventListener("submit", handleSaveData);

    // 새로고침 버튼
    elements.btnRefreshAll.addEventListener("click", async () => {
        await Promise.all([loadSummary(), loadDataList(), loadConversations()]);
    });

    // API 주소 설정 프롬프트
    elements.btnConfigApi.addEventListener("click", () => {
        const current = window.API_BASE_URL || "(현재 호스트와 동일)";
        const next = prompt("연결할 백엔드 API 서버 URL을 입력하세요 (예: https://your-backend.onrender.com):", current);
        if (next !== null) {
            localStorage.setItem("API_BASE_URL", next.trim());
            window.API_BASE_URL = next.trim();
            alert("API URL이 저장되었습니다. 페이지를 새로고침합니다.");
            window.location.reload();
        }
    });

    // 모달 배경 클릭 시 닫기
    elements.dataModal.addEventListener("click", (e) => {
        if (e.target === elements.dataModal) closeModal();
    });

    // 실행 시작
    initApp();
});
