"use strict";

(() => {
    const message = document.querySelector("[data-message]");
    function showMessage(text, isError = false) {
        if (!message) return;
        message.hidden = false;
        message.textContent = text;
        message.classList.toggle("form-error", isError);
        message.classList.toggle("form-notice", !isError);
        message.scrollIntoView({block: "nearest"});
    }
    async function request(path, method, data) {
        const response = await window.apiFetch(path, {
            method, headers: {"Content-Type": "application/json"},
            ...(data === undefined ? {} : {body: JSON.stringify(data)}),
        });
        const result = await response.json();
        if (!response.ok) {
            if (result.code === "cart_changed") {
                const refresh = document.querySelector("[data-refresh-cart]");
                if (refresh) refresh.hidden = false;
            }
            const text = typeof result.detail === "string" ? result.detail : "입력 내용을 확인해 주세요.";
            const error = new Error(text);
            error.result = result;
            throw error;
        }
        return result;
    }
    async function submit(button, action) {
        if (button.disabled) return;
        button.disabled = true;
        try { await action(); }
        catch (error) { showMessage(error.message || "요청을 처리하지 못했습니다. 다시 시도해 주세요.", true); }
        finally { button.disabled = false; }
    }
    const productForm = document.querySelector("[data-product-form]");
    const addButton = document.querySelector("[data-add-cart]");
    if (productForm && addButton) addButton.addEventListener("click", () => {
        if (!productForm.reportValidity()) return;
        const form = new FormData(productForm);
        // 미인증 401 복귀 후에도 사용자가 선택한 수량을 유지합니다.
        const url = new URL(window.location.href);
        url.searchParams.set("quantity", form.get("quantity"));
        window.history.replaceState(null, "", url.pathname + url.search);
        submit(addButton, async () => {
            await request("/api/cart/items", "POST", {product_id: form.get("product_id"), quantity: Number(form.get("quantity"))});
            showMessage("장바구니에 담았습니다. 장바구니에서 주문 내용을 확인해 주세요.");
        });
    });
    const selection = document.querySelector("[data-selection-form]");
    if (selection) selection.addEventListener("submit", (event) => {
        event.preventDefault();
        const data = new FormData(selection);
        submit(selection.querySelector("button"), async () => {
            await request("/api/cart/items", "POST", {product_id: data.get("product_id"), quantity: Number(data.get("quantity"))});
            window.location.assign("/cart");
        });
    });
    document.querySelectorAll("[data-quantity-form]").forEach((form) => {
        const id = form.closest("[data-item-id]").dataset.itemId;
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            submit(form.querySelector('button[type="submit"]'), async () => {
                await request("/api/cart/items/" + id, "PUT", {quantity: Number(new FormData(form).get("quantity"))});
                window.location.reload();
            });
        });
        const remove = form.querySelector("[data-remove-item]");
        remove.addEventListener("click", () => submit(remove, async () => {
            await request("/api/cart/items/" + id, "DELETE");
            window.location.reload();
        }));
    });
    const order = document.querySelector("[data-order-form]");
    if (order) order.addEventListener("submit", (event) => {
        event.preventDefault();
        submit(order.querySelector("button"), async () => {
            const result = await request("/api/orders", "POST", Object.fromEntries(new FormData(order)));
            window.location.assign(result.checkout_url);
        });
    });
    const payment = document.querySelector("[data-payment-form]");
    if (payment) payment.addEventListener("submit", (event) => {
        event.preventDefault();
        submit(payment.querySelector("button"), async () => {
            try {
                const result = await request("/api/payments", "POST", Object.fromEntries(new FormData(payment)));
                window.location.assign(result.redirect_url);
            } catch (error) {
                // 확정된 실패에만 새 키를 발급합니다. 네트워크 오류는 기존 키로 재시도합니다.
                if (error.result && error.result.status === "FAILED") {
                    payment.elements.idempotency_key.value = window.crypto.randomUUID();
                }
                throw error;
            }
        });
    });
})();
