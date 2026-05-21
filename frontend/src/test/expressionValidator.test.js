import { describe, it, expect } from 'vitest'
import { validateBody } from '@/features/templates/expressionValidator'

describe('validateBody', () => {
  it('accepts a valid path expression', () => {
    expect(validateBody('Hola {{ project.cliente }}')).toEqual([])
  })

  it('accepts a known filter with correct arity', () => {
    expect(validateBody('{{ project.kwp | number(2) }}')).toEqual([])
    expect(validateBody('{{ project.name | upper }}')).toEqual([])
  })

  it('rejects a dunder / leading underscore identifier', () => {
    const errors = validateBody('{{ project.__class__ }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/atributo interno/i)
    expect(errors[0].expr).toBe('project.__class__')
  })

  it('rejects a leading underscore segment', () => {
    const errors = validateBody('{{ _secret }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/atributo interno/i)
  })

  it('rejects an unknown filter', () => {
    const errors = validateBody('{{ project.kwp | danger }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/desconocido/i)
  })

  it('rejects wrong filter arity', () => {
    const errors = validateBody('{{ project.name | upper(2) }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/no admite/i)
  })

  it('rejects an empty expression', () => {
    const errors = validateBody('{{ }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/vacía/i)
  })

  it('reports unbalanced delimiters', () => {
    const errors = validateBody('{{ project.cliente }')
    expect(errors).toHaveLength(1)
    expect(errors[0].message).toMatch(/balancear/i)
  })

  it('reports the position of the offending expression', () => {
    const errors = validateBody('ok {{ project.cliente }} bad {{ __x }}')
    expect(errors).toHaveLength(1)
    expect(errors[0].start).toBe(29)
  })
})
