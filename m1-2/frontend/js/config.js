// 백엔드 API 기본 주소 설정
// Vercel 배포 시 window.ENV_API_BASE_URL 등을 주입받거나,
// 로컬 실행 환경(FastAPI와 동시 실행 또는 포트 분리 실행)에 따라 자동 감지합니다.

const hostname = window.location.hostname;
const isLocalHost = hostname === "localhost" || hostname === "127.0.0.1";
const DEFAULT_API_URL = isLocalHost
    ? (window.location.port === "8000" ? "" : "http://localhost:8000")
    : "https://storesense-api.vercel.app";

window.API_BASE_URL = window.API_BASE_URL || localStorage.getItem("API_BASE_URL") || DEFAULT_API_URL;

console.log("[Config] Using API_BASE_URL:", window.API_BASE_URL || "(relative origin)");
