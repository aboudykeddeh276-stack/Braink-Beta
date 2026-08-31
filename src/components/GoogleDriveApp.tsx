import React, { useState, useEffect } from 'react';
import { googleSignIn, initAuth, getAccessToken, logout } from '../lib/auth';
import { User } from 'firebase/auth';
import { HardDrive, LogOut, File, Loader2 } from 'lucide-react';

export default function GoogleDriveApp() {
  const [needsAuth, setNeedsAuth] = useState(true);
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const [files, setFiles] = useState<any[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = initAuth(
      (u, t) => {
        setUser(u);
        setToken(t);
        setNeedsAuth(false);
        fetchFiles(t);
      },
      () => setNeedsAuth(true)
    );
    return () => unsubscribe();
  }, []);

  const handleLogin = async () => {
    setIsLoggingIn(true);
    try {
      const result = await googleSignIn();
      if (result) {
        setToken(result.accessToken);
        setUser(result.user);
        setNeedsAuth(false);
        fetchFiles(result.accessToken);
      }
    } catch (err) {
      console.error('Login failed:', err);
      setError('Login failed. Please try again.');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    setUser(null);
    setToken(null);
    setNeedsAuth(true);
    setFiles([]);
  };

  const fetchFiles = async (accessToken: string) => {
    setLoadingFiles(true);
    setError(null);
    try {
      const res = await fetch('https://www.googleapis.com/drive/v3/files?pageSize=20&fields=files(id,name,mimeType)', {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) {
        throw new Error('Failed to fetch files');
      }
      const data = await res.json();
      setFiles(data.files || []);
    } catch (err: any) {
      console.error(err);
      setError('Failed to load files from Google Drive.');
    } finally {
      setLoadingFiles(false);
    }
  };

  if (needsAuth) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-zinc-900 rounded-lg text-white">
        <HardDrive className="w-12 h-12 mb-4 text-blue-400" />
        <h2 className="text-xl font-bold mb-2">Connect Google Drive</h2>
        <p className="text-zinc-400 mb-6 text-center max-w-sm">
          Please sign in to access and manage your Google Drive files.
        </p>
        
        {error && <p className="text-red-400 mb-4">{error}</p>}
        
        <button 
          onClick={handleLogin}
          disabled={isLoggingIn}
          className="flex items-center gap-2 bg-white text-zinc-900 px-4 py-2 rounded font-medium hover:bg-zinc-200 transition-colors disabled:opacity-50"
        >
          {isLoggingIn ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <svg version="1.1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" className="w-5 h-5" style={{display: 'block'}}>
              <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"></path>
              <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"></path>
              <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"></path>
              <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"></path>
              <path fill="none" d="M0 0h48v48H0z"></path>
            </svg>
          )}
          Sign in with Google
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-zinc-900 rounded-lg overflow-hidden text-white">
      <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-950">
        <div className="flex items-center gap-3">
          <HardDrive className="w-5 h-5 text-blue-400" />
          <h2 className="font-semibold">Google Drive</h2>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-zinc-400">
            {user?.email}
          </div>
          <button 
            onClick={handleLogout}
            className="p-2 hover:bg-zinc-800 rounded-md transition-colors text-zinc-400 hover:text-white"
            title="Sign Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-4">
        {error && (
          <div className="bg-red-900/50 border border-red-500/50 text-red-200 p-3 rounded mb-4">
            {error}
          </div>
        )}
        
        {loadingFiles ? (
          <div className="flex items-center justify-center h-32 text-zinc-500">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            Loading files...
          </div>
        ) : files.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-zinc-500">
            No files found in your Google Drive.
          </div>
        ) : (
          <ul className="space-y-1">
            {files.map(file => (
              <li key={file.id} className="flex items-center p-3 hover:bg-zinc-800 rounded-md transition-colors border border-transparent hover:border-zinc-700">
                <File className="w-4 h-4 mr-3 text-zinc-400" />
                <span className="truncate flex-1">{file.name}</span>
                <span className="text-xs text-zinc-500 ml-4 font-mono">{file.mimeType.split('.').pop()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
