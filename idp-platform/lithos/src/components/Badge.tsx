import { StarIcon } from './Icons';

export const Badge = () => {
  return (
    <div className="inline-flex items-center gap-[10px] p-1 pr-4 bg-[#f8f8f8] border border-black/5 rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.06)] backdrop-blur-sm">
      {/* Dark inner pill */}
      <div className="inline-flex items-center gap-1.5 bg-[#0e1311] text-white px-3 py-1 rounded-full font-inter font-normal text-[14px]">
        <StarIcon className="w-3.5 h-3.5 text-yellow-300 fill-yellow-300" />
        <span>New</span>
      </div>

      {/* Light text */}
      <span className="font-inter font-normal text-[14px] text-black">
        Discover what's possible
      </span>
    </div>
  );
};
