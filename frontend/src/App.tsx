import { createContext, useContext, useEffect, useState } from 'react'
import { Link, Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { ArrowUpRight, Bell, CalendarDays, CircleUserRound, Home, LogOut, MessageCircle, ShieldCheck, Sparkles, Trophy, Users, Repeat2 } from 'lucide-react'
import { api, setCsrf, useAction, useApi } from './api'
import { Avatar, Button, ErrorBox, Loading } from './components'
import type { Session } from './types'
import { LoginPage, ProfilePage, ReviewPage } from './pages/Account'
import { HomePage } from './pages/Home'
import { MarketPage } from './pages/Market'
import { PeoplePage, MessagesPage } from './pages/Community'
import { MatchesPage } from './pages/Matches'
import { CoachPage } from './pages/Coach'

const SessionContext = createContext<Session | null>(null)
export const useSession = () => useContext(SessionContext)!
const nav = [ ['/', '球场首页', Home], ['/courts', '场地集市', CalendarDays], ['/trade', '场地交换', Repeat2], ['/games', '寻找球搭子', Users], ['/matches', '比赛与排名', Trophy], ['/people', '球友圈', CircleUserRound], ['/messages', '站内消息', MessageCircle], ['/coach', '我的 AI 教练', Sparkles] ] as const

function Shell() {
  const session = useSession(), user = session.user!
  const location = useLocation(), action = useAction()
  const [showNotices, setShowNotices] = useState(false)
  const notifications = useApi<{ items: { id: number; kind: string; text: string; read: boolean }[]; unread: number; unread_messages: number }>('/notifications/', { enabled: user.verification === 'approved', poll: 10_000 })
  useEffect(() => { setShowNotices(false); window.scrollTo(0, 0) }, [location.pathname])
  const approved = user.verification === 'approved'
  return <div className="app-shell"><aside className="sidebar"><Link className="brand" to="/"><span className="brand-ball">◒</span><span>清网同行<small>THUCOURT</small></span></Link><div className="sidebar-label">一起上场，一起成长</div><nav>{nav.map(([path, label, Icon]) => <NavLink key={path} end={path === '/'} to={approved ? path : '/profile'} className={({ isActive }) => isActive && (approved || path === '/') ? 'active' : ''}><Icon size={20} /><span>{label}</span>{path === '/messages' && !!notifications.data?.unread_messages && <b className="unread-count">{notifications.data.unread_messages}</b>}</NavLink>)}</nav><div className="sidebar-bottom"><div className="sidebar-note"><span className="tiny-dot" /> Tsinghua Tennis Community<p>球场上的每一次相遇，<br />都是进步的开始。</p></div><a href="https://github.com/paulinxu/thucourt" target="_blank" rel="noreferrer">关于项目 <ArrowUpRight size={14} /></a></div></aside><div className="workspace"><header className="topbar"><span className="topbar-title">清华大学 · 网球社区</span><div className="topbar-actions">{session.demo_mode && <span className="demo-label">课程演示环境</span>}<button className="icon-button notification-button" aria-label="通知" onClick={() => setShowNotices(!showNotices)}><Bell size={20} />{!!notifications.data?.unread && <i />}</button><Link to="/profile" className="user-link"><Avatar player={user} small /><span>{user.display_name}</span></Link><button className="icon-button" aria-label="退出登录" onClick={() => action.mutate(async () => { await api('/auth/logout/', 'POST'); window.location.assign('/') })}><LogOut size={18} /></button></div>{showNotices && <div className="notifications"><h3>消息通知</h3>{notifications.data?.items.length ? notifications.data.items.map(n => <Link key={n.id} to={n.kind === 'match' ? '/matches' : n.kind === 'friend' ? '/people' : '/profile'}>{!n.read && <span className="tiny-dot" />}{n.text}</Link>) : <p>暂无新通知</p>}<Button className="secondary" onClick={() => action.mutate(() => api('/notifications/', 'POST'))}>全部标为已读</Button></div>}</header><main className="main-content"><ErrorBox error={action.error} />{!approved && <div className="notice"><ShieldCheck size={20} />社区功能需要管理员审核学生身份。请先完善个人资料。</div>}<Routes><Route path="/profile" element={<ProfilePage />} /><Route path="/review" element={user.is_staff ? <ReviewPage /> : <Navigate to="/" />} /><Route path="/" element={approved ? <HomePage /> : <Navigate to="/profile" />} /><Route path="/courts" element={approved ? <MarketPage section="market" /> : <Navigate to="/profile" />} /><Route path="/trade" element={approved ? <MarketPage section="trade" /> : <Navigate to="/profile" />} /><Route path="/games" element={approved ? <MarketPage section="game" /> : <Navigate to="/profile" />} /><Route path="/people" element={approved ? <PeoplePage /> : <Navigate to="/profile" />} /><Route path="/messages" element={approved ? <MessagesPage /> : <Navigate to="/profile" />} /><Route path="/matches" element={approved ? <MatchesPage /> : <Navigate to="/profile" />} /><Route path="/coach" element={approved ? <CoachPage /> : <Navigate to="/profile" />} /><Route path="*" element={<Navigate to="/" />} /></Routes></main><footer>清网同行 · THUCourt <span>让每一场网球，都有所收获。</span></footer></div></div>
}

export default function App() {
  const session = useApi<Session>('/auth/session/')
  if (session.isPending) return <Loading />
  if (session.error || !session.data) return <div className="standalone"><ErrorBox error={session.error} /><Button onClick={() => session.refetch()}>重新连接</Button></div>
  setCsrf(session.data.csrf_token)
  return <SessionContext.Provider value={session.data}>{session.data.user ? <Shell /> : <LoginPage />}</SessionContext.Provider>
}
