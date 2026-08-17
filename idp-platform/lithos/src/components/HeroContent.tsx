import { useState, useEffect } from 'react';
import { Badge } from './Badge';
import { SearchInputBox } from './SearchInputBox';

const CYCLING_WORDS = ['complex', 'messy', 'medical', 'handwritten'];

export const HeroContent = () => {
  const [wordIndex, setWordIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    const interval = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setWordIndex((prev) => (prev + 1) % CYCLING_WORDS.length);
        setIsFading(false);
      }, 350);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative z-10 w-full max-w-[1440px] mx-auto px-[120px] -mt-[50px] flex flex-col items-center text-center">
      {/* Header Container */}
      <div className="flex flex-col items-center max-w-[840px]">
        {/* Badge Component */}
        <Badge />

        {/* Main Headline */}
        <h1 className="mt-[34px] font-fustat font-bold text-[72px] tracking-[-3.8px] leading-tight text-black text-center">
          Transform{' '}
          <span
            className={`inline-block text-[#ff3d8b] bg-gradient-to-r from-[#ff3d8b] to-[#6366f1] bg-clip-text text-transparent transition-all duration-300 ${
              isFading ? 'opacity-0 -translate-y-2' : 'opacity-100 translate-y-0'
            }`}
          >
            {CYCLING_WORDS[wordIndex]}
          </span>{' '}
          documents into AI-ready data
        </h1>

        {/* Subtitle */}
        <p className="mt-[24px] w-[542px] max-w-[736px] font-fustat font-medium text-[20px] tracking-[-0.4px] text-[#505050] text-center mx-auto">
          Upload any unstructured PDF or image and extract 100% accurate, grounded JSON powered by Unlimited-OCR 3B-MoE VLM.
        </p>
      </div>

      {/* Search Input Box */}
      <div className="mt-[44px] w-full flex justify-center">
        <SearchInputBox />
      </div>
    </div>
  );
};

