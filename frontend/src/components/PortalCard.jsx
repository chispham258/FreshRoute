"use client";

import React from "react";
import Link from "next/link";

export default function PortalCard({
  title,
  subtitle,
  features,
  icon,
  href,
  buttonText,
  bgColorClass,
  btnColorClass,
}) {
  return (
    <div className="bg-white rounded-2xl shadow-xl w-full max-w-md lg:max-w-lg mx-auto flex flex-col min-h-112 overflow-hidden transition-all hover:shadow-2xl">
      <div
        className={`${bgColorClass} p-6 text-white flex flex-col md:flex-row items-center space-y-3 md:space-y-0 md:space-x-4`}
      >
        <div className="shrink-0 bg-white/20 p-3 rounded-xl flex items-center justify-center">
          {icon}
        </div>
        <div className="text-center md:text-left">
          <h2 className="font-bold text-2xl tracking-wide uppercase">
            {title}
          </h2>
          <p className="text-sm opacity-90 mt-1">{subtitle}</p>
        </div>
      </div>

      <div className="p-8 grow flex flex-col justify-between bg-white">
        <ul className="space-y-6 mb-8">
          {features.map((feature, index) => (
            <li key={index} className="flex items-start space-x-4">
              <div className="shrink-0 h-10 w-10 flex items-center justify-center rounded-xl bg-gray-50 text-gray-400">
                {feature.icon}
              </div>
              <div className="flex flex-col justify-center">
                <h3 className="font-semibold text-gray-800 text-[15px] leading-tight">
                  {feature.title}
                </h3>
                <p className="text-gray-500 text-[13px] mt-1 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </li>
          ))}
        </ul>

        <Link href={href} className="mt-auto block w-full">
          <button
            className={`w-full text-white font-bold py-3 px-4 rounded-xl transition-all transform hover:-translate-y-1 ${btnColorClass} flex items-center justify-center space-x-2`}
          >
            <span>{buttonText}</span>
            <svg
              className="w-5 h-5 transition-transform"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M14 5l7 7m0 0l-7 7m7-7H3"
              />
            </svg>
          </button>
        </Link>
      </div>
    </div>
  );
}
