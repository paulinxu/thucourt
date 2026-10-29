import { useEffect, useRef } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { ArrowLeft, ArrowRight, LoaderCircle, X } from 'lucide-react'
import type { Page, Player } from './types'

export const statusNames: Record<string, string> = { active: '进行中', fulfilled: '已完成', cancelled: '已取消', expired: '已过期', pending: '待确认', confirmed: '已确认', rejected: '已拒绝', queued: '排队中', processing: '处理中', ready: '已完成', failed: '失败', approved: '已认证', unsubmitted: '未提交' }
export const kindNames: Record<string, string> = { buy: '求场', sell: '转场', trade: '换场', game: '约球' }
export const strokeNames: Record<string, string> = { forehand: '正手', backhand: '反手', serve: '发球', slice: '切削', volley: '截击', movement: '移动' }
export const levels = Array.from({ length: 10 }, (_, i) => (1 + i / 2).toFixed(1))
export function dateLabel(date: string) { return new Date(date + 'T12:00:00+08:00').toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', weekday: 'short', timeZone: 'Asia/Shanghai' }) }
export function today() { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date()) }
export function Avatar({ player, small = false }: { player: Pick<Player, 'display_name' | 'id'>; small?: boolean }) { return <span className={`avatar color-${player.id % 4} ${small ? 'small' : ''}`}>{player.display_name.slice(0, 1)}</span> }
export function Badge({ status }: { status: string }) { return <span className={`badge ${status}`}>{statusNames[status] || status}</span> }
export function ErrorBox({ error }: { error: Error | null | undefined }) { return error ? <div className="error" role="alert">{error.message}</div> : null }
export function Loading() { return <div className="loading" role="status"><LoaderCircle className="spin" size={20} /> 加载中…</div> }
export function Empty({ children = '这里还很安静，发布第一条动态吧。' }: { children?: ReactNode }) { return <div className="empty"><span>◎</span><p>{children}</p></div> }
export function Button({ children, busy, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { busy?: boolean }) { return <button className={`button ${className}`} disabled={busy || props.disabled} {...props}>{busy && <LoaderCircle size={16} className="spin" />}{children}</button> }
export function PageTitle({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) { return <div className="page-title"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div> }
export function Pager({ data, page, setPage }: { data?: Pick<Page<unknown>, 'count' | 'next' | 'previous'>; page: number; setPage: (p: number) => void }) { if (!data || data.count <= 50) return null; return <div className="pager"><Button className="secondary" disabled={!data.previous} onClick={() => setPage(page - 1)}><ArrowLeft size={16} />上一页</Button><span>第 {page} 页 · 共 {data.count} 条</span><Button className="secondary" disabled={!data.next} onClick={() => setPage(page + 1)}>下一页<ArrowRight size={16} /></Button></div> }
export function Modal({ title, children, close }: { title: string; children: ReactNode; close: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close() }, [])
  return <dialog ref={ref} className="modal" onCancel={close} onClick={e => { if (e.target === e.currentTarget) close() }}><div className="modal-header"><h2>{title}</h2><button aria-label="关闭" className="icon-button" onClick={close}><X /></button></div>{children}</dialog>
}
