import type { ReactNode } from 'react'
import { Heading } from '@astryxdesign/core/Heading'
import { Text } from '@astryxdesign/core/Text'
import { VStack } from '@astryxdesign/core/VStack'

interface PageProps {
  eyebrow: string
  title: string
  description: string
  children: ReactNode
}

interface FeedbackProps {
  tone: 'error' | 'success'
  role: 'alert' | 'status'
  children: ReactNode
}

export function Page({ eyebrow, title, description, children }: PageProps) {
  return (
    <VStack as="section" className="page" gap={4}>
      <VStack as="header" className="page-heading" gap={1}>
        <Text as="p" color="accent" type="label">
          {eyebrow}
        </Text>
        <Heading level={1}>{title}</Heading>
        <Text as="p" color="secondary">
          {description}
        </Text>
      </VStack>
      {children}
    </VStack>
  )
}

export function Feedback({ tone, role, children }: FeedbackProps) {
  return (
    <Text as="p" className={`feedback feedback-${tone}`} role={role}>
      {children}
    </Text>
  )
}
