import { toVndInteger } from "@/lib/currency";

const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

const DEFAULT_COMBO_IMAGE =
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=800&auto=format&fit=crop";

function buildUrl(path, query = {}) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    url.searchParams.set(key, String(value));
  });
  return url.toString();
}

async function requestJson(path, { method = "GET", query, body } = {}) {
  const response = await fetch(buildUrl(path, query), {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep status-based error when payload is missing/invalid.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function mapIngredientStatus(status) {
  const normalized = String(status || "").toLowerCase();
  return normalized.includes("hết") || normalized.includes("khẩn")
    ? "warning"
    : "safe";
}

function mapCustomerCombo(combo) {
  const ingredients = Array.isArray(combo?.ingredients)
    ? combo.ingredients
    : [];

  return {
    id: combo?.id || "",
    name: combo?.name || "Combo chưa đặt tên",
    description: combo?.description || "Combo gợi ý theo dữ liệu cửa hàng.",
    discount: Math.round(toNumber(combo?.discount)),
    originalPrice: toVndInteger(combo?.originalPrice),
    newPrice: toVndInteger(combo?.newPrice),
    tags: Array.isArray(combo?.tags) ? combo.tags : [],
    image: combo?.image || DEFAULT_COMBO_IMAGE,
    ingredients: ingredients.map((ingredient) => ({
      name: ingredient?.name || "Nguyên liệu",
      status: mapIngredientStatus(ingredient?.status),
    })),
    instructions: Array.isArray(combo?.instructions) ? combo.instructions : [],
  };
}

export async function fetchCustomerCombos({ storeId, limit = 10 }) {
  const payload = await requestJson("/consumer/api/customer/combos", {
    query: { storeId, limit },
  });
  return Array.isArray(payload) ? payload.map(mapCustomerCombo) : [];
}

export async function sendConsumerChat({ message, threadId }) {
  const payload = await requestJson("/consumer/chat", {
    method: "POST",
    body: {
      message,
      thread_id: threadId,
    },
  });

  return {
    reply: String(payload?.reply || ""),
    threadId: String(payload?.thread_id || threadId || ""),
  };
}
