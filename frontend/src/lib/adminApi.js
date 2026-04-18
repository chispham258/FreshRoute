const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

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
      const errorPayload = await response.json();
      if (errorPayload?.detail) {
        detail = errorPayload.detail;
      }
    } catch {
      // Ignore invalid error payload and keep status-based message.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function formatWeight(weightInGrams) {
  const grams = Number(weightInGrams || 0);
  if (grams >= 1000) {
    const kilos = grams / 1000;
    return `${Number.isInteger(kilos) ? kilos : kilos.toFixed(1)} kg`;
  }
  return `${Math.round(grams)} g`;
}

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function mapComboFromBackend(combo) {
  const ingredients = Array.isArray(combo?.ingredients)
    ? combo.ingredients
    : [];

  return {
    id: combo?.id || "",
    name: combo?.name || "Combo chưa đặt tên",
    discount: Math.round(toNumber(combo?.discount)),
    confidence: Math.round(toNumber(combo?.confidence)),
    ingredients: ingredients.map((ing) => ing?.name || "Nguyên liệu"),
    ingredientsDetail: ingredients.map((ing) => ({
      name: ing?.name || "Nguyên liệu",
      weight: `${toNumber(ing?.quantity)}${ing?.unit || ""}`,
      status: ing?.status || "Bình Thường",
    })),
    aiReason: combo?.aiReasoning || "AI chưa cung cấp giải thích chi tiết.",
    originalPrice: toNumber(combo?.originalPrice),
    newPrice: toNumber(combo?.newPrice),
  };
}

function mapInventoryFromBackend(item) {
  return {
    id: item?.id || "",
    name: item?.name || "Sản phẩm",
    weight: formatWeight(item?.weight),
    daysLeft: Math.max(0, Math.round(toNumber(item?.daysLeft))),
    limit: Math.max(1, Math.round(toNumber(item?.limit, 14))),
    status: item?.status || "Bình Thường",
  };
}

export async function fetchAdminCombos({ storeId, limit = 10 }) {
  const payload = await requestJson("/api/admin/combos", {
    query: { storeId, limit },
  });
  return Array.isArray(payload) ? payload.map(mapComboFromBackend) : [];
}

export async function fetchAdminInventory({ storeId, daysThreshold = 14 }) {
  const payload = await requestJson("/api/admin/inventory", {
    query: { storeId, daysThreshold },
  });
  return Array.isArray(payload) ? payload.map(mapInventoryFromBackend) : [];
}

export async function acceptAdminCombo({ comboId, storeId, combo }) {
  return requestJson(
    `/api/admin/combos/${encodeURIComponent(comboId)}/accept`,
    {
      method: "POST",
      body: {
        storeId,
        combo: {
          id: combo.id,
          name: combo.name,
          discount: combo.discount,
          confidence: combo.confidence,
          ingredients: combo.ingredientsDetail.map((ing) => ({
            name: ing.name,
            status: ing.status,
            quantity: parseFloat(ing.weight) || 0,
            unit: ing.weight.replace(/[\d.]/g, "") || "g",
          })),
          originalPrice: combo.originalPrice,
          newPrice: combo.newPrice,
          aiReasoning: combo.aiReason,
        },
      },
    },
  );
}

export async function rejectAdminCombo({ comboId, storeId, reason }) {
  return requestJson(
    `/api/admin/combos/${encodeURIComponent(comboId)}/reject`,
    {
      method: "POST",
      body: { storeId, reason },
    },
  );
}
