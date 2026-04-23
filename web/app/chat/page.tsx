'use client';

import { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { EmptyState } from '@/components/empty-state';
import { streamSSE } from '@/lib/api';
import { useDataset } from '@/lib/dataset-context';
import { t } from '@/lib/i18n';
import type { ChatMessage } from '@/lib/types';

export default function ChatPage() {
  const { dataset, filters } = useDataset();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    setTimeout(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    }, 0);
  };

  const send = async () => {
    if (!dataset || !input.trim() || streaming) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const next = [...messages, userMsg];
    setMessages([...next, { role: 'assistant', content: '' }]);
    setInput('');
    setStreaming(true);
    scrollToBottom();

    const qs: string[] = [];
    if (filters.regions) for (const r of filters.regions) qs.push(`regions=${encodeURIComponent(r)}`);
    if (filters.services) for (const s of filters.services) qs.push(`services=${encodeURIComponent(s)}`);
    if (filters.start) qs.push(`start=${encodeURIComponent(filters.start)}`);
    if (filters.end)   qs.push(`end=${encodeURIComponent(filters.end)}`);
    const url = `/api/datasets/${dataset.dataset_id}/chat${qs.length ? '?' + qs.join('&') : ''}`;

    try {
      await streamSSE(
        url,
        {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ messages: next }),
        },
        {
          onDelta: (text) => {
            setMessages((prev) => {
              const copy = prev.slice();
              const last = copy[copy.length - 1];
              if (last && last.role === 'assistant') {
                copy[copy.length - 1] = { ...last, content: last.content + text };
              }
              return copy;
            });
            scrollToBottom();
          },
          onDone: () => setStreaming(false),
          onError: (msg) => {
            setMessages((prev) => {
              const copy = prev.slice();
              copy[copy.length - 1] = { role: 'assistant', content: `⚠️ ${msg}` };
              return copy;
            });
            setStreaming(false);
          },
        },
      );
    } catch (e) {
      setMessages((prev) => {
        const copy = prev.slice();
        copy[copy.length - 1] = { role: 'assistant', content: `⚠️ ${(e as Error).message}` };
        return copy;
      });
      setStreaming(false);
    }
  };

  if (!dataset) return <EmptyState />;

  return (
    <div className="app-page flex h-[calc(100vh-3rem)] flex-col">
      <header className="app-header">
        <div>
          <div className="app-kicker">Natural-language analysis</div>
          <h1 className="app-title">{t('chat.title')}</h1>
          <p className="app-subtitle">{t('chat.subtitle')}</p>
        </div>
        <div className="eyebrow-chip">Filtered dataset context is included</div>
      </header>

      {messages.length === 0 && (
        <div className="hero-panel">
          <div className="font-semibold text-wisag-navy mb-1">{t('chat.try_asking')}</div>
          <div className="text-sm text-wisag-gray600 whitespace-pre-line">
            {t('chat.examples')}
          </div>
        </div>
      )}

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto space-y-3 pr-1"
      >
        {messages.map((m, i) => (
          <div
            key={i}
            className={
              'wisag-card ' +
              (m.role === 'assistant' ? 'wisag-card-accent' : 'border-wisag-gray200')
            }
          >
            <div className="text-xs font-semibold text-wisag-gray600 uppercase mb-1">
              {m.role === 'user' ? 'Sie' : 'Co-Pilot'}
            </div>
            <div className="prose prose-sm max-w-none text-wisag-navy">
              {m.content ? <ReactMarkdown>{m.content}</ReactMarkdown>
                : <span className="text-wisag-gray500">{t('chat.thinking')}</span>}
            </div>
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); send(); }}
        className="hero-panel flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('chat.input_placeholder')}
          className="wisag-input flex-1"
          disabled={streaming}
        />
        <button type="submit" className="wisag-primary-btn" disabled={streaming || !input.trim()}>
          {t('chat.send')}
        </button>
        {messages.length > 0 && (
          <button
            type="button"
            className="wisag-secondary-btn"
            onClick={() => setMessages([])}
            disabled={streaming}
          >
            {t('chat.clear')}
          </button>
        )}
      </form>
    </div>
  );
}
