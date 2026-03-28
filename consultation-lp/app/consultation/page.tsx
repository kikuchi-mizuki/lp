import ConsultationLanding from '@/components/consultation/ConsultationLanding'
import { consultationMetadata } from '@/lib/consultationMetadata'

export const metadata = consultationMetadata

export default function ConsultationPage() {
  return <ConsultationLanding />
}
