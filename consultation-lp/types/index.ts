import { Database } from './supabase'

// 型エイリアス
export type Case = Database['public']['Tables']['cases']['Row']
export type CaseInsert = Database['public']['Tables']['cases']['Insert']
export type CaseUpdate = Database['public']['Tables']['cases']['Update']

export type ConsultationLead = Database['public']['Tables']['consultation_leads']['Row']
export type ConsultationLeadInsert = Database['public']['Tables']['consultation_leads']['Insert']

// フォームデータ型
export interface ConsultationFormData {
  company_name: string
  name: string
  email: string
  phone?: string
  inquiry: string
}

// よくある質問の型
export interface FAQ {
  question: string
  answer: string
}

// よくある悩みの型
export interface CommonProblem {
  title: string
  description: string
  icon: string
}
