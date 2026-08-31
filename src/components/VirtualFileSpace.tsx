import React, { useState, useEffect } from 'react';
import { Folder, File, ChevronRight, HardDrive } from 'lucide-react';

export default function VirtualFileSpace() {
  const [currentPath, setCurrentPath] = useState('.');
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPath = async (path: string) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/fs?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      if (data.items) {
        setItems(data.items);
        setCurrentPath(data.currentPath);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchPath('.');
  }, []);

  const handleNavigate = (path: string) => {
    fetchPath(path);
  };

  const handleUp = () => {
    if (currentPath === '.') return;
    const parts = currentPath.split('/');
    parts.pop();
    fetchPath(parts.length ? parts.join('/') : '.');
  };

  return (
    <div className="flex-1 flex flex-col p-6 bg-white dark:bg-[#09090b] overflow-hidden">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-500 flex items-center justify-center">
          <HardDrive size={20} />
        </div>
        <div>
          <h2 className="text-xl font-semibold">Virtual File Space</h2>
          <p className="text-sm text-neutral-500">Live Host Filesystem Explorer</p>
        </div>
      </div>

      <div className="bg-neutral-50 dark:bg-neutral-900 border border-border rounded-xl flex-1 flex flex-col overflow-hidden">
        <div className="p-3 border-b border-border bg-white dark:bg-neutral-800 flex items-center gap-2 text-sm font-mono text-neutral-600 dark:text-neutral-300">
          <span className="text-indigo-500 font-semibold cursor-pointer" onClick={() => fetchPath('.')}>workspace</span>
          {currentPath !== '.' && currentPath.split('/').map((part, i, arr) => (
            <React.Fragment key={i}>
              <ChevronRight size={14} className="text-neutral-400" />
              <span 
                className="hover:text-indigo-500 cursor-pointer"
                onClick={() => fetchPath(arr.slice(0, i + 1).join('/'))}
              >{part}</span>
            </React.Fragment>
          ))}
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          {loading ? (
            <div className="p-4 text-neutral-400 text-sm">Scanning sector...</div>
          ) : (
            <div className="flex flex-col gap-1">
              {currentPath !== '.' && (
                <div 
                  onClick={handleUp}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-neutral-200/50 dark:hover:bg-neutral-800 cursor-pointer text-sm font-medium"
                >
                  <Folder size={16} className="text-neutral-400" />
                  ..
                </div>
              )}
              {items.map((item, idx) => (
                <div 
                  key={idx}
                  onClick={() => item.isDirectory && handleNavigate(item.path)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${item.isDirectory ? 'hover:bg-neutral-200/50 dark:hover:bg-neutral-800 cursor-pointer font-medium' : 'text-neutral-600 dark:text-neutral-400'}`}
                >
                  {item.isDirectory ? (
                    <Folder size={16} className="text-indigo-400" />
                  ) : (
                    <File size={16} className="text-neutral-400" />
                  )}
                  {item.name}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
