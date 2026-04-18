/* eslint-disable @next/next/no-img-element */
"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import {
  FaShoppingCart,
  FaStore,
  FaFire,
  FaLeaf,
  FaTimes,
  FaCheckCircle,
} from "react-icons/fa";
import { MdChat, MdOutlineFastfood } from "react-icons/md";
import { HiOutlineSparkles } from "react-icons/hi";
import { motion, AnimatePresence } from "framer-motion";
import { fetchCustomerCombos } from "@/lib/customerApi";
import { loadCart, addItemToCart } from "@/lib/cart";

const DEFAULT_STORE_ID = "BHX-HCM001";
const COMBO_LIMIT = 12;

export default function CustomerPage() {
  const [combos, setCombos] = useState([]);

  const [cart, setCart] = useState(() => loadCart());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);
  const [selectedCombo, setSelectedCombo] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const fetchCombos = async () => {
      setLoading(true);
      setError("");

      try {
        const comboData = await fetchCustomerCombos({
          storeId: DEFAULT_STORE_ID,
          limit: COMBO_LIMIT,
        });

        if (!cancelled) {
          setCombos(comboData);
        }
      } catch (fetchError) {
        if (!cancelled) {
          setCombos([]);
          setError(fetchError.message || "Không thể tải danh sách combo.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchCombos();

    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  const addToCart = (combo) => {
    const updated = addItemToCart(combo);
    setCart(updated);
    setSelectedCombo(null);
  };

  const cartItemCount = cart.reduce((total, item) => total + item.quantity, 0);

  return (
    <div className="min-h-screen bg-[#f8f9fc] pb-24 relative font-sans">
      {/* Header Navbar */}
      <nav className="bg-white border-b border-gray-200 px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-30 shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="bg-orange-500 p-1.5 rounded-lg text-white">
            <FaLeaf className="text-xl" />
          </div>
          <div>
            <h1 className="font-extrabold text-gray-900 text-lg leading-tight">
              FreshRoute
            </h1>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">
              Siêu Thị Thông Minh
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <Link href="/admin">
            <button className="hidden sm:flex text-gray-500 hover:text-gray-800 text-sm font-bold transition-colors items-center gap-1.5 px-3 py-1.5 bg-gray-50 rounded-lg border border-gray-200/60 shadow-sm">
              <FaStore /> Về Admin
            </button>
          </Link>

          <Link href="/customer/cart">
            <div className="relative cursor-pointer bg-orange-50 p-2.5 rounded-full hover:bg-orange-100 transition-colors group">
              <FaShoppingCart className="text-orange-600 text-lg group-hover:scale-110 transition-transform" />
              {cartItemCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-4.5 text-center border-2 border-white shadow-sm animate-in zoom-in">
                  {cartItemCount}
                </span>
              )}
            </div>
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 sm:mt-8">
        {/* Banner */}
        <div className="mb-8 rounded-2xl overflow-hidden relative shadow-md">
          <img
            src="https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1200&auto=format&fit=crop"
            alt="Banner"
            className="w-full h-40 sm:h-56 object-cover"
          />
          <div className="absolute inset-0 bg-linear-to-r from-black/70 to-transparent flex items-center px-6 sm:px-10">
            <div className="text-white max-w-md">
              <h2 className="text-2xl sm:text-3xl font-extrabold mb-2 flex items-center gap-2">
                Chống Lãng Phí <FaFire className="text-orange-500" />
              </h2>
              <p className="text-sm sm:text-base text-gray-200 font-medium">
                Mua các set Combo nguyên liệu sơ chế sạch sẽ với giá siêu ưu
                đãi. Giảm rác thải thực phẩm!
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            Combo Đề Xuất Hôm Nay{" "}
            <HiOutlineSparkles className="text-orange-500" />
          </h2>
          <div className="flex gap-2 pb-2 overflow-x-auto no-scrollbar">
            {["Tất cả", "Thịt cá", "Rau củ", "Siêu rẻ"].map((cat) => (
              <button
                key={cat}
                className="px-4 py-1.5 rounded-full text-sm font-semibold whitespace-nowrap bg-white border border-gray-200 text-gray-600 shadow-sm hover:border-orange-500 hover:text-orange-600 transition-colors focus:bg-orange-50 focus:text-orange-600 focus:border-orange-500"
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64 text-gray-500 font-semibold text-lg animate-pulse">
            Đang tìm kiếm món ngon cho bạn...
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <p className="font-semibold">{error}</p>
            <button
              onClick={() => setReloadToken((value) => value + 1)}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-semibold text-sm"
            >
              Thử lại
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {combos.length === 0 ? (
              <div className="col-span-full text-center text-gray-500 bg-gray-50 border border-gray-200 rounded-xl py-8 px-4 font-medium">
                Hiện chưa có combo khả dụng cho cửa hàng này.
              </div>
            ) : (
              combos.map((combo) => (
                <div
                  key={combo.id}
                  onClick={() => setSelectedCombo(combo)}
                  className="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-xl hover:-translate-y-1.5 transition-all duration-300 ease-out group flex flex-col cursor-pointer"
                >
                  {/* Image Section */}
                  <div className="relative h-48 overflow-hidden">
                    <div className="absolute top-3 right-3 z-10 bg-red-500 text-white text-xs font-black px-2 py-1 rounded shadow-md">
                      -{combo.discount}%
                    </div>
                    <img
                      src={combo.image}
                      alt={combo.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>

                  {/* Content Section */}
                  <div className="p-4 sm:p-5 flex-1 flex flex-col relative bg-white z-10">
                    <div className="flex gap-1.5 flex-wrap mb-2">
                      {combo.tags.map((tag, idx) => (
                        <span
                          key={idx}
                          className="bg-orange-50 text-orange-600 text-[10px] font-bold px-2 py-0.5 rounded-full border border-orange-100"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>

                    <h3 className="text-lg font-bold text-gray-900 mb-1.5 leading-tight group-hover:text-orange-600 transition-colors">
                      {combo.name}
                    </h3>

                    <p className="text-xs text-gray-500 mb-4 line-clamp-2 leading-relaxed flex-1">
                      {combo.description}
                    </p>

                    <div className="flex items-end justify-between mt-auto">
                      <div>
                        <div className="text-xs text-gray-400 line-through font-medium mb-0.5">
                          {combo.originalPrice.toLocaleString("vi-VN")} đ
                        </div>
                        <div className="text-lg font-black text-orange-500">
                          {combo.newPrice.toLocaleString("vi-VN")} đ
                        </div>
                      </div>

                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          addToCart(combo);
                        }}
                        className="bg-orange-500 hover:bg-orange-600 hover:-translate-y-0.5 active:scale-95 text-white rounded-full p-2.5 shadow-md shadow-orange-200/50 hover:shadow-lg transition-all duration-200"
                        title="Thêm vào giỏ"
                      >
                        <FaShoppingCart className="text-[14px]" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </main>

      {/* Floating AI Chat Button */}
      <Link href="/customer/ai-chat">
        <button className="fixed bottom-6 right-6 sm:bottom-8 sm:right-8 bg-[#00b14f] hover:bg-[#009e46] text-white p-4 rounded-full shadow-xl shadow-[#00b14f]/30 hover:scale-105 transition-all duration-300 group z-40 flex items-center justify-center animate-bounce hover:animate-none">
          <MdChat className="text-2xl" />
          <div className="absolute right-full mr-4 top-1/2 -translate-y-1/2 bg-gray-900 text-white text-xs font-bold py-1.5 px-3 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
            Chat gợi ý món ăn AI
            <div className="absolute top-1/2 -translate-y-1/2 -right-1 border-[5px] border-transparent border-l-gray-900"></div>
          </div>
        </button>
      </Link>

      {/* Combo Details Modal */}
      <AnimatePresence>
        {selectedCombo && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4 pt-4 pb-20 sm:p-0">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedCombo(null)}
              className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm transition-opacity"
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-white rounded-2xl shadow-2xl relative overflow-hidden w-full max-w-lg z-10 max-h-[90vh] flex flex-col"
            >
              <div className="relative h-48 sm:h-56 shrink-0">
                <img
                  src={selectedCombo.image}
                  alt={selectedCombo.name}
                  className="w-full h-full object-cover"
                />
                <button
                  onClick={() => setSelectedCombo(null)}
                  className="absolute top-4 right-4 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full backdrop-blur-md transition-colors"
                >
                  <FaTimes />
                </button>
                <div className="absolute bottom-0 left-0 right-0 bg-linear-to-t from-black/80 to-transparent p-4">
                  <div className="flex gap-2 mb-1">
                    {selectedCombo.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="bg-orange-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-white">
                    {selectedCombo.name}
                  </h2>
                </div>
              </div>

              <div className="p-5 sm:p-6 overflow-y-auto flex-1 bg-gray-50/50">
                <p className="text-sm text-gray-600 mb-6 font-medium leading-relaxed bg-orange-50 border border-orange-100 p-3 rounded-xl shadow-sm">
                  <FaFire className="inline-block text-orange-500 mb-1 mr-1" />
                  {selectedCombo.description}
                </p>

                <div className="space-y-6">
                  {/* Ingredients */}
                  <div>
                    <h4 className="text-sm font-extrabold text-gray-900 mb-3 flex items-center gap-2">
                      <FaLeaf className="text-emerald-500" /> Nguyên Liệu Chính
                      ({selectedCombo.ingredients?.length || 0})
                    </h4>
                    <div className="space-y-2.5">
                      {selectedCombo.ingredients?.map((ing, idx) => (
                        <div
                          key={idx}
                          className="flex justify-between items-center text-sm bg-white p-3 rounded-xl border border-gray-200 shadow-sm"
                        >
                          <span className="flex items-center gap-2 font-medium text-gray-700">
                            <FaCheckCircle className="text-emerald-500" />{" "}
                            {ing.name}
                          </span>
                          {ing.status === "warning" && (
                            <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-1 rounded-full border border-red-100">
                              Cận Date
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Instructions */}
                  <div>
                    <h4 className="text-sm font-extrabold text-gray-900 mb-3 flex items-center gap-2">
                      <MdOutlineFastfood className="text-blue-500 text-lg" />{" "}
                      Các bước nấu ăn
                    </h4>
                    <ul className="space-y-3 bg-white p-4 border border-gray-200 rounded-xl shadow-sm">
                      {selectedCombo.instructions?.map((inst, idx) => (
                        <li
                          key={idx}
                          className="flex gap-3 text-sm text-gray-600"
                        >
                          <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-extrabold shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span className="leading-snug font-medium">
                            {inst}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              <div className="p-4 sm:p-5 bg-white border-t border-gray-100 flex items-center justify-between shrink-0 shadow-[0_-4px_10px_rgba(0,0,0,0.02)]">
                <div>
                  <div className="text-xs text-gray-500 line-through font-semibold mb-0.5">
                    {selectedCombo.originalPrice.toLocaleString("vi-VN")} VNĐ
                  </div>
                  <div className="text-2xl font-black text-orange-600">
                    {selectedCombo.newPrice.toLocaleString("vi-VN")}{" "}
                    <span className="text-sm font-bold text-gray-500">VNĐ</span>
                  </div>
                </div>
                <button
                  onClick={() => addToCart(selectedCombo)}
                  className="bg-orange-500 hover:bg-orange-600 text-white font-extrabold py-3 px-6 rounded-xl shadow-lg shadow-orange-500/30 transition-transform active:scale-95 flex items-center gap-2"
                >
                  <FaShoppingCart /> Thêm Vào Giỏ
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

    </div>
  );
}
