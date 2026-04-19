import { toVndInteger } from "@/lib/currency";
import R006Image from "@/images/R006.jpg";
import R011Image from "@/images/R011.jpg";
import R013Image from "@/images/R013.jpg";
import R024Image from "@/images/R024.jpg";
import R026Image from "@/images/R026.jpg";
import R035Image from "@/images/R035.jpg";

const DEFAULT_COMBO_IMAGE =
  "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=800&auto=format&fit=crop";

const LOCAL_COMBO_IMAGE_BY_RECIPE_ID = {
  R006: R006Image,
  R011: R011Image,
  R013: R013Image,
  R024: R024Image,
  R026: R026Image,
  R035: R035Image,
};

function buildUrl(path, query = {}) {
  const url = new URL(path, window.location.origin);
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

function extractRecipePrefix(comboId) {
  const raw = String(comboId || "").toUpperCase();
  const match = raw.match(/^(R\d{3})/);
  return match ? match[1] : null;
}

function resolveComboImage(combo) {
  const recipePrefix = extractRecipePrefix(combo?.id);
  const localImage = recipePrefix
    ? LOCAL_COMBO_IMAGE_BY_RECIPE_ID[recipePrefix]
    : null;

  if (localImage && typeof localImage === "object" && localImage.src) {
    return localImage.src;
  }

  if (typeof localImage === "string" && localImage.length > 0) {
    return localImage;
  }

  if (typeof combo?.image === "string" && combo.image.length > 0) {
    return combo.image;
  }

  return DEFAULT_COMBO_IMAGE;
}

function mapCustomerCombo(combo) {
  const ingredients = Array.isArray(combo?.ingredients)
    ? combo.ingredients
    : [];
  const instructions = Array.isArray(combo?.instructions)
    ? combo.instructions.filter(
        (step) => typeof step === "string" && step.length > 0,
      )
    : [];

  const mappedTime =
    combo?.time && typeof combo.time === "object"
      ? {
          prepMinutes: Math.max(
            0,
            Math.round(toNumber(combo.time.prepMinutes)),
          ),
          cookMinutes: Math.max(
            0,
            Math.round(toNumber(combo.time.cookMinutes)),
          ),
          totalMinutes: Math.max(
            0,
            Math.round(toNumber(combo.time.totalMinutes)),
          ),
        }
      : null;

  return {
    id: combo?.id || "",
    name: combo?.name || "Combo chưa đặt tên",
    description: combo?.description || "Combo gợi ý theo dữ liệu cửa hàng.",
    aiReasoning: combo?.aiReasoning || "",
    discount: Math.round(toNumber(combo?.discount)),
    confidence: Math.round(toNumber(combo?.confidence)),
    originalPrice: toVndInteger(combo?.originalPrice),
    newPrice: toVndInteger(combo?.newPrice),
    tags: Array.isArray(combo?.tags) ? combo.tags : [],
    image: resolveComboImage(combo),
    time: mappedTime,
    ingredients: ingredients.map((ingredient) => ({
      name: ingredient?.name || "Nguyên liệu",
      status: mapIngredientStatus(ingredient?.status),
      quantity: toNumber(ingredient?.quantity),
      unit: ingredient?.unit || "g",
      retailPrice: toVndInteger(ingredient?.retailPrice),
    })),
    instructions,
  };
}

export async function fetchCustomerCombos({ storeId, limit = 10 }) {
  const payload = await requestJson("/api/customer/combos", {
    query: { storeId, limit },
  });
  return Array.isArray(payload) ? payload.map(mapCustomerCombo) : [];
}

export async function sendConsumerChat({ message, threadId, allergies }) {
  const payload = await requestJson("/consumer/chat", {
    method: "POST",
    body: {
      message,
      thread_id: threadId,
      ...(allergies && allergies.length > 0 ? { allergies } : {}),
    },
  });

  return {
    reply: String(payload?.reply || ""),
    threadId: String(payload?.thread_id || threadId || ""),
    shoppingList: Array.isArray(payload?.shopping_list)
      ? payload.shopping_list
      : null,
    recipeSuggestions: Array.isArray(payload?.recipe_suggestions)
      ? payload.recipe_suggestions
      : null,
  };
}
