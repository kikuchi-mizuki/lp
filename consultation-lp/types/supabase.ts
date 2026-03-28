export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      cases: {
        Row: {
          id: string
          title: string
          target: string
          catch_copy: string
          before_problem: string
          solution: string
          result: string
          detail_text: string | null
          thumbnail_url: string | null
          video_url: string | null
          tags: string[]
          sort_order: number
          is_published: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          title: string
          target: string
          catch_copy: string
          before_problem: string
          solution: string
          result: string
          detail_text?: string | null
          thumbnail_url?: string | null
          video_url?: string | null
          tags?: string[]
          sort_order?: number
          is_published?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          title?: string
          target?: string
          catch_copy?: string
          before_problem?: string
          solution?: string
          result?: string
          detail_text?: string | null
          thumbnail_url?: string | null
          video_url?: string | null
          tags?: string[]
          sort_order?: number
          is_published?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      consultation_leads: {
        Row: {
          id: string
          company_name: string
          name: string
          email: string
          phone: string | null
          inquiry: string
          created_at: string
        }
        Insert: {
          id?: string
          company_name: string
          name: string
          email: string
          phone?: string | null
          inquiry: string
          created_at?: string
        }
        Update: {
          id?: string
          company_name?: string
          name?: string
          email?: string
          phone?: string | null
          inquiry?: string
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}
