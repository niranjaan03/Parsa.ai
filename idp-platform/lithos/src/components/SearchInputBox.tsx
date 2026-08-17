import { useState, useRef } from 'react';
import {
  AISparkleIcon,
  UpArrowIcon,
  PlusIcon,
  FolderIcon,
  FileTextIcon,
  WorkspaceIcon,
  CloseIcon,
} from './Icons';

interface AttachedItem {
  id: string;
  name: string;
  type: 'folder' | 'document' | 'workspace';
  count?: number;
}

export const SearchInputBox = () => {
  const [query, setQuery] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [attachments, setAttachments] = useState<AttachedItem[]>([]);
  const [workspaceActive, setWorkspaceActive] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);

  const handleClearOrSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() || attachments.length > 0 || workspaceActive) {
      const attachSummary = attachments.map((a) => a.name).join(', ');
      const wsStr = workspaceActive ? ' [Workspace Context Active]' : '';
      alert(`Submitting query: "${query}"${attachSummary ? ` with attached: ${attachSummary}` : ''}${wsStr}`);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      const newItems: AttachedItem[] = files.map((file, idx) => ({
        id: `doc-${Date.now()}-${idx}`,
        name: file.name,
        type: 'document',
      }));
      setAttachments((prev) => [...prev, ...newItems]);
      setIsMenuOpen(false);
    }
  };

  const handleFolderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      const firstPath = files[0].webkitRelativePath || '';
      const folderName = firstPath.split('/')[0] || 'Selected Folder';
      setAttachments((prev) => [
        ...prev,
        {
          id: `folder-${Date.now()}`,
          name: folderName,
          type: 'folder',
          count: files.length,
        },
      ]);
      setIsMenuOpen(false);
    }
  };

  const toggleWorkspaceContext = () => {
    const nextState = !workspaceActive;
    setWorkspaceActive(nextState);
    if (nextState) {
      if (!attachments.some((a) => a.type === 'workspace')) {
        setAttachments((prev) => [
          ...prev,
          {
            id: 'ws-context',
            name: 'Workspace Context (/idp-platform)',
            type: 'workspace',
          },
        ]);
      }
    } else {
      setAttachments((prev) => prev.filter((a) => a.type !== 'workspace'));
    }
    setIsMenuOpen(false);
  };

  const removeItem = (id: string) => {
    setAttachments((prev) => prev.filter((item) => item.id !== id));
    if (id === 'ws-context') {
      setWorkspaceActive(false);
    }
  };

  return (
    <div className="relative w-full max-w-[728px] rounded-[18px] bg-[rgba(0,0,0,0.24)] backdrop-blur-md border border-white/10 p-[16px] flex flex-col justify-between shadow-2xl mx-auto transition-all">
      {/* Hidden inputs for document & folder uploads */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        multiple
        accept="*/*"
        className="hidden"
      />
      <input
        type="file"
        ref={folderInputRef}
        onChange={handleFolderChange}
        // @ts-ignore - webkitdirectory non-standard attribute
        webkitdirectory=""
        directory=""
        className="hidden"
      />

      {/* Top Row: Credit Info & Powered by */}
      <div className="flex items-center justify-between text-white font-schibsted font-medium text-[12px] mb-2">
        {/* Left: Credits & Upgrade Button */}
        <div className="flex items-center gap-2">
          <span>60/450 credits</span>
          <button
            type="button"
            className="bg-[rgba(90,225,76,0.89)] text-black px-2.5 py-0.5 rounded-[6px] font-schibsted font-medium text-[12px] hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
          >
            Upgrade
          </button>
        </div>

        {/* Right: AI Icon + Powered by */}
        <div className="flex items-center gap-1.5 opacity-90">
          <AISparkleIcon className="w-3.5 h-3.5 text-white" />
          <span>Powered by Gemini</span>
        </div>
      </div>

      {/* Attachment Chips Row (if any items attached) */}
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2 px-1">
          {attachments.map((item) => (
            <div
              key={item.id}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium font-schibsted transition-all shadow-sm ${
                item.type === 'workspace'
                  ? 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 text-emerald-300 border border-emerald-500/30'
                  : item.type === 'folder'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                  : 'bg-white/15 text-white border border-white/20'
              }`}
            >
              {item.type === 'folder' && <FolderIcon className="w-3 h-3 text-amber-400" />}
              {item.type === 'document' && <FileTextIcon className="w-3 h-3 text-blue-300" />}
              {item.type === 'workspace' && <WorkspaceIcon className="w-3 h-3 text-emerald-400" />}
              <span className="truncate max-w-[180px]">
                {item.name} {item.count ? `(${item.count} files)` : ''}
              </span>
              <button
                type="button"
                onClick={() => removeItem(item.id)}
                className="hover:bg-white/20 rounded p-0.5 transition-colors cursor-pointer ml-0.5"
                title="Remove attachment"
              >
                <CloseIcon className="w-3 h-3 opacity-70 hover:opacity-100" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Main Input Area */}
      <form
        onSubmit={handleClearOrSubmit}
        className="w-full min-h-[56px] bg-white rounded-[12px] shadow-[0_4px_16px_rgba(0,0,0,0.08)] flex items-center justify-between px-4 py-2 my-1"
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            workspaceActive
              ? "Ask using active workspace context or paste schema..."
              : "Ask anything about your document or paste schema..."
          }
          className="w-full bg-transparent border-none outline-none font-inter text-[16px] text-black placeholder:text-[rgba(0,0,0,0.6)] placeholder:font-inter"
        />
        <button
          type="submit"
          aria-label="Submit search"
          className="w-[36px] h-[36px] min-w-[36px] bg-black rounded-full flex items-center justify-center text-white cursor-pointer hover:bg-neutral-800 transition-colors flex-shrink-0 ml-2"
        >
          <UpArrowIcon className="w-4 h-4" />
        </button>
      </form>

      {/* Bottom Row: Actions & Character Counter */}
      <div className="flex items-center justify-between mt-2">
        {/* Left: Action Buttons */}
        <div className="relative flex items-center gap-2">
          {/* Plus (+) Button with Popover */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsMenuOpen((prev) => !prev)}
              className="flex items-center gap-1.5 bg-[#0e1311] hover:bg-black text-white px-3 py-1.5 rounded-[6px] text-[12px] font-schibsted font-semibold transition-all cursor-pointer shadow-md border border-white/10 hover:border-white/30"
              title="Add folders, documents, or workspace context"
            >
              <PlusIcon className="w-4 h-4 text-emerald-400" />
              <span>Plus</span>
            </button>

            {/* Popover Dropdown Menu */}
            {isMenuOpen && (
              <div className="absolute bottom-full left-0 mb-2 w-[240px] bg-[#14151a] border border-white/15 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150 backdrop-blur-xl">
                <div className="px-2 py-1 text-[10px] font-bold text-gray-400 tracking-wider uppercase border-b border-white/10 mb-1 font-schibsted">
                  Attach Context & Data
                </div>

                {/* Option 1: Folder Upload */}
                <button
                  type="button"
                  onClick={() => {
                    folderInputRef.current?.click();
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-[13px] text-white hover:bg-white/10 transition-colors font-schibsted cursor-pointer group"
                >
                  <div className="p-1.5 rounded-md bg-amber-500/20 text-amber-400 group-hover:bg-amber-500/30">
                    <FolderIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-medium">Upload Folder</div>
                    <div className="text-[10px] text-gray-400">Select directory of documents</div>
                  </div>
                </button>

                {/* Option 2: Any Document */}
                <button
                  type="button"
                  onClick={() => {
                    fileInputRef.current?.click();
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-[13px] text-white hover:bg-white/10 transition-colors font-schibsted cursor-pointer group"
                >
                  <div className="p-1.5 rounded-md bg-blue-500/20 text-blue-400 group-hover:bg-blue-500/30">
                    <FileTextIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-medium">Any Document Type</div>
                    <div className="text-[10px] text-gray-400">PDF, DOCX, CSV, TXT, JSON, Scans</div>
                  </div>
                </button>

                {/* Option 3: Workspace Context */}
                <button
                  type="button"
                  onClick={toggleWorkspaceContext}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left text-[13px] transition-colors font-schibsted cursor-pointer group ${
                    workspaceActive ? 'bg-emerald-500/20 text-emerald-300' : 'text-white hover:bg-white/10'
                  }`}
                >
                  <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400 group-hover:bg-emerald-500/30">
                    <WorkspaceIcon className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between font-medium">
                      <span>Workspace Context</span>
                      {workspaceActive && <span className="text-[10px] bg-emerald-400 text-black px-1.5 rounded font-bold">ON</span>}
                    </div>
                    <div className="text-[10px] text-gray-400">Use current workspace project files</div>
                  </div>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right: Character Counter */}
        <div className="text-[12px] font-schibsted font-medium text-gray-300">
          {query.length.toLocaleString()}/3,000
        </div>
      </div>
    </div>
  );
};
