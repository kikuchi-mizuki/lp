import { redirect } from 'next/navigation'

// ルートパスは /consultation にリダイレクト
export default function Home() {
  redirect('/consultation')
}
