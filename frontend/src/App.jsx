import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers, Wand2, Download, AlertCircle, RefreshCcw, Settings2, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from './config';

export default function App() {
  const [prompt, setPrompt] = useState('');
  const [modelProvider, setModelProvider] = useState('imagen_4');
  const [mode, setMode] = useState('sketch');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [difficultyLevels, setDifficultyLevels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [cacheStatus, setCacheStatus] = useState({ cached: false, image_count: 0 });
  const [refreshingCache, setRefreshingCache] = useState(false);

  useEffect(() => {
    fetchDifficultyLevels();
    fetchCacheStatus();

    // Test backend connection immediately
    axios.get(`${API_BASE_URL}/health`).catch(() => {
        console.warn("Backend might not be running. Start it with `python main.py`.");
    });
  }, []);

  const fetchDifficultyLevels = async () => {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/difficulty-levels`);
      setDifficultyLevels(data);
    } catch (err) {
      console.error('Failed to fetch difficulty levels', err);
    }
  };

  const fetchCacheStatus = async () => {
    try {
      const { data } = await axios.get(`${API_BASE_URL}/cache/status`);
      setCacheStatus(data);
    } catch (err) {
      console.error('Failed to fetch cache status', err);
    }
  };

  const handleRefreshCache = async () => {
    setRefreshingCache(true);
    try {
      const { data } = await axios.post(`${API_BASE_URL}/cache/refresh`);
      setCacheStatus({ cached: true, image_count: data.image_count });
    } catch (err) {
      console.error('Failed to refresh cache', err);
    } finally {
      setRefreshingCache(false);
    }
  };

  const handleClearCache = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/cache`);
      setCacheStatus({ cached: false, image_count: 0 });
    } catch (err) {
      console.error('Failed to clear cache', err);
    }
  };

  const handleGenerate = async () => {
    if (!prompt) return;
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/generate`, {
        prompt,
        mode,
        difficulty,
        model_provider: modelProvider,
      });
      setResults(response.data);
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.response?.data?.error || err.message;
      setError(
        status === 422
          ? `Validation error (422): ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`
          : status === 500
          ? `Server error (500): ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`
          : `Failed to connect to backend API! Please run \`python main.py\`. (${err.message})`
      );
    } finally {
      setLoading(false);
    }
  };

  const currentDiff = difficultyLevels.find(d => d.id === difficulty);

  return (
    <div className="min-h-screen bg-black text-white font-sans flex flex-col items-center pb-24">
      
      {/* Absolute Header Area */}
      <header className="w-full max-w-7xl mx-auto px-8 py-10 flex justify-between items-center border-b border-white/10">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col">
          <h1 className="text-3xl font-serif font-bold tracking-widest uppercase">Chris Carves</h1>
          <p className="text-zinc-500 text-xs tracking-[0.2em] mt-1 uppercase">AI Studio Framework</p>
        </motion.div>
        
        {/* API Connection Indicator */}
        <div className="flex items-center gap-4 text-xs font-mono uppercase tracking-wider text-zinc-400">
           {cacheStatus.cached ? (
             <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-white animate-pulse"></span> Ref Cached ({cacheStatus.image_count})</span>
           ) : (
             <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-zinc-600"></span> No Refs</span>
           )}
           <button onClick={handleRefreshCache} disabled={refreshingCache} className="hover:text-white transition-colors duration-200">
             {refreshingCache ? 'Syncing...' : 'Sync'}
           </button>
           <button onClick={handleClearCache} className="hover:text-white transition-colors duration-200">Clear</button>
        </div>
      </header>

      {/* Main Studio Interface */}
      <main className="w-full max-w-7xl mx-auto px-8 mt-12 flex flex-col lg:flex-row gap-12">
        
        {/* Configuration Column */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full lg:w-[420px] shrink-0 flex flex-col gap-10"
        >
          {/* Section: Concept */}
          <section className="flex flex-col gap-4">
            <header className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-zinc-400">
              <Settings2 size={16} /> Concept Definition
            </header>
            <textarea
              className="w-full h-40 glass-input rounded-none p-5 text-white placeholder:text-zinc-600 resize-none font-medium leading-relaxed"
              placeholder="Describe the subject. Keep it precise. (e.g., A minimalist bear figure...)"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
          </section>

          {/* Section: AI Engine */}
          <section className="flex flex-col gap-4">
            <header className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-zinc-400">
              <Settings2 size={16} /> AI Engine
            </header>
            <div className="grid grid-cols-1 gap-px bg-white/10 p-px">
              {[
                { id: 'imagen_4', label: 'Imagen 4' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => setModelProvider(m.id)}
                  className={`py-4 text-xs font-semibold uppercase tracking-widest transition-all duration-300 ${
                    modelProvider === m.id ? 'bg-indigo-600 text-white' : 'bg-black text-zinc-400 hover:text-white'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </section>

          {/* Section: Output Parameters */}
          <section className="flex flex-col gap-6">
            <header className="flex items-center gap-3 text-sm font-medium uppercase tracking-widest text-zinc-400">
              <Layers size={16} /> Output Parameters
            </header>
            
            <div className="grid grid-cols-2 gap-px bg-white/10 p-px">
              {['sketch', 'color'].map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`py-4 text-sm font-semibold uppercase tracking-widest transition-all duration-300 ${
                    mode === m ? 'bg-white text-black' : 'bg-black text-zinc-400 hover:text-white'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <div className="flex flex-col gap-3">
              <label className="text-xs font-semibold uppercase tracking-widest text-zinc-500">Complexity Curve</label>
              <div className="relative border border-white/10 bg-black">
                <select
                  className="w-full bg-transparent p-4 pr-12 text-sm font-semibold tracking-wider text-white appearance-none outline-none cursor-pointer"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                >
                  {difficultyLevels.length === 0 ? (
                    <option value="" disabled>Awaiting API Connection...</option>
                  ) : (
                    difficultyLevels.map((d) => (
                      <option key={d.id} value={d.id} className="bg-zinc-900 text-white py-2">
                        {d.label}
                      </option>
                    ))
                  )}
                </select>
                <div className="absolute inset-y-0 right-4 flex items-center pointer-events-none text-white">
                  ↓
                </div>
              </div>
              
              {/* Detailed Description */}
              <AnimatePresence>
                {currentDiff && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="overflow-hidden"
                  >
                    <p className="text-sm text-zinc-400 leading-relaxed p-4 bg-white/5 border-l-2 border-white">
                      {currentDiff.details}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </section>

          {/* Execute Action */}
          <div className="mt-4">
            <AnimatePresence>
              {error && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-6 p-4 border border-white/20 text-white text-sm flex gap-3 bg-zinc-900/50">
                  <AlertCircle size={18} className="shrink-0" />
                  <p>{error}</p>
                </motion.div>
              )}
            </AnimatePresence>

            <button
              onClick={handleGenerate}
              disabled={loading || !prompt}
              className="w-full relative flex items-center justify-center gap-3 py-6 uppercase tracking-[0.2em] font-bold text-sm bg-white text-black transition-all duration-300 disabled:opacity-50 disabled:bg-zinc-800 disabled:text-zinc-500 hover:bg-zinc-200 group"
            >
              {loading ? (
                 <RefreshCcw size={18} className="animate-spin" />
              ) : (
                 <Wand2 size={18} className="group-hover:translate-x-1 transition-transform" />
              )}
              {loading ? 'Processing...' : 'Execute Generation'}
            </button>
          </div>
        </motion.div>

        {/* Dynamic Studio Canvas View */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className="flex-1 flex flex-col min-h-[600px] bg-zinc-950 border border-white/10"
        >
          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex-1 flex flex-col items-center justify-center">
                <div className="w-16 h-16 border-t-2 border-l-2 border-white rounded-full animate-spin mb-8"></div>
                <h3 className="text-sm font-mono uppercase tracking-widest text-white">Synthesizing Turnarounds</h3>
                <p className="text-xs font-mono tracking-wider text-zinc-500 mt-2">
                  Connecting to Google GenAI
                </p>
              </motion.div>
            ) : results ? (
              <motion.div key="results" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col flex-1 p-8">
                <header className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
                   <div className="flex flex-col">
                     <h2 className="text-lg font-serif">Character Sheet</h2>
                     <span className="text-xs font-mono text-zinc-500 uppercase">Generated in {results.generation_time_ms}ms</span>
                   </div>
                   <button 
                     onClick={() => {
                       // Download the single sheet image
                       const view = results.views[0];
                       const a = document.createElement('a');
                       a.href = `data:${view.mime_type};base64,${view.image_b64}`;
                       a.download = 'character-sheet.png';
                       a.click();
                     }}
                     className="text-xs font-bold uppercase tracking-widest flex items-center gap-2 hover:text-zinc-400 transition-colors"
                   >
                     <Download size={14} /> Export Sheet
                   </button>
                </header>

                {/* Single full-width character sheet */}
                <div className="flex-1 flex items-center justify-center overflow-auto">
                  {results.views[0] && (
                    <motion.img 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      src={`data:${results.views[0].mime_type};base64,${results.views[0].image_b64}`} 
                      alt="Character sheet — front, left side, back, right side"
                      style={{ maxWidth: "100%", maxHeight: "100%", width: "100%", height: "auto", objectFit: "contain", display: "block" }}
                    />
                  )}
                </div>
              </motion.div>
            ) : (
              <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 flex flex-col items-center justify-center text-zinc-600">
                 <ImageIcon size={48} strokeWidth={1} className="mb-6 opacity-50" />
                 <p className="font-mono text-xs uppercase tracking-[0.2em]">Canvas Uninitialized</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

      </main>
    </div>
  );
}
