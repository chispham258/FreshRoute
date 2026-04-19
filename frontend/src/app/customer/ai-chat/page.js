"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  FaPaperPlane,
  FaShoppingCart,
  FaArrowLeft,
  FaCheckCircle,
} from "react-icons/fa";
import { HiOutlineSparkles, HiChevronDown } from "react-icons/hi";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { sendConsumerChat } from "@/lib/customerApi";
import { addItemToCart } from "@/lib/cart";
import { formatVnd } from "@/lib/currency";

const CHIPS = [
  { id: "today", icon: "🎯", label: "Gợi ý món ăn hôm nay" },
  { id: "inventory", icon: "🧑‍🍳", label: "Nấu với nguyên liệu sẵn có" },
  { id: "preference", icon: "🔎", label: "Tìm món theo sở thích" },
];

function MarkdownMessage({ text }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => (
          <p className="text-sm leading-relaxed text-gray-700 mb-2 last:mb-0">
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1 mb-2">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal list-inside text-sm text-gray-700 space-y-1 mb-2">
            {children}
          </ol>
        ),
        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
        strong: ({ children }) => (
          <strong className="font-extrabold text-gray-900">{children}</strong>
        ),
        em: ({ children }) => <em className="italic">{children}</em>,
        code: ({ children }) => (
          <code className="bg-gray-100 border border-gray-200 rounded px-1 py-0.5 text-xs font-semibold text-gray-800">
            {children}
          </code>
        ),
        a: ({ children, href }) => (
          <a
            href={href}
            className="text-indigo-600 underline underline-offset-2 font-semibold"
            target="_blank"
            rel="noreferrer"
          >
            {children}
          </a>
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  );
}

function RecipeSuggestionCard({ suggestion }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className="border border-indigo-100 rounded-lg p-2.5 mb-1.5 bg-white cursor-pointer hover:border-indigo-300 transition-colors"
      onClick={() => setExpanded((v) => !v)}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold text-gray-800 text-sm">
          {suggestion.name}
        </span>
        <HiChevronDown
          className={`text-gray-400 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`}
        />
      </div>
      {expanded &&
        (suggestion.ingredients?.length > 0 ? (
          <ul className="mt-2 space-y-1">
            {suggestion.ingredients.map((ing, i) => (
              <li key={i} className="flex items-center gap-1.5 text-xs">
                <span
                  className={ing.have ? "text-emerald-500" : "text-gray-300"}
                >
                  ●
                </span>
                <span
                  className={
                    ing.have ? "text-gray-700 font-medium" : "text-gray-500"
                  }
                >
                  {ing.name}
                </span>
                {ing.optional && (
                  <span className="text-gray-400">(tùy chọn)</span>
                )}
                {!ing.have && !ing.optional && (
                  <span className="ml-auto text-indigo-500 font-semibold">
                    cần mua
                  </span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-xs text-gray-400 italic">
            Đang tải danh sách nguyên liệu...
          </p>
        ))}
    </div>
  );
}

function RecipeSuggestionsPanel({ suggestions }) {
  if (!suggestions || suggestions.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-2">
        Gợi ý món ăn
      </p>
      {suggestions.map((s) => (
        <RecipeSuggestionCard key={s.recipe_id} suggestion={s} />
      ))}
    </div>
  );
}

function BotMessage({ text, shoppingList, recipeSuggestions, allergies }) {
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
      <div className="flex-1 max-w-[85%] bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm p-4 relative z-10 w-full overflow-hidden">
        <MarkdownMessage text={text} />
        <RecipeSuggestionsPanel suggestions={recipeSuggestions} />
        <ShoppingListPanel items={shoppingList} allergies={allergies} />
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

function ShoppingListPanel({ items, allergies = [] }) {
  const [added, setAdded] = useState(false);
  const [selected, setSelected] = useState(
    () => new Set(items?.map((i) => i.ingredient_id) ?? []),
  );

  useEffect(() => {
    if (allergies.length === 0) return;
    const timeoutId = setTimeout(() => {
      setSelected((prev) => {
        const next = new Set(prev);
        items?.forEach((item) => {
          const hasAllergen = allergies.some((a) =>
            (item.name || "").toLowerCase().includes(a.toLowerCase()),
          );

          if (hasAllergen) {
            next.delete(item.ingredient_id);
          }
        });
        return next;
      });
    }, 0);

    return () => {
      clearTimeout(timeoutId);
    };
  }, [allergies, items]);

  const isAllergen = (item) =>
    allergies.some((a) =>
      (item.name || "").toLowerCase().includes(a.toLowerCase()),
    );

  if (!items || items.length === 0) return null;

  const toggleItem = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleAdd = () => {
    items
      .filter((item) => selected.has(item.ingredient_id))
      .forEach((item) => {
        addItemToCart({
          id: item.sku_id || item.ingredient_id,
          name: item.name,
          originalPrice: item.estimated_unit_price,
          newPrice: item.estimated_unit_price,
          discount: 0,
          tags: [],
          ingredients: null,
        });
      });
    setAdded(true);
  };

  return (
    <div className="mt-3 border border-indigo-100 rounded-xl bg-indigo-50/60 p-3">
      <p className="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-2">
        Nguyên liệu cần mua
      </p>
      <ul className="space-y-1.5 mb-3">
        {items.map((item) => (
          <li
            key={item.ingredient_id}
            className="flex items-center gap-2 text-sm"
          >
            <input
              type="checkbox"
              checked={selected.has(item.ingredient_id)}
              onChange={() => toggleItem(item.ingredient_id)}
              className="accent-indigo-600 shrink-0"
            />
            <span
              className={`flex-1 font-medium ${selected.has(item.ingredient_id) ? "text-gray-800" : "text-gray-400 line-through"}`}
            >
              {item.name}
              {item.is_optional && (
                <span className="ml-1 text-xs text-gray-400 font-normal">
                  (không bắt buộc)
                </span>
              )}
            </span>
            <span className="text-gray-500 text-xs shrink-0">
              {item.required_qty_g}g
              {item.estimated_unit_price > 0 && (
                <span className="ml-1 text-indigo-600 font-semibold">
                  · {formatVnd(item.estimated_unit_price)}
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      {added ? (
        <div className="flex items-center gap-2 text-sm text-emerald-700 font-semibold">
          <FaCheckCircle className="text-emerald-500" />
          <span>Đã thêm!</span>
          <Link href="/customer/cart" className="underline text-indigo-600">
            Xem giỏ hàng →
          </Link>
        </div>
      ) : (
        <button
          onClick={handleAdd}
          disabled={selected.size === 0}
          className="w-full py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-bold transition-colors"
        >
          Thêm {selected.size > 0 ? `${selected.size} nguyên liệu` : ""} vào giỏ
          hàng
        </button>
      )}
    </div>
  );
}

export default function AIChatPage() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "bot",
      text: "👋 Chào bạn! Tôi là FreshRoute AI.\n\nTôi có thể gợi ý công thức và cách tận dụng nguyên liệu sẵn có để giảm lãng phí thực phẩm.",
    },
  ]);
  const [inputStr, setInputStr] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState("");
  const [allergies, setAllergies] = useState([]);
  const [allergyInput, setAllergyInput] = useState("");

  const addAllergy = (val) => {
    const trimmed = val.trim();
    if (trimmed && !allergies.includes(trimmed)) {
      setAllergies((prev) => [...prev, trimmed]);
    }
    setAllergyInput("");
  };

  const removeAllergy = (val) => {
    setAllergies((prev) => prev.filter((a) => a !== val));
  };

  const bottomRef = useRef(null);
  const threadIdRef = useRef("customer-chat");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  const handleSend = async (textOverride = inputStr) => {
    const text =
      typeof textOverride === "string" ? textOverride.trim() : inputStr.trim();

    if (!text || isThinking) {
      return;
    }

    setError("");
    setInputStr("");
    setMessages((prev) => [...prev, { id: Date.now(), type: "user", text }]);
    setIsThinking(true);

    try {
      const response = await sendConsumerChat({
        message: text,
        threadId: threadIdRef.current,
        allergies: allergies.length > 0 ? allergies : undefined,
      });

      threadIdRef.current = response.threadId || threadIdRef.current;

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "bot",
          text:
            response.reply ||
            "Xin lỗi, tôi chưa có phản hồi phù hợp ở thời điểm này.",
          shoppingList: response.shoppingList || null,
          recipeSuggestions: response.recipeSuggestions || null,
        },
      ]);
    } catch (chatError) {
      const errorMessage =
        chatError?.message || "Không thể kết nối trợ lý AI ở thời điểm này.";
      setError(errorMessage);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "bot",
          text: `Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu.\n\n**Chi tiết:** ${errorMessage}`,
        },
      ]);
    } finally {
      setIsThinking(false);
    }
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
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Sẵn sàng gợi ý món ngon
              </p>
            </div>
          </div>
        </div>

        <Link href="/customer/cart">
          <button className="p-3 rounded-full bg-white border border-gray-200 text-gray-700 shadow-sm transition-all hover:bg-gray-50">
            <FaShoppingCart className="text-lg" />
          </button>
        </Link>
      </header>

      <main className="flex-1 overflow-y-auto px-4 py-8 relative scroll-smooth bg-linear-to-b from-slate-50 to-white">
        <div className="max-w-2xl mx-auto flex flex-col justify-end min-h-full">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-3 text-sm font-semibold mb-4">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <AnimatePresence>
              {messages.map((msg) => (
                <div key={msg.id} className="w-full relative">
                  {msg.type === "bot" ? (
                    <BotMessage
                      text={msg.text}
                      shoppingList={msg.shoppingList}
                      recipeSuggestions={msg.recipeSuggestions}
                      allergies={allergies}
                    />
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
          <div className="flex items-center gap-1.5 mb-3 flex-wrap min-h-[22px]">
            <span className="text-[11px] text-gray-400 font-semibold shrink-0">
              Dị ứng:
            </span>
            {allergies.map((a) => (
              <span
                key={a}
                className="inline-flex items-center gap-1 bg-red-50 border border-red-200 text-red-600 text-[11px] font-semibold px-2 py-0.5 rounded-full"
              >
                {a}
                <button
                  onClick={() => removeAllergy(a)}
                  className="text-red-400 hover:text-red-700 leading-none"
                >
                  ×
                </button>
              </span>
            ))}
            <input
              value={allergyInput}
              onChange={(e) => setAllergyInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && allergyInput.trim())
                  addAllergy(allergyInput);
              }}
              placeholder="Thêm..."
              className="text-[11px] text-gray-600 placeholder-gray-300 outline-none bg-transparent w-14 border-b border-gray-200 focus:border-red-300"
            />
          </div>

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
              className={`w-12 h-12 flex items-center justify-center rounded-full text-white transition-all shadow-md ${inputStr.trim() && !isThinking ? "bg-indigo-600 hover:bg-indigo-700 shadow-indigo-500/30" : "bg-gray-300 pointer-events-none"}`}
            >
              <FaPaperPlane className="-ml-1 text-lg" />
            </motion.button>
          </div>
        </div>
      </footer>
    </div>
  );
}
