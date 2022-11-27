#!/usr/bin/env node

import fse from 'fs-extra'
import path from 'path'

import root from '../root'
import version from '../version'

const GEN_DIR = 'gen'
const UPDATES_JSON_PATH = `${GEN_DIR}/updates.json`
const UPDATE_RDF_PATH = `${GEN_DIR}/update.rdf`

const [,, updateLink] = process.argv

if (!updateLink) {
  throw new Error('Update link must be provided as first argument')
}

const pkg = { ...require(path.join(root, 'package.json')) }

if (!pkg.id) {
  (pkg.id as string) = `${pkg.name.replace(
    /^zotero-/,
    ''
  )}@${pkg.author.email.replace(/.*@/, '')}`.toLowerCase()
}

console.log(`Generating ${UPDATES_JSON_PATH} and copying to ${UPDATE_RDF_PATH}`)

const updatesJson = {
  addons: {
    [pkg.id]: {
      updates: [
        {
          version,
          update_link: updateLink,
          applications: {
            gecko: {
              strict_min_version: '60.9',
              strict_max_version: '60.9',
            },
            ...(pkg.xpi.supportsZotero7 ? {
              zotero: {
                strict_min_version: '6.999',
                strict_max_version: '7.0.*',
              },
            } : null),
          },
        },
      ],
    },
  },
}

fse.outputJsonSync(
  path.join(root, UPDATES_JSON_PATH),
  updatesJson,
  { spaces: 2 }
)
fse.copySync(
  path.join(root, UPDATES_JSON_PATH),
  path.join(root, UPDATE_RDF_PATH)
)
