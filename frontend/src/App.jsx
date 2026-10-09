import { useCallback, useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import {
  Activity,
  ArrowLeft,
  ArrowRight,
  Bell,
  BookMarked,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  ImagePlus,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Library,
  LogOut,
  Menu,
  Plus,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Star,
  TimerReset,
  Trash2,
  Upload,
  Users,
  X,
} from 'lucide-react'
import { Link, NavLink, Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './auth/useAuth.js'
import api from './lib/api'
import './App.css'

const roleNames = {
  student: 'Student',
  parent: 'Parent',
  teacher: 'Teacher',
  admin: 'Administrator',
}

const avatarPresets = [
  { id: 'aurora', label: 'Aurora', icon: Sparkles, colors: 'from-fuchsia-500 to-violet-600' },
  { id: 'atlas', label: 'Atlas', icon: GraduationCap, colors: 'from-sky-500 to-blue-700' },
  { id: 'nova', label: 'Nova', icon: Star, colors: 'from-amber-400 to-orange-600' },
  { id: 'river', label: 'River', icon: Activity, colors: 'from-cyan-400 to-teal-700' },
  { id: 'sage', label: 'Sage', icon: BookOpen, colors: 'from-emerald-400 to-green-700' },
  { id: 'comet', label: 'Comet', icon: ArrowRight, colors: 'from-rose-400 to-pink-700' },
  { id: 'maple', label: 'Maple', icon: Library, colors: 'from-orange-400 to-red-700' },
  { id: 'orbit', label: 'Orbit', icon: CalendarDays, colors: 'from-indigo-400 to-slate-700' },
]

const roleLinks = {
  student: [
    { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
    { to: '/app/courses', label: 'My courses', icon: GraduationCap },
    { to: '/app/lessons', label: 'Lessons', icon: BookOpen },
    { to: '/app/assignments', label: 'Assignments', icon: ClipboardCheck },
    { to: '/app/exams', label: 'Exams', icon: FileText },
    { to: '/app/grades', label: 'Grades', icon: CheckCircle2 },
    { to: '/app/calendar', label: 'Calendar', icon: CalendarDays },
    { to: '/app/messages', label: 'Messages', icon: FileText },
    { to: '/app/library', label: 'Library', icon: Library },
    { to: '/app/notifications', label: 'Notifications', icon: Bell },
    { to: '/app/profile', label: 'Profile & avatar', icon: Settings },
  ],
  parent: [
    { to: '/app', label: 'Overview', icon: LayoutDashboard, end: true },
    { to: '/app/children', label: 'My children', icon: Users },
    { to: '/app/courses', label: 'Courses', icon: GraduationCap },
    { to: '/app/assignments', label: 'Assignments', icon: ClipboardCheck },
    { to: '/app/exams', label: 'Exams', icon: FileText },
    { to: '/app/grades', label: 'Grades', icon: CheckCircle2 },
    { to: '/app/attendance', label: 'Attendance', icon: CalendarDays },
    { to: '/app/calendar', label: 'Calendar', icon: CalendarDays },
    { to: '/app/messages', label: 'Messages', icon: FileText },
    { to: '/app/notifications', label: 'Notifications', icon: Bell },
    { to: '/app/profile', label: 'Profile & avatar', icon: Settings },
  ],
  teacher: [
    { to: '/app/teacher', label: 'Teacher dashboard', icon: LayoutDashboard, end: true },
    { to: '/app/courses', label: 'My courses', icon: GraduationCap },
    { to: '/app/lessons', label: 'Lessons', icon: BookOpen },
    { to: '/app/assignments', label: 'Assignments', icon: ClipboardCheck },
    { to: '/app/exams', label: 'Exams', icon: FileText },
    { to: '/app/submissions', label: 'Submissions', icon: FileText },
    { to: '/app/grades', label: 'Grades', icon: CheckCircle2 },
    { to: '/app/attendance', label: 'Attendance', icon: CalendarDays },
    { to: '/app/calendar', label: 'Calendar', icon: CalendarDays },
    { to: '/app/messages', label: 'Messages', icon: FileText },
    { to: '/app/notifications', label: 'Notifications', icon: Bell },
    { to: '/app/profile', label: 'Profile & avatar', icon: Settings },
  ],
  admin: [
    { to: '/app/admin', label: 'Administration', icon: LayoutDashboard, end: true },
    { to: '/app/courses', label: 'Courses', icon: GraduationCap },
    { to: '/app/assignments', label: 'Assignments', icon: ClipboardCheck },
    { to: '/app/exams', label: 'Exams', icon: FileText },
    { to: '/app/grades', label: 'Grades', icon: CheckCircle2 },
    { to: '/app/attendance', label: 'Attendance', icon: CalendarDays },
    { to: '/app/calendar', label: 'Calendar', icon: CalendarDays },
    { to: '/app/messages', label: 'Messages', icon: FileText },
    { to: '/app/library', label: 'Library', icon: Library },
    { to: '/app/notifications', label: 'Notifications', icon: Bell },
    { to: '/app/accounts', label: 'User management', icon: Users },
    { to: '/app/profile', label: 'Profile & avatar', icon: Settings },
  ],
}

function errorMessage(error) {
  const data = error?.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data === 'object' && data) {
    const firstError = Object.values(data).flat()[0]
    if (typeof firstError === 'string') return firstError
  }
  return 'Something went wrong. Please try again.'
}

function Brand({ compact = false }) {
  return (
    <Link to="/" className="flex items-center gap-3" aria-label="EDUCORE home">
      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-violet-500 text-white shadow-lg shadow-violet-900/40">
        <GraduationCap size={21} aria-hidden="true" />
      </span>
      {!compact && <span className="text-lg font-extrabold tracking-[0.12em] text-white">EDUCORE</span>}
    </Link>
  )
}

function ProfileAvatar({ user, size = 'h-10 w-10' }) {
  const preset = avatarPresets.find(({ id }) => id === user?.avatar_key) || avatarPresets[0]
  const Icon = preset.icon
  return user?.profile_photo_url ? (
    <img
      src={user.profile_photo_url}
      alt={`${user.first_name || user.username}'s profile`}
      className={`${size} shrink-0 rounded-full border border-slate-700 object-cover`}
    />
  ) : (
    <span className={`${size} flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${preset.colors} text-white`}>
      <Icon size={20} aria-hidden="true" />
    </span>
  )
}

function PublicHome() {
  return (
    <div className="min-h-screen overflow-hidden bg-slate-950 text-slate-100">
      <div className="grid-pattern absolute inset-0 opacity-30" aria-hidden="true" />
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <Brand />
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex" aria-label="Main navigation">
          <a href="#platform" className="transition hover:text-white">Platform</a>
          <a href="#roles" className="transition hover:text-white">For every role</a>
          <a href="#security" className="transition hover:text-white">Security</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link to="/staff/login" className="rounded-full px-3 py-2 text-xs font-semibold text-violet-200 hover:text-white sm:px-4 sm:text-sm">Staff portal</Link>
          <Link to="/login" className="rounded-full px-4 py-2 text-sm font-semibold text-slate-200 hover:text-white">Log in</Link>
          <Link to="/register" className="rounded-full bg-violet-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/25 transition hover:bg-violet-400">
            Create account
          </Link>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-7xl px-6 lg:px-8">
        <section className="grid items-center gap-12 pb-24 pt-16 lg:grid-cols-[1.1fr_0.9fr] lg:pb-32 lg:pt-24">
          <div>
            <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-400/20 bg-violet-400/10 px-4 py-2 text-sm font-medium text-violet-200">
              <Activity size={16} /> One connected learning environment
            </p>
            <h1 className="max-w-3xl text-5xl font-black leading-[1.08] tracking-tight text-white md:text-7xl">
              Make every learning step count.
            </h1>
            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
              EDUCORE brings courses, assignments, progress, and communication together for students, families, and educators.
            </p>
            <div className="mt-9 flex flex-wrap gap-4">
              <Link to="/register" className="inline-flex items-center gap-2 rounded-full bg-violet-500 px-6 py-3.5 font-semibold text-white shadow-lg shadow-violet-500/20 transition hover:bg-violet-400">
                Get started <ArrowRight size={17} />
              </Link>
              <a href="#platform" className="rounded-full border border-slate-700 px-6 py-3.5 font-semibold text-slate-200 transition hover:border-slate-500 hover:bg-slate-900">
                Explore the platform
              </a>
            </div>
            <div className="mt-9 flex flex-wrap gap-x-7 gap-y-3 text-sm text-slate-300">
              {['Role-aware workspaces', 'Learning progress', 'Secure account access'].map((item) => (
                <span key={item} className="inline-flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-400" /> {item}
                </span>
              ))}
            </div>
          </div>

          <div className="glass-panel relative rounded-[2rem] p-5 shadow-2xl shadow-violet-950/30">
            <div className="rounded-[1.5rem] border border-slate-800 bg-slate-950/80 p-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-5">
                <div>
                  <p className="text-sm text-slate-400">Learning workspace</p>
                  <p className="mt-1 text-xl font-bold text-white">Your next step, clearly in view</p>
                </div>
                <span className="rounded-2xl bg-violet-500/15 p-3 text-violet-200"><BookMarked size={21} /></span>
              </div>
              <div className="mt-6 space-y-4">
                {[
                  { icon: GraduationCap, title: 'Courses and lessons', caption: 'Follow learning paths and record lesson progress', color: 'text-violet-200 bg-violet-500/15' },
                  { icon: ClipboardCheck, title: 'Assignments and assessments', caption: 'Keep deadlines and submissions organized', color: 'text-sky-200 bg-sky-500/15' },
                  { icon: Users, title: 'Family and educator connection', caption: 'Give each role a dedicated workspace', color: 'text-emerald-200 bg-emerald-500/15' },
                ].map(({ icon: Icon, title, caption, color }) => (
                  <div key={title} className="flex items-center gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-4">
                    <span className={`rounded-xl p-3 ${color}`}><Icon size={19} /></span>
                    <div>
                      <p className="font-semibold text-white">{title}</p>
                      <p className="mt-1 text-sm text-slate-400">{caption}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-5 flex items-center gap-3 rounded-xl bg-slate-900 p-4 text-sm text-slate-300">
                <ShieldCheck size={18} className="shrink-0 text-emerald-300" />
                Access to private learning data is enforced by the platform API.
              </div>
            </div>
          </div>
        </section>

        <section id="platform" className="scroll-mt-10 py-16">
          <div className="max-w-2xl">
            <p className="text-sm font-bold uppercase tracking-[0.22em] text-violet-300">Platform</p>
            <h2 className="mt-4 text-3xl font-bold text-white md:text-4xl">The essential tools, connected.</h2>
            <p className="mt-4 leading-7 text-slate-300">A shared foundation for content, academic activity, and communication, with access shaped around each account.</p>
          </div>
          <div className="mt-9 grid gap-5 md:grid-cols-3">
            {[
              { icon: GraduationCap, title: 'Learn', text: 'Discover courses, study lessons, use the library, and follow assignment deadlines.' },
              { icon: CalendarDays, title: 'Coordinate', text: 'Keep academic work and important updates in one dependable place.' },
              { icon: ShieldCheck, title: 'Manage access', text: 'Protect student and family information with role-based API permissions.' },
            ].map(({ icon: Icon, title, text }) => (
              <article key={title} className="glass-panel rounded-3xl p-6">
                <span className="inline-flex rounded-2xl bg-violet-500/15 p-3 text-violet-200"><Icon size={21} /></span>
                <h3 className="mt-5 text-xl font-bold text-white">{title}</h3>
                <p className="mt-3 leading-7 text-slate-300">{text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="roles" className="grid gap-10 py-16 lg:grid-cols-2">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.22em] text-emerald-300">Made for your role</p>
            <h2 className="mt-4 text-3xl font-bold text-white md:text-4xl">A clearer experience for everyone involved.</h2>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ['Students', 'Courses, assignments, lesson progress, and learning resources.'],
              ['Parents', 'A dedicated view of explicitly linked children and their academic activity.'],
              ['Teachers', 'Course and lesson management with assignment review workflows.'],
              ['Administrators', 'Platform management and governance through protected controls.'],
            ].map(([title, text]) => (
              <div key={title} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
                <h3 className="font-bold text-white">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{text}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="security" className="glass-panel mb-20 rounded-[2rem] p-8 md:p-10">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-bold uppercase tracking-[0.22em] text-violet-300">Security and privacy</p>
              <h2 className="mt-3 text-3xl font-bold text-white">Private data stays behind permission checks.</h2>
              <p className="mt-3 max-w-2xl leading-7 text-slate-300">Course access, parent-child relationships, and student submissions are checked on the backend for every request.</p>
            </div>
            <Link to="/register" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-full bg-white px-6 py-3 font-semibold text-slate-950 transition hover:bg-slate-200">
              Create your account <ArrowRight size={17} />
            </Link>
          </div>
        </section>
      </main>
      <footer className="border-t border-slate-800 px-6 py-7 text-center text-sm text-slate-500">
        EDUCORE · Learning, connected.
      </footer>
    </div>
  )
}

function staffHomePath(role) {
  return role === 'admin' ? '/staff/admin' : '/staff/teacher'
}

function AuthPage({ mode, staffOnly = false }) {
  const registering = mode === 'register'
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const { register, handleSubmit, formState: { errors } } = useForm()

  useEffect(() => {
    if (user) navigate(user.role === 'teacher' || user.role === 'admin' ? staffHomePath(user.role) : '/app', { replace: true })
  }, [user, navigate])

  async function submit(values) {
    setBusy(true)
    setError('')
    try {
      if (registering) {
        await api.post('/auth/register/', values)
      }
      const profile = await login({ username: values.username, password: values.password })
      navigate(
        profile.role === 'teacher' || profile.role === 'admin' ? staffHomePath(profile.role) : '/app',
        { replace: true },
      )
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-5 py-10 text-slate-100">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-[2rem] border border-slate-800 bg-slate-900/80 shadow-2xl shadow-black/30 md:grid-cols-2">
        <div className="hidden flex-col justify-between bg-gradient-to-br from-violet-600 to-indigo-900 p-10 md:flex">
          <Brand />
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-violet-100">EDUCORE workspace</p>
            <h1 className="mt-4 text-4xl font-black leading-tight text-white">{registering ? 'Start your learning journey.' : 'Welcome back to your learning space.'}</h1>
            <p className="mt-5 leading-7 text-indigo-100">One secure account for courses, academic activity, and the people who support learning.</p>
          </div>
          <p className="text-sm text-indigo-200">Student · Parent · Teacher · Administrator</p>
        </div>
        <div className="p-7 sm:p-10">
          <Link to="/" className="mb-8 inline-flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white">
            <ArrowLeft size={16} /> Back to EDUCORE
          </Link>
          <h2 className="text-3xl font-bold text-white">{registering ? 'Create your account' : staffOnly ? 'Staff portal sign in' : 'Sign in'}</h2>
          <p className="mt-2 text-slate-400">{registering ? 'Set up your student or parent account.' : staffOnly ? 'Sign in with your teacher or administrator account.' : 'Enter your credentials to continue.'}</p>
          <form className="mt-8 space-y-5" onSubmit={handleSubmit(submit)} noValidate>
            {registering && (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="First name" error={errors.first_name?.message}>
                  <input autoComplete="given-name" {...register('first_name', { required: 'Enter your first name.' })} />
                </Field>
                <Field label="Last name" error={errors.last_name?.message}>
                  <input autoComplete="family-name" {...register('last_name', { required: 'Enter your last name.' })} />
                </Field>
              </div>
            )}
            <Field label="Username" error={errors.username?.message}>
              <input autoComplete="username" {...register('username', { required: 'Enter your username.' })} />
            </Field>
            {registering && (
              <Field label="Email address" error={errors.email?.message}>
                <input type="email" autoComplete="email" {...register('email', { required: 'Enter your email address.' })} />
              </Field>
            )}
            <Field label="Password" error={errors.password?.message}>
              <input type="password" autoComplete={registering ? 'new-password' : 'current-password'} {...register('password', { required: 'Enter your password.', minLength: registering ? { value: 12, message: 'Use at least 12 characters.' } : undefined })} />
              {registering && <small className="mt-1 block text-xs text-slate-500">Use at least 12 characters.</small>}
            </Field>
            {registering && (
              <Field label="Account type" error={errors.role?.message}>
                <select defaultValue="student" {...register('role', { required: true })}>
                  <option value="student">Student</option>
                  <option value="parent">Parent</option>
                </select>
                <small className="mt-1 block text-xs text-slate-500">Teacher and administrator accounts are provisioned by an administrator.</small>
              </Field>
            )}
            {error && <p role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/10 p-3 text-sm text-rose-200">{error}</p>}
            <button disabled={busy} className="w-full rounded-xl bg-violet-500 px-5 py-3.5 font-semibold text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-60">
              {busy ? 'Please wait…' : registering ? 'Create account' : 'Sign in'}
            </button>
          </form>
          {staffOnly ? (
            <p className="mt-6 text-sm text-slate-400">Student or parent? <Link className="font-semibold text-violet-300 hover:text-violet-200" to="/login">Use the learning portal</Link></p>
          ) : (
            <p className="mt-6 text-sm text-slate-400">
              {registering ? 'Already registered?' : 'New to EDUCORE?'}{' '}
              <Link className="font-semibold text-violet-300 hover:text-violet-200" to={registering ? '/login' : '/register'}>
                {registering ? 'Sign in' : 'Create an account'}
              </Link>
            </p>
          )}
        </div>
      </div>
    </main>
  )
}

function Field({ label, error, children }) {
  return (
    <label className="block text-sm font-medium text-slate-200">
      {label}
      {children}
      {error && <span role="alert" className="mt-1 block text-xs text-rose-300">{error}</span>}
    </label>
  )
}

function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <LoadingState label="Checking your account…" />
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />
  if (user.role === 'teacher' || user.role === 'admin') return <Navigate to={staffHomePath(user.role)} replace />
  return <PortalLayout />
}

function StaffHomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={staffHomePath(user.role)} replace />
}

function StaffDashboardRoute({ role }) {
  const { user } = useAuth()
  if (user.role !== role) return <Navigate to={staffHomePath(user.role)} replace />
  return <DashboardPage />
}

function AdminOnlyRoute({ children }) {
  const { user } = useAuth()
  if (user.role !== 'admin') return <Navigate to={staffHomePath(user.role)} replace />
  return children
}

function ProtectedStaffRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <LoadingState label="Checking your account…" />
  if (!user) return <Navigate to="/staff/login" replace state={{ from: location }} />
  if (user.role !== 'teacher' && user.role !== 'admin') return <Navigate to="/app" replace />
  return <PortalLayout />
}

function PortalLayout() {
  const { user, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const isStaffPortal = location.pathname.startsWith('/staff')
  const links = (roleLinks[user.role] || roleLinks.student).map((link) => ({
    ...link,
    to: isStaffPortal ? link.to.replace('/app', '/staff') : link.to,
  }))

  function signOut() {
    logout()
    navigate(isStaffPortal ? '/staff/login' : '/', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 md:flex">
      {mobileOpen && <button aria-label="Close navigation" className="fixed inset-0 z-30 bg-black/60 md:hidden" onClick={() => setMobileOpen(false)} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col overflow-y-auto border-r border-slate-800 bg-slate-950 px-5 py-6 transition-transform md:sticky md:top-0 md:h-screen md:translate-x-0 ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex items-center justify-between">
          <Brand />
          <button className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 md:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu"><X size={18} /></button>
        </div>
        <div className="mt-10">
          <p className="px-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500">Workspace</p>
          <nav className="mt-3 space-y-1" aria-label="Workspace navigation">
            {links.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} onClick={() => setMobileOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? 'bg-violet-500/15 text-violet-100' : 'text-slate-400 hover:bg-slate-900 hover:text-white'}`}>
                <Icon size={18} /> {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="mt-auto border-t border-slate-800 pt-5">
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <ProfileAvatar user={user} />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-white">{user.first_name || user.username}</p>
              <p className="text-xs capitalize text-slate-500">{roleNames[user.role] || user.role}</p>
            </div>
          </div>
          <button onClick={signOut} className="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-900 hover:text-white">
            <LogOut size={17} /> Sign out
          </button>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-800/80 bg-slate-950/85 px-5 backdrop-blur-xl md:px-8">
          <button className="rounded-lg p-2 text-slate-300 hover:bg-slate-800 md:hidden" aria-label="Open menu" onClick={() => setMobileOpen(true)}><Menu size={20} /></button>
          <div className="hidden items-center gap-2 text-sm text-slate-500 md:flex"><span>EDUCORE</span><span>/</span><span className="capitalize text-slate-300">{isStaffPortal ? 'Staff portal' : 'Learning portal'}</span></div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-400 sm:block">{user.email}</span>
            <ProfileAvatar user={user} size="h-9 w-9" />
          </div>
        </header>
        <main className="mx-auto max-w-7xl p-5 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && <p className="text-xs font-bold uppercase tracking-[0.2em] text-violet-300">{eyebrow}</p>}
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-white">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">{description}</p>}
      </div>
      {action}
    </div>
  )
}

function DashboardPage() {
  const { user } = useAuth()
  const location = useLocation()
  const portalRoot = location.pathname.startsWith('/staff') ? '/staff' : '/app'
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/dashboard/')
      .then(({ data: response }) => setData(response))
      .catch((requestError) => setError(errorMessage(requestError)))
  }, [])

  if (error) return <ErrorState message={error} />
  if (!data) return <LoadingState label="Loading your learning overview…" />

  const studentStats = [
    ['Courses', data.course_count ?? 0, GraduationCap],
    ['Active courses', data.active_courses ?? 0, Activity],
    ['Lessons completed', data.completed_lessons ?? 0, CheckCircle2],
    ['Upcoming assignments', data.pending_assignments ?? 0, ClipboardCheck],
  ]
  const teacherStats = [
    ['My courses', data.course_count ?? 0, GraduationCap],
    ['Learners', data.learner_count ?? 0, Users],
  ]
  const adminStats = [
    ['Accounts', data.user_count ?? 0, Users],
    ['Students', data.student_count ?? 0, GraduationCap],
    ['Teachers', data.teacher_count ?? 0, BookOpen],
    ['Courses', data.course_count ?? 0, ClipboardCheck],
  ]
  const stats = user.role === 'student' ? studentStats : user.role === 'teacher' ? teacherStats : user.role === 'admin' ? adminStats : [
    ['Linked children', data.child_count ?? 0, Users],
    ['Unread notifications', data.unread_notifications ?? 0, Bell],
  ]

  return (
    <>
      <PageHeader eyebrow={`Welcome, ${roleNames[user.role] || 'learner'}`} title={`Good to see you, ${user.first_name || user.username}.`} description="Here is your current EDUCORE activity, based on your account and authorized records." />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map(([label, value, Icon]) => (
          <div key={label} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5">
            <div className="flex items-center justify-between"><p className="text-sm text-slate-400">{label}</p><Icon size={18} className="text-violet-300" /></div>
            <p className="mt-4 text-3xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>
      <div className="mt-7 grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
          <div className="flex items-center justify-between">
            <div><h2 className="text-lg font-bold text-white">{user.role === 'parent' ? 'Your children' : 'Your courses'}</h2><p className="mt-1 text-sm text-slate-400">Current records associated with your account.</p></div>
            <Link to={`${portalRoot}/${user.role === 'parent' ? 'children' : 'courses'}`} className="text-sm font-semibold text-violet-300 hover:text-violet-200">View all</Link>
          </div>
          {user.role === 'parent' ? <SimpleList items={data.children} empty="No student accounts are linked yet." name={(item) => [item.first_name, item.last_name].filter(Boolean).join(' ') || item.username} detail={(item) => item.email} /> : <CourseList items={data.courses} empty="No courses are linked to your account yet." />}
        </section>
        <section className="rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
          <div className="flex items-center gap-3"><span className="rounded-xl bg-emerald-500/10 p-2.5 text-emerald-300"><ShieldCheck size={19} /></span><h2 className="font-bold text-white">Your workspace</h2></div>
          <p className="mt-4 text-sm leading-6 text-slate-400">Your role determines what information and actions are available. Family and course records are restricted by server-side permissions.</p>
          <div className="mt-5 rounded-xl border border-slate-800 bg-slate-950/60 p-4 text-sm">
            <p className="text-slate-500">Signed in as</p>
            <p className="mt-1 font-semibold text-white">{user.email}</p>
          </div>
        </section>
      </div>
      {user.role === 'student' && <section className="mt-7 rounded-2xl border border-slate-800 bg-slate-900/65 p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-bold text-white">Upcoming assignments</h2><p className="mt-1 text-sm text-slate-400">Deadlines for your enrolled courses.</p></div><Link to={`${portalRoot}/assignments`} className="text-sm font-semibold text-violet-300">Open assignments</Link></div><AssignmentList items={data.upcoming_assignments || []} empty="No upcoming assignments." /></section>}
      {(user.role === 'teacher' || user.role === 'admin') && <section className="mt-7 rounded-2xl border border-violet-500/20 bg-violet-500/5 p-6"><div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="text-lg font-bold text-white">{user.role === 'admin' ? 'Administration workspace' : 'Teaching workspace'}</h2><p className="mt-1 text-sm text-slate-400">{user.role === 'admin' ? 'Manage user accounts and platform activity from the staff portal.' : 'Manage your courses, assignments, assessments, and learners.'}</p></div>{user.role === 'admin' ? <Link to={`${portalRoot}/accounts`} className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400">Manage accounts</Link> : <Link to={`${portalRoot}/courses`} className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400">Open my courses</Link>}</div></section>}
    </>
  )
}

function AdminAccountsPage() {
  const [users, setUsers] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const { register, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: { role: 'teacher', is_active: true },
  })

  const loadUsers = useCallback(async () => {
    const { data } = await api.get('/admin/users/', { params: search ? { search } : {} })
    setUsers(data.results || data)
  }, [search])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setLoading(true)
      loadUsers()
        .catch((requestError) => setError(errorMessage(requestError)))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadUsers])

  async function createUser(values) {
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await api.post('/admin/users/', values)
      await loadUsers()
      reset({ role: 'teacher', is_active: true, username: '', email: '', first_name: '', last_name: '', password: '' })
      setNotice('The account was created. The user can now sign in to the appropriate EDUCORE portal.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <PageHeader eyebrow="Administration" title="User management" description="Create student, parent, teacher, or administrator accounts without using the command line." />
      {error && <div className="mb-5"><ErrorState message={error} /></div>}
      {notice && <Notice message={notice} />}
      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <form onSubmit={handleSubmit(createUser)} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
          <h2 className="text-lg font-bold text-white">Create an account</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Username" error={errors.username?.message}><input autoComplete="off" {...register('username', { required: 'Enter a username.' })} /></Field>
            <Field label="Email" error={errors.email?.message}><input type="email" autoComplete="email" {...register('email', { required: 'Enter an email address.' })} /></Field>
            <Field label="First name"><input {...register('first_name')} /></Field>
            <Field label="Last name"><input {...register('last_name')} /></Field>
          </div>
          <Field label="Account role">
            <select {...register('role', { required: true })}>
              <option value="teacher">Teacher</option>
              <option value="admin">Administrator</option>
              <option value="student">Student</option>
              <option value="parent">Parent</option>
            </select>
          </Field>
          <Field label="Temporary password" error={errors.password?.message}>
            <input type="password" autoComplete="new-password" {...register('password', { required: 'Enter a temporary password.', minLength: { value: 12, message: 'Use at least 12 characters.' } })} />
            <small className="mt-1 block text-xs text-slate-500">Share this password with the new user through a private channel.</small>
          </Field>
          <button disabled={saving} className="rounded-xl bg-violet-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-violet-400 disabled:opacity-60">
            {saving ? 'Creating…' : 'Create account'}
          </button>
        </form>
        <section className="rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div><h2 className="text-lg font-bold text-white">Accounts</h2><p className="mt-1 text-sm text-slate-400">Search accounts by name, username, or email.</p></div>
            <input aria-label="Search accounts" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search accounts" className="w-full sm:max-w-56" />
          </div>
          {loading ? <LoadingState label="Loading accounts…" /> : !users.length ? (
            <p className="mt-5 rounded-xl border border-dashed border-slate-700 p-5 text-center text-sm text-slate-500">No accounts found.</p>
          ) : (
            <div className="mt-5 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-slate-500"><tr><th className="pb-3 pr-4">User</th><th className="pb-3 pr-4">Role</th><th className="pb-3">Status</th></tr></thead>
                <tbody className="divide-y divide-slate-800">
                  {users.map((account) => (
                    <tr key={account.id}>
                      <td className="py-3 pr-4"><p className="font-medium text-white">{[account.first_name, account.last_name].filter(Boolean).join(' ') || account.username}</p><p className="text-xs text-slate-500">{account.email}</p></td>
                      <td className="py-3 pr-4 capitalize text-slate-300">{roleNames[account.role] || account.role}</td>
                      <td className="py-3"><span className={account.is_active ? 'text-emerald-300' : 'text-rose-300'}>{account.is_active ? 'Active' : 'Inactive'}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </>
  )
}

function CoursesPage() {
  const { user } = useAuth()
  const [courses, setCourses] = useState([])
  const [subjects, setSubjects] = useState([])
  const [enrollments, setEnrollments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [creating, setCreating] = useState(false)
  const { register, handleSubmit, reset, formState: { errors } } = useForm()
  const canCreate = user.role === 'teacher' || user.role === 'admin'

  const load = useCallback(async () => {
    try {
      const requests = [api.get('/courses/'), api.get('/subjects/')]
      if (user.role === 'student') requests.push(api.get('/enrollments/'))
      const [courseResponse, subjectResponse, enrollmentResponse] = await Promise.all(requests)
      setCourses(courseResponse.data.results || courseResponse.data)
      setSubjects(subjectResponse.data.results || subjectResponse.data)
      setEnrollments(enrollmentResponse?.data.results || enrollmentResponse?.data || [])
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [user.role])

  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function createCourse(values) {
    setError('')
    setNotice('')
    try {
      const slug = values.title.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
      await api.post('/courses/', { ...values, slug })
      setNotice('Course created. An administrator can publish it when it is ready.')
      setCreating(false)
      reset()
      setLoading(true)
      load()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  async function enroll(courseId) {
    setError('')
    try {
      await api.post('/enrollments/', { course: courseId })
      setNotice('You are enrolled in this course.')
      setLoading(true)
      load()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  const enrolledIds = new Set(enrollments.map((item) => item.course))
  return (
    <>
      <PageHeader eyebrow="Learning" title={user.role === 'teacher' ? 'My courses' : 'Courses'} description="Explore course information and the courses available to your account." action={canCreate && <button onClick={() => setCreating(!creating)} className="inline-flex items-center justify-center gap-2 rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400"><Plus size={17} /> Create course</button>} />
      {notice && <Notice message={notice} />}
      {error && <ErrorState message={error} />}
      {creating && <form onSubmit={handleSubmit(createCourse)} className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/70 p-5 sm:grid-cols-2">
        <Field label="Course title" error={errors.title?.message}><input {...register('title', { required: 'Enter a course title.' })} /></Field>
        <Field label="Subject" error={errors.subject?.message}><select defaultValue="" {...register('subject', { required: 'Choose a subject.' })}><option value="" disabled>Select a subject</option>{subjects.map((subject) => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></Field>
        <Field label="Academic level"><input {...register('academic_level')} /></Field>
        <Field label="Description"><input {...register('description')} /></Field>
        <div className="flex items-center gap-3 sm:col-span-2"><button className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white">Save course</button><button type="button" onClick={() => setCreating(false)} className="rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-300">Cancel</button></div>
      </form>}
      {loading ? <LoadingState /> : <CourseCards items={courses} empty="No courses are available yet." enrolledIds={enrolledIds} onEnroll={user.role === 'student' ? enroll : undefined} />}
    </>
  )
}

function CourseCards({ items = [], empty, enrolledIds = new Set(), onEnroll }) {
  if (!items.length) return <EmptyState title="No courses yet" description={empty} />
  return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{items.map((course) => (
    <article key={course.id} className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/65">
      <div className="h-2 bg-gradient-to-r from-violet-500 via-indigo-500 to-sky-500" />
      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-violet-300">{course.subject_name || 'Course'}{course.academic_level ? ` · ${course.academic_level}` : ''}</p>
        <h2 className="mt-3 text-xl font-bold text-white">{course.title}</h2>
        <p className="mt-2 line-clamp-3 min-h-12 text-sm leading-6 text-slate-400">{course.description || 'Course information and learning materials will be available here.'}</p>
        <div className="mt-5 flex items-center justify-between border-t border-slate-800 pt-4 text-xs text-slate-500"><span>{course.teacher_name || 'EDUCORE educator'}</span><span>{course.enrollment_count ?? 0} learners</span></div>
        {onEnroll && (enrolledIds.has(course.id) ? <span className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-300"><CheckCircle2 size={16} /> Enrolled</span> : <button onClick={() => onEnroll(course.id)} className="mt-4 rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400">Enroll</button>)}
      </div>
    </article>
  ))}</div>
}

function LessonsPage() {
  const { user } = useAuth()
  const [lessons, setLessons] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [completed, setCompleted] = useState(new Set())

  useEffect(() => {
    Promise.all([api.get('/lessons/'), api.get('/lesson-progress/')])
      .then(([lessonResponse, progressResponse]) => {
        setLessons(lessonResponse.data.results || lessonResponse.data)
        setCompleted(new Set((progressResponse.data.results || progressResponse.data).filter((item) => item.completed_at).map((item) => item.lesson)))
      })
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false))
  }, [])

  async function markComplete(lesson) {
    try {
      await api.post('/lesson-progress/', { lesson: lesson.id, completed: true })
      setCompleted((current) => new Set([...current, lesson.id]))
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  return <><PageHeader eyebrow="Learning" title="Lessons" description="Continue course content available to your account." />{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !lessons.length ? <EmptyState title="No lessons available" description="Enroll in a course or check back when your teacher has published lessons." /> : <div className="space-y-3">{lessons.map((lesson) => <article key={lesson.id} className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 sm:flex-row sm:items-center"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-500/10 text-violet-200"><BookOpen size={20} /></div><div className="min-w-0 flex-1"><h2 className="font-semibold text-white">{lesson.title}</h2><p className="mt-1 line-clamp-2 text-sm text-slate-400">{lesson.content || 'Lesson resources will be shown here.'}</p></div>{user.role === 'student' && (completed.has(lesson.id) ? <span className="inline-flex items-center gap-2 text-sm text-emerald-300"><CheckCircle2 size={16} /> Completed</span> : <button onClick={() => markComplete(lesson)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-200 hover:border-violet-400">Mark complete</button>)}</article>)}</div>}</>
}

function AssignmentsPage() {
  const { user } = useAuth()
  const [items, setItems] = useState([])
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const isTeacher = user.role === 'teacher' || user.role === 'admin'
  const { register, handleSubmit, reset } = useForm()

  const load = useCallback(async () => {
    try {
      const responses = await Promise.all([api.get('/assignments/'), ...(isTeacher ? [api.get('/courses/')] : [])])
      setItems(responses[0].data.results || responses[0].data)
      if (isTeacher) setCourses(responses[1].data.results || responses[1].data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally { setLoading(false) }
  }, [isTeacher])

  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function createAssignment(values) {
    setError('')
    try {
      await api.post('/assignments/', { ...values, max_score: Number(values.max_score), due_at: new Date(values.due_at).toISOString() })
      setNotice('Assignment created.')
      reset()
      setLoading(true)
      load()
    } catch (requestError) { setError(errorMessage(requestError)) }
  }

  return <>
    <PageHeader eyebrow="Academic work" title="Assignments" description="Review assignment instructions, due dates, and submission status." />
    {notice && <Notice message={notice} />}{error && <ErrorState message={error} />}
    {isTeacher && <form onSubmit={handleSubmit(createAssignment)} className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 sm:grid-cols-2">
      <Field label="Course"><select required defaultValue="" {...register('course')}><option value="" disabled>Select course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></Field>
      <Field label="Title"><input required {...register('title')} /></Field>
      <Field label="Due date"><input required type="datetime-local" {...register('due_at')} /></Field>
      <Field label="Maximum score"><input type="number" min="1" max="100" defaultValue="100" {...register('max_score')} /></Field>
      <Field label="Instructions"><textarea rows="3" {...register('description')} /></Field>
      <div className="flex items-end"><button className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white">Create assignment</button></div>
    </form>}
    {loading ? <LoadingState /> : user.role === 'student' ? <StudentAssignmentList items={items} onSubmit={async (assignment, values) => {
      setError('')
      try { await api.post('/submissions/', { assignment, submission_text: values }); setNotice('Your assignment has been submitted.'); }
      catch (requestError) { setError(errorMessage(requestError)) }
    }} /> : <AssignmentList items={items} empty="No assignments are available." />}
  </>
}

function StudentAssignmentList({ items, onSubmit }) {
  const [drafts, setDrafts] = useState({})
  if (!items.length) return <EmptyState title="No assignments" description="Assignments for your courses will appear here." />
  return <div className="space-y-4">{items.map((assignment) => <article key={assignment.id} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-semibold uppercase tracking-wider text-violet-300">{assignment.course_title}</p><h2 className="mt-2 text-lg font-bold text-white">{assignment.title}</h2></div><time className="text-sm text-slate-400">{new Date(assignment.due_at).toLocaleString()}</time></div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-400">{assignment.description}</p><label className="mt-4 block text-sm font-medium text-slate-300">Your response<textarea rows="3" value={drafts[assignment.id] || ''} onChange={(event) => setDrafts({ ...drafts, [assignment.id]: event.target.value })} className="mt-2" /></label><button onClick={() => onSubmit(assignment.id, drafts[assignment.id] || '')} className="mt-3 rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400">Submit assignment</button></article>)}</div>
}

function SubmissionsPage() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [scores, setScores] = useState({})

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/submissions/')
      setItems(data.results || data)
    } catch (requestError) { setError(errorMessage(requestError)) }
    finally { setLoading(false) }
  }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])

  async function grade(submission) {
    try {
      await api.patch(`/submissions/${submission.id}/`, { score: Number(scores[submission.id]), feedback: '' })
      setError('')
      setLoading(true)
      load()
    } catch (requestError) { setError(errorMessage(requestError)) }
  }

  return <><PageHeader eyebrow="Teaching" title="Assignment submissions" description="Review student responses and record a score." />{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !items.length ? <EmptyState title="No submissions" description="Student submissions for your courses will appear here." /> : <div className="space-y-3">{items.map((item) => <article key={item.id} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><div className="flex flex-wrap justify-between gap-2"><h2 className="font-semibold text-white">{item.assignment}</h2><span className="text-sm text-slate-400">{item.student?.first_name || item.student?.username}</span></div><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-300">{item.submission_text || 'No written response.'}</p><div className="mt-4 flex flex-wrap items-end gap-3"><label className="text-sm text-slate-400">Score<input type="number" min="0" max="100" value={scores[item.id] ?? item.score ?? ''} onChange={(event) => setScores({ ...scores, [item.id]: event.target.value })} className="mt-1 block w-28" /></label><button onClick={() => grade(item)} className="rounded-lg bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400">Save grade</button></div></article>)}</div>}</>
}

function ExamsPage() {
  const { user } = useAuth()
  const canManage = user.role === 'teacher' || user.role === 'admin'
  const [exams, setExams] = useState([])
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [questionExam, setQuestionExam] = useState(null)
  const [activeExam, setActiveExam] = useState(null)
  const [answers, setAnswers] = useState({})
  const [result, setResult] = useState(null)
  const [now, setNow] = useState(() => Date.now())
  const examForm = useForm()
  const questionForm = useForm()

  const load = useCallback(async () => {
    try {
      const responses = await Promise.all([api.get('/exams/'), ...(canManage ? [api.get('/courses/')] : [])])
      setExams(responses[0].data.results || responses[0].data)
      if (canManage) setCourses(responses[1].data.results || responses[1].data)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoading(false)
    }
  }, [canManage])

  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), activeExam ? 1000 : 30000)
    return () => window.clearInterval(timer)
  }, [activeExam])

  async function createExam(values) {
    setError('')
    setNotice('')
    try {
      await api.post('/exams/', {
        ...values,
        starts_at: new Date(values.starts_at).toISOString(),
        ends_at: new Date(values.ends_at).toISOString(),
        duration_minutes: Number(values.duration_minutes),
        published: true,
      })
      setNotice('Examination scheduled and published. Add its questions before students begin.')
      examForm.reset()
      setLoading(true)
      load()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  async function addQuestion(values) {
    if (!questionExam) return
    setError('')
    try {
      const options = values.options.split('\n').map((option) => option.trim()).filter(Boolean)
      await api.post('/exam-questions/', {
        exam: questionExam.id,
        prompt: values.prompt,
        options,
        answer: values.answer,
        points: Number(values.points),
        order: questionExam.questions.length + 1,
      })
      setNotice('Question added to the examination.')
      questionForm.reset()
      setQuestionExam(null)
      setLoading(true)
      load()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  async function startExam(exam) {
    setError('')
    setResult(null)
    try {
      const { data: attempt } = await api.post(`/exams/${exam.id}/start/`, {})
      setAnswers({})
      setActiveExam({ ...exam, attempt_started_at: attempt.started_at })
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  async function submitExam() {
    if (!activeExam) return
    setError('')
    try {
      const { data } = await api.post(`/exams/${activeExam.id}/submit/`, { answers })
      setResult(data)
      setActiveExam(null)
      setLoading(true)
      load()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  const remainingSeconds = activeExam?.attempt_started_at
    ? Math.max(
      0,
      Math.ceil(
        (Date.parse(activeExam.attempt_started_at) + activeExam.duration_minutes * 60000 - now) / 1000,
      ),
    )
    : 0
  return <>
    <PageHeader eyebrow="Assessment" title="Examinations" description="View scheduled examinations, prepare assessments, and review completed scores." />
    {notice && <Notice message={notice} />}{error && <ErrorState message={error} />}
    {result && <div role="status" className="mb-5 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-4 text-emerald-200">Examination submitted. Score: {result.score}%</div>}
    {canManage && <form onSubmit={examForm.handleSubmit(createExam)} className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 md:grid-cols-2">
      <div className="md:col-span-2"><h2 className="font-bold text-white">Schedule an examination</h2></div>
      <Field label="Course"><select required defaultValue="" {...examForm.register('course')}><option value="" disabled>Select a course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></Field>
      <Field label="Title"><input required {...examForm.register('title')} /></Field>
      <Field label="Starts at"><input required type="datetime-local" {...examForm.register('starts_at')} /></Field>
      <Field label="Ends at"><input required type="datetime-local" {...examForm.register('ends_at')} /></Field>
      <Field label="Duration (minutes)"><input required type="number" min="1" max="600" defaultValue="60" {...examForm.register('duration_minutes')} /></Field>
      <Field label="Instructions"><textarea rows="2" {...examForm.register('instructions')} /></Field>
      <div className="md:col-span-2"><button className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-400">Schedule exam</button></div>
    </form>}
    {loading ? <LoadingState /> : !exams.length ? <EmptyState title="No examinations" description="Scheduled examinations available to your account will appear here." /> : <div className="space-y-4">{exams.map((exam) => {
      const starts = new Date(exam.starts_at).getTime()
      const ends = new Date(exam.ends_at).getTime()
      const available = exam.published && now >= starts && now <= ends
      return <article key={exam.id} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><p className="text-xs font-semibold uppercase tracking-wider text-violet-300">{exam.course_title}</p><h2 className="mt-2 text-lg font-bold text-white">{exam.title}</h2><p className="mt-2 text-sm text-slate-400">{exam.instructions || 'Read each question carefully before submitting.'}</p></div>
          <div className="text-right text-sm text-slate-400"><p>{new Date(exam.starts_at).toLocaleString()}</p><p className="mt-1">{exam.duration_minutes} minutes · {exam.questions.length} questions</p></div>
        </div>
        {canManage ? <div className="mt-4">{questionExam?.id === exam.id ? <form onSubmit={questionForm.handleSubmit(addQuestion)} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 md:grid-cols-2">
          <Field label="Question"><textarea required rows="2" {...questionForm.register('prompt')} /></Field>
          <Field label="Correct answer"><input required {...questionForm.register('answer')} /></Field>
          <Field label="Choices (one per line)"><textarea rows="3" {...questionForm.register('options')} /></Field>
          <Field label="Points"><input type="number" min="1" defaultValue="1" {...questionForm.register('points')} /></Field>
          <div className="flex gap-2 md:col-span-2"><button className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white">Add question</button><button type="button" onClick={() => setQuestionExam(null)} className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300">Cancel</button></div>
        </form> : <button onClick={() => setQuestionExam(exam)} className="mt-4 rounded-lg border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 hover:border-violet-400">Add question</button>}</div> : <button disabled={!available || !exam.questions.length} onClick={() => startExam(exam)} className="mt-4 rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-40">{!exam.questions.length ? 'Questions not available' : available ? 'Start examination' : now < starts ? 'Not yet open' : 'Closed'}</button>}
      </article>
    })}</div>}
    {activeExam && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <section role="dialog" aria-modal="true" aria-labelledby="active-exam-title" className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-950 p-6">
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs uppercase tracking-wider text-violet-300">Timed examination</p><h2 id="active-exam-title" className="mt-2 text-xl font-bold text-white">{activeExam.title}</h2></div><button aria-label="Close examination" onClick={() => setActiveExam(null)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800"><X size={18} /></button></div>
        <p className="mt-2 flex items-center gap-2 text-sm text-slate-400"><TimerReset size={16} /> Time remaining: {Math.floor(remainingSeconds / 60)}:{String(remainingSeconds % 60).padStart(2, '0')}</p>
        {remainingSeconds === 0 && <p role="alert" className="mt-3 rounded-lg bg-rose-500/10 p-3 text-sm text-rose-200">The time limit has expired. Your answers can no longer be submitted.</p>}
        <div className="mt-5 space-y-5">{activeExam.questions.map((question, index) => <fieldset key={question.id} className="rounded-xl border border-slate-800 p-4"><legend className="px-2 text-sm font-semibold text-white">{index + 1}. {question.prompt} ({question.points} points)</legend>{question.options?.length ? <select aria-label={`Answer question ${index + 1}`} value={answers[String(question.id)] ?? ''} onChange={(event) => setAnswers({ ...answers, [String(question.id)]: event.target.value })}><option value="" disabled>Select an answer</option>{question.options.map((option) => <option key={option} value={option}>{option}</option>)}</select> : <input aria-label={`Answer question ${index + 1}`} value={answers[String(question.id)] ?? ''} onChange={(event) => setAnswers({ ...answers, [String(question.id)]: event.target.value })} />}</fieldset>)}</div>
        <div className="mt-6 flex justify-end"><button disabled={remainingSeconds === 0 || activeExam.questions.some((question) => answers[String(question.id)] === undefined)} onClick={submitExam} className="rounded-xl bg-violet-500 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40">Submit examination</button></div>
      </section>
    </div>}
  </>
}

function GradesPage() {
  const [grades, setGrades] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    api.get('/grades/')
      .then(({ data }) => setGrades(data.results || data))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false))
  }, [])
  const average = grades.length ? (grades.reduce((sum, grade) => sum + Number(grade.score), 0) / grades.length).toFixed(1) : null
  return <><PageHeader eyebrow="Academic record" title="Grades" description="Review scores recorded for your own courses or the courses you are authorized to manage." />{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !grades.length ? <EmptyState title="No grades yet" description="Grades will appear here after an assignment, quiz, or examination has been assessed." /> : <><div className="mb-5 rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><p className="text-sm text-slate-400">Average across listed records</p><p className="mt-2 text-3xl font-bold text-white">{average}%</p></div><div className="overflow-hidden rounded-2xl border border-slate-800"><div className="grid grid-cols-2 gap-3 bg-slate-900 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-slate-500 sm:grid-cols-5"><span>Assessment</span><span>Course</span><span>Learner</span><span>Score</span><span>Date</span></div>{grades.map((grade) => <div key={grade.id} className="grid grid-cols-2 gap-3 border-t border-slate-800 bg-slate-900/40 px-4 py-4 text-sm sm:grid-cols-5"><span className="capitalize text-slate-200">{grade.source_type}</span><span className="text-slate-300">{grade.course_title}</span><span className="text-slate-400">{grade.student_name}</span><span className="font-semibold text-white">{grade.score}%</span><time className="text-slate-500">{new Date(grade.graded_at).toLocaleDateString()}</time>{grade.feedback && <p className="col-span-2 text-slate-400 sm:col-span-5">{grade.feedback}</p>}</div>)}</div></>}</>
}

function AttendancePage() {
  const { user } = useAuth()
  const canManage = user.role === 'teacher' || user.role === 'admin'
  const [records, setRecords] = useState([])
  const [courses, setCourses] = useState([])
  const [enrollments, setEnrollments] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [courseId, setCourseId] = useState('')
  const [today] = useState(() => new Date().toLocaleDateString('en-CA'))
  const { register, handleSubmit, reset } = useForm()
  const load = useCallback(async () => {
    try {
      const requests = [api.get('/attendance/')]
      if (canManage) requests.push(api.get('/courses/'), api.get('/enrollments/'))
      const [recordResponse, courseResponse, enrollmentResponse] = await Promise.all(requests)
      setRecords(recordResponse.data.results || recordResponse.data)
      if (canManage) {
        setCourses(courseResponse.data.results || courseResponse.data)
        setEnrollments(enrollmentResponse.data.results || enrollmentResponse.data)
      }
    } catch (requestError) { setError(errorMessage(requestError)) }
    finally { setLoading(false) }
  }, [canManage])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  const roster = enrollments.filter((enrollment) => String(enrollment.course) === String(courseId) && enrollment.student)
  async function recordAttendance(values) {
    setError('')
    try {
      await api.post('/attendance/', { ...values, course: Number(values.course), student: Number(values.student) })
      setNotice('Attendance record saved.')
      reset()
      setCourseId('')
      setLoading(true)
      load()
    } catch (requestError) { setError(errorMessage(requestError)) }
  }
  return <><PageHeader eyebrow="Academic record" title="Attendance" description="View attendance records, or record attendance for a course you teach." />{notice && <Notice message={notice} />}{error && <ErrorState message={error} />}
    {canManage && <form onSubmit={handleSubmit(recordAttendance)} className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 sm:grid-cols-2">
      <Field label="Course"><select required value={courseId} {...register('course', { required: true, onChange: (event) => setCourseId(event.target.value) })}><option value="" disabled>Select course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></Field>
      <Field label="Student"><select required disabled={!courseId} defaultValue="" {...register('student', { required: true })}><option value="" disabled>Select student</option>{roster.map((item) => <option key={item.student.id} value={item.student.id}>{[item.student.first_name, item.student.last_name].filter(Boolean).join(' ') || item.student.username}</option>)}</select></Field>
      <Field label="Date"><input required type="date" defaultValue={today} {...register('date')} /></Field>
      <Field label="Status"><select defaultValue="present" {...register('status')}><option value="present">Present</option><option value="absent">Absent</option><option value="late">Late</option><option value="excused">Excused</option></select></Field>
      <div className="sm:col-span-2"><button className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white">Save attendance</button></div>
    </form>}
    {loading ? <LoadingState /> : !records.length ? <EmptyState title="No attendance records" description="Attendance recorded for your account or classes will be shown here." /> : <div className="space-y-3">{records.map((record) => <article key={record.id} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-800 bg-slate-900/65 p-4"><div><p className="font-semibold text-white">{record.student_name} · {record.course_title}</p><p className="mt-1 text-sm text-slate-400">{new Date(`${record.date}T00:00:00`).toLocaleDateString()}{record.note ? ` · ${record.note}` : ''}</p></div><span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${record.status === 'present' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-amber-500/10 text-amber-200'}`}>{record.status}</span></article>)}</div>}
  </>
}

function CalendarPage() {
  const { user } = useAuth()
  const canManage = user.role === 'teacher' || user.role === 'admin'
  const [events, setEvents] = useState([])
  const [courses, setCourses] = useState([])
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const { register, handleSubmit, reset } = useForm()
  const load = useCallback(async () => {
    try {
      const requests = [api.get('/calendar/')]
      if (canManage) requests.push(api.get('/courses/'))
      const [eventResponse, courseResponse] = await Promise.all(requests)
      setEvents(eventResponse.data.results || eventResponse.data)
      if (canManage) setCourses(courseResponse.data.results || courseResponse.data)
    } catch (requestError) { setError(errorMessage(requestError)) }
    finally { setLoading(false) }
  }, [canManage])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  async function createEvent(values) {
    setError('')
    try {
      await api.post('/calendar/', {
        ...values,
        course: values.course ? Number(values.course) : null,
        starts_at: new Date(values.starts_at).toISOString(),
        ends_at: new Date(values.ends_at).toISOString(),
      })
      setNotice('Calendar event created.')
      reset()
      setLoading(true)
      load()
    } catch (requestError) { setError(errorMessage(requestError)) }
  }
  return <><PageHeader eyebrow="Planning" title="Academic calendar" description="See events associated with your account and authorized courses." />{notice && <Notice message={notice} />}{error && <ErrorState message={error} />}
    {canManage && <form onSubmit={handleSubmit(createEvent)} className="mb-6 grid gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 md:grid-cols-2">
      <Field label="Title"><input required {...register('title')} /></Field>
      <Field label="Event type"><select defaultValue="course" {...register('event_type')}><option value="course">Course</option><option value="exam">Examination</option><option value="assignment">Assignment</option><option value="school">School event</option></select></Field>
      <Field label="Course (optional for administrators)"><select defaultValue="" {...register('course')}><option value="">No course / platform event</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></Field>
      <Field label="Description"><input {...register('description')} /></Field>
      <Field label="Starts at"><input required type="datetime-local" {...register('starts_at')} /></Field>
      <Field label="Ends at"><input required type="datetime-local" {...register('ends_at')} /></Field>
      <div className="md:col-span-2"><button className="rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white">Add calendar event</button></div>
    </form>}
    {loading ? <LoadingState /> : !events.length ? <EmptyState title="No calendar events" description="Events from your courses and school will appear here." /> : <div className="space-y-3">{events.map((event) => <article key={event.id} className="flex gap-4 rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><div className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-xl bg-violet-500/10 text-violet-200"><span className="text-xs uppercase">{new Date(event.starts_at).toLocaleString(undefined, { month: 'short' })}</span><span className="text-lg font-bold">{new Date(event.starts_at).getDate()}</span></div><div><p className="text-xs font-semibold uppercase tracking-wider text-violet-300">{event.event_type}{event.course_title ? ` · ${event.course_title}` : ''}</p><h2 className="mt-1 font-bold text-white">{event.title}</h2><p className="mt-1 text-sm text-slate-400">{new Date(event.starts_at).toLocaleString()} – {new Date(event.ends_at).toLocaleTimeString()}</p>{event.description && <p className="mt-2 text-sm text-slate-400">{event.description}</p>}</div></article>)}</div>}
  </>
}

function MessagesPage() {
  const { user } = useAuth()
  const [conversations, setConversations] = useState([])
  const [messages, setMessages] = useState([])
  const [courses, setCourses] = useState([])
  const [contacts, setContacts] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [courseId, setCourseId] = useState('')
  const [recipientId, setRecipientId] = useState('')
  const [draft, setDraft] = useState('')
  const [composing, setComposing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const loadConversations = useCallback(async () => {
    const { data } = await api.get('/conversations/')
    setConversations(data.results || data)
  }, [])

  useEffect(() => {
    Promise.all([api.get('/conversations/'), api.get('/courses/')])
      .then(([conversationResponse, courseResponse]) => {
        const items = conversationResponse.data.results || conversationResponse.data
        setConversations(items)
        setCourses(courseResponse.data.results || courseResponse.data)
        setSelectedId((current) => current || items[0]?.id || null)
      })
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (!courseId) return
    let active = true
    api.get('/message-contacts/', { params: { course: courseId } })
      .then(({ data }) => { if (active) setContacts(data) })
      .catch((requestError) => { if (active) setError(errorMessage(requestError)) })
    return () => { active = false }
  }, [courseId])

  useEffect(() => {
    if (!selectedId) return
    let active = true
    const loadMessages = async () => {
      try {
        const { data } = await api.get(`/conversations/${selectedId}/messages/`)
        if (active) setMessages(data.results || data)
      } catch (requestError) {
        if (active) setError(errorMessage(requestError))
      }
    }
    loadMessages()
    const timer = window.setInterval(loadMessages, 10000)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [selectedId])

  async function startConversation(event) {
    event.preventDefault()
    setError('')
    try {
      const { data } = await api.post('/conversations/', {
        course: Number(courseId),
        recipient: Number(recipientId),
      })
      await loadConversations()
      setMessages([])
      setSelectedId(data.id)
      setComposing(false)
      setCourseId('')
      setRecipientId('')
      setNotice('Conversation started.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  async function sendMessage(event) {
    event.preventDefault()
    if (!selectedId || !draft.trim()) return
    setError('')
    try {
      const { data } = await api.post(`/conversations/${selectedId}/messages/`, { body: draft })
      setMessages((current) => [...current, data])
      setDraft('')
      await loadConversations()
    } catch (requestError) {
      setError(errorMessage(requestError))
    }
  }

  const selected = conversations.find((conversation) => conversation.id === selectedId)
  const otherParticipants = selected?.participants.filter((participant) => participant.id !== user.id) || []
  return <>
    <PageHeader eyebrow="Communication" title="Messages" description="Private conversations with people connected to your courses." action={!composing && <button onClick={() => setComposing(true)} className="inline-flex items-center gap-2 rounded-xl bg-violet-500 px-4 py-2.5 text-sm font-semibold text-white"><Plus size={16} /> New conversation</button>} />
    {notice && <Notice message={notice} />}{error && <ErrorState message={error} />}
    {composing && <form onSubmit={startConversation} className="mb-5 grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/65 p-5 sm:grid-cols-2">
      <Field label="Course"><select required value={courseId} onChange={(event) => { setContacts([]); setCourseId(event.target.value); setRecipientId('') }}><option value="" disabled>Select a course</option>{courses.map((course) => <option key={course.id} value={course.id}>{course.title}</option>)}</select></Field>
      <Field label="Contact"><select required disabled={!courseId} value={recipientId} onChange={(event) => setRecipientId(event.target.value)}><option value="" disabled>Select a contact</option>{contacts.map((contact) => <option key={contact.id} value={contact.id}>{[contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.username} · {roleNames[contact.role]}</option>)}</select></Field>
      <div className="flex gap-2 sm:col-span-2"><button disabled={!recipientId} className="rounded-lg bg-violet-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40">Start conversation</button><button type="button" onClick={() => setComposing(false)} className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300">Cancel</button></div>
    </form>}
    {loading ? <LoadingState /> : <div className="grid min-h-[30rem] overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/55 md:grid-cols-[16rem_1fr]">
      <aside className="border-b border-slate-800 md:border-b-0 md:border-r">
        <div className="border-b border-slate-800 p-4"><h2 className="font-semibold text-white">Conversations</h2></div>
        {!conversations.length ? <p className="p-4 text-sm text-slate-500">No conversations yet.</p> : conversations.map((conversation) => {
          const names = conversation.participants.filter((participant) => participant.id !== user.id).map((participant) => participant.first_name || participant.username).join(', ')
          return <button key={conversation.id} onClick={() => { setMessages([]); setSelectedId(conversation.id) }} className={`block w-full border-b border-slate-800/70 p-4 text-left transition ${selectedId === conversation.id ? 'bg-violet-500/10' : 'hover:bg-slate-800/60'}`}><p className="truncate text-sm font-semibold text-white">{names || conversation.title}</p><p className="mt-1 truncate text-xs text-slate-500">{conversation.course_title}</p><p className="mt-1 truncate text-xs text-slate-600">{conversation.title}</p></button>
        })}
      </aside>
      <section className="flex min-h-[30rem] min-w-0 flex-col">
        {selected ? <>
          <header className="border-b border-slate-800 p-4"><h2 className="font-semibold text-white">{otherParticipants.map((participant) => [participant.first_name, participant.last_name].filter(Boolean).join(' ') || participant.username).join(', ')}</h2><p className="mt-1 text-xs text-slate-500">{selected.course_title}</p></header>
          <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">{messages.map((message) => <div key={message.id} className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${message.sender.id === user.id ? 'ml-auto bg-violet-500/20 text-violet-50' : 'bg-slate-800 text-slate-200'}`}><p className="mb-1 text-xs font-semibold opacity-70">{message.sender.first_name || message.sender.username}</p><p className="whitespace-pre-wrap break-words">{message.body}</p><time className="mt-2 block text-right text-[10px] opacity-50">{new Date(message.sent_at).toLocaleString()}</time></div>)}</div>
          <form onSubmit={sendMessage} className="flex items-end gap-3 border-t border-slate-800 p-4"><label className="sr-only" htmlFor="message-draft">Message</label><textarea id="message-draft" required maxLength="5000" rows="2" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Write a message…" className="mt-0 resize-y" /><button disabled={!draft.trim()} className="shrink-0 rounded-xl bg-violet-500 px-4 py-3 text-sm font-semibold text-white disabled:opacity-40">Send</button></form>
        </> : <div className="flex flex-1 flex-col items-center justify-center p-8 text-center"><FileText size={28} className="text-slate-600" /><p className="mt-3 font-semibold text-white">Select a conversation</p><p className="mt-1 text-sm text-slate-500">Or start a new conversation with a course contact.</p></div>}
      </section>
    </div>}
  </>
}

function LibraryPage() {
  const [books, setBooks] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    const timer = window.setTimeout(() => {
      api.get('/books/', { params: search ? { search } : {} })
        .then(({ data }) => setBooks(data.results || data))
        .catch((requestError) => setError(errorMessage(requestError)))
        .finally(() => setLoading(false))
    }, 250)
    return () => window.clearTimeout(timer)
  }, [search])
  return <><PageHeader eyebrow="Resources" title="Digital library" description="Search learning resources made available to EDUCORE accounts." /><label className="mb-6 flex max-w-xl items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 px-4"><Search size={18} className="text-slate-500" /><input aria-label="Search books" value={search} onChange={(event) => { setLoading(true); setSearch(event.target.value) }} placeholder="Search by title, author, or subject" className="border-0 bg-transparent px-0 focus:ring-0" /></label>{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !books.length ? <EmptyState title="No books found" description="Try another search or return later when resources have been added." /> : <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{books.map((book) => <article key={book.id} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><div className="flex gap-4"><div className="flex h-24 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-slate-800">{book.cover_url ? <img src={book.cover_url} alt="" className="h-full w-full object-cover" /> : <Library className="text-violet-300" />}</div><div><p className="text-xs uppercase tracking-wider text-violet-300">{book.subject_name}</p><h2 className="mt-2 font-bold text-white">{book.title}</h2><p className="mt-1 text-sm text-slate-400">{book.author}</p></div></div><p className="mt-4 line-clamp-3 text-sm leading-6 text-slate-400">{book.description}</p>{book.resource_url && <a href={book.resource_url} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-violet-300 hover:text-violet-200">Open resource <ArrowRight size={15} /></a>}</article>)}</div>}</>
}

function NotificationsPage() {
  const [items, setItems] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    try { const { data } = await api.get('/notifications/'); setItems(data.results || data) }
    catch (requestError) { setError(errorMessage(requestError)) }
    finally { setLoading(false) }
  }, [])
  useEffect(() => {
    const timer = window.setTimeout(() => { void load() }, 0)
    return () => window.clearTimeout(timer)
  }, [load])
  async function markRead(id) {
    try { await api.post(`/notifications/${id}/read/`); load() }
    catch (requestError) { setError(errorMessage(requestError)) }
  }
  return <><PageHeader eyebrow="Updates" title="Notifications" description="Important messages and updates for your account." />{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !items.length ? <EmptyState title="You're all caught up" description="New notifications will appear here." /> : <div className="space-y-3">{items.map((item) => <article key={item.id} className={`rounded-2xl border p-5 ${item.read_at ? 'border-slate-800 bg-slate-900/50' : 'border-violet-500/30 bg-violet-500/5'}`}><div className="flex items-start justify-between gap-4"><div><p className="font-semibold text-white">{item.title}</p><p className="mt-2 text-sm leading-6 text-slate-400">{item.message}</p><time className="mt-3 block text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</time></div>{!item.read_at && <button onClick={() => markRead(item.id)} className="shrink-0 rounded-lg border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-300 hover:border-violet-400">Mark read</button>}</div></article>)}</div>}</>
}

function ChildrenPage() {
  const [children, setChildren] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    api.get('/parent/children/')
      .then(({ data }) => setChildren(data))
      .catch((requestError) => setError(errorMessage(requestError)))
      .finally(() => setLoading(false))
  }, [])
  return <><PageHeader eyebrow="Family" title="My children" description="Only students explicitly linked to your account are shown." />{error && <ErrorState message={error} />}{loading ? <LoadingState /> : !children.length ? <EmptyState title="No linked students" description="Ask an EDUCORE administrator to connect a student account to your parent account." /> : <div className="grid gap-4 md:grid-cols-2">{children.map(({ id, student, relationship }) => <article key={id} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-5"><div className="flex items-center gap-4"><span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15 text-violet-200"><Users size={20} /></span><div><h2 className="font-bold text-white">{[student.first_name, student.last_name].filter(Boolean).join(' ') || student.username}</h2><p className="text-sm text-slate-400">{student.email}</p></div></div>{relationship && <p className="mt-4 text-sm text-slate-500">Relationship: {relationship}</p>}</article>)}</div>}</>
}

function ProfilePage() {
  const { user, refreshUser } = useAuth()
  const [firstName, setFirstName] = useState(user.first_name || '')
  const [lastName, setLastName] = useState(user.last_name || '')
  const [avatarKey, setAvatarKey] = useState(user.avatar_key || 'aurora')
  const [photos, setPhotos] = useState([])
  const [selectedImage, setSelectedImage] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [photoAction, setPhotoAction] = useState('')
  useEffect(() => () => {
    if (selectedImage?.url) URL.revokeObjectURL(selectedImage.url)
  }, [selectedImage])

  const loadPhotos = useCallback(async () => {
    const { data } = await api.get('/profile/photos/')
    setPhotos(data)
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      loadPhotos()
        .catch((requestError) => setError(errorMessage(requestError)))
        .finally(() => setLoading(false))
    }, 0)
    return () => window.clearTimeout(timer)
  }, [loadPhotos])

  async function saveProfile(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      await api.patch('/auth/me/', {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        avatar_key: avatarKey,
      })
      await refreshUser()
      setNotice('Your profile has been updated.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  async function uploadPhoto(event) {
    event.preventDefault()
    if (!selectedImage?.file) {
      setError('Choose an image before uploading.')
      return
    }
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(selectedImage.file.type)) {
      setError('Choose a JPEG, PNG, or WebP image.')
      return
    }
    if (selectedImage.file.size > 5 * 1024 * 1024) {
      setError('Choose an image smaller than 5 MB.')
      return
    }
    const body = new FormData()
    body.append('image', selectedImage.file)
    setPhotoAction('upload')
    setError('')
    setNotice('')
    try {
      await api.post('/profile/photos/', body)
      await Promise.all([refreshUser(), loadPhotos()])
      setSelectedImage(null)
      setNotice('Your photo has been uploaded and selected.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setPhotoAction('')
    }
  }

  async function selectPhoto(photoId) {
    setPhotoAction(`select-${photoId}`)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post(`/profile/photos/${photoId}/select/`)
      await refreshUser()
      setPhotos((current) => current.map((photo) => ({ ...photo, is_current: photo.id === photoId })))
      if (data.profile_photo_url) setNotice('Your saved photo is now selected.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setPhotoAction('')
    }
  }

  async function deletePhoto(photoId) {
    setPhotoAction(`delete-${photoId}`)
    setError('')
    setNotice('')
    try {
      await api.delete(`/profile/photos/${photoId}/`)
      await Promise.all([refreshUser(), loadPhotos()])
      setNotice('The saved photo has been deleted.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setPhotoAction('')
    }
  }

  return (
    <>
      <PageHeader eyebrow="Account" title="Profile & avatar" description="Update your details, choose a preset avatar, or manage your profile photos." />
      {error && <div className="mb-5"><ErrorState message={error} /></div>}
      {notice && <Notice message={notice} />}
      <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <form onSubmit={saveProfile} className="space-y-6 rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
          <div className="flex items-center gap-4">
            <ProfileAvatar user={user} size="h-16 w-16" />
            <div><h2 className="font-semibold text-white">Your account</h2><p className="text-sm text-slate-400">{user.email}</p></div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="First name"><input autoComplete="given-name" value={firstName} onChange={(event) => setFirstName(event.target.value)} maxLength={150} /></Field>
            <Field label="Last name"><input autoComplete="family-name" value={lastName} onChange={(event) => setLastName(event.target.value)} maxLength={150} /></Field>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Choose a preset avatar</h3>
            <div className="mt-3 grid grid-cols-4 gap-3">
              {avatarPresets.map(({ id, label, icon: Icon, colors }) => (
                <button
                  key={id}
                  type="button"
                  aria-label={`Choose ${label} avatar`}
                  aria-pressed={avatarKey === id}
                  onClick={() => setAvatarKey(id)}
                  className={`flex flex-col items-center gap-2 rounded-xl border p-3 text-xs transition ${avatarKey === id ? 'border-violet-400 bg-violet-500/10 text-white' : 'border-slate-800 text-slate-400 hover:border-slate-600'}`}
                >
                  <span className={`flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br ${colors} text-white`}><Icon size={21} /></span>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <button disabled={saving} className="rounded-xl bg-violet-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-60">
            {saving ? 'Saving…' : 'Save profile'}
          </button>
        </form>

        <div className="space-y-6">
          <form onSubmit={uploadPhoto} className="rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
            <div className="flex items-center gap-3">
              <span className="rounded-xl bg-violet-500/15 p-2.5 text-violet-200"><ImagePlus size={20} /></span>
              <div><h2 className="font-semibold text-white">Upload a profile photo</h2><p className="text-sm text-slate-400">JPEG, PNG, or WebP · maximum 5 MB</p></div>
            </div>
            <div className="mt-5 flex flex-wrap items-center gap-4">
              <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-semibold text-slate-200 transition hover:border-violet-400">
                <Upload size={16} /> Choose image
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="sr-only"
                  onChange={(event) => {
                    const file = event.target.files?.[0]
                    setSelectedImage(file ? { file, url: URL.createObjectURL(file) } : null)
                    event.target.value = ''
                  }}
                />
              </label>
              {selectedImage && <span className="max-w-56 truncate text-sm text-slate-400">{selectedImage.file.name}</span>}
            </div>
            {selectedImage?.url && <img src={selectedImage.url} alt="Selected photo preview" className="mt-4 h-24 w-24 rounded-2xl border border-slate-700 object-cover" />}
            <button disabled={!selectedImage || photoAction === 'upload'} className="mt-5 rounded-xl bg-violet-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet-400 disabled:cursor-not-allowed disabled:opacity-50">
              {photoAction === 'upload' ? 'Uploading…' : 'Upload and use photo'}
            </button>
          </form>

          <section className="rounded-2xl border border-slate-800 bg-slate-900/65 p-6">
            <h2 className="font-semibold text-white">Your saved photos</h2>
            <p className="mt-1 text-sm text-slate-400">Select a previous photo or delete one you no longer need.</p>
            {loading ? <LoadingState label="Loading your photos…" /> : !photos.length ? (
              <p className="mt-5 rounded-xl border border-dashed border-slate-700 p-5 text-center text-sm text-slate-500">Your uploaded photos will appear here.</p>
            ) : (
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                {photos.map((photo) => (
                  <article key={photo.id} className={`flex items-center gap-3 rounded-xl border p-3 ${photo.is_current ? 'border-violet-400/50 bg-violet-500/5' : 'border-slate-800'}`}>
                    <img src={photo.url} alt="Saved profile" className="h-14 w-14 rounded-xl object-cover" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-white">{photo.is_current ? 'Current photo' : new Date(photo.uploaded_at).toLocaleDateString()}</p>
                      <div className="mt-2 flex gap-3">
                        {!photo.is_current && <button disabled={Boolean(photoAction)} onClick={() => selectPhoto(photo.id)} className="text-xs font-semibold text-violet-300 hover:text-violet-200 disabled:opacity-50">{photoAction === `select-${photo.id}` ? 'Selecting…' : 'Use photo'}</button>}
                        <button disabled={Boolean(photoAction)} onClick={() => deletePhoto(photo.id)} aria-label="Delete saved photo" className="inline-flex items-center gap-1 text-xs font-semibold text-rose-300 hover:text-rose-200 disabled:opacity-50">{photoAction === `delete-${photo.id}` ? 'Deleting…' : <><Trash2 size={13} /> Delete</>}</button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </div>
      </section>
    </>
  )
}

function AssignmentList({ items, empty }) {
  if (!items?.length) return <p className="mt-6 text-sm text-slate-500">{empty}</p>
  return <div className="mt-5 divide-y divide-slate-800">{items.map((assignment) => <div key={assignment.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><p className="font-semibold text-white">{assignment.title}</p><p className="mt-1 text-sm text-slate-400">{assignment.course_title}</p></div><time className="text-sm text-slate-400">{new Date(assignment.due_at).toLocaleDateString()}</time></div>)}</div>
}

function CourseList({ items, empty }) {
  if (!items?.length) return <p className="mt-6 text-sm text-slate-500">{empty}</p>
  return <div className="mt-5 divide-y divide-slate-800">{items.slice(0, 5).map((course) => <div key={course.id} className="py-4"><p className="font-semibold text-white">{course.title}</p><p className="mt-1 text-sm text-slate-400">{course.subject_name} {course.academic_level && `· ${course.academic_level}`}</p></div>)}</div>
}

function SimpleList({ items = [], empty, name, detail }) {
  if (!items.length) return <p className="mt-6 text-sm text-slate-500">{empty}</p>
  return <div className="mt-5 divide-y divide-slate-800">{items.map((item) => <div key={item.id} className="py-4"><p className="font-semibold text-white">{name(item)}</p><p className="mt-1 text-sm text-slate-400">{detail(item)}</p></div>)}</div>
}

function Notice({ message }) {
  return <p role="status" className="mb-5 rounded-xl border border-emerald-400/20 bg-emerald-400/10 p-3 text-sm text-emerald-200">{message}</p>
}

function EmptyState({ title, description }) {
  return <div className="rounded-2xl border border-dashed border-slate-700 bg-slate-900/30 px-6 py-14 text-center"><span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800 text-slate-400"><BookOpen size={20} /></span><h2 className="mt-4 font-semibold text-white">{title}</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-400">{description}</p></div>
}

function EmptyPage({ title, description }) {
  return <><PageHeader title={title} description={description} /><Link to="/app" className="inline-flex items-center gap-2 text-sm font-semibold text-violet-300"><ArrowLeft size={16} /> Back to overview</Link></>
}

function ErrorState({ message }) {
  return <div role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/10 p-4 text-sm text-rose-200">{message}</div>
}

function LoadingState({ label = 'Loading…' }) {
  return <div className="flex min-h-36 items-center justify-center gap-3 text-sm text-slate-400"><span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-700 border-t-violet-400" />{label}</div>
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<PublicHome />} />
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route path="/staff/login" element={<AuthPage mode="login" staffOnly />} />
      <Route path="/staff" element={<ProtectedStaffRoute />}>
        <Route index element={<StaffHomeRedirect />} />
        <Route path="teacher" element={<StaffDashboardRoute role="teacher" />} />
        <Route path="admin" element={<StaffDashboardRoute role="admin" />} />
        <Route path="courses" element={<CoursesPage />} />
        <Route path="lessons" element={<LessonsPage />} />
        <Route path="assignments" element={<AssignmentsPage />} />
        <Route path="exams" element={<ExamsPage />} />
        <Route path="submissions" element={<SubmissionsPage />} />
        <Route path="grades" element={<GradesPage />} />
        <Route path="attendance" element={<AttendancePage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="messages" element={<MessagesPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="accounts" element={<AdminOnlyRoute><AdminAccountsPage /></AdminOnlyRoute>} />
        <Route path="*" element={<EmptyPage title="Page not found" description="This staff portal page is not available." />} />
      </Route>
      <Route path="/app" element={<ProtectedRoute />}>
        <Route index element={<DashboardPage />} />
        <Route path="courses" element={<CoursesPage />} />
        <Route path="lessons" element={<LessonsPage />} />
        <Route path="assignments" element={<AssignmentsPage />} />
        <Route path="exams" element={<ExamsPage />} />
        <Route path="submissions" element={<SubmissionsPage />} />
        <Route path="grades" element={<GradesPage />} />
        <Route path="attendance" element={<AttendancePage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="messages" element={<MessagesPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="children" element={<ChildrenPage />} />
        <Route path="*" element={<EmptyPage title="Page not found" description="This workspace page is not available." />} />
      </Route>
      <Route path="*" element={<EmptyPage title="Page not found" description="The page you requested could not be found." />} />
    </Routes>
  )
}

export default App
