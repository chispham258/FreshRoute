const CART_KEY = "freshroute_cart";

export function loadCart() {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCart(cart) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

export function clearCart() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CART_KEY);
}

export function addItemToCart(combo) {
  const cart = loadCart();
  const existing = cart.find((item) => item.id === combo.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({
      id: combo.id,
      name: combo.name,
      originalPrice: combo.originalPrice,
      price: combo.newPrice,
      quantity: 1,
      image: combo.image || null,
      tags: combo.ingredients
        ? combo.ingredients.map((ing) => ing.name || ing)
        : combo.tags || [],
      discount: combo.discount || 0,
    });
  }
  saveCart(cart);
  return cart;
}
