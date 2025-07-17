import React, { useState, useRef } from 'react';
import { Send, Feather, Sparkles, Loader2 } from 'lucide-react';

export default function PoemGenerator() {
  const [input, setInput] = useState('');
  const [poem, setPoem] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    setIsLoading(true);
    setPoem('');
    setIsStreaming(true);

    // Create abort controller for canceling requests
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('http://localhost:8000/api/generate-poem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
  prompt: input.trim(),
  max_length: 200, // or any user-controlled value
  temperature: 0.7
}),

        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setIsLoading(false);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              setIsStreaming(false);
              return;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.text) {
                setPoem(prev => prev + parsed.text);
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted');
      } else {
        console.error('Error generating poem:', error);
        setPoem('Error generating poem. Please try again.');
      }
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
    setIsLoading(false);
  };

  const handleClear = () => {
    setPoem('');
    setInput('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 pt-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Feather className="w-8 h-8 text-amber-400" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent">
              Shakespearean Verse Generator
            </h1>
            <Sparkles className="w-8 h-8 text-amber-400" />
          </div>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto">
            Transform your thoughts into eloquent Shakespearean poetry. Enter a few lines and watch as they bloom into timeless verse.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Send className="w-5 h-5" />
              Your Inspiration
            </h2>
            <div className="space-y-4">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Enter a few lines to inspire your Shakespearean poem..."
                className="w-full h-40 p-4 bg-white/5 border border-white/30 rounded-xl text-white placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-amber-400 focus:border-transparent transition-all"
                disabled={isStreaming}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
              />
              <div className="flex gap-3">
                <button
                  onClick={handleSubmit}
                  disabled={!input.trim() || isStreaming || isLoading}
                  className="flex-1 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 disabled:from-slate-600 disabled:to-slate-700 text-white px-6 py-3 rounded-xl font-medium transition-all duration-200 flex items-center justify-center gap-2 disabled:cursor-not-allowed"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Composing...
                    </>
                  ) : isStreaming ? (
                    <>
                      <div className="w-4 h-4 bg-white rounded-full animate-pulse" />
                      Streaming...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Generate Poem
                    </>
                  )}
                </button>
                {isStreaming && (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-all duration-200"
                  >
                    Stop
                  </button>
                )}
                {poem && !isStreaming && (
                  <button
                    type="button"
                    onClick={handleClear}
                    className="px-6 py-3 bg-slate-600 hover:bg-slate-700 text-white rounded-xl font-medium transition-all duration-200"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Output Section */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Feather className="w-5 h-5" />
              Shakespearean Verse
            </h2>
            <div className="h-80 overflow-y-auto">
              {poem ? (
                <div className="text-slate-100 leading-relaxed whitespace-pre-wrap font-serif text-lg">
                  {poem}
                  {isStreaming && (
                    <span className="inline-block w-2 h-5 bg-amber-400 animate-pulse ml-1" />
                  )}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-400 text-center">
                  <div>
                    <Feather className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Your Shakespearean poem will appear here...</p>
                    <p className="text-sm mt-2">Enter your inspiration and click "Generate Poem"</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-12 text-slate-400">
          <p className="italic">
            "All the world's a stage, and all the men and women merely players..." - As You Like It
          </p>
        </div>
      </div>
    </div>
    // <div>Hi</div>
  );
}
