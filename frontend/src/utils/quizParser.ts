export interface QuizQuestion {
  number: number
  question: string
  options: {
    letter: string
    text: string
  }[]
  answer?: string
  explanation?: string
  detailedExplanation?: string
  hint?: string
}

export interface ParsedQuiz {
  questions: QuizQuestion[]
  hasQuiz: boolean
  introText?: string
  outroText?: string
}

/**
 * Cleans quiz content by removing preambles, special characters, and conversational text
 */
function cleanQuizContent(content: string): string {
  // Remove common preambles at the start
  const preamblePatterns = [
    /^(of course|i can|i'll|let me|sure|absolutely|definitely|i'd be happy|i'm happy|here you go|here's|ready to start|let's begin|let's do|let's go|my apologies|sorry|apologize)[\s\S]*?(\*\*Question\s+\d+:|Question\s+\d+)/i,
    /^[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}\-]+[\s\S]*?(\*\*Question\s+\d+:|Question\s+\d+)/iu,
    /^[^\w\*]*(\*\*Question\s+\d+:|Question\s+\d+)/i,
  ]
  
  let cleaned = content
  for (const pattern of preamblePatterns) {
    cleaned = cleaned.replace(pattern, (match) => {
      // Keep only the question part
      const questionMatch = match.match(/(\*\*Question\s+\d+:|Question\s+\d+)/i)
      return questionMatch ? questionMatch[0] : match
    })
  }
  
  // Remove emojis and decorative characters (using Unicode escapes)
  cleaned = cleaned.replace(/[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}\-]+/gu, '')
  
  // Remove lines that are just decorative dashes or separators
  cleaned = cleaned.replace(/^[-─━═]{3,}$/gm, '')
  
  return cleaned.trim()
}

/**
 * Parses quiz content from message text and extracts structured quiz data
 */
export function parseQuiz(content: string): ParsedQuiz {
  // Clean the content first
  const cleanedContent = cleanQuizContent(content)
  
  const result: ParsedQuiz = {
    questions: [],
    hasQuiz: false,
  }

  // Try to detect quiz patterns - be more lenient
  // Pattern 1: **Question N:** format (with or without bold)
  const questionPattern = /\*\*Question\s+(\d+):\*\*\s*(.+?)(?=\*\*Question\s+\d+:\*\*|\*\*Answer:|$)/gis
  // Pattern 2: Question N: format (without bold)
  const questionPatternAlt = /Question\s+(\d+):\s*(.+?)(?=Question\s+\d+:|Answer:|$)/gis
  // Pattern 3: Option patterns like "A) ", "B) ", etc. (case-insensitive)
  const optionPattern = /^([A-Da-d])\)\s*(.+)$/gmi
  // Pattern 4: Answer pattern (with or without bold)
  const answerPattern = /\*\*Answer:\*\*\s*([A-D])/gi
  const answerPatternAlt = /Answer:\s*([A-D])/gi

  // Check if content contains quiz-like patterns - be more lenient
  const hasQuestionMarkers = /\*\*Question\s+\d+:/i.test(cleanedContent) || /Question\s+\d+:/i.test(cleanedContent)
  // Check for options anywhere in the content (case-insensitive)
  const hasOptions = /^[A-Da-d]\)\s+/mi.test(cleanedContent)
  const hasAnswers = /Answer:\s*[A-Da-d]/i.test(cleanedContent)
  
  // If we have questions and options/answers, it's likely a quiz
  if (!hasQuestionMarkers || (!hasOptions && !hasAnswers)) {
    return result
  }

  // Extract intro text (everything before first question) - but filter out common preambles
  const firstQuestionMatch = cleanedContent.match(/\*\*Question\s+\d+:/i)
  if (firstQuestionMatch && firstQuestionMatch.index !== undefined) {
    const intro = cleanedContent.substring(0, firstQuestionMatch.index).trim()
    // Filter out common preambles and conversational text
    if (intro) {
      const preamblePatterns = [
        /^(of course|i can|i'll|let me|sure|absolutely|definitely|i'd be happy|i'm happy|here you go|here's|ready to start|let's begin|let's do|let's go)/i,
        /^(my apologies|sorry|apologize)/i,
        /^(quiz|question|answer|mcq|multiple choice)/i,
        /^[^\w]*$/, // Only special characters/emojis
        /^[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}]+/u, // Emoji-only
      ]
      
      const isPreamble = preamblePatterns.some(pattern => pattern.test(intro))
      const isTooShort = intro.length < 20 // Very short intros are likely noise
      
      if (!isPreamble && !isTooShort && intro.length > 0) {
        // Clean up special characters and emojis
        const cleaned = intro
          .replace(/[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}\-]+/gu, '') // Remove emojis and decorative dashes
          .replace(/^[^\w]+|[^\w]+$/g, '') // Remove leading/trailing special chars
          .trim()
        
        if (cleaned.length > 10) {
          result.introText = cleaned
        }
      }
    }
  }

  // Extract questions - try multiple patterns
  let match
  const questionMatches: Array<{ number: number; start: number; end: number; text: string }> = []
  
  // Try Pattern 1: **Question N:** format
  questionPattern.lastIndex = 0
  while ((match = questionPattern.exec(cleanedContent)) !== null) {
    questionMatches.push({
      number: parseInt(match[1], 10),
      start: match.index,
      end: match.index + match[0].length,
      text: match[2].trim(),
    })
  }

  // If no structured questions found, try Pattern 2: Question N: format (without bold)
  if (questionMatches.length === 0) {
    questionPatternAlt.lastIndex = 0
    while ((match = questionPatternAlt.exec(cleanedContent)) !== null) {
      questionMatches.push({
        number: parseInt(match[1], 10),
        start: match.index,
        end: match.index + match[0].length,
        text: match[2].trim(),
      })
    }
  }

  // If still no questions found, try alternative pattern: look for numbered questions
  if (questionMatches.length === 0) {
    // Use a simpler line-by-line approach to avoid complex regex
    const lines = cleanedContent.split('\n')
    let currentQuestion: { number: number; start: number; text: string; lineIndex: number } | null = null
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      // Check for question patterns
      const questionMatch = line.match(/^(\d+\.|\*\*Question\s+(\d+):\*\*|Question\s+(\d+):)\s*(.+)$/i)
      
      if (questionMatch) {
        // Save previous question if exists
        if (currentQuestion && currentQuestion.text.trim().length > 10) {
          const questionStart = lines.slice(0, currentQuestion.lineIndex).join('\n').length + (currentQuestion.lineIndex > 0 ? 1 : 0)
          questionMatches.push({
            number: currentQuestion.number,
            start: questionStart,
            end: questionStart + currentQuestion.text.length,
            text: currentQuestion.text.trim(),
          })
        }
        
        // Start new question
        const questionNum = parseInt(questionMatch[2] || questionMatch[3] || '1', 10)
        const questionText = questionMatch[4] || ''
        const questionStart = lines.slice(0, i).join('\n').length + (i > 0 ? 1 : 0)
        currentQuestion = {
          number: questionNum,
          start: questionStart,
          text: questionText,
          lineIndex: i
        }
      } else if (currentQuestion && line.trim() && !line.match(/^[A-Da-d]\)/i)) {
        // Continue building current question (until we hit options)
        currentQuestion.text += '\n' + line
      } else if (currentQuestion && line.match(/^[A-Da-d]\)/i)) {
        // Hit options, question is complete
        if (currentQuestion.text.trim().length > 10) {
          const questionStart = lines.slice(0, currentQuestion.lineIndex).join('\n').length + (currentQuestion.lineIndex > 0 ? 1 : 0)
          questionMatches.push({
            number: currentQuestion.number,
            start: questionStart,
            end: questionStart + currentQuestion.text.length,
            text: currentQuestion.text.trim(),
          })
        }
        currentQuestion = null
      }
    }
    
    // Add last question if exists
    if (currentQuestion && currentQuestion.text.trim().length > 10) {
      const questionStart = lines.slice(0, currentQuestion.lineIndex).join('\n').length + (currentQuestion.lineIndex > 0 ? 1 : 0)
      questionMatches.push({
        number: currentQuestion.number,
        start: questionStart,
        end: questionStart + currentQuestion.text.length,
        text: currentQuestion.text.trim(),
      })
    }
  }

  // Process each question
  for (let i = 0; i < questionMatches.length; i++) {
    const qMatch = questionMatches[i]
    const nextMatch = questionMatches[i + 1]
    const questionSection = cleanedContent.substring(
      qMatch.start,
      nextMatch ? nextMatch.start : cleanedContent.length
    )

    // Extract question text (remove question number marker and clean up)
    let questionText = qMatch.text
      .replace(/^\d+\.\s*/, '')
      .replace(/\*\*Question\s+\d+:\*\*\s*/i, '')
      .replace(/Question\s+\d+:\s*/i, '')
      .trim()
    
    // Remove any options that might be embedded in the question text
    // Look for patterns like "A) option B) option" at the end of the question
    questionText = questionText.replace(/\s*[A-D]\)\s*[^\n]*(?:\s+[A-D]\)\s*[^\n]*){0,3}\s*$/i, '').trim()
    
    // Also check if question text contains options on separate lines
    const questionLines = questionText.split('\n')
    const cleanQuestionLines: string[] = []
    for (const line of questionLines) {
      // Stop if we hit an option line
      if (line.trim().match(/^[A-Da-d]\)\s+/i)) {
        break
      }
      cleanQuestionLines.push(line)
    }
    questionText = cleanQuestionLines.join('\n').trim()

    // Extract options - try multiple patterns
    const options: { letter: string; text: string }[] = []
    
    // Pattern 1: Standard "A) text" format
    optionPattern.lastIndex = 0
    const optionMatches = questionSection.matchAll(optionPattern)
    for (const optMatch of optionMatches) {
      const optText = optMatch[2].trim()
      // Skip if it's part of the answer line
      if (!optText.match(/^(Answer|answer|Correct|correct)/i)) {
        options.push({
          letter: optMatch[1].toUpperCase(), // Normalize to uppercase
          text: optText,
        })
      }
    }

    // Pattern 2: If no options found, try "A. text" format (case-insensitive)
    if (options.length === 0) {
      const altOptionPattern = /^([A-Da-d])\.\s*(.+)$/gmi
      altOptionPattern.lastIndex = 0
      const altMatches = questionSection.matchAll(altOptionPattern)
      for (const optMatch of altMatches) {
        options.push({
          letter: optMatch[1].toUpperCase(), // Normalize to uppercase
          text: optMatch[2].trim(),
        })
      }
    }

    // Extract answer - try multiple patterns with improved matching
    let answer: string | undefined
    
    // Pattern 1: **Answer:** format (with optional whitespace/newlines)
    answerPattern.lastIndex = 0
    const answerMatch = questionSection.match(answerPattern)
    if (answerMatch && answerMatch[1]) {
      answer = answerMatch[1].toUpperCase().trim()
    } else {
      // Pattern 2: "Answer: A" format (without bold, with optional whitespace)
      answerPatternAlt.lastIndex = 0
      const altAnswerMatch = questionSection.match(answerPatternAlt)
      if (altAnswerMatch && altAnswerMatch[1]) {
        answer = altAnswerMatch[1].toUpperCase().trim()
      } else {
        // Pattern 3: Look for answer in the section more broadly (case-insensitive, multiline)
        // This handles cases where answer might be on a separate line
        const broadAnswerMatch = questionSection.match(/[Aa]nswer[:\s]*\n?\s*([A-Da-d])/i)
        if (broadAnswerMatch && broadAnswerMatch[1]) {
          answer = broadAnswerMatch[1].toUpperCase().trim()
        } else {
          // Pattern 4: Look for standalone answer lines (e.g., "Answer: A" on its own line)
          const lines = questionSection.split('\n')
          for (const line of lines) {
            const lineMatch = line.trim().match(/^(?:\*\*)?Answer:\s*\*?\*?\s*([A-Da-d])\s*$/i)
            if (lineMatch && lineMatch[1]) {
              answer = lineMatch[1].toUpperCase().trim()
              break
            }
          }
        }
      }
    }
    
    // Debug: Log if answer is found
    if (answer) {
      console.log(`✅ Found answer "${answer}" for question ${qMatch.number}`)
    } else {
      console.warn(`⚠️ No answer found for question ${qMatch.number}. Question section sample:`, questionSection.substring(0, 200))
    }

    // Only add if we have a valid question
    if (questionText.length > 5) {
      result.questions.push({
        number: qMatch.number,
        question: questionText,
        options: options.length > 0 ? options : [], // If no options found, leave empty
        answer,
      })
    }
  }

  // If we found questions, mark as quiz
  if (result.questions.length > 0) {
    result.hasQuiz = true
  }

  // Extract outro text (everything after last question) - but filter out noise
  if (result.questions.length > 0) {
    const lastQuestion = questionMatches[questionMatches.length - 1]
    const outro = cleanedContent.substring(lastQuestion.end).trim()
    
    if (outro) {
      // Filter out common outro phrases and noise
      const outroPatterns = [
        /^(answer|question|\*\*Answer)/i,
        /^(good luck|hope this helps|enjoy|have fun)/i,
        /^[^\w]*$/, // Only special characters
        /^[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}\-]+/u, // Emoji-only
      ]
      
      const isNoise = outroPatterns.some(pattern => pattern.test(outro))
      const isTooShort = outro.length < 20
      
      if (!isNoise && !isTooShort && outro.length > 0) {
        // Clean up special characters and emojis
        const cleaned = outro
          .replace(/[\u{1F44B}\u{1F3AF}\u{1F4DD}\u{1F4DA}\u{1F393}\u{1F4A1}\u{1F525}\u{2728}\u{1F389}\-]+/gu, '')
          .replace(/^[^\w]+|[^\w]+$/g, '')
          .trim()
        
        if (cleaned.length > 10) {
          result.outroText = cleaned
        }
      }
    }
  }

  return result
}

/**
 * Checks if content appears to be a quiz
 */
export function isQuizContent(content: string): boolean {
  const parsed = parseQuiz(content)
  return parsed.hasQuiz && parsed.questions.length > 0
}

