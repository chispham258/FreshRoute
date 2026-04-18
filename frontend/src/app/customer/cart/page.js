/* eslint-disable @next/next/no-img-element */
"use client";
import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { FaArrowLeft, FaTrash, FaLeaf } from "react-icons/fa";
import {
  CheckCircle,
  Share2,
  Sparkles,
  RefreshCw,
  ChevronRight,
  Check,
} from "lucide-react";
import { loadCart, saveCart, clearCart } from "@/lib/cart";

// Odometer effect for price ticker
const PriceTicker = ({ value }) => {
  return (
    <motion.div
      key={value}
      initial={{ y: -10, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="inline-block"
    >
      {value.toLocaleString("vi-VN")}
    </motion.div>
  );
};

export default function CartPage() {
  const [cart, setCart] = useState(() => loadCart());
  const [removedItem, setRemovedItem] = useState(null);
  const [showUndo, setShowUndo] = useState(false);
  const [checkoutStep, setCheckoutStep] = useState(0); // 0: Cart, 1: Checkout, 2: Success
  const [paymentMethod, setPaymentMethod] = useState("momo");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const subtotal = cart.reduce(
    (sum, item) => sum + item.originalPrice * item.quantity,
    0,
  );
  const totalDiscount = cart.reduce(
    (sum, item) => sum + (item.originalPrice - item.price) * item.quantity,
    0,
  );
  const finalTotal = subtotal - totalDiscount + 25000; // 25k shipping
  const totalImpact = totalDiscount > 0 ? (totalDiscount / 100000).toFixed(1) : 0;
  const totalItemsCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  const handlePullToRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
    }, 1500);
  };

  const updateCartState = (newCart) => {
    setCart(newCart);
    saveCart(newCart);
  };

  const updateQuantity = (id, delta) => {
    const updated = cart.map((item) => {
      if (item.id === id) {
        const newQty = item.quantity + delta;
        return newQty > 0 ? { ...item, quantity: newQty } : item;
      }
      return item;
    });
    updateCartState(updated);
  };

  const removeItem = (id) => {
    const itemToRemove = cart.find((i) => i.id === id);
    setRemovedItem(itemToRemove);
    const updated = cart.filter((i) => i.id !== id);
    updateCartState(updated);
    setShowUndo(true);

    setTimeout(() => {
      setShowUndo(false);
    }, 3000);
  };

  const undoRemove = () => {
    if (removedItem) {
      const updated = [...cart, removedItem].sort((a, b) =>
        String(a.id).localeCompare(String(b.id)),
      );
      updateCartState(updated);
      setShowUndo(false);
      setRemovedItem(null);
    }
  };

  const handleCheckout = () => {
    setCheckoutStep(1);
  };

  const processPayment = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      setCheckoutStep(2);
      clearCart();
    }, 2000);
  };

  if (checkoutStep === 2) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center px-4 relative overflow-hidden">
        {/* Confetti / Sparkle background effect */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", damping: 10, duration: 1 }}
          className="absolute top-1/4"
        >
          <Sparkles className="w-64 h-64 text-green-100 opacity-50 absolute -top-12 -left-12 drop-shadow-xl" />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          className="bg-white p-8 rounded-3xl shadow-xl w-full max-w-sm text-center relative z-10 border border-green-50"
        >
          <motion.div
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ duration: 1, ease: "easeInOut" }}
            className="w-24 h-24 bg-green-100 text-green-500 rounded-full flex items-center justify-center mx-auto mb-6 relative"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              className="w-12 h-12"
            >
              <motion.path
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 0.8, delay: 0.2 }}
                d="M20 6L9 17l-5-5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.8, type: "spring" }}
              className="absolute -bottom-2 -right-2 bg-yellow-400 p-2 rounded-full border-4 border-white text-white"
            >
              <Sparkles className="w-4 h-4" />
            </motion.div>
          </motion.div>

          <h2 className="text-2xl font-extrabold text-gray-800 mb-2">
            Thanh toán Thành công!
          </h2>
          <p className="text-gray-500 mb-6 text-sm">
            Cảm ơn bạn đã đồng hành cùng FreshRoute.
          </p>

          <div className="bg-green-50 border border-green-100 rounded-2xl p-5 mb-8 text-left shadow-sm">
            <div className="flex items-center gap-3 mb-2">
              <FaLeaf className="text-green-500 text-xl" />
              <h3 className="font-bold text-green-800 text-[15px]">
                Thành tích của bạn
              </h3>
            </div>
            <p className="text-[13px] text-green-700 leading-relaxed font-medium">
              Chúc mừng! Bạn vừa giải cứu{" "}
              <strong>{totalImpact}kg</strong> thực phẩm và giảm
              tương đương <strong>{(totalImpact * 2).toFixed(1)}kg</strong> khí
              thải CO2.
            </p>
          </div>

          <button className="w-full relative group overflow-hidden bg-linear-to-r from-emerald-500 to-green-500 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-green-200 hover:shadow-green-300 transition-all flex items-center justify-center gap-2">
            <Share2 className="w-5 h-5" />
            Khoe chiến tích giải cứu
            <motion.div
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 w-1/2 bg-linear-to-r from-transparent via-white/30 to-transparent skew-x-12"
            />
          </button>

          <Link
            href="/customer"
            className="block mt-4 text-emerald-600 font-semibold text-sm hover:underline"
          >
            Tiếp tục mua sắm
          </Link>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f3f4f6] pb-64 sm:pb-72">
      {/* Header */}
      <header className="bg-white sticky top-0 z-40 border-b border-gray-100 shadow-sm">
        <div className="flex items-center justify-between px-4 py-4 max-w-2xl mx-auto">
          <Link
            href="/customer"
            className="text-gray-600 hover:text-gray-800 p-2 -ml-2"
          >
            <FaArrowLeft className="text-lg" />
          </Link>
          <div className="flex items-center gap-2">
            <h1 className="text-[18px] font-extrabold text-gray-900 tracking-tight">
              Giỏ Hàng Của Bạn
            </h1>
            {isRefreshing && (
              <RefreshCw className="animate-spin text-orange-500 w-4 h-4" />
            )}
          </div>
          <div className="w-8 relative" onClick={handlePullToRefresh}>
            <span className="absolute -top-1 -right-1 bg-emerald-500 text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
              {totalItemsCount}
            </span>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-6 h-6 text-gray-700"
            >
              <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z" />
              <path d="M3 6h18" />
              <path d="M16 10a4 4 0 0 1-8 0" />
            </svg>
          </div>
        </div>

        {/* Gamification Bar */}
        <div className="bg-linear-to-r from-emerald-50 via-green-50 to-emerald-50 px-4 py-2.5 border-b border-emerald-100">
          <div className="max-w-2xl mx-auto flex items-center justify-between text-xs sm:text-[13px]">
            <span className="font-semibold text-emerald-800 flex items-center gap-1.5">
              <FaLeaf className="text-emerald-500" /> Giải cứu Kim cương
            </span>
            <span className="text-emerald-600 font-medium">
              Còn 1 combo nữa!
            </span>
          </div>
          <div className="max-w-2xl mx-auto mt-2 h-1.5 bg-emerald-100 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: cart.length >= 2 ? "80%" : "40%" }}
              className="h-full bg-linear-to-r from-emerald-400 to-green-500 rounded-full relative"
            >
              <div className="absolute inset-0 w-full h-full opacity-50 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4IiBoZWlnaHQ9IjgiPgo8cmVjdCB3aWR0aD0iOCIgaGVpZ2h0PSI4IiBmaWxsPSIjZmZmIiBmaWxsLW9wYWNpdHk9IjAuMSI+PC9yZWN0Pgo8cGF0aCBkPSJNMCAwTDggOFoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2Utb3BhY2l0eT0iMC4yIj48L3BhdGg+Cjwvc3ZnPg==')]"></div>
            </motion.div>
          </div>
        </div>
      </header>

      {/* Main Content Area: Cart or Checkout Slide */}
      <div className="max-w-2xl mx-auto relative overflow-hidden">
        <AnimatePresence mode="wait">
          {checkoutStep === 0 && (
            <motion.div
              key="cart-view"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100, filter: "blur(4px)" }}
              transition={{ duration: 0.3 }}
              className="px-4 py-5 space-y-4"
            >
              {/* Cart Items List */}
              <AnimatePresence>
                {cart.map((item) => (
                  <motion.div
                    layout
                    key={item.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{
                      opacity: 0,
                      height: 0,
                      scale: 0.8,
                      marginBottom: 0,
                      overflow: "hidden",
                    }}
                    transition={{ type: "spring", damping: 25, stiffness: 200 }}
                    className="bg-white rounded-2xl p-4 shadow-xs border border-gray-100 relative overflow-hidden"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-800 text-[15px] leading-tight mb-1">
                          {item.name}
                        </h3>
                        <p className="text-[11px] text-gray-400 mb-1 max-w-[260px] truncate">
                          {(item.tags || []).join(", ")}
                        </p>
                        {item.discount > 0 && (
                          <span className="inline-block bg-red-50 text-red-500 text-[10px] font-bold px-2 py-0.5 rounded-full border border-red-100">
                            -{item.discount}%
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="text-gray-300 hover:text-red-500 transition-colors p-1"
                      >
                        <FaTrash className="text-sm" />
                      </button>
                    </div>

                    <div className="flex justify-between items-end mt-2">
                      <div>
                        {item.originalPrice > item.price && (
                          <div className="text-[11px] text-gray-400 line-through mb-0.5">
                            {item.originalPrice.toLocaleString("vi-VN")}đ
                          </div>
                        )}
                        <div className="font-extrabold text-[15px] text-emerald-600">
                          {item.price.toLocaleString("vi-VN")}đ
                        </div>
                      </div>

                      {/* Quantity Controls */}
                      <div className="flex items-center bg-gray-50 border border-gray-200 rounded-lg p-0.5">
                        <button
                          onClick={() => updateQuantity(item.id, -1)}
                          className="w-7 h-7 flex items-center justify-center text-gray-500 hover:bg-white hover:shadow-sm rounded-md transition-all font-medium text-lg"
                        >
                          -
                        </button>
                        <span className="w-8 text-center text-[13px] font-bold text-gray-800">
                          {item.quantity}
                        </span>
                        <button
                          onClick={() => updateQuantity(item.id, 1)}
                          className="w-7 h-7 flex items-center justify-center text-gray-500 hover:bg-white hover:shadow-sm rounded-md transition-all font-medium text-lg"
                        >
                          +
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}

                {cart.length === 0 && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-center py-12"
                  >
                    <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <FaLeaf className="text-gray-300 text-3xl" />
                    </div>
                    <h3 className="text-gray-500 font-medium">
                      Giỏ hàng trồng trơn
                    </h3>
                    <Link
                      href="/customer"
                      className="mt-4 inline-block bg-orange-500 text-white px-6 py-2 rounded-full font-bold text-sm"
                    >
                      Mua sắm ngay
                    </Link>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {checkoutStep === 1 && (
            <motion.div
              key="checkout-view"
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -100 }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="px-4 py-5 space-y-5"
            >
              <div
                className="flex items-center gap-3 mb-2"
                onClick={() => setCheckoutStep(0)}
              >
                <button className="p-2 bg-white rounded-full shadow-sm text-gray-600">
                  <FaArrowLeft className="text-sm" />
                </button>
                <h2 className="font-extrabold text-xl text-gray-800">
                  Phương thức thanh toán
                </h2>
              </div>

              <div className="space-y-3 relative z-10">
                {/* Payment Method 1 */}
                <motion.div
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setPaymentMethod("momo")}
                  className={`relative p-4 rounded-2xl border-2 transition-all cursor-pointer flex items-center gap-4 bg-white ${paymentMethod === "momo" ? "border-emerald-500 shadow-md shadow-emerald-100/50" : "border-gray-100"}`}
                >
                  <div className="w-12 h-12 bg-pink-50 rounded-xl flex items-center justify-center">
                    <span className="text-pink-600 font-black text-xl italic">
                      MoMo
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-800 text-[15px]">
                      Ví MoMo
                    </h3>
                    <p className="text-[12px] text-gray-400">
                      Thanh toán siêu tốc
                    </p>
                  </div>
                  <AnimatePresence>
                    {paymentMethod === "momo" && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white"
                      >
                        <Check className="w-4 h-4 stroke-3" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>

                {/* Payment Method 2 */}
                <motion.div
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setPaymentMethod("vnpay")}
                  className={`relative p-4 rounded-2xl border-2 transition-all cursor-pointer flex items-center gap-4 bg-white ${paymentMethod === "vnpay" ? "border-emerald-500 shadow-md shadow-emerald-100/50" : "border-gray-100"}`}
                >
                  <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center">
                    <span className="text-blue-600 font-extrabold text-[15px]">
                      VNPAY
                    </span>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-gray-800 text-[15px]">
                      VNPAY-QR
                    </h3>
                    <p className="text-[12px] text-gray-400">
                      Quét mã qua ứng dụng ngân hàng
                    </p>
                  </div>
                  <AnimatePresence>
                    {paymentMethod === "vnpay" && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        className="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center text-white"
                      >
                        <Check className="w-4 h-4 stroke-3" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>

                {/* Delivery Address skeleton */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h3 className="font-bold text-gray-800 text-[15px] mb-3">
                    Giao hàng đến
                  </h3>
                  <div className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex gap-3">
                    <div className="mt-0.5">
                      <CheckCircle className="text-emerald-500 w-5 h-5 fill-emerald-50" />
                    </div>
                    <div>
                      <p className="font-bold text-[14px]">
                        Nguyễn Văn A - 0987123456
                      </p>
                      <p className="text-[13px] text-gray-500 mt-0.5">
                        123 Đường ABC, Quận 1, TP. HCM
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Undo Toast */}
      <AnimatePresence>
        {showUndo && removedItem && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            className="fixed bottom-36 left-4 right-4 max-w-sm mx-auto bg-gray-900 text-white px-4 py-3 rounded-xl shadow-2xl flex justify-between items-center z-50 pointer-events-auto"
          >
            <div className="text-[13px] font-medium flex items-center gap-2">
              <span className="w-6 h-6 bg-gray-800 rounded-md flex items-center justify-center">
                <FaTrash className="text-[10px] text-gray-400" />
              </span>
              Đã xóa món hàng
            </div>
            <button
              onClick={undoRemove}
              className="text-emerald-400 font-bold text-[13px] hover:text-emerald-300 px-3 py-1 bg-white/10 rounded-lg transition-colors"
            >
              HOÀN TÁC
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sticky Bottom Summary Sticky bar for step 0 and 1 */}
      {cart.length > 0 && checkoutStep < 2 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-[0_-10px_20px_rgba(0,0,0,0.03)] z-40 rounded-t-3xl">
          <div className="max-w-2xl mx-auto">
            <div className="space-y-2 mb-4 px-2">
              <div className="flex justify-between text-gray-500 text-[13px] font-medium">
                <span>Tạm tính</span>
                <span>
                  <PriceTicker value={subtotal} />đ
                </span>
              </div>
              <div className="flex justify-between text-amber-600 text-[13px] font-medium">
                <span>Tiết kiệm giải cứu</span>
                <span className="font-bold">
                  -<PriceTicker value={totalDiscount} />đ
                </span>
              </div>
              <div className="flex justify-between text-gray-500 text-[13px] font-medium pb-2 border-b border-gray-100">
                <span>Phí giao hàng</span>
                <span>25.000đ</span>
              </div>
              <div className="flex justify-between items-center pt-1">
                <span className="font-bold text-gray-800 text-[16px]">
                  Tổng cộng
                </span>
                <span className="font-black text-2xl text-emerald-600 tracking-tight">
                  <PriceTicker value={finalTotal} />đ
                </span>
              </div>
            </div>

            {checkoutStep === 0 ? (
              <button
                onClick={handleCheckout}
                className="w-full bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-[16px] py-4 rounded-xl shadow-lg shadow-emerald-200 transition-colors flex items-center justify-center gap-2"
              >
                <span>Tiếp tục thanh toán</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={processPayment}
                disabled={isProcessing}
                className="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-400 text-white font-bold text-[16px] py-4 rounded-xl shadow-lg shadow-emerald-200 transition-all flex items-center justify-center gap-2 relative overflow-hidden"
              >
                {isProcessing ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{
                      repeat: Infinity,
                      duration: 1,
                      ease: "linear",
                    }}
                  >
                    <RefreshCw className="w-5 h-5 text-white" />
                  </motion.div>
                ) : (
                  <>
                    Thanh toán ngay <CheckCircle className="w-5 h-5" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
