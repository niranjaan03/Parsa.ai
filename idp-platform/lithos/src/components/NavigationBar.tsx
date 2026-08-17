import { useState } from 'react';
import { ChevronDownIcon } from './Icons';

export const NavigationBar = () => {
  const [platformOpen, setPlatformOpen] = useState(false);

  return (
    <header className="relative z-30 w-full px-[120px] py-[16px] mb-[60px]">
      <nav className="flex items-center justify-between w-full max-w-[1440px] mx-auto">
        {/* Logo */}
        <a
          href="/"
          className="font-schibsted font-semibold text-[24px] tracking-[-1.44px] text-black hover:opacity-80 transition-opacity"
        >
          Logoipsum
        </a>

        {/* Menu Items */}
        <div className="hidden md:flex items-center gap-[32px] font-schibsted font-medium text-[16px] tracking-[-0.2px] text-black">
          {/* Platform Dropdown */}
          <div
            className="relative group py-2"
            onMouseEnter={() => setPlatformOpen(true)}
            onMouseLeave={() => setPlatformOpen(false)}
          >
            <button
              type="button"
              onClick={() => setPlatformOpen(!platformOpen)}
              className="flex items-center gap-1.5 hover:opacity-70 transition-opacity cursor-pointer text-black"
            >
              <span>Platform</span>
              <ChevronDownIcon className="w-4 h-4 text-black transition-transform duration-200 group-hover:rotate-180" />
            </button>

            {/* Platform Dropdown Menu in requested style */}
            <div className="absolute top-full left-0 mt-1 w-[220px] bg-[#111118] border border-white/10 rounded-2xl shadow-2xl p-5 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-all duration-200 transform translate-y-1 group-hover:translate-y-0 z-50">
              <div className="text-[11px] font-bold tracking-[0.12em] text-white/50 uppercase mb-3 font-schibsted">
                PLATFORM
              </div>
              <div className="flex flex-col gap-2.5 font-inter text-[15px] font-normal">
                <a
                  href="#product"
                  className="text-white/85 hover:text-white hover:translate-x-1 transition-all"
                >
                  Product
                </a>
                <a
                  href="#pipeline"
                  className="text-white/85 hover:text-white hover:translate-x-1 transition-all"
                >
                  Architecture
                </a>
                <a
                  href="#benchmarks"
                  className="text-white/85 hover:text-white hover:translate-x-1 transition-all"
                >
                  Benchmarks
                </a>
                <a
                  href="#pricing"
                  className="text-white/85 hover:text-white hover:translate-x-1 transition-all"
                >
                  Pricing
                </a>
              </div>
            </div>
          </div>

          <a href="#product" className="hover:opacity-70 transition-opacity">
            Product
          </a>
          <a href="#pipeline" className="hover:opacity-70 transition-opacity">
            Architecture
          </a>
          <a href="#benchmarks" className="hover:opacity-70 transition-opacity">
            Benchmarks
          </a>
          <a href="#pricing" className="hover:opacity-70 transition-opacity">
            Pricing
          </a>
          <a href="#contact" className="hover:opacity-70 transition-opacity">
            Contact
          </a>
        </div>

        {/* Right Side Buttons */}
        <div className="flex items-center gap-[12px]">
          <button
            type="button"
            className="w-[82px] h-[40px] bg-transparent text-black font-schibsted font-medium text-[16px] hover:bg-black/5 rounded-full transition-colors cursor-pointer flex items-center justify-center"
          >
            Sign Up
          </button>
          <button
            type="button"
            className="w-[101px] h-[40px] bg-black text-white font-schibsted font-medium text-[16px] rounded-full hover:bg-neutral-800 transition-colors cursor-pointer flex items-center justify-center shadow-sm"
          >
            Log In
          </button>
        </div>
      </nav>
    </header>
  );
};
