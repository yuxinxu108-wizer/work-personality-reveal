import { defineConfig, loadEnv } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import {
  buildAiMaterialsRequest,
  buildDeepSeekChatPayload,
  createFallbackMaterials,
  normalizeAiMaterials,
} from './src/app/aiMaterials.js'


function figmaAssetResolver() {
  return {
    name: 'figma-asset-resolver',
    resolveId(id) {
      if (id.startsWith('figma:asset/')) {
        const filename = id.replace('figma:asset/', '')
        return path.resolve(__dirname, 'src/assets', filename)
      }
    },
  }
}

function aiMaterialsApi() {
  return {
    name: 'ai-materials-api',
    configureServer(server) {
      const env = loadEnv(server.config.mode, process.cwd(), '')
      const provider = (env.AI_PROVIDER || process.env.AI_PROVIDER || 'openai').toLowerCase()
      const openaiApiKey = env.OPENAI_API_KEY || process.env.OPENAI_API_KEY
      const openaiModel = env.OPENAI_MODEL || process.env.OPENAI_MODEL || 'gpt-5.4-mini'
      const deepseekApiKey = env.DEEPSEEK_API_KEY || process.env.DEEPSEEK_API_KEY
      const deepseekModel = env.DEEPSEEK_MODEL || process.env.DEEPSEEK_MODEL || 'deepseek-v4-flash'
      const deepseekBaseUrl = env.DEEPSEEK_BASE_URL || process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com'

      server.middlewares.use('/api/generate-materials', async (req, res) => {
        if (req.method !== 'POST') {
          res.statusCode = 405
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Method not allowed' }))
          return
        }

        try {
          const payload = await readJsonBody(req)
          const request = buildAiMaterialsRequest(payload)

          if (provider === 'deepseek' && !deepseekApiKey) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({
              error: '缺少 DEEPSEEK_API_KEY。请在 .env.local 中设置后重启 dev server。',
              fallback: normalizeAiMaterials(createFallbackMaterials(request)),
            }))
            return
          }

          if (provider !== 'deepseek' && !openaiApiKey) {
            res.statusCode = 500
            res.setHeader('Content-Type', 'application/json')
            res.end(JSON.stringify({
              error: '缺少 OPENAI_API_KEY。请在 .env.local 中设置后重启 dev server。',
              fallback: normalizeAiMaterials(createFallbackMaterials(request)),
            }))
            return
          }

          const result = provider === 'deepseek'
            ? await generateWithDeepSeek({
                apiKey: deepseekApiKey,
                baseUrl: deepseekBaseUrl,
                model: deepseekModel,
                request,
              })
            : await generateWithOpenAI({
                apiKey: openaiApiKey,
                model: openaiModel,
                request,
              })

          res.statusCode = 200
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({
            materials: normalizeAiMaterials(result.parsed),
            model: result.model,
            provider,
          }))
        } catch (error) {
          res.statusCode = 500
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({
            error: error instanceof Error ? error.message : 'AI 生成失败',
          }))
        }
      })
    },
  }
}

const statusSchema = {
  type: 'string',
  enum: ['sufficient', 'needs-more', 'not-recommended'],
}

const resumeBulletSchema = {
  type: 'object',
  additionalProperties: false,
  required: ['text', 'status', 'note'],
  properties: {
    text: { type: 'string' },
    status: statusSchema,
    note: { type: 'string' },
  },
}

const aiMaterialsSchema = {
  type: 'object',
  additionalProperties: false,
  required: [
    'fitScore',
    'overallComment',
    'summaryCards',
    'followUpQuestions',
    'matchReport',
    'portfolio',
    'resumeOptimized',
    'resumeRaw',
    'interview',
  ],
  properties: {
    fitScore: { type: 'number' },
    overallComment: { type: 'string' },
    summaryCards: {
      type: 'array',
      minItems: 3,
      maxItems: 3,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['label', 'title', 'detail', 'status'],
        properties: {
          label: { type: 'string' },
          title: { type: 'string' },
          detail: { type: 'string' },
          status: statusSchema,
        },
      },
    },
    followUpQuestions: {
      type: 'array',
      minItems: 5,
      maxItems: 5,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['question', 'hint'],
        properties: {
          question: { type: 'string' },
          hint: { type: 'string' },
        },
      },
    },
    matchReport: {
      type: 'array',
      minItems: 4,
      maxItems: 6,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['ability', 'status', 'evidence', 'suggestion'],
        properties: {
          ability: { type: 'string' },
          status: statusSchema,
          evidence: { type: 'string' },
          suggestion: { type: 'string' },
        },
      },
    },
    portfolio: {
      type: 'array',
      minItems: 4,
      maxItems: 5,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['section', 'items', 'status'],
        properties: {
          section: { type: 'string' },
          items: {
            type: 'array',
            minItems: 2,
            maxItems: 5,
            items: { type: 'string' },
          },
          status: statusSchema,
        },
      },
    },
    resumeOptimized: {
      type: 'array',
      minItems: 3,
      maxItems: 5,
      items: resumeBulletSchema,
    },
    resumeRaw: {
      type: 'array',
      minItems: 3,
      maxItems: 5,
      items: resumeBulletSchema,
    },
    interview: {
      type: 'array',
      minItems: 4,
      maxItems: 4,
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['part', 'content', 'status', 'tip'],
        properties: {
          part: { type: 'string' },
          content: { type: 'string' },
          status: statusSchema,
          tip: { type: 'string' },
        },
      },
    },
  },
}

async function generateWithOpenAI({ apiKey, model, request }) {
  const response = await fetch('https://api.openai.com/v1/responses', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      input: [
        {
          role: 'system',
          content:
            '你是一个严谨的中文产品/运营实习求职材料助手。只根据用户提供的信息生成材料，不编造数据，不夸大经历。返回必须是合法 JSON。',
        },
        {
          role: 'user',
          content: JSON.stringify(request),
        },
      ],
      text: {
        format: {
          type: 'json_schema',
          name: 'internship_materials',
          strict: true,
          schema: aiMaterialsSchema,
        },
      },
      max_output_tokens: 5000,
    }),
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data?.error?.message || `OpenAI request failed: ${response.status}`)
  }

  return {
    parsed: JSON.parse(extractResponseText(data)),
    model,
  }
}

async function generateWithDeepSeek({ apiKey, baseUrl, model, request }) {
  const response = await fetch(`${baseUrl.replace(/\/$/, '')}/chat/completions`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildDeepSeekChatPayload({ model, request })),
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data?.error?.message || `DeepSeek request failed: ${response.status}`)
  }

  const content = data?.choices?.[0]?.message?.content
  if (typeof content !== 'string' || !content.trim()) {
    throw new Error('DeepSeek 返回为空')
  }

  return {
    parsed: JSON.parse(stripJsonFence(content)),
    model,
  }
}

function stripJsonFence(value) {
  return value
    .trim()
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/\s*```$/i, '')
    .trim()
}

function extractResponseText(data) {
  if (typeof data.output_text === 'string') return data.output_text

  const chunks = []
  for (const output of data.output || []) {
    for (const content of output.content || []) {
      if (typeof content.text === 'string') chunks.push(content.text)
    }
  }
  return chunks.join('')
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = ''
    req.on('data', (chunk) => {
      body += chunk
    })
    req.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {})
      } catch (error) {
        reject(error)
      }
    })
    req.on('error', reject)
  })
}

export default defineConfig({
  plugins: [
    aiMaterialsApi(),
    figmaAssetResolver(),
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],
})
