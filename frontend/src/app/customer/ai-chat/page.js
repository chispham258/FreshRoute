"use client";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaRobot,
  FaPaperPlane,
  FaShoppingCart,
  FaArrowLeft,
  FaCheckCircle,
  FaSpinner,
} from "react-icons/fa";
import { MdOutlineFastfood } from "react-icons/md";
import { HiOutlineSparkles } from "react-icons/hi";

const CHIPS = [
  { id: "today", icon: "🎯", label: "Gợi ý món ăn hôm nay" },
  { id: "inventory", icon: "🧑‍🍳", label: "Nấu với nguyên liệu sẵn có" },
  { id: "preference", icon: "🔎", label: "Tìm món theo sở thích" },
];

const MOCK_BUNDLE = {
  id: 101,
  type: "bundle",
  name: "Combo Phở Bò Chóp",
  price: 139000,
  inStock: true,
  ingredients: [
    { name: "Thịt Bò Bắp 500g", expiry: 2, status: "warning" },
    { name: "Bánh Phở 300g", expiry: 5, status: "safe" },
    { name: "Rau Thơm 100g", expiry: 3, status: "warning" },
    { name: "Hành Tây 200g", expiry: 7, status: "safe" },
    { name: "Nước Dùng Xương 500ml", expiry: 4, status: "safe" },
  ],
  instructions: [
    "Luộc nước dùng xương ở lửa vừa trong 20 phút",
    "Thái thịt bò bắp thành lát mỏng",
    "Trụng bánh phở trong nước sôi 2-3 phút",
    "Rửa sạch rau thơm và cắt hành lá",
    "Cho bánh phở vào tô, xếp thịt bò lên trên",
    "Chan nước dùng nóng, thêm rau thơm và hành",
  ],
};

const MOCK_RECIPE = {
  id: 201,
  type: "recipe",
  name: "Lẩu Bò Nhúng Dấm",
  price: "Theo nguyên liệu",
  inStock: false,
  ingredients: [
    {
      name: "Thịt Bò Thăn 500g",
      inStock: false,
      price: 150000,
      selected: true,
    },
    { name: "Nước lẩu dấm", inStock: true, price: 30000, selected: false },
    { name: "Rau cải thảo 500g", inStock: false, price: 20000, selected: true },
  ],
};

function BotMessage({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className="flex gap-4 w-full mb-6"
    >
      <div className="w-10 h-10 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 text-white shrink-0 flex items-center justify-center shadow-md">
        <HiOutlineSparkles className="text-xl" />
      </div>
      <div className="flex-1 max-w-[85%] bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm p-4 text-gray-800 relative z-10 w-full overflow-hidden">
        {children}
      </div>
    </motion.div>
  );
}

function UserMessage({ text }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      className="flex gap-4 w-full justify-end mb-6"
    >
      <div className="bg-[#00b14f] shadow-md shadow-green-200/50 rounded-2xl rounded-tr-sm p-4 text-white max-w-[80%] font-medium whitespace-pre-wrap">
        {text}
      </div>
    </motion.div>
  );
}

function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      className="flex gap-4 w-full mb-6"
    >
      <div className="w-10 h-10 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 text-white shrink-0 flex items-center justify-center shadow-md">
        <HiOutlineSparkles className="text-xl animate-pulse" />
      </div>
      <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-5 py-4 text-gray-800 flex items-center gap-2 h-12 w-24 justify-center">
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1, delay: 0 }}
          className="w-2 h-2 rounded-full bg-indigo-500"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1, delay: 0.2 }}
          className="w-2 h-2 rounded-full bg-indigo-500"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1, delay: 0.4 }}
          className="w-2 h-2 rounded-full bg-indigo-500"
        />
      </div>
    </motion.div>
  );
}

// Expandable Bundle Card with Framer Motion Layout animations
function BundleCard({ item, onAddToCart }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      layout="position"
      className="bg-white border-2 border-green-100 rounded-xl overflow-hidden mb-4 shadow-sm hover:shadow-md transition-shadow relative"
    >
      {item.inStock && (
        <div className="absolute top-3 right-3 bg-green-100 text-green-700 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 z-10">
          <FaCheckCircle /> Sẵn kho
        </div>
      )}

      <motion.div
        layout="position"
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <motion.h4
          layout="position"
          className="font-bold text-gray-900 text-lg pr-20"
        >
          {item.name}
        </motion.h4>
        <motion.p
          layout="position"
          className="text-sm font-semibold text-orange-600 mt-1"
        >
          {item.price
            ? item.price.toLocaleString("vi-VN") + " VNĐ"
            : "Chưa rõ giá"}
        </motion.p>
      </motion.div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-100 bg-gray-50/50"
          >
            <div className="p-4 space-y-4">
              {/* Ingredients */}
              <div>
                <h5 className="text-sm font-bold text-gray-700 mb-2">
                  Thành phần trong Bundle
                </h5>
                <div className="space-y-2">
                  {item.ingredients.map((ing, idx) => (
                    <div
                      key={idx}
                      className="flex justify-between items-center text-sm bg-white p-2.5 rounded-lg border border-gray-200"
                    >
                      <span className="flex items-center gap-2 font-medium text-gray-700">
                        <FaCheckCircle className="text-[#00b14f]" /> {ing.name}
                      </span>
                      {ing.status === "warning" && (
                        <span className="text-[10px] font-bold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full animate-pulse shadow-sm shadow-amber-200">
                          Date cận
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Price Panel */}
              <div className="bg-orange-50/80 border border-orange-200 rounded-xl p-3 flex justify-between items-center">
                <span className="font-bold text-gray-800">
                  Giá siêu tiết kiệm
                </span>
                <span className="text-xl font-extrabold text-orange-600">
                  {item.price.toLocaleString("vi-VN")} VNĐ
                </span>
              </div>

              {/* Instructions */}
              <div>
                <h5 className="text-sm font-bold text-gray-700 mb-2 flex items-center gap-1.5">
                  <MdOutlineFastfood className="text-lg text-blue-500" /> Gợi ý
                  cách nấu
                </h5>
                <ul className="space-y-3 bg-white p-3 border border-gray-200 rounded-xl">
                  {item.instructions.map((inst, idx) => (
                    <li key={idx} className="flex gap-3 text-sm text-gray-600">
                      <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-extrabold shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="leading-snug">{inst}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <motion.button
                whileTap={{ scale: 0.96 }}
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart(item);
                }}
                className="w-full bg-[#00b14f] hover:bg-[#009e46] text-white font-bold py-3.5 rounded-xl shadow-lg shadow-green-500/30 flex justify-center items-center gap-2 mt-2"
              >
                <FaShoppingCart className="text-lg" /> Thêm Gói Này Vào Giỏ
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

// Recipe Card with interactive selection
function RecipeCard({ item, onAddToCart }) {
  const [expanded, setExpanded] = useState(false);
  const [selectedIngs, setSelectedIngs] = useState(
    item.ingredients.map((i) => i.selected),
  );

  const total = item.ingredients.reduce(
    (acc, ing, idx) => (selectedIngs[idx] ? acc + ing.price : acc),
    0,
  );

  const toggleIng = (idx) => {
    const newSel = [...selectedIngs];
    newSel[idx] = !newSel[idx];
    setSelectedIngs(newSel);
  };

  return (
    <motion.div
      layout="position"
      className="bg-white border-2 border-indigo-100 rounded-xl overflow-hidden mb-4 shadow-sm hover:shadow-md transition-shadow relative"
    >
      {!item.inStock && (
        <div className="absolute top-3 right-3 bg-rose-100 text-rose-700 border border-rose-200 text-[10px] font-bold px-2 py-0.5 rounded flex items-center gap-1 z-10">
          Thiếu nguyên liệu
        </div>
      )}

      <motion.div
        layout="position"
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <motion.h4
          layout="position"
          className="font-bold text-gray-900 text-lg pr-24"
        >
          {item.name}
        </motion.h4>
        <motion.p
          layout="position"
          className="text-sm font-medium text-gray-500 mt-1"
        >
          Lạc vào công thức: bạn chọn mua gì?
        </motion.p>
      </motion.div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-gray-100 bg-gray-50/50"
          >
            <div className="p-4 space-y-4">
              <div>
                <h5 className="text-sm font-bold text-gray-700 mb-2">
                  Nguyên Liệu Cần Cho Món Này
                </h5>
                <div className="space-y-2">
                  {item.ingredients.map((ing, idx) => (
                    <label
                      key={idx}
                      className={`flex justify-between items-center text-sm bg-white p-3 rounded-xl border border-gray-200 cursor-pointer transition-colors ${selectedIngs[idx] ? "border-indigo-300 bg-indigo-50/30" : "hover:bg-gray-50"}`}
                    >
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={selectedIngs[idx]}
                          onChange={() => toggleIng(idx)}
                          className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500 border-gray-300"
                        />
                        <span
                          className={`font-medium ${selectedIngs[idx] ? "text-indigo-900" : "text-gray-600"}`}
                        >
                          {ing.name}
                        </span>
                        {ing.inStock && (
                          <span className="text-[10px] text-emerald-600 bg-emerald-100 px-1.5 py-0.5 rounded font-bold">
                            Có sẵn ở nhà
                          </span>
                        )}
                      </div>
                      <span className="font-bold text-gray-700">
                        {ing.price.toLocaleString("vi-VN")}đ
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="bg-indigo-50/80 border border-indigo-200 rounded-xl p-3 flex justify-between items-center">
                <span className="font-bold text-gray-800">
                  Tạm tính phần mua thêm
                </span>
                <span className="text-xl font-extrabold text-indigo-600">
                  {total.toLocaleString("vi-VN")} VNĐ
                </span>
              </div>

              <motion.button
                whileTap={{ scale: 0.96 }}
                onClick={(e) => {
                  e.stopPropagation();
                  onAddToCart({ ...item, price: total });
                }}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-indigo-500/30 flex justify-center items-center gap-2 mt-2"
              >
                <FaShoppingCart className="text-lg" /> Thêm Các Món Này Vào Giỏ
              </motion.button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function AIChatPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "bot",
      content: (
        <div className="space-y-2">
          <p className="text-base leading-relaxed font-medium">
            👋 Chào bạn! Tôi là FreshRoute AI.
          </p>
          <p className="text-sm text-gray-600">
            Tôi có thể giúp bạn lên thực đơn từ nguyên liệu sẵn có, hoặc săn các
            Combo thực phẩm siêu rẻ sắp hết hạn. Hôm nay bạn cần gì?
          </p>
        </div>
      ),
    },
  ]);
  const [inputStr, setInputStr] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const bottomRef = useRef(null);

  const [cartCount, setCartCount] = useState(0);
  const [cartAnimating, setCartAnimating] = useState(false);

  // Scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // Install hi-outline-sparkles dynamically? Wait, I used hi react-icons!
  const handleAddToCart = (item) => {
    if (typeof navigator !== "undefined" && navigator.vibrate)
      navigator.vibrate(50);

    setCartCount((prev) => prev + 1);
    setCartAnimating(true);
    setTimeout(() => setCartAnimating(false), 600);

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        type: "bot",
        content: (
          <div className="flex items-center gap-2 text-emerald-700 bg-emerald-50 px-3 py-2 -mx-2 -my-1 rounded-lg">
            <FaCheckCircle className="text-lg" />
            <span className="text-sm font-semibold">
              Đã thêm <strong>{item.name}</strong> vào giỏ hàng!
            </span>
          </div>
        ),
      },
    ]);
  };

  const handleSend = (textOverride = inputStr) => {
    const text =
      typeof textOverride === "string" ? textOverride.trim() : inputStr.trim();
    if (!text) return;

    setInputStr("");
    setMessages((prev) => [...prev, { id: Date.now(), type: "user", text }]);
    setIsThinking(true);

    setTimeout(() => {
      setIsThinking(false);

      let botContent;
      const lower = text.toLowerCase();

      if (
        lower.includes("nguyên liệu") ||
        lower.includes("thịt") ||
        lower.includes("có sẵn")
      ) {
        botContent = (
          <div className="space-y-3 w-full">
            <p className="text-sm font-medium">
              Tôi tìm thấy một Bundle hoàn hảo để nấu cùng nguyên liệu của bạn,
              lại đang được giảm giá cực tốt:
            </p>
            <BundleCard item={MOCK_BUNDLE} onAddToCart={handleAddToCart} />
          </div>
        );
      } else if (
        lower.includes("sở thích") ||
        lower.includes("lẩu") ||
        lower.includes("nhúng")
      ) {
        botContent = (
          <div className="space-y-3 w-full">
            <p className="text-sm font-medium">
              Bạn muốn ăn lẩu? Đây là công thức kèm danh sách mua sắm những món
              bạn còn thiếu:
            </p>
            <RecipeCard item={MOCK_RECIPE} onAddToCart={handleAddToCart} />
          </div>
        );
      } else {
        botContent = (
          <div className="space-y-3 w-full">
            <p className="text-sm font-medium">
              Tôi có 1 Combo đang Hot hôm nay, mua ngay để tiết kiệm và giảm
              lãng phí nhé:
            </p>
            <BundleCard
              item={{
                ...MOCK_BUNDLE,
                name: "Combo Đặc Biệt Tối Nay",
                price: 99000,
              }}
              onAddToCart={handleAddToCart}
            />
          </div>
        );
      }

      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, type: "bot", content: botContent },
      ]);
    }, 1800);
  };

  return (
    <div className="flex flex-col h-screen max-h-dvh bg-slate-50 font-sans">
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 px-4 py-3 flex items-center justify-between shadow-sm z-20 shrink-0 sticky top-0">
        <div className="flex items-center gap-3">
          <Link href="/customer">
            <button className="p-2.5 hover:bg-gray-100 rounded-full transition-colors text-gray-700 bg-gray-50 border border-transparent hover:border-gray-200">
              <FaArrowLeft />
            </button>
          </Link>
          <div className="flex gap-2 items-center">
            <div className="w-10 h-10 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-200">
              <HiOutlineSparkles className="text-2xl" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="font-extrabold text-gray-900 text-base">
                  FreshRoute AI
                </h1>
                <span className="bg-purple-100 text-purple-700 text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-wider">
                  Beta
                </span>
              </div>
              <p className="text-[10px] text-gray-500 font-semibold flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>{" "}
                Sẵn sàng gợi ý món ngon
              </p>
            </div>
          </div>
        </div>

        <div className="relative">
          <Link href="/customer/cart">
            <motion.button
              animate={
                cartAnimating
                  ? { scale: [1, 1.2, 1], rotate: [0, -10, 10, 0] }
                  : {}
              }
              transition={{ duration: 0.5 }}
              className="p-3 rounded-full bg-white border border-gray-200 text-gray-700 shadow-sm transition-all hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-1 relative"
            >
              <FaShoppingCart className="text-lg" />
            </motion.button>
          </Link>
          <AnimatePresence>
            {cartCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[11px] font-black w-6 h-6 flex items-center justify-center rounded-full border-2 border-white shadow-sm"
              >
                {cartCount}
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-8 relative scroll-smooth bg-linear-to-b from-slate-50 to-white">
        <div className="max-w-2xl mx-auto flex flex-col justify-end min-h-full">
          <div className="space-y-2">
            <AnimatePresence>
              {messages.map((msg) => (
                <div key={msg.id} className="w-full relative">
                  {msg.type === "bot" ? (
                    <BotMessage>{msg.content}</BotMessage>
                  ) : (
                    <UserMessage text={msg.text} />
                  )}
                </div>
              ))}
              {isThinking && <TypingIndicator key="thinking" />}
            </AnimatePresence>
            <div ref={bottomRef} className="h-6" />
          </div>
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 px-4 py-4 pb-6 sm:pb-8 w-full shrink-0 shadow-[0_-4px_20px_-10px_rgba(0,0,0,0.05)] z-20">
        <div className="max-w-3xl mx-auto">
          {/* Action Chips */}
          <div className="flex gap-2.5 mb-4 overflow-x-auto pb-2 no-scrollbar px-1 -mx-1 snap-x">
            {CHIPS.map((chip) => (
              <button
                key={chip.id}
                onClick={() => handleSend(chip.label)}
                className="snap-start shrink-0 px-4 py-2 border border-gray-200 text-gray-700 bg-white hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 rounded-full text-sm font-semibold whitespace-nowrap transition-colors flex items-center gap-2 shadow-sm"
              >
                <span className="text-lg">{chip.icon}</span> {chip.label}
              </button>
            ))}
          </div>

          <div className="relative flex items-center bg-gray-100 rounded-full border border-gray-200 focus-within:border-indigo-500 focus-within:ring-4 focus-within:ring-indigo-500/10 transition-all p-1.5 shadow-inner">
            <input
              type="text"
              value={inputStr}
              onChange={(e) => setInputStr(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Bạn đang muốn ăn món gì hôm nay?"
              className="flex-1 bg-transparent py-3 pl-5 pr-4 outline-none text-gray-800 font-medium placeholder-gray-400"
            />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleSend()}
              className={`w-12 h-12 flex items-center justify-center rounded-full text-white transition-all shadow-md ${inputStr.trim() ? "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-500/30" : "bg-gray-300 pointer-events-none"}`}
            >
              <FaPaperPlane className="-ml-1 text-lg" />
            </motion.button>
          </div>

          <p className="text-center text-[10px] text-gray-400 mt-4 flex items-center justify-center gap-1.5 font-semibold uppercase tracking-wider">
            <FaCheckCircle className="text-emerald-500 text-xs" /> Tối ưu nguyên
            liệu - Giảm lãng phí thực phẩm
          </p>
        </div>
      </footer>
    </div>
  );
}
