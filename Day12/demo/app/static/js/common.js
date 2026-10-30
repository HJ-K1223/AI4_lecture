"use strict";

// JSON API에서 공통으로 사용합니다. 인증정보를 외부 주소에 전송하지 않습니다.
window.apiFetch = async function apiFetch(path, options = {}) {
    const url = new URL(path, window.location.origin);
    if (url.origin !== window.location.origin) {
        throw new Error("내부 API 주소만 사용할 수 있습니다.");
    }
    const method = (options.method || "GET").toUpperCase();
    const headers = new Headers(options.headers || {});
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
        headers.set("X-CSRF-Token", document.querySelector('meta[name="csrf-token"]').content);
    }
    const response = await fetch(url.pathname + url.search, {
        ...options, method, headers, credentials: "same-origin",
    });
    if (response.status === 401) {
        const next = window.location.pathname + window.location.search + window.location.hash;
        window.location.assign("/login?next=" + encodeURIComponent(next));
        throw new Error("로그인이 필요합니다.");
    }
    return response;
};
