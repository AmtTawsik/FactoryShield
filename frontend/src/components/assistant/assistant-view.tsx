"use client";

import {
  ArrowUp,
  BadgeCheck,
  Bot,
  Building2,
  Check,
  ClipboardCheck,
  Copy,
  Database,
  ExternalLink,
  FileText,
  Languages,
  ListChecks,
  MessageSquarePlus,
  PanelLeft,
  RotateCw,
  Scale,
  Search,
  X,
} from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from "react";
import useSWR from "swr";
import { useSession } from "@/components/shell/session";
import { ErrorState, LoadingBlock, Skeleton } from "@/components/ui/states";
import { useAllFactories } from "@/hooks/use-factories";
import { api, errorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import { formatDate, todayInDhaka } from "@/lib/format";
import type { ChatMessage, ChatResponse, Conversation, ConversationDetail, KnowledgeSource, Page } from "@/lib/types";
import { MessageText } from "./message-text";

const MAX_LENGTH = 4000;
const LIST_KEY = "/chat/conversations?size=100";

const SUGGESTIONS = [
  {
    icon: ListChecks,
    topic: "Your records",
    prompt: "Which corrective actions are overdue, and which factory has the most?",
  },
  {
    icon: ClipboardCheck,
    topic: "Your records",
    prompt: "Summarise the latest inspection results for my factories.",
  },
  {
    icon: Scale,
    topic: "Labour law",
    prompt: "How often must fire drills be held under the Bangladesh Labour Act?",
  },
  {
    icon: FileText,
    topic: "Safety guidance",
    prompt: "What should we check during an electrical safety inspection?",
  },
];

const TOOL_LABELS: Record<string, string> = {
  get_factory_inspection_summary: "Inspection records",
  get_overdue_corrective_actions: "Overdue actions",
  search_recent_safety_incidents: "Recent incidents",
};

type Pending = { text: string; conversationId: number | null };
type Extras = { reply: string; sources: KnowledgeSource[]; tools: string[] };

const timeFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Dhaka" });
const dhakaDay = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Dhaka" });

function dayDiff(value: string): number {
  const day = new Date(`${dhakaDay.format(new Date(value))}T00:00:00Z`).getTime();
  return Math.round((new Date(`${todayInDhaka()}T00:00:00Z`).getTime() - day) / 86_400_000);
}

function groupLabel(value: string): string {
  const diff = dayDiff(value);
  if (diff <= 0) return "Today";
  if (diff === 1) return "Yesterday";
  if (diff < 7) return "Previous 7 days";
  return "Older";
}

function messageTime(value: string): string {
  const diff = dayDiff(value);
  const time = timeFormat.format(new Date(value));
  return diff <= 0 ? time : `${formatDate(value)}, ${time}`;
}

function AssistantAvatar({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-white ring-4 ring-brand-50",
        className,
      )}
    >
      <Bot className="size-4" aria-hidden="true" />
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(text);
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        } catch {
        }
      }}
      className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-slate-500 hover:bg-slate-100 hover:text-slate-800"
      aria-label={copied ? "Copied" : "Copy answer"}
    >
      {copied ? <Check className="size-3.5 text-green-600" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Sources({ extras }: { extras: Extras }) {
  if (extras.sources.length === 0 && extras.tools.length === 0) return null;
  return (
    <div className="mt-4 space-y-3">
      {extras.tools.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
          <Database className="size-3.5" aria-hidden="true" />
          <span>Checked your records:</span>
          {extras.tools.map((tool) => (
            <span key={tool} className="rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
              {TOOL_LABELS[tool] ?? tool}
            </span>
          ))}
        </div>
      )}
      {extras.sources.length > 0 && (
        <div>
          <p className="mb-1.5 text-xs font-medium text-slate-500">Sources</p>
          <ol className="grid gap-2 sm:grid-cols-2">
            {extras.sources.map((source, index) => {
              const official = source.content_status === "official_verified";
              const body = (
                <>
                  <span className="flex size-5 shrink-0 items-center justify-center rounded bg-slate-100 text-[11px] font-semibold text-slate-600">
                    {index + 1}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-start gap-1 text-xs font-medium text-slate-800">
                      <span className="line-clamp-2">{source.title}</span>
                      {source.source_url && <ExternalLink className="mt-0.5 size-3 shrink-0 text-slate-400" aria-hidden="true" />}
                    </span>
                    <span className="mt-0.5 block truncate text-[11px] text-slate-500">{source.source_authority}</span>
                    <span
                      className={cn(
                        "mt-1 inline-flex items-center gap-1 text-[11px] font-medium",
                        official ? "text-green-700" : "text-slate-500",
                      )}
                    >
                      {official && <BadgeCheck className="size-3" aria-hidden="true" />}
                      {official
                        ? `Official · verified ${source.verified_on ? formatDate(source.verified_on) : ""}`
                        : "General guidance"}
                    </span>
                  </span>
                </>
              );
              const style = "flex gap-2 rounded-lg border border-slate-200 bg-white p-2.5 text-left";
              return (
                <li key={source.document_id}>
                  {source.source_url ? (
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={cn(style, "transition-colors hover:border-brand-300 hover:bg-brand-50/40")}
                    >
                      {body}
                      <span className="sr-only">(opens in a new tab)</span>
                    </a>
                  ) : (
                    <div className={style}>{body}</div>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </div>
  );
}

function UserMessage({ content, time }: { content: string; time?: string }) {
  return (
    <div className="flex flex-col items-end">
      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm leading-6 whitespace-pre-wrap text-white">
        {content}
      </div>
      {time && <span className="mt-1 text-[11px] text-slate-400">{time}</span>}
    </div>
  );
}

function AssistantMessage({ content, time, extras }: { content: string; time: string; extras?: Extras }) {
  return (
    <div className="group flex gap-3">
      <AssistantAvatar />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-900">FactoryShield Assistant</span>
          <span className="text-[11px] text-slate-400">{time}</span>
        </div>
        <div className="text-slate-800">
          <MessageText text={content} />
        </div>
        {extras && <Sources extras={extras} />}
        <div className="mt-1.5 -ml-1.5 opacity-100 transition-opacity sm:opacity-0 sm:group-focus-within:opacity-100 sm:group-hover:opacity-100">
          <CopyButton text={content} />
        </div>
      </div>
    </div>
  );
}

function Thinking() {
  return (
    <div className="flex gap-3" role="status">
      <AssistantAvatar />
      <div className="flex items-center gap-2.5 rounded-2xl bg-white px-4 py-2.5 text-sm text-slate-500 ring-1 ring-slate-200">
        <span className="flex gap-1" aria-hidden="true">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              className="size-1.5 animate-bounce rounded-full bg-brand-500"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </span>
        Checking your records and documents…
      </div>
    </div>
  );
}

function ConversationList({
  activeId,
  onSelect,
  onNew,
  onClose,
}: {
  activeId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
  onClose?: () => void;
}) {
  const { data, error, isLoading, mutate } = useSWR<Page<Conversation>>(LIST_KEY);
  const factories = useAllFactories();
  const [filter, setFilter] = useState("");

  const groups = useMemo(() => {
    const items = (data?.items ?? []).filter((item) => item.title.toLowerCase().includes(filter.trim().toLowerCase()));
    const result: { label: string; items: Conversation[] }[] = [];
    for (const item of items) {
      const label = groupLabel(item.updated_at);
      const group = result.find((entry) => entry.label === label);
      if (group) group.items.push(item);
      else result.push({ label, items: [item] });
    }
    return result;
  }, [data, filter]);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="space-y-3 border-b border-slate-200 p-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-slate-900">Conversations</p>
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-1 text-slate-500 hover:bg-slate-100 lg:hidden"
              aria-label="Close conversations"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          <MessageSquarePlus className="size-4" aria-hidden="true" />
          New conversation
        </button>
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <input
            type="search"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="Search conversations"
            aria-label="Search conversations"
            className="h-8 w-full rounded-md border border-slate-200 bg-slate-50 pr-2 pl-8 text-sm placeholder:text-slate-400 focus:border-brand-500 focus:bg-white focus:ring-2 focus:ring-brand-500/20 focus:outline-none"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 py-3">
        {error ? (
          <ErrorState message={errorMessage(error)} onRetry={() => mutate()} className="py-6" />
        ) : isLoading || !data ? (
          <div className="space-y-2 px-1">
            {[0, 1, 2, 3, 4].map((key) => (
              <Skeleton key={key} className="h-11" />
            ))}
          </div>
        ) : data.items.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-slate-500">
            No conversations yet. Ask your first question to start one.
          </p>
        ) : groups.length === 0 ? (
          <p className="px-3 py-8 text-center text-sm text-slate-500">No conversations match “{filter}”.</p>
        ) : (
          <nav aria-label="Conversation history" className="space-y-4">
            {groups.map((group) => (
              <div key={group.label}>
                <p className="mb-1 px-2.5 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">{group.label}</p>
                <ul className="space-y-0.5">
                  {group.items.map((conversation) => {
                    const active = conversation.id === activeId;
                    return (
                      <li key={conversation.id}>
                        <button
                          type="button"
                          onClick={() => onSelect(conversation.id)}
                          aria-current={active ? "true" : undefined}
                          className={cn(
                            "relative w-full rounded-md py-2 pr-2 pl-3 text-left transition-colors",
                            active ? "bg-brand-50" : "hover:bg-slate-50",
                          )}
                        >
                          {active && <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-brand-600" aria-hidden="true" />}
                          <span
                            className={cn(
                              "block truncate text-sm",
                              active ? "font-medium text-brand-900" : "text-slate-700",
                            )}
                          >
                            {conversation.title}
                          </span>
                          {conversation.factory_id && (
                            <span className="mt-0.5 flex items-center gap-1 truncate text-xs text-slate-500">
                              <Building2 className="size-3 shrink-0" aria-hidden="true" />
                              {factories.nameOf(conversation.factory_id)}
                            </span>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </nav>
        )}
      </div>
    </div>
  );
}

export function AssistantView() {
  const { user } = useSession();
  const factories = useAllFactories();
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const conversationId = Number(searchParams.get("c")) || null;

  const { data: conversation, error, isLoading, mutate } = useSWR<ConversationDetail>(
    conversationId ? `/chat/conversations/${conversationId}` : null,
  );
  const { mutate: mutateList } = useSWR<Page<Conversation>>(LIST_KEY);

  const [text, setText] = useState("");
  const [factoryId, setFactoryId] = useState("");
  const [pending, setPending] = useState<Pending | null>(null);
  const [failed, setFailed] = useState<{ text: string; message: string } | null>(null);
  const [extras, setExtras] = useState<Record<number, Extras>>({});
  const [showList, setShowList] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const factorySelectId = useId();

  const messages: ChatMessage[] = conversation?.messages ?? [];
  const conversationExtras = conversationId ? extras[conversationId] : undefined;
  const lastAssistantIndex = messages.findLastIndex((message) => message.role === "assistant");
  const contextFactory = conversationId ? conversation?.factory_id : factoryId ? Number(factoryId) : null;

  const isWelcome = !conversationId && !pending && !failed;

  useEffect(() => {
    if (!isWelcome) bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [isWelcome, messages.length, pending, failed]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 192)}px`;
  }, [text]);

  function open(id: number | null) {
    setShowList(false);
    setFailed(null);
    setPending(null);
    router.replace(id ? `${pathname}?c=${id}` : pathname, { scroll: false });
    if (!id) setTimeout(() => textareaRef.current?.focus(), 0);
  }

  async function send(message = text) {
    const content = message.trim();
    if (!content || pending) return;
    setPending({ text: content, conversationId });
    setFailed(null);
    setText("");
    try {
      const response = await api<ChatResponse>("/chat", {
        method: "POST",
        body: conversationId
          ? { message: content, conversation_id: conversationId }
          : { message: content, factory_id: factoryId ? Number(factoryId) : null },
      });
      setExtras((current) => ({
        ...current,
        [response.conversation_id]: { reply: response.reply, sources: response.sources, tools: response.tools_used },
      }));
      if (response.conversation_id !== conversationId) {
        router.replace(`${pathname}?c=${response.conversation_id}`, { scroll: false });
      } else {
        await mutate();
      }
      await mutateList();
    } catch (caught) {
      setFailed({ text: content, message: errorMessage(caught) });
    } finally {
      setPending(null);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      send();
    }
  }

  const firstName = user.full_name.split(" ")[0];

  return (
    <div className="-mx-4 -my-6 flex h-[calc(100dvh-3.5rem)] sm:-mx-6 lg:-mx-8 lg:-my-8 lg:h-dvh">
      <aside
        className={cn(
          "w-72 shrink-0 border-r border-slate-200",
          showList ? "fixed inset-y-0 left-0 z-40 shadow-xl lg:static lg:shadow-none" : "hidden lg:block",
        )}
      >
        <ConversationList
          activeId={conversationId}
          onSelect={open}
          onNew={() => open(null)}
          onClose={showList ? () => setShowList(false) : undefined}
        />
      </aside>
      {showList && <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={() => setShowList(false)} />}

      <section className="flex min-w-0 flex-1 flex-col bg-slate-50/60">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b border-slate-200 bg-white px-4">
          <button
            type="button"
            onClick={() => setShowList(true)}
            className="-ml-1 rounded-md p-1.5 text-slate-500 hover:bg-slate-100 lg:hidden"
            aria-label="Show conversations"
          >
            <PanelLeft className="size-5" aria-hidden="true" />
          </button>
          <div className="min-w-0 flex-1">
            <h1 className="truncate text-sm font-semibold text-slate-900 sm:text-base">
              {conversationId ? (conversation?.title ?? "Conversation") : "AI Assistant"}
            </h1>
            <p className="flex items-center gap-1 truncate text-xs text-slate-500">
              <Building2 className="size-3 shrink-0" aria-hidden="true" />
              {contextFactory ? factories.nameOf(contextFactory) : "All your factories"}
            </p>
          </div>
          {conversationId && (
            <button
              type="button"
              onClick={() => open(null)}
              className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-2.5 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              <MessageSquarePlus className="size-4" aria-hidden="true" />
              <span className="hidden sm:inline">New chat</span>
            </button>
          )}
        </header>

        <div className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
            {isWelcome ? (
              <div className="pt-2 sm:pt-8">
                <AssistantAvatar className="size-11 rounded-xl" />
                <h2 className="mt-5 text-2xl font-semibold tracking-tight text-slate-900">Hello, {firstName}</h2>
                <p className="mt-1 text-base text-slate-500">
                  Ask about your factories&apos; safety records, Bangladesh labour law or safety rules.
                </p>
                <ul className="mt-5 flex flex-wrap gap-2 text-xs text-slate-600">
                  {[
                    { icon: Database, label: "Reads your inspections, incidents and actions" },
                    { icon: Scale, label: "Cites labour law and safety documents" },
                    { icon: Languages, label: "English or Bangla" },
                  ].map((item) => (
                    <li key={item.label} className="flex items-center gap-1.5 rounded-full bg-white px-3 py-1 ring-1 ring-slate-200">
                      <item.icon className="size-3.5 text-brand-600" aria-hidden="true" />
                      {item.label}
                    </li>
                  ))}
                </ul>
                <p className="mt-10 mb-3 text-xs font-semibold tracking-wider text-slate-400 uppercase">Try asking</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion.prompt}
                      type="button"
                      onClick={() => send(suggestion.prompt)}
                      className="group flex flex-col items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left transition-colors hover:border-brand-300 hover:bg-brand-50/30"
                    >
                      <span className="flex items-center gap-2 text-xs font-medium text-slate-500">
                        <span className="flex size-7 items-center justify-center rounded-lg bg-slate-100 text-slate-600 group-hover:bg-brand-100 group-hover:text-brand-700">
                          <suggestion.icon className="size-4" aria-hidden="true" />
                        </span>
                        {suggestion.topic}
                      </span>
                      <span className="text-sm leading-5 text-slate-800">{suggestion.prompt}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {error ? (
                  <ErrorState message={errorMessage(error)} onRetry={() => mutate()} />
                ) : conversationId && isLoading ? (
                  <LoadingBlock label="Loading conversation…" />
                ) : (
                  messages.map((message, index) =>
                    message.role === "user" ? (
                      <UserMessage key={message.id} content={message.content} time={messageTime(message.created_at)} />
                    ) : (
                      <AssistantMessage
                        key={message.id}
                        content={message.content}
                        time={messageTime(message.created_at)}
                        extras={
                          index === lastAssistantIndex && conversationExtras?.reply === message.content
                            ? conversationExtras
                            : undefined
                        }
                      />
                    ),
                  )
                )}

                {pending && pending.conversationId === conversationId && (
                  <>
                    <UserMessage content={pending.text} />
                    <Thinking />
                  </>
                )}

                {failed && (
                  <div className="flex flex-col items-end gap-2">
                    <UserMessage content={failed.text} />
                    <div
                      role="alert"
                      className="flex max-w-[85%] flex-wrap items-center gap-x-3 gap-y-1.5 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
                    >
                      <span>Not sent. {failed.message}</span>
                      <button
                        type="button"
                        onClick={() => send(failed.text)}
                        className="inline-flex items-center gap-1 font-medium text-red-700 hover:text-red-900"
                      >
                        <RotateCw className="size-3.5" aria-hidden="true" />
                        Retry
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        </div>

        <div className="shrink-0 px-4 pb-4 sm:px-6">
          <form
            className="mx-auto max-w-3xl"
            onSubmit={(event) => {
              event.preventDefault();
              send();
            }}
          >
            <div className="rounded-2xl border border-slate-300 bg-white shadow-sm transition-colors focus-within:border-brand-500 focus-within:ring-4 focus-within:ring-brand-500/10">
              <label htmlFor="assistant-message" className="sr-only">
                Message
              </label>
              <textarea
                id="assistant-message"
                ref={textareaRef}
                value={text}
                onChange={(event) => setText(event.target.value)}
                onKeyDown={onKeyDown}
                rows={1}
                maxLength={MAX_LENGTH}
                placeholder={conversationId ? "Ask a follow-up question…" : "Ask about your factories, labour law or safety rules…"}
                className="block max-h-48 min-h-13 w-full resize-none rounded-t-2xl bg-transparent px-4 pt-3.5 pb-1 text-sm leading-6 text-slate-900 placeholder:text-slate-400 focus:outline-none"
              />
              <div className="flex items-center justify-between gap-2 px-2.5 pb-2.5">
                {!conversationId && factories.factories.length > 0 ? (
                  <div className="flex min-w-0 items-center gap-1.5 rounded-lg bg-slate-100 py-1 pr-1 pl-2 text-xs text-slate-600">
                    <Building2 className="size-3.5 shrink-0" aria-hidden="true" />
                    <label htmlFor={factorySelectId} className="sr-only">
                      Focus on factory
                    </label>
                    <select
                      id={factorySelectId}
                      value={factoryId}
                      onChange={(event) => setFactoryId(event.target.value)}
                      className="max-w-48 min-w-0 truncate bg-transparent font-medium text-slate-700 focus:outline-none sm:max-w-64"
                    >
                      <option value="">All my factories</option>
                      {factories.options.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <span />
                )}
                <div className="flex items-center gap-2">
                  {text.length > MAX_LENGTH - 500 && (
                    <span className="text-xs text-slate-400 tabular-nums">
                      {text.length}/{MAX_LENGTH}
                    </span>
                  )}
                  <button
                    type="submit"
                    disabled={!text.trim() || Boolean(pending)}
                    aria-label="Send message"
                    className="flex size-9 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:bg-slate-200 disabled:text-slate-400"
                  >
                    <ArrowUp className="size-4" aria-hidden="true" />
                  </button>
                </div>
              </div>
            </div>
            <p className="mt-2 text-center text-[11px] text-slate-400">
              Enter to send · Shift + Enter for a new line · Answers can be wrong; check important legal points with the
              official source.
            </p>
          </form>
        </div>
      </section>
    </div>
  );
}
