'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Plus, Edit, Trash2, Eye, EyeOff, LogOut } from 'lucide-react'
import type { Case } from '@/types'
import CaseForm from '@/components/admin/CaseForm'

export default function AdminCasesPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingCase, setEditingCase] = useState<Case | null>(null)

  const supabase = createBrowserClient()

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession()

    if (session) {
      setIsLoggedIn(true)
      loadCases()
    } else {
      setIsLoggedIn(false)
      setLoading(false)
    }
  }

  const loadCases = async () => {
    setLoading(true)
    const { data, error } = await supabase
      .from('cases')
      .select('*')
      .order('sort_order', { ascending: true })
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Error loading cases:', error)
      alert('事例の読み込みに失敗しました')
    } else {
      setCases(data || [])
    }
    setLoading(false)
  }

  const handleLogin = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      alert('ログインに失敗しました')
    } else {
      setIsLoggedIn(true)
      loadCases()
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setIsLoggedIn(false)
    setCases([])
  }

  const handleDelete = async (id: string) => {
    if (!confirm('この事例を削除してもよろしいですか？')) return

    const { error } = await supabase.from('cases').delete().eq('id', id)

    if (error) {
      alert('削除に失敗しました')
    } else {
      loadCases()
    }
  }

  const handleTogglePublish = async (caseItem: Case) => {
    const { error } = await supabase
      .from('cases')
      .update({ is_published: !caseItem.is_published })
      .eq('id', caseItem.id)

    if (error) {
      alert('更新に失敗しました')
    } else {
      loadCases()
    }
  }

  const handleEdit = (caseItem: Case) => {
    setEditingCase(caseItem)
    setShowForm(true)
  }

  const handleFormClose = () => {
    setShowForm(false)
    setEditingCase(null)
    loadCases()
  }

  if (!isLoggedIn) {
    return <LoginForm onLogin={handleLogin} />
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">読み込み中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold gradient-text">
            事例管理画面
          </h1>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            ログアウト
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Action Bar */}
        <div className="flex items-center justify-between mb-6">
          <p className="text-gray-600">
            全 {cases.length} 件の事例
          </p>
          <button
            onClick={() => {
              setEditingCase(null)
              setShowForm(true)
            }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="w-5 h-5" />
            新規作成
          </button>
        </div>

        {/* Cases List */}
        <div className="space-y-4">
          {cases.map((caseItem) => (
            <div
              key={caseItem.id}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-bold text-gray-900">
                      {caseItem.title}
                    </h3>
                    <span
                      className={`badge ${
                        caseItem.is_published
                          ? 'badge-success'
                          : 'bg-gray-200 text-gray-700'
                      }`}
                    >
                      {caseItem.is_published ? '公開中' : '非公開'}
                    </span>
                    <span className="text-sm text-gray-500">
                      並び順: {caseItem.sort_order}
                    </span>
                  </div>
                  <p className="text-sm text-primary-600 mb-2">
                    {caseItem.target}
                  </p>
                  <p className="text-gray-600 text-sm mb-3">
                    {caseItem.catch_copy}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {caseItem.tags.map((tag, idx) => (
                      <span key={idx} className="badge-primary text-xs">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => handleTogglePublish(caseItem)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title={caseItem.is_published ? '非公開にする' : '公開する'}
                  >
                    {caseItem.is_published ? (
                      <Eye className="w-5 h-5 text-green-600" />
                    ) : (
                      <EyeOff className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                  <button
                    onClick={() => handleEdit(caseItem)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="編集"
                  >
                    <Edit className="w-5 h-5 text-blue-600" />
                  </button>
                  <button
                    onClick={() => handleDelete(caseItem.id)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    title="削除"
                  >
                    <Trash2 className="w-5 h-5 text-red-600" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {cases.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg">
            <p className="text-gray-500 mb-4">まだ事例が登録されていません</p>
            <button
              onClick={() => setShowForm(true)}
              className="btn-primary"
            >
              最初の事例を作成
            </button>
          </div>
        )}
      </div>

      {/* Form Modal */}
      {showForm && (
        <CaseForm
          caseData={editingCase}
          onClose={handleFormClose}
        />
      )}
    </div>
  )
}

function LoginForm({ onLogin }: { onLogin: (email: string, password: string) => void }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(email, password)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-accent-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold gradient-text mb-2">
            管理画面ログイン
          </h1>
          <p className="text-gray-600">
            事例管理にアクセスするにはログインしてください
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="label">メールアドレス</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              required
            />
          </div>

          <div>
            <label className="label">パスワード</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
              required
            />
          </div>

          <button type="submit" className="w-full btn-primary">
            ログイン
          </button>
        </form>
      </div>
    </div>
  )
}
