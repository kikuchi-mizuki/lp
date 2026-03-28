import Header from '@/components/shared/Header'
import Footer from '@/components/shared/Footer'
import HeroSection from '@/components/consultation/HeroSection'
import ProblemsSection from '@/components/consultation/ProblemsSection'
import CasesSection from '@/components/consultation/CasesSection'
import FAQSection from '@/components/consultation/FAQSection'
import ContactForm from '@/components/consultation/ContactForm'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: '業務改善無料相談 | AIコレクションズ',
  description:
    'AIや自動化で業務を改善したいけど、何から始めればいいかわからない方へ。あなたの業務に合った改善方法を無料で整理します。無理な営業なし、まずは無料相談から。',
}

export default function ConsultationPage() {
  return (
    <>
      <Header />
      <main>
        <HeroSection />
        <ProblemsSection />
        <CasesSection />
        <FAQSection />

        {/* Contact Section */}
        <section id="contact" className="section-container bg-gradient-to-br from-primary-50 via-white to-accent-50">
          <div className="text-center mb-12">
            <h2 className="section-heading">
              まずは<span className="gradient-text">無料相談</span>から
            </h2>
            <p className="section-subheading">
              現状の業務について、お気軽にご相談ください
              <br />
              無理な営業は一切ありません
            </p>
          </div>
          <ContactForm />
        </section>
      </main>
      <Footer />
    </>
  )
}
