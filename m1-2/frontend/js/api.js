// API 호출 래퍼 객체
const api = {
    getBaseUrl() {
        return window.API_BASE_URL || "";
    },

    async request(endpoint, options = {}) {
        const url = `${this.getBaseUrl()}${endpoint}`;
        const defaultHeaders = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        };

        const config = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                let errorDetail = `요청 실패 (HTTP ${response.status})`;
                try {
                    const errData = await response.json();
                    if (errData && errData.detail) {
                        errorDetail = typeof errData.detail === "string" 
                            ? errData.detail 
                            : JSON.stringify(errData.detail);
                    }
                } catch (_) {}
                throw new Error(errorDetail);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${endpoint}:`, error);
            throw error;
        }
    },

    // 1. 헬스체크 (Render 콜드스타트 감지)
    async checkHealth() {
        return this.request("/health");
    },

    // 2. 데이터 관련 API
    async getSummary() {
        return this.request("/api/data/summary");
    },

    async getDataList() {
        return this.request("/api/data");
    },

    async createData(payload) {
        return this.request("/api/data", {
            method: "POST",
            body: JSON.stringify(payload)
        });
    },

    async updateData(id, payload) {
        return this.request(`/api/data/${id}`, {
            method: "PUT",
            body: JSON.stringify(payload)
        });
    },

    async deleteData(id) {
        return this.request(`/api/data/${id}`, {
            method: "DELETE"
        });
    },

    // 3. 대화 관련 API
    async getConversations() {
        return this.request("/api/conversations");
    },

    async getConversation(id) {
        return this.request(`/api/conversations/${id}`);
    },

    async deleteConversation(id) {
        return this.request(`/api/conversations/${id}`, {
            method: "DELETE"
        });
    },

    // 4. AI 챗봇 API
    async chat(message, conversationId = null) {
        return this.request("/api/chat", {
            method: "POST",
            body: JSON.stringify({
                message: message,
                conversation_id: conversationId
            })
        });
    }
};

window.api = api;
