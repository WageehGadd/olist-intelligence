document.addEventListener("DOMContentLoaded", () => {
    const PREDICT_URL = "/api/v1/predict";
    const DATE_ORDER_MESSAGE = "Estimated delivery date cannot be earlier than the purchase date.";
    const NETWORK_ERROR = {
        type: "danger",
        message: "Unable to reach the prediction service. Check your connection and try again.",
    };
    const UNEXPECTED_ERROR = {
        type: "danger",
        message: "The prediction service returned an unexpected response. Please try again later.",
    };
    const STATUS_ERRORS = {
        422: {
            type: "warning",
            message: "The order details were not accepted. Please review every field and try again.",
        },
        503: {
            type: "warning",
            message: "The prediction model is currently unavailable. Please try again later.",
        },
    };

    const form = document.getElementById("prediction-form");
    const purchaseInput = document.getElementById("purchase-timestamp");
    const deliveryInput = document.getElementById("estimated-delivery-date");
    const stateInput = document.getElementById("customer-state");
    const itemsContainer = document.getElementById("items-container");
    const itemTemplate = document.getElementById("item-template");
    const addItemButton = document.getElementById("add-item-btn");
    const resultContainer = document.getElementById("prediction-result");
    const submitButton = document.getElementById("predict-btn");

    if (!form || !purchaseInput || !deliveryInput || !stateInput || !itemsContainer ||
        !itemTemplate || !addItemButton || !resultContainer || !submitButton) {
        return;
    }

    const submitLabel = submitButton.querySelector(".btn-label");
    const submitSpinner = submitButton.querySelector(".spinner-border");
    const defaultLabel = submitLabel.textContent;
    let isSubmitting = false;

    function createElement(tag, className, text) {
        const element = document.createElement(tag);
        if (className) {
            element.className = className;
        }
        if (text !== undefined) {
            element.textContent = text;
        }
        return element;
    }

    function updateFeedback() {
        const showErrors = form.classList.contains("show-errors");

        form.querySelectorAll(".form-field").forEach((field) => {
            const input = field.querySelector("input, select");
            const feedback = field.querySelector(".invalid-feedback");

            feedback.id = `${input.id}-error`;
            input.setAttribute("aria-describedby", feedback.id);
            input.setAttribute("aria-invalid", String(showErrors && !input.validity.valid));
            feedback.textContent = showErrors ? input.validationMessage : "";
        });
    }

    function validateForm() {
        const purchaseDate = purchaseInput.value.slice(0, 10);

        deliveryInput.min = purchaseDate;
        deliveryInput.setCustomValidity(
            purchaseDate && deliveryInput.value && deliveryInput.value < purchaseDate
                ? DATE_ORDER_MESSAGE
                : "",
        );
        updateFeedback();

        return form.checkValidity();
    }

    function refreshItems() {
        const rows = itemsContainer.querySelectorAll(".item-row");

        rows.forEach((row, index) => {
            const number = index + 1;
            const title = row.querySelector(".item-title");

            title.id = `item-${number}-title`;
            title.textContent = `Item ${number}`;
            row.setAttribute("aria-labelledby", title.id);

            const removeButton = row.querySelector(".remove-item-btn");
            removeButton.setAttribute("aria-label", `Remove item ${number}`);
            removeButton.disabled = rows.length === 1;

            row.querySelectorAll(".form-field").forEach((field) => {
                const input = field.querySelector("input");
                input.id = `item-${number}-${input.name}`;
                field.querySelector("label").htmlFor = input.id;
            });
        });

        updateFeedback();
    }

    function setSubmitting(state) {
        isSubmitting = state;
        submitButton.setAttribute("aria-disabled", String(state));
        submitButton.classList.toggle("disabled", state);
        submitSpinner.classList.toggle("d-none", !state);
        submitLabel.textContent = state ? "Predicting…" : defaultLabel;
        resultContainer.setAttribute("aria-busy", String(state));
    }

    function buildPayload() {
        const purchaseTimestamp = purchaseInput.value;

        return {
            purchase_timestamp: purchaseTimestamp.length === 16
                ? `${purchaseTimestamp}:00`
                : purchaseTimestamp,
            estimated_delivery_date: deliveryInput.value,
            customer_state: stateInput.value,
            items: Array.from(itemsContainer.querySelectorAll(".item-row"), (row) => ({
                price: Number(row.querySelector('[name="price"]').value),
                freight_value: Number(row.querySelector('[name="freight_value"]').value),
            })),
        };
    }

    const isPrediction = (data) => Boolean(data)
        && ["late", "on_time"].includes(data.prediction)
        && Number.isFinite(data.probability_late)
        && data.probability_late >= 0
        && data.probability_late <= 1
        && typeof data.model_version === "string"
        && typeof data.notice === "string";

    async function requestPrediction(payload) {
        let response;

        try {
            response = await fetch(PREDICT_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
        } catch {
            return { alert: NETWORK_ERROR };
        }

        if (!response.ok) {
            return { alert: STATUS_ERRORS[response.status] ?? UNEXPECTED_ERROR };
        }

        try {
            const data = await response.json();
            return isPrediction(data) ? { data } : { alert: UNEXPECTED_ERROR };
        } catch {
            return { alert: UNEXPECTED_ERROR };
        }
    }

    function showAlert({ type, message }) {
        const alert = createElement("div", `alert alert-${type} mb-0`, message);
        resultContainer.replaceChildren(alert);
    }

    function showPrediction(data) {
        const isLate = data.prediction === "late";
        const card = createElement("div", `result-card ${isLate ? "result-late" : "result-on-time"}`);

        const meter = createElement("div", "probability-meter");
        meter.setAttribute("aria-hidden", "true");
        const meterFill = createElement("div", "probability-meter-fill");
        meterFill.style.width = `${data.probability_late * 100}%`;
        meter.appendChild(meterFill);

        const meta = createElement("dl", "result-meta");
        meta.append(
            createElement("dt", "", "Model version"),
            createElement("dd", "", data.model_version),
        );

        card.append(
            createElement("h3", "result-status", isLate ? "Predicted late" : "Predicted on time"),
            createElement("p", "result-label", "Model-reported probability of lateness"),
            createElement("p", "result-probability", `${(data.probability_late * 100).toFixed(2)}%`),
            meter,
            meta,
            createElement("p", "result-notice", data.notice),
        );

        resultContainer.replaceChildren(card);
    }

    addItemButton.addEventListener("click", () => {
        const row = itemTemplate.content.firstElementChild.cloneNode(true);

        itemsContainer.appendChild(row);
        form.classList.remove("show-errors");
        refreshItems();
        row.querySelector("input").focus();
    });

    itemsContainer.addEventListener("click", (event) => {
        const button = event.target.closest(".remove-item-btn");

        if (!button || itemsContainer.querySelectorAll(".item-row").length === 1) {
            return;
        }

        button.closest(".item-row").remove();
        refreshItems();
        addItemButton.focus();
    });

    form.addEventListener("input", validateForm);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (isSubmitting) {
            return;
        }

        form.classList.add("show-errors");

        if (!validateForm()) {
            form.querySelector(":invalid")?.focus();
            return;
        }

        setSubmitting(true);
        resultContainer.replaceChildren();

        try {
            const outcome = await requestPrediction(buildPayload());

            if (outcome.data) {
                showPrediction(outcome.data);
            } else {
                showAlert(outcome.alert);
            }

            resultContainer.scrollIntoView({ block: "nearest" });
        } finally {
            setSubmitting(false);
        }
    });

    refreshItems();
});
